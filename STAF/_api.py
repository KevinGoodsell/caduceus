import ctypes

from ._errors import STAFResultError

staf = ctypes.cdll.LoadLibrary('libSTAF.so')

# errcheck function
def check_rc(result, func, arguments):
    if result != 0:
        raise STAFResultError(result)

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
RegisterUTF8 = staf.STAFRegisterUTF8
RegisterUTF8.argtypes = (Utf8, ctypes.POINTER(Handle_t))
RegisterUTF8.restype = RC_t
RegisterUTF8.errcheck = check_rc

UnRegister = staf.STAFUnRegister
UnRegister.argtypes = (Handle_t,)
UnRegister.restype = RC_t
UnRegister.errcheck = check_rc

Submit2UTF8 = staf.STAFSubmit2UTF8
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

Free = staf.STAFFree
Free.argtypes = (Handle_t, ctypes.POINTER(ctypes.c_char))
Free.restype = RC_t
Free.errcheck = check_rc

# STAFString APIs:
StringConstruct = staf.STAFStringConstruct
StringConstruct.argtypes = (
    ctypes.POINTER(String_t),      # pString
    ctypes.POINTER(ctypes.c_char), # buffer
    ctypes.c_uint,                 # len
    ctypes.POINTER(ctypes.c_uint), # osRC
)
StringConstruct.restype = RC_t
StringConstruct.errcheck = check_rc

StringGetBuffer = staf.STAFStringGetBuffer
StringGetBuffer.argtypes = (
    String_t,                                      # aString
    ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), # buffer
    ctypes.POINTER(ctypes.c_uint),                 # len
    ctypes.POINTER(ctypes.c_uint),                 # osRC
)
StringGetBuffer.restype = RC_t
StringGetBuffer.errcheck = check_rc

StringDestruct = staf.STAFStringDestruct
StringDestruct.argtypes = (ctypes.POINTER(String_t),
                           ctypes.POINTER(ctypes.c_uint))
StringDestruct.restype = RC_t
StringDestruct.errcheck = check_rc

# Private data APIs:
AddPrivacyDelimiters = staf.STAFAddPrivacyDelimiters
AddPrivacyDelimiters.argtypes = (String_t, ctypes.POINTER(String_t))
AddPrivacyDelimiters.restype = RC_t
AddPrivacyDelimiters.errcheck = check_rc

RemovePrivacyDelimiters = staf.STAFRemovePrivacyDelimiters
RemovePrivacyDelimiters.argtypes = (String_t, ctypes.c_uint,
                                    ctypes.POINTER(String_t))
RemovePrivacyDelimiters.restype = RC_t
RemovePrivacyDelimiters.errcheck = check_rc

MaskPrivateData = staf.STAFMaskPrivateData
MaskPrivateData.argtypes = (String_t, ctypes.POINTER(String_t))
MaskPrivateData.restype = RC_t
MaskPrivateData.errcheck = check_rc

EscapePrivacyDelimiters = staf.STAFEscapePrivacyDelimiters
EscapePrivacyDelimiters.argtypes = (String_t, ctypes.POINTER(String_t))
EscapePrivacyDelimiters.restype = RC_t
EscapePrivacyDelimiters.errcheck = check_rc

# Wrapper for String_t
class String(object):
    def __init__(self, data=None):
        self._as_parameter_ = String_t()

        if data is None:
            return

        try:
            utf8 = data.encode('utf-8')
            StringConstruct(ctypes.byref(self._as_parameter_), utf8,len(utf8),
                            None)
        except:
            self.destroy()
            raise

    def byref(self):
        return ctypes.byref(self._as_parameter_)

    def destroy(self):
        if self._as_parameter_:
            StringDestruct(ctypes.byref(self._as_parameter_), None)

    def __nonzero__(self):
        return bool(self._as_parameter_)

    def __unicode__(self):
        buf = ctypes.POINTER(ctypes.c_char)()
        length = ctypes.c_uint()
        StringGetBuffer(self, ctypes.byref(buf), ctypes.byref(length), None)
        result = buf[:length.value]
        return result.decode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.destroy()

        # Don't supress an exception
        return False
