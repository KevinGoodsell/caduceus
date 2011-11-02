# XXX Missing:
# * Windows support
# * Unmarshalling
# * Support a sequence for request

import ctypes

########################
# Interface to the C API
########################

class _StafApi(object):
    '''
    Container for libSTAF wrappers.
    '''
    _staf = ctypes.cdll.LoadLibrary('libSTAF.so')

    # errcheck function
    def check_rc(result, func, arguments):
        if result != 0:
            raise STAFError(result)

    # Types
    Handle_t = ctypes.c_uint     # From STAF.h
    SyncOption_t = ctypes.c_uint # From STAF.h
    RC_t = ctypes.c_uint         # From STAFError.h
    # From STAFString.h:
    class StringImplementation(ctypes.Structure):
        # Incomplete type
        pass
    String_t = ctypes.POINTER(StringImplementation)

    class Utf8(object):
        @classmethod
        def from_param(cls, text):
            return text.encode('utf-8')

    # Functions
    RegisterUTF8 = _staf.STAFRegisterUTF8
    RegisterUTF8.argtypes = (Utf8, ctypes.POINTER(Handle_t))
    RegisterUTF8.restype = RC_t
    RegisterUTF8.errcheck = check_rc

    UnRegister = _staf.STAFUnRegister
    UnRegister.argtypes = (Handle_t,)
    UnRegister.restype = RC_t
    UnRegister.errcheck = check_rc

    Submit2UTF8 = _staf.STAFSubmit2UTF8
    Submit2UTF8.argtypes = (
        Handle_t,                       # handle
        SyncOption_t,                   # syncOption
        Utf8,                           # where
        Utf8,                           # service
        ctypes.POINTER(ctypes.c_char),  # request
        ctypes.c_uint,                  # requestLength
        ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), # resultPtr
        ctypes.POINTER(ctypes.c_uint),  # resultLength
    )
    Submit2UTF8.restype = RC_t
    Submit2UTF8.errcheck = check_rc

    Free = _staf.STAFFree
    Free.argtypes = (Handle_t, ctypes.POINTER(ctypes.c_char))
    Free.restype = RC_t
    Free.errcheck = check_rc

    # STAFString APIs:
    StringConstruct = _staf.STAFStringConstruct
    StringConstruct.argtypes = (
        ctypes.POINTER(String_t),      # pString
        ctypes.POINTER(ctypes.c_char), # buffer
        ctypes.c_uint,                 # len
        ctypes.POINTER(ctypes.c_uint), # osRC
    )
    StringConstruct.restype = RC_t
    StringConstruct.errcheck = check_rc

    StringGetBuffer = _staf.STAFStringGetBuffer
    StringGetBuffer.argtypes = (
        String_t,                                      # aString
        ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), # buffer
        ctypes.POINTER(ctypes.c_uint),                 # len
        ctypes.POINTER(ctypes.c_uint),                 # osRC
    )
    StringGetBuffer.restype = RC_t
    StringGetBuffer.errcheck = check_rc

    StringDestruct = _staf.STAFStringDestruct
    StringDestruct.argtypes = (ctypes.POINTER(String_t),
                               ctypes.POINTER(ctypes.c_uint))
    StringDestruct.restype = RC_t
    StringDestruct.errcheck = check_rc

    # Private data APIs:
    AddPrivacyDelimiters = _staf.STAFAddPrivacyDelimiters
    AddPrivacyDelimiters.argtypes = (String_t, ctypes.POINTER(String_t))
    AddPrivacyDelimiters.restype = RC_t
    AddPrivacyDelimiters.errcheck = check_rc

    RemovePrivacyDelimiters = _staf.STAFRemovePrivacyDelimiters
    RemovePrivacyDelimiters.argtypes = (String_t, ctypes.c_uint,
                                        ctypes.POINTER(String_t))
    RemovePrivacyDelimiters.restype = RC_t
    RemovePrivacyDelimiters.errcheck = check_rc

    MaskPrivateData = _staf.STAFMaskPrivateData
    MaskPrivateData.argtypes = (String_t, ctypes.POINTER(String_t))
    MaskPrivateData.restype = RC_t
    MaskPrivateData.errcheck = check_rc

    EscapePrivacyDelimiters = _staf.STAFEscapePrivacyDelimiters
    EscapePrivacyDelimiters.argtypes = (String_t, ctypes.POINTER(String_t))
    EscapePrivacyDelimiters.restype = RC_t
    EscapePrivacyDelimiters.errcheck = check_rc

# Wrapper for String_t
class _String(object):
    def __init__(self, data=None):
        self._as_parameter_ = _StafApi.String_t()

        if data is None:
            return

        try:
            utf8 = data.encode('utf-8')
            _StafApi.StringConstruct(ctypes.byref(self._as_parameter_), utf8,
                                     len(utf8), None)
        except:
            self.destroy()
            raise

    def byref(self):
        return ctypes.byref(self._as_parameter_)

    def destroy(self):
        if self._as_parameter_:
            _StafApi.StringDestruct(ctypes.byref(self._as_parameter_), None)

    def __nonzero__(self):
        return bool(self._as_parameter_)

    def __unicode__(self):
        buf = ctypes.POINTER(ctypes.c_char)()
        length = ctypes.c_uint()
        _StafApi.StringGetBuffer(self, ctypes.byref(buf), ctypes.byref(length),
                                 None)
        result = buf[:length.value]
        return result.decode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.destroy()

        # Don't supress an exception
        return False

#################################
# Error handling, codes, messages
#################################

# Only for internal use
_return_codes = [
    ('Ok',                          'No error'),
    ('InvalidAPI',                  'Invalid API'),
    ('UnknownService',              'Unknown service'),
    ('InvalidHandle',               'Invalid handle'),
    ('HandleAlreadyExists',         'Handle already exists'),
    ('HandleDoesNotExist',          'Handle does not exist'),
    ('UnknownError',                'Unknown error'),
    ('InvalidRequestString',        'Invalid request string'),
    ('InvalidServiceResult',        'Invalid service result'),
    ('REXXError',                   'REXX Error'),
    ('BaseOSError',                 'Base operating system error'),
    ('ProcessAlreadyComplete',      'Process already complete'),
    ('ProcessNotComplete',          'Process not complete'),
    ('VariableDoesNotExist',        'Variable does not exist'),
    ('UnResolvableString',          'Unresolvable string'),
    ('InvalidResolveString',        'Invalid resolve string'),
    ('NoPathToMachine',             'No path to endpoint'),
    ('FileOpenError',               'File open error'),
    ('FileReadError',               'File read error'),
    ('FileWriteError',              'File write error'),
    ('FileDeleteError',             'File delete error'),
    ('STAFNotRunning',              'STAF not running'),
    ('CommunicationError',          'Communication error'),
    ('TrusteeDoesNotExist',         'Trusteee does not exist'),
    ('InvalidTrustLevel',           'Invalid trust level'),
    ('AccessDenied',                'Insufficient trust level'),
    ('STAFRegistrationError',       'Registration error'),
    ('ServiceConfigurationError',   'Service configuration error'),
    ('QueueFull',                   'Queue full'),
    ('NoQueueElement',              'No queue element'),
    ('NotifieeDoesNotExist',        'Notifiee does not exist'),
    ('InvalidAPILevel',             'Invalid API level'),
    ('ServiceNotUnregisterable',    'Service not unregisterable'),
    ('ServiceNotAvailable',         'Service not available'),
    ('SemaphoreDoesNotExist',       'Semaphore does not exist'),
    ('NotSemaphoreOwner',           'Not semaphore owner'),
    ('SemaphoreHasPendingRequests', 'Semaphore has pending requests'),
    ('Timeout',                     'Timeout'),
    ('JavaError',                   'Java error'),
    ('ConverterError',              'Converter error'),
    ('MoveError',                   'Move error'),
    ('InvalidObject',               'Invalid object'),
    ('InvalidParm',                 'Invalid parm'),
    ('RequestNumberNotFound',       'Request number not found'),
    ('InvalidAsynchOption',         'Invalid asynchronous option'),
    ('RequestNotComplete',          'Request not complete'),
    ('ProcessAuthenticationDenied', 'Process authentication denied'),
    ('InvalidValue',                'Invalid value'),
    ('DoesNotExist',                'Does not exist'),
    ('AlreadyExists',               'Already exists'),
    ('DirectoryNotEmpty',           'Directory Not Empty'),
    ('DirectoryCopyError',          'Directory Copy Error'),
    ('DiagnosticsNotEnabled',       'Diagnostics Not Enabled'),
    ('HandleAuthenticationDenied',  'Handle Authentication Denied'),
    ('HandleAlreadyAuthenticated',  'Handle Already Authenticated'),
    ('InvalidSTAFVersion',          'Invalid STAF Version'),
    ('RequestCancelled',            'Request Cancelled'),
    ('CreateThreadError',           'Create Thread Error'),
    ('MaximumSizeExceeded',         'Maximum Size Exceeded'),
    ('MaximumHandlesExceeded',      'Maximum Handles Exceeded'),
    ('NotRequester',                'Not Pending Requester'),
]

class errors(object):
    '''
    Holds constants for STAF errors.
    '''
    for (i, (name, description)) in enumerate(_return_codes):
        locals()[name] = i

    del i
    del name
    del description

def strerror(rc):
    try:
        return _return_codes[rc][1]
    except IndexError:
        return None

class STAFError(Exception):
    # This is modelled after EnvironmentError.
    def __init__(self, *args):
        super(STAFError, self).__init__(*args)

        self.rc = None
        self.strerror = None
        if len(args) == 1:
            self.rc = args[0]
            self.strerror = strerror(self.rc)
        elif len(args) == 2:
            self.rc = args[0]
            self.strerror = args[1]


#########################
# The main STAF interface
#########################

class Handle(object):
    # Submit modes
    Sync          = 0
    FireAndForget = 1
    Queue         = 2
    Retain        = 3
    QueueRetain   = 4

    def __init__(self, name):
        if isinstance(name, basestring):
            handle = _StafApi.Handle_t()
            _StafApi.RegisterUTF8(name, ctypes.byref(handle))
            self._handle = handle.value
            self._static = False
        else:
            self._handle = name
            self._static = True

    def submit(self, where, service, request, sync_option=Sync,
               unmarshal=True):
        request = request.encode('utf-8')
        result_ptr = ctypes.POINTER(ctypes.c_char)()
        result_len = ctypes.c_uint()
        try:
            _StafApi.Submit2UTF8(self._handle, sync_option, where, service,
                                 request, len(request),
                                 ctypes.byref(result_ptr),
                                 ctypes.byref(result_len))
            result = result_ptr[:result_len.value]
            return result.decode('utf-8')
        finally:
            # Need to free result_ptr even when rc indicates an error.
            if result_ptr:
                _StafApi.Free(self._handle, result_ptr)

    def unregister(self):
        if not self._static:
            try:
                _StafApi.UnRegister(self._handle)
            except STAFError, exc:
                # If the handle isn't registered, we got what we wanted. This
                # could happen if the STAF server restarts.
                if exc.rc != errors.HandleDoesNotExist:
                    raise

            self._handle = 0

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

###################
# Private data APIs
###################

def _string_translate(data, translator):
    # contextlib.nested can't handle errors in object construction.
    with _String(data) as instr:
        with _String() as result:
            translator(instr, result.byref())
            return unicode(result)

def add_privacy_delimiters(data):
    return _string_translate(data, _StafApi.AddPrivacyDelimiters)

def remove_privacy_delimiters(data, num_levels=0):
    def translator(instr, outstr):
        return _StafApi.RemovePrivacyDelimiters(instr, num_levels, outstr)

    return _string_translate(data, translator)

def mask_private_data(data):
    return _string_translate(data, _StafApi.MaskPrivateData)

def escape_privacy_delimiters(data):
    return _string_translate(data, _StafApi.EscapePrivacyDelimiters)
