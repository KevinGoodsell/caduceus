# XXX Missing:
# * Windows support
# * Unmarshalling
# * Additional APIs
#   - Private data manipulation
# * Support a sequence for request


import warnings
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
            raise STAFError.from_rc(result)

    # Types
    Handle_t = ctypes.c_uint     # From STAF.h
    SyncOption_t = ctypes.c_uint # From STAF.h
    RC_t = ctypes.c_uint         # From STAFError.h

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
    def __init__(self, args):
        super(STAFError, self).__init__(args)

        self.rc = None
        self.errstr = None
        if isinstance(args, tuple) and len(args) == 2:
            self.rc = args[0]
            self.errstr = args[1]

    @classmethod
    def from_rc(cls, rc):
        msg = strerror(rc)
        return cls((rc, msg))


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
            _StafApi.UnRegister(self._handle)
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
