
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
    pass

class STAFResultError(STAFError):
    # This is modelled after EnvironmentError.
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
            # 'extra' isn't very predictable. It can be a big mess, but it's
            # sometimes very handy. We include it if it's one line.
            if self.extra is not None and '\n' not in self.extra:
                extra = ' (%s)' % self.extra
            else:
                extra = ''

            return '[RC %d] %s%s' % (self.rc, self.strerror, extra)

        else:
            if len(self.args) == 0:
                return ''
            else:
                return str(self.args)
