# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

from __future__ import with_statement

import ctypes

from . import _api
from ._errors import errors, strerror, STAFResultError
from ._marshal import unmarshal_recursive

#########################
# The main STAF interface
#########################

class Handle(object):
    # Submit modes (from STAF.h, STAFSyncOption_e)
    req_sync            = 0
    req_fire_and_forget = 1
    req_queue           = 2
    req_retain          = 3
    req_queue_retain    = 4

    def __init__(self, name):
        if isinstance(name, basestring):
            handle = _api.Handle_t()
            _api.RegisterUTF8(name, ctypes.byref(handle))
            self._handle = handle.value
            self._static = False
        else:
            self._handle = name
            self._static = True

    def submit(self, where, service, request, sync_option=req_sync,
               unmarshal=unmarshal_recursive):
        '''
        Send a command to a STAF service. Arguments work mostly like the
        Submit2UTF8 C API. Unmarshaling is done automatically unless otherwise
        specified. 'request' can be a string like the C API, or it can be a
        sequence. As a sequence of strings, the strings alternate between option
        names and values. Multiple option names can be combined into a single
        string. This avoids the need to escape or wrap values.
        '''
        from ._marshal import unmarshal as f_unmarshal

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

            return f_unmarshal(result, unmarshal)

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
        if not self._static:
            try:
                _api.UnRegister(self._handle)
            except STAFResultError, exc:
                # If the handle isn't registered, we got what we wanted. This
                # could happen if the STAF server restarts.
                if exc.rc != errors.HandleDoesNotExist:
                    raise

            self._handle = 0

    def handle_num(self):
        return self._handle

    def is_static(self):
        return self._static

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.unregister()

        # Don't supress an exception
        return False

    def __repr__(self):
        if self._static:
            static = 'Static '
        else:
            static = ''
        return '<STAF %sHandle %d>' % (static, self._handle)


def wrap_data(data):
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
    return _string_translate(data, _api.AddPrivacyDelimiters)

def remove_privacy_delimiters(data, num_levels=0):
    def translator(instr, outstr):
        return _api.RemovePrivacyDelimiters(instr, num_levels, outstr)

    return _string_translate(data, translator)

def mask_private_data(data):
    return _string_translate(data, _api.MaskPrivateData)

def escape_privacy_delimiters(data):
    return _string_translate(data, _api.EscapePrivacyDelimiters)
