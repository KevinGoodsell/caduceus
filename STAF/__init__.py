# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
Python bindings for STAF.

General Notes
-------------
* Most string results are unicode objects, because the underlying STAF APIs
  being used are UTF-8 versions when available. unicode objects are also
  accepted as parameters.
* Unmarshalled objects are common Python types -- lists, strings (actually
  unicode objects), and dicts. Which type is returned depends on the request.
  MapClass instances are specialized dicts which are returned for some requests.

Handles
-------
Handles are used for all interactions with STAF. They are represented with the
Handle class.

Handles implement the context manager interface. This allows handles to be
unregistered automatically:

    with Handle('my-handle') as h:
        h.submit('local', 'ping', 'ping')

    # h is unregistered here.

The most important part of the Handle class is the submit() method, described in
detail below.

Handle.submit(where, service, request[, sync_option[, unmarshall]])

    submit() submits a request to STAF.

    'where' is the name of the destination machine.

    'service' is the service name.

    'request' may be either a string or a sequence of strings giving the
    request. As a string, 'request' is sent as-is. As a sequence of strings, the
    odd-numbered elements are automatically wrapped as option values. For
    example:

        h.submit('local', 'service', ['add service', serv_name, 'library',
                lib_name, 'executable', exe_name])

    This is equivalent to:

        h.submit('local', 'service',
                'add service ' + STAF.wrap_data(serv_name) +
                ' library ' + STAF.wrap_data(lib_name) +
                ' executable ' + STAF.wrap_data(exe_name))

    When using the sequence form, you must put the command name and option names
    at even-numbered indices. Only option values may be at odd-numbered indices.
    STAF will produce an error if the command name or option names are wrapped,
    and items at odd-numbered indices are always wrapped.

    'sync_option' describes how the request and response should be handled. The
    allowed values are:

        STAF.REQ_SYNC
            (default) The request is synchronous, returning only when it is
            complete.

        STAF.REQ_FIRE_AND_FORGET
            The request is sent asynchronously. A request number is returned
            immediately. No response is received.

        STAF.REQ_QUEUE
            The request is sent asynchronously. A request number is returned
            immediately. The final result is placed in the submitter's queue,
            retrievable via the QUEUE service.

        STAF.REQ_RETAIN
            The request is sent asynchronously. A request number is returned
            immediately. The final result is stored, and can be retrieved and
            freed with the SERVICE service's FREE command.

        STAF.REQ_QUEUE_RETAIN
            The request is sent asynchronously. A request number is returned
            immediately. The final result is stored with the SERVICE service and
            placed in the submitter's queue.

    'unmarshall' determines what unmarshalling is done to the result. The
    allowed values are:

        STAF.UNMARSHALL_RECURSIVE
            (default) The result is fully unmarshalled. Marshalled strings in
            the results are unmarshalled recursively. This is similar to using
            kSTAFUnmarshallingDefaults in the STAF C API.

        STAF.UNMARSHALL_NON_RECURSIVE
            The result is unmarshalled, but strings in the result are not
            unmarshalled. This is similar to using kSTAFIgnoreIndirectObjects in
            the STAF C API.

        STAF.UNMARSHALL_NONE
            No unmarshalling is done. The result is returned as a string.

Errors and Exceptions
---------------------
class STAFError(Exception)

    Base class for all exceptions in the STAF package.

class STAFResultError(STAFError)

    Exception raised for errors returned by STAF. Includes the following
    attributes:

        rc  The integer return code returned by STAF. Will be None if the
            exception was created with no arguments.

        strerror
            The string representation of the error. This is normally the string
            that would be reported by the STAF HELP service for rc, though an
            alternative string can be provided when the exception is created.
            This will be None if rc is None.

        extra
            This will be a string with additional information about the error,
            or None. Typically this is the result from a failed submit() call,
            if there was a result.

class STAFUnmarshallError(STAFError)

    Exception raised when unmarshalling fails. Note that typically you won't see
    this, since by default unmarshalling is attempted and the original string is
    returned if unmarshalling fails. The exception is unmarshall_force, which
    will raise this if unmarshalling isn't possible.

class errors(object)

    This is a class that simply collects the STAF error codes:

        errors.Ok = 0
        errors.InvalidAPI = 1
        errors.UnknownService = 2
        errors.InvalidHanle = 3
        ...

def strerror(rc)

    Returns a string describing the given error code.

Unmarshalling
-------------
Two functions are available for doing unmarshalling:

    def unmarshall(data[, mode])
    def unmarshall_force(data[, mode])

Note: Unmarshalling usually happens automatically in the Handle.submit() call,
so the unmarshall() and unmarshall_force() functions aren't needed most of the
time. Unmarshalling can be skipped in the Handle.submit() call by passing
mode=STAF.UNMARSHALL_NONE.

unmarshall() and unmarshall_force() differ in how they deal with errors.
unmarshall() assumes that the string it is given may or may not actually be
marshalled data, so any unmarshalling error is taken to mean that the string is
just a plain string, and it is returned as-is. unmarshall_force() assumes that
the string is marshalled data and raises STAFUnmarshallError if it cannot be
unmarshalled.

The optional 'mode' argument has the same meaning as the 'unmarshall' argument
for Handle.submit(). Using STAF.UNMARSHALL_NONE makes both of these functions
no-ops, but is still supported for consistency with Handle.submit().

STAF has six data types that can appear in marshalled strings. This data types
and the corresponding Python type used to represent the unmarshalled forms are
as follows:

     STAF Type           | Python Type
    --------------------------------------
     None                | None
     String              | str or unicode
     List                | list
     Map                 | dict
     Map Class           | STAF.MapClass
     Marshalling Context | (not used)

The first four are straight-forward. String results have the same type as the
original marshalled data string.

A Map Class is basically a Map with an associated Map Class Definition. The Map
Class Definition includes extra information that is typically only relevant for
displaying the Map Class data. This includes an ordering for the Map keys, a
display name for each key, and optionally a short form of the display name. The
Map Class Definition is represented in Python with the type
STAF.MapClassDefinition, described below.

Because Map Classes are just a special case of Maps, the STAF.MapClass type is
derived from dict and can be used much like any other dict. There are some
restrictions, however. See the full description of STAF.MapClass below.

A Marshalling Context is just a collection of Map Class Definitions and a "root
object" that may use those definitions. The root object is the interesting part,
and when a Marshalling Context is unmarshalled, this is the only part that is
returned. Thus, when unmarshalling is performed on a marshalled Marshalling
Context, the result will be one of the other types. Any Map Class Definitions
are always accessible through the 'definition' attribute of a corresponding
STAF.MapClass instance.

class MapClass(dict)

    Class used to represent unmarshalled Map Class objects. Functions like a
    normal dict, but has a few additional attributes and restrictions, and some
    slightly modified behaviors.

    The main restriction is that you must not add keys to or remove keys from a
    MapClass, because the structure of a MapClass is externally imposed by a
    MapClassDefinition. This is currently not enforced, but bad things will
    probably happen if you do it.

    The methods 'viewitems', 'viewkeys', and 'viewvalues' are not supported in
    MapClasses.

    MapClasses impose an ordering on the items they contain. This ordering is
    determined by the corresponding MapClassDefinition. What this means is that
    the various methods that return iterators over keys, values, or both will
    always produce items in the same order. Likewise methods that return a list
    of keys, values, or both will always have the items ordered in the same way.
    This can be useful for printing formatted tables of MapClass items.

    The following extra attributes are available:

    mapclass.definition

        This instance attribute is a reference to a STAF.MapClassDefinition
        instance that defines the keys, item ordering, and key display names for
        the MapClass.

    mapclass.display_name(key)
    mapclass.display_short_name(key)

        These are convenience methods for calling
        mapclass.definition.display_name(key) and
        mapclass.definition.display_short_name(key), respectively.

class MapClassDefinition(object)

    Defines the structure of a MapClass instance. This includes which keys will
    be present in the MapClass, the ordering for those keys, the display name
    for each key, and an optional short form of the display name for each key.
    Short display names may exist for some keys in the MapClassDefinition and
    not others.

    MapClassDefinitions are used by MapClasses. There's nothing wrong with using
    MapClassDefinitions directly, but it shouldn't be necessary most of the
    time.

    Note that a MapClassDefinition should not be modified once it has been used
    to create a MapClass, since this would invalidate the structure of any
    MapClass using the MapClassDefinition.

    The following attributes are available:

    mapclassdef.name

        This instance attribute is a string giving the name of the Map Class
        Definition. This is primarily used internally for identifying the Map
        Class Definition used by a particular Map Class.

    mapclassdef.keys

        This instance attribute is a list of key names defined for Map Classes
        using this Map Class Definition. The ordering of the keys in this list
        gives the ordering of Map Class items. This attribute should not be
        modified directly. Use the add_item() method to add new keys.

    mapclassdef.add_item(key, display_name[, display_short_name])

        Add a new key along with its display name and optionally a short display
        name. This adds the key to the end of the 'keys' list.

    mapclassdef.display_name(key)
    mapclassdef.display_short_name(key)

        Returns the display name or short display name for the given key.
        display_short_name() will return None if no short display name was
        defined for the key.

Misc. Functions
---------------
See the docstrings for the full documentation for these functions.

wrap_data(data)
add_privacy_delimiters(data)
remove_privacy_delimiters(data[, num_levels])
mask_private_data(data)
escape_privacy_delimiters(data)
'''

# Using __all__ makes pydoc work properly. Otherwise it looks at the modules the
# items actually come from and assumes they don't belong in the docs for
# __init__.
__all__ = [
    'REQ_SYNC', 'REQ_FIRE_AND_FORGET', 'REQ_QUEUE', 'REQ_RETAIN',
    'REQ_QUEUE_RETAIN', 'Handle', 'wrap_data', 'add_privacy_delimiters',
    'remove_privacy_delimiters', 'mask_private_data',
    'escape_privacy_delimiters', 'errors', 'strerror', 'STAFError',
    'STAFResultError', 'unmarshall', 'unmarshall_force', 'STAFUnmarshallError',
    'MapClassDefinition', 'MapClass', 'UNMARSHALL_RECURSIVE',
    'UNMARSHALL_NON_RECURSIVE', 'UNMARSHALL_NONE',
]

from ._staf import (
    REQ_SYNC,
    REQ_FIRE_AND_FORGET,
    REQ_QUEUE,
    REQ_RETAIN,
    REQ_QUEUE_RETAIN,
    Handle,
    wrap_data,
    add_privacy_delimiters,
    remove_privacy_delimiters,
    mask_private_data,
    escape_privacy_delimiters,
)

from ._errors import (
    errors,
    strerror,
    STAFError,
    STAFResultError,
)

from ._marshall import (
    unmarshall,
    unmarshall_force,
    STAFUnmarshallError,
    MapClassDefinition,
    MapClass,
    UNMARSHALL_RECURSIVE,
    UNMARSHALL_NON_RECURSIVE,
    UNMARSHALL_NONE,
)

# Clean up names. This gives 'STAF.Handle' istead of 'STAF._staf.Handle'
for name in __all__:
    obj = globals()[name]
    if hasattr(obj, '__module__'):
        obj.__module__ = 'STAF'
del name
del obj
