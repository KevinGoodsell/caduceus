# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.
'''
Python versions of STAF APIs.
'''

from __future__ import with_statement

import ctypes

from . import _api
from ._errors import errors, strerror, STAFResultError
from ._marshall import UNMARSHALL_RECURSIVE

# Submit modes (from STAF.h, STAFSyncOption_e)
REQ_SYNC            = 0
REQ_FIRE_AND_FORGET = 1
REQ_QUEUE           = 2
REQ_RETAIN          = 3
REQ_QUEUE_RETAIN    = 4

#########################
# The main STAF interface
#########################

class Handle(object):
    '''
    Represents a STAF handle, used for most STAF interactions. Use as a context
    manager to automatically unregister the handle.
    '''

    def __init__(self, name):
        '''
        Create a Handle. If 'name' is a string, it is used as the name for
        registering the handle. If 'name' is an integer then it must be the
        number of a previously registered static handle. Note that static
        handles don't get unregistered, even if you call unregister().
        '''
        if isinstance(name, basestring):
            handle = _api.Handle_t()
            _api.RegisterUTF8(name, ctypes.byref(handle))
            self._handle = handle.value
            self._static = False
        else:
            self._handle = name
            self._static = True

        self._registered = True

    def submit(self, where, service, request, sync_option=REQ_SYNC,
               unmarshall=UNMARSHALL_RECURSIVE):
        '''
        Send a command to a STAF service. Arguments work mostly like the
        Submit2UTF8 C API. See the STAF package documentation for full details.
        '''
        from ._marshall import unmarshall as f_unmarshall

        request = self._build_request(request).encode('utf-8')
        result_ptr = ctypes.POINTER(ctypes.c_char)()
        result_len = ctypes.c_uint()
        try:
            rc = _api.Submit2UTF8(self._handle, sync_option, where, service,
                                  request, len(request),
                                  ctypes.byref(result_ptr),
                                  ctypes.byref(result_len))

            if result_len.value > 0:
                result = result_ptr[:result_len.value].decode('utf-8')
            else:
                result = ''

            if rc != 0:
                raise STAFResultError(rc, strerror(rc), result or None)

            return f_unmarshall(result, unmarshall)

        finally:
            # Need to free result_ptr even when rc indicates an error.
            if result_ptr:
                _api.Free(self._handle, result_ptr)

    @classmethod
    def _build_request(cls, request):
        if isinstance(request, basestring):
            return request

        result = []
        on_name = True
        # look for alternating "option name", "option value". The latter needs
        # to be wrapped, the former cannot be.
        for piece in request:
            if on_name:
                result.append(piece)
            else:
                result.append(wrap_data(piece))

            on_name = not on_name

        return " ".join(result)

    def unregister(self):
        '''
        Unregister the handle. For static handles this is a no-op. The error
        HandleDoesNotExist is ignored, since this indicates that the handle
        isn't registered, which is the requested state.
        '''
        if not self._static:
            try:
                _api.UnRegister(self._handle)
            except STAFResultError, exc:
                # If the handle isn't registered, we got what we wanted. This
                # could happen if the STAF server restarts.
                if exc.rc != errors.HandleDoesNotExist:
                    raise

            self._registered = False

    def handle_num(self):
        '''
        Returns the handle number.
        '''
        return self._handle

    def is_static(self):
        '''
        Returns true if the handle is static, false otherwise.
        '''
        return self._static

    def is_registered(self):
        '''
        Returns true if the handle is registered, false if it has been
        unregistered.
        '''
        return self._registered

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.unregister()

        # Don't suppress an exception
        return False

    def __repr__(self):
        if self._registered:
            closed = ''
        else:
            closed = ' (unregistered)'

        if self._static:
            static = 'Static '
        else:
            static = ''

        return '<STAF %sHandle %d%s>' % (static, self._handle, closed)


def wrap_data(data):
    '''
    Make a colon-length-colon-prefixed string suitable for use as a single
    service option value in a submit() call.
    '''
    # Note that the colon-length-colon-data format uses the length in
    # characters, not bytes.
    return ':%d:%s' % (len(data), data)

###################
# Private data APIs
###################

def _string_translate(data, translator):
    # contextlib.nested can't handle errors in object construction.
    with _api.String(data) as instr:
        with _api.String() as result:
            translator(instr, result.byref())
            return unicode(result)

def add_privacy_delimiters(data):
    '''
    Encloses the given string in privacy delimiters, identifying it as a section
    that should be masked when displayed. E.g., for passwords.
    '''
    return _string_translate(data, _api.AddPrivacyDelimiters)

def remove_privacy_delimiters(data, num_levels=0):
    '''
    Removes privacy delimiters from the given string. By default this is done
    repeatedly until no privacy delimiters remain. Alternatively, num_levels
    gives the number of levels of delimiters to remove.
    '''
    def translator(instr, outstr):
        return _api.RemovePrivacyDelimiters(instr, num_levels, outstr)

    return _string_translate(data, translator)

def mask_private_data(data):
    '''
    Replaces private data in the given string with asterisks.
    '''
    return _string_translate(data, _api.MaskPrivateData)

def escape_privacy_delimiters(data):
    '''
    Escapes any privacy delimiters in the given string. This prevents them from
    being interpreted as privacy delimiters when displayed by commands that hide
    private data.
    '''
    return _string_translate(data, _api.EscapePrivacyDelimiters)
