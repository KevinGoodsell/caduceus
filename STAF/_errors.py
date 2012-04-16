# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
STAF error information.
'''

# Only for internal use
_return_codes = {
    0    : ('Ok',                          'No error'),
    1    : ('InvalidAPI',                  'Invalid API'),
    2    : ('UnknownService',              'Unknown service'),
    3    : ('InvalidHandle',               'Invalid handle'),
    4    : ('HandleAlreadyExists',         'Handle already exists'),
    5    : ('HandleDoesNotExist',          'Handle does not exist'),
    6    : ('UnknownError',                'Unknown error'),
    7    : ('InvalidRequestString',        'Invalid request string'),
    8    : ('InvalidServiceResult',        'Invalid service result'),
    9    : ('REXXError',                   'REXX Error'),
    10   : ('BaseOSError',                 'Base operating system error'),
    11   : ('ProcessAlreadyComplete',      'Process already complete'),
    12   : ('ProcessNotComplete',          'Process not complete'),
    13   : ('VariableDoesNotExist',        'Variable does not exist'),
    14   : ('UnResolvableString',          'Unresolvable string'),
    15   : ('InvalidResolveString',        'Invalid resolve string'),
    16   : ('NoPathToMachine',             'No path to endpoint'),
    17   : ('FileOpenError',               'File open error'),
    18   : ('FileReadError',               'File read error'),
    19   : ('FileWriteError',              'File write error'),
    20   : ('FileDeleteError',             'File delete error'),
    21   : ('STAFNotRunning',              'STAF not running'),
    22   : ('CommunicationError',          'Communication error'),
    23   : ('TrusteeDoesNotExist',         'Trusteee does not exist'),
    24   : ('InvalidTrustLevel',           'Invalid trust level'),
    25   : ('AccessDenied',                'Insufficient trust level'),
    26   : ('STAFRegistrationError',       'Registration error'),
    27   : ('ServiceConfigurationError',   'Service configuration error'),
    28   : ('QueueFull',                   'Queue full'),
    29   : ('NoQueueElement',              'No queue element'),
    30   : ('NotifieeDoesNotExist',        'Notifiee does not exist'),
    31   : ('InvalidAPILevel',             'Invalid API level'),
    32   : ('ServiceNotUnregisterable',    'Service not unregisterable'),
    33   : ('ServiceNotAvailable',         'Service not available'),
    34   : ('SemaphoreDoesNotExist',       'Semaphore does not exist'),
    35   : ('NotSemaphoreOwner',           'Not semaphore owner'),
    36   : ('SemaphoreHasPendingRequests', 'Semaphore has pending requests'),
    37   : ('Timeout',                     'Timeout'),
    38   : ('JavaError',                   'Java error'),
    39   : ('ConverterError',              'Converter error'),
    40   : ('MoveError',                   'Move error'),
    41   : ('InvalidObject',               'Invalid object'),
    42   : ('InvalidParm',                 'Invalid parm'),
    43   : ('RequestNumberNotFound',       'Request number not found'),
    44   : ('InvalidAsynchOption',         'Invalid asynchronous option'),
    45   : ('RequestNotComplete',          'Request not complete'),
    46   : ('ProcessAuthenticationDenied', 'Process authentication denied'),
    47   : ('InvalidValue',                'Invalid value'),
    48   : ('DoesNotExist',                'Does not exist'),
    49   : ('AlreadyExists',               'Already exists'),
    50   : ('DirectoryNotEmpty',           'Directory Not Empty'),
    51   : ('DirectoryCopyError',          'Directory Copy Error'),
    52   : ('DiagnosticsNotEnabled',       'Diagnostics Not Enabled'),
    53   : ('HandleAuthenticationDenied',  'Handle Authentication Denied'),
    54   : ('HandleAlreadyAuthenticated',  'Handle Already Authenticated'),
    55   : ('InvalidSTAFVersion',          'Invalid STAF Version'),
    56   : ('RequestCancelled',            'Request Cancelled'),
    57   : ('CreateThreadError',           'Create Thread Error'),
    58   : ('MaximumSizeExceeded',         'Maximum Size Exceeded'),
    59   : ('MaximumHandlesExceeded',      'Maximum Handles Exceeded'),
    60   : ('NotRequester',                'Not Pending Requester'),
    4000 : ('UserDefined',                 'Service specific errors'),
}

class errors(object):
    '''
    Constants for STAF errors.
    '''
    for (rc, (name, description)) in _return_codes.iteritems():
        locals()[name] = rc

    del rc
    del name
    del description

def strerror(rc):
    '''
    Return the string description for a STAF error code, or None if the error
    code is unknown.
    '''
    try:
        return _return_codes[rc][1]
    except KeyError:
        return None

class STAFError(Exception):
    '''
    Base class for all STAF errors.
    '''
    pass

class STAFResultError(STAFError):
    '''
    Error for STAF API return codes, modelled after EnvironmetError. This should
    usually be created with STAFResultError(rc[, strerror[, extra]]). 'strerror'
    will be filled in from strerror() if it's not included. 'extra' is an
    optional string with additional information. Typically 'extra' is set to the
    result of a submit() call that returns an error.

    These arguments are available as the attributes 'rc', 'strerror', and
    'extra'. 'extra' will be None if not specified. All will be None if the
    object is created with no arguments, or with more than three.
    '''

    def __init__(self, *args):
        super(STAFResultError, self).__init__(*args)

        self.rc = None
        self.strerror = None
        self.extra = None
        if len(args) == 1:
            self.rc = args[0]
            self.strerror = strerror(self.rc)
        elif len(args) == 2:
            self.rc = args[0]
            self.strerror = args[1]
        elif len(args) == 3:
            self.rc = args[0]
            self.strerror = args[1]
            self.extra = args[2]

    def __str__(self):
        if self.rc is not None:
            if self.strerror is not None:
                strerr = ' %s' % self.strerror
            else:
                strerr = ''

            # 'extra' isn't very predictable. It can be a big mess, but it's
            # sometimes very handy. We include it if it's one line.
            if self.extra is not None and '\n' not in self.extra:
                extra = ' (%s)' % self.extra
            else:
                extra = ''

            return '[RC %d]%s%s' % (self.rc, strerr, extra)

        else:
            if len(self.args) == 0:
                return ''
            else:
                return str(self.args)
