# XXX Missing Windows support

import warnings
import ctypes

class STAFException(Exception):
    def __init__(self, rc=0, result=''):
        self.rc = rc
        self.result = result

    def __str__(self):
        return '[RC %d] %s' % (self.rc, self.result)


class _StafApi(object):
    '''
    Container for libSTAF wrappers.
    '''
    _staf = ctypes.cdll.LoadLibrary('libSTAF.so')

    # errcheck function
    def check_rc(result, func, arguments):
        if result != 0:
            raise STAFException(result)

    # Types
    Handle_t = ctypes.c_uint     # From STAF.h
    SyncOption_t = ctypes.c_uint # From STAF.h
    RC_t = ctypes.c_uint         # From STAFError.h

    # Functions
    RegisterUTF8 = _staf.STAFRegisterUTF8
    RegisterUTF8.argtypes = (ctypes.c_char_p, ctypes.POINTER(Handle_t))
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
        ctypes.c_char_p,                # where
        ctypes.c_char_p,                # service
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


class STAFResult(object):
    Ok                          = 0
    InvalidAPI                  = 1
    UnknownService              = 2
    InvalidHandle               = 3
    HandleAlreadyExists         = 4
    HandleDoesNotExist          = 5
    UnknownError                = 6
    InvalidRequestString        = 7
    InvalidServiceResult        = 8
    REXXError                   = 9
    BaseOSError                 = 10
    ProcessAlreadyComplete      = 11
    ProcessNotComplete          = 12
    VariableDoesNotExist        = 13
    UnResolvableString          = 14
    InvalidResolveString        = 15
    NoPathToMachine             = 16
    FileOpenError               = 17
    FileReadError               = 18
    FileWriteError              = 19
    FileDeleteError             = 20
    STAFNotRunning              = 21
    CommunicationError          = 22
    TrusteeDoesNotExist         = 23
    InvalidTrustLevel           = 24
    AccessDenied                = 25
    STAFRegistrationError       = 26
    ServiceConfigurationError   = 27
    QueueFull                   = 28
    NoQueueElement              = 29
    NotifieeDoesNotExist        = 30
    InvalidAPILevel             = 31
    ServiceNotUnregisterable    = 32
    ServiceNotAvailable         = 33
    SemaphoreDoesNotExist       = 34
    NotSemaphoreOwner           = 35
    SemaphoreHasPendingRequests = 36
    Timeout                     = 37
    JavaError                   = 38
    ConverterError              = 39
    MoveError                   = 40
    InvalidObject               = 41
    InvalidParm                 = 42
    RequestNumberNotFound       = 43
    InvalidAsynchOption         = 44
    RequestNotComplete          = 45
    ProcessAuthenticationDenied = 46
    InvalidValue                = 47
    DoesNotExist                = 48
    AlreadyExists               = 49
    DirectoryNotEmpty           = 50
    DirectoryCopyError          = 51
    DiagnosticsNotEnabled       = 52
    HandleAuthenticationDenied  = 53
    HandleAlreadyAuthenticated  = 54
    InvalidSTAFVersion          = 55
    RequestCancelled            = 56
    CreateThreadError           = 57
    MaximumSizeExceeded         = 58
    MaximumHandlesExceeded      = 59
    NotRequester                = 60

    def __init__(self, rc=0, result='', doUnmarshallResult=False):
        self.rc = rc
        self.result = result
        if doUnmarshallResult:
            # XXX unmarshall doesn't exist yet.
            self.resultContext = unmarshall(self.result)
            self.resultObj = self.resultContext.getRootObject()
        else:
            self.resultContext = None
            self.resultObj = None

    def __repr__(self):
        if len(self.result) > 40:
            result = repr(self.result[:40]) + '...'
        else:
            result = repr(self.result)

        return '<%s rc=%d result=%s>' % (self.__class__.__name__, self.rc,
                                         result)


class STAFHandle(object):
    # Handle types
    Standard = 0
    Static   = 1

    # Submit modes
    Synchronous   = 0
    FireAndForget = 1
    Queue         = 2
    Retain        = 3
    QueueRetain   = 4

    def __init__(self, handleNameOrNumber, handleType=None):
        self.doUnmarshallResult = True

        if handleType is not None:
            warnings.warn('handleType parameter is unnecessary and deprecated',
                          DeprecationWarning)

            if (handleType == self.Standard and
                    not isinstance(handleNameOrNumber, basestring)):
                raise TypeError('A string is required if using standard handle type')
            if (handleType == self.Static and
                    not isinstance(handleNameOrNumber, (int, long))):
                raise TypeError('An integer is required if using static handle type')

        if isinstance(handleNameOrNumber, basestring):
            handle = _StafApi.Handle_t()
            _StafApi.RegisterUTF8(handleNameOrNumber.encode('utf-8'),
                                  ctypes.byref(handle))

            self.handle = handle.value
            self._static = False
        else:
            self.handle = handleNameOrNumber
            self._static = True

    def unregister(self):
        if not self._static:
            _StafApi.UnRegister(self.handle)
            self.handle = 0

    def submit(self, location, service, request, mode=Synchronous):
        # XXX
        # * Using unicode output unconditionally probably breaks compatibility.
        location = location.encode('utf-8')
        service = service.encode('utf-8')
        request = request.encode('utf-8')
        result_ptr = ctypes.POINTER(ctypes.c_char)()
        result_len = ctypes.c_uint()
        try:
            _StafApi.Submit2UTF8(self.handle, mode, location, service, request,
                                 len(request), ctypes.byref(result_ptr),
                                 ctypes.byref(result_len))

            result = result_ptr[:result_len.value]
            return STAFResult(0, result.decode('utf-8'),
                              self.doUnmarshallResult)

        finally:
            # Need to free result_ptr even when rc indicates an error.
            if result_ptr:
                ptr = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_char))
                _StafApi.Free(self.handle, ptr)

    def setDoUnmarshallResult(self, flag):
        warnings.warn('setDoUnmarshallResult is deprecated '
                      '(use doUnmarshallResult directly)', DeprecationWarning)
        self.doUnmarshallResult = bool(flag)

    def getDoUnmarshallResult(self):
        warnings.warn('getDoUnmarshallResult is deprecated '
                      '(use doUnmarshallResult directly)', DeprecationWarning)
        return self.doUnmarshallResult

    # XXX Add repr, context management
