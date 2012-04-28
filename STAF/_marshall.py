# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
STAF data type marshalling.
'''

import re

from ._errors import STAFError

class STAFUnmarshallError(STAFError):
    pass

class NamedConstant(object):
    '''
    Simple class for singleton constants.
    '''
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '.'.join([self.__module__, self.name])

UNMARSHALL_RECURSIVE = NamedConstant('UNMARSHALL_RECURSIVE')
UNMARSHALL_NON_RECURSIVE = NamedConstant('UNMARSHALL_NON_RECURSIVE')
UNMARSHALL_NONE = NamedConstant('UNMARSHALL_NONE')

marker = '@SDT/'

def unmarshall(data, mode=UNMARSHALL_RECURSIVE):
    '''
    Try to unmarshall the string in 'data'. 'mode' determines how unmarshalling
    is done.

    'mode' can be one of the following:

        UNMARSHALL_RECURSIVE (default) - Tries to recursively unmarshall any
        string result.

        UNMARSHALL_NON_RECURSIVE - leaves string results as they are, doesn't
        attept further unmarshalling.

        UNMARSHALL_NONE - doesn't do any unmarshalling.

    Returns 'data' if it doesn't appear to be a marshalled object, or if 'mode'
    is UNMARSHALL_NONE.
    '''
    try:
        return unmarshall_force(data, mode)
    except STAFUnmarshallError:
        return data

def unmarshall_force(data, mode=UNMARSHALL_RECURSIVE):
    '''
    Same as unmarshall, but raises STAFUnmarshallError if unmarshalling isn't
    possible.
    '''
    if mode == UNMARSHALL_NONE:
        return data

    (obj, remainder) = unmarshall_internal(data, mode)

    if remainder != '':
        raise STAFUnmarshallError('unexpected trailing data')

    return obj

# Special classes for dealing with STAF Map Class types. Unmarshalled map
# classes will be instances of MapClass, which is derived from dict and can be
# used as a dict. It also provides display_name() and display_short_name() to
# access those attributes if desired.

class MapClassDefinition(object):
    '''
    Represents a map class definition, which provides the set of key names and
    long and short display names for the keys.
    '''

    def __init__(self, name):
        self.name = name
        self.keys = []
        self._names = {} # {'key' : ('display name', 'short display name')}

    def __repr__(self):
        cls = self.__class__
        return '<%s.%s %s>' % (cls.__module__, cls.__name__, self.name)

    def add_item(self, key, display_name, display_short_name=None):
        '''
        Add a key and a display name for it. Optionally include a short display
        name.
        '''
        self.keys.append(key)
        self._names[key] = (display_name, display_short_name)

    def display_name(self, key):
        '''
        Returns the display name for 'key'.
        '''
        return self._names[key][0]

    def display_short_name(self, key):
        '''
        Returns the short form of the display name for 'key', or None if no
        short name is defined.
        '''
        return self._names[key][1]

    def map_class(self, *args, **kwargs):
        '''
        Return a MapClass instance based on this definition.
        '''
        cls = MapClass(self.name, self.keys, self._names)
        cls.update(*args, **kwargs)
        return cls

def add_docstring(method):
    '''
    Add a docstring to method by pulling it from the corresponding method in
    dict. Only for use with dict-derived classes overriding dict methods.
    '''
    method.__doc__ = getattr(dict, method.__name__).__doc__

class MapClass(dict):
    '''
    Represents a map class instance. This is a dict and can be accessed the same
    way. It also has 'display_name' and 'display_short_name' methods for getting
    the display names for a key.

    Adding and removing keys are not supported.
    '''

    def __init__(self, class_name, keys, disp_names):
        '''
        Create a new MapClass. 'class_name' gives the Map Class name, 'keys'
        is a sequence giving the keys in the Map and their ordering, and
        disp_names is a dict mapping key names to (display_name,
        display_short_name) tuples, where display_short_name may be None.

        This should generally not be used directly. Instead, create a
        MapClassDefinition, populate it with keys, then use its map_class method
        to create MapClass instances.
        '''
        super(MapClass, self).__init__()

        self.class_name = class_name
        self._keys = list(keys)
        self._names = dict(disp_names)

        for key in self._keys:
            self[key] = None

    def display_name(self, key):
        '''
        Returns the display name for 'key'.
        '''
        return self._names[key][0]

    def display_short_name(self, key):
        '''
        Returns the short form of the display name for 'key', or None if no
        short name is defined.
        '''
        return self._names[key][1]

    def definition(self):
        '''
        Return a new MapClassDefinition using the structure of this MapClass.
        '''
        definition = MapClassDefinition(self.class_name)
        for key in self._keys:
            (disp_name, disp_short) = self._names[key]
            definition.add_item(key, disp_name, disp_short)

        return definition

    # Overrides to prevent adding/removing keys.

    def __setitem__(self, key, value):
        '''
        Implements self[key] = value, but raises KeyError if key is not in the
        Map Class Definition.
        '''
        if key in self._names:
            super(MapClass, self).__setitem__(key, value)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        'Not supported, raises NotImplementedError.'
        raise NotImplementedError('item deletion is not supported in MapClass')

    def clear(self):
        'Not supported, raises NotImplementedError.'
        raise NotImplementedError('clear() is not supported in MapClass')

    def pop(self, key, default=None):
        'Not supported, raises NotImplementedError.'
        raise NotImplementedError('pop() is not supported in MapClass')

    def popitem(self):
        'Not supported, raises NotImplementedError.'
        raise NotImplementedError('popitem() is not supported in MapClass')

    def setdefault(key, default=None):
        '''
        Modified dict.setdefault, raises KeyError if the key is not in the Map
        Class Definition.
        '''
        if key in self:
            return super(MapClass, self).setdefault(key, default)
        else:
            raise KeyError(key)

    def update(self, *args, **kwargs):
        '''
        Modified dict.update, raises KeyError if the any key is not in the Map
        Class Definition.
        '''
        as_dict = dict(*args, **kwargs)
        for key in as_dict.iterkeys():
            if key not in self:
                raise KeyError(key)

        self.update(as_dict)

    # Overrides to preserve ordering on item access.

    def __iter__(self):
        return iter(self._keys)

    def iterkeys(self):
        return iter(self._keys)

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        for key in self._keys:
            yield self[key]

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for key in self._keys:
            yield (key, self[key])

    def items(self):
        return list(self.iteritems())

    # The default dict repr would be fine, but the order of the fields is kind
    # of important for MapClass instances.
    def __repr__(self):
        items = []
        for (k, v) in self.iteritems():
            items.append('%r: %r' % (k, v))

        return '{%s}' % ', '.join(items)

    add_docstring(__iter__)
    add_docstring(iterkeys)
    add_docstring(keys)
    add_docstring(itervalues)
    add_docstring(values)
    add_docstring(iteritems)
    add_docstring(items)
    add_docstring(__repr__)


def unmarshall_internal(data, mode, context=None):
    if context is None:
        context = {}

    if not data.startswith(marker):
        raise STAFUnmarshallError('missing marshalled data marker')

    sym_index = len(marker)
    try:
        symbol = data[sym_index]
        rest = data[sym_index+1:]
    except IndexError:
        raise STAFUnmarshallError('incomplete marshalled data')

    unmarshaller = get_unmarshaller(symbol)
    if unmarshaller is None:
        raise STAFUnmarshallError('unrecognized data type indicator')

    return unmarshaller.unmarshall(rest, mode, context)

def get_unmarshaller(symbol):
    if symbol == '$':
        return ScalarUnmarshaller
    elif symbol == '{':
        return MapUnmarshaller
    elif symbol == '[':
        return ListUnmarshaller
    elif symbol == '%':
        return MapClassUnmarshaller
    elif symbol == '*':
        return ContextUnmarshaller
    else:
        return None

class Unmarshaller(object):
    '''
    Base class for all unmarshallers.
    '''
    clc_matcher = re.compile(
        r'''^
        :(?P<len>\d+):  # Colon-length-colon
        (?P<rest>.*)    # Data
        $''', re.VERBOSE | re.DOTALL)

    @classmethod
    def unmarshall(cls, data, mode, context):
        raise NotImplementedError()

    @classmethod
    def read_clc_obj(cls, data):
        '''
        Read a colon-length-colon denoted object from data. That is, a colon,
        integer length, colon, and finally a sequence of characters of the given
        length. Returns a tuple of the object and everything that's left in
        data. Raises STAFUnmarshallError if the format is not as expected.
        '''
        m = cls.clc_matcher.match(data)
        if m is None:
            raise STAFUnmarshallError('bad format for colon-length-colon '
                                      'object')

        (length, rest) = m.group('len', 'rest')
        length = int(length)

        if length > len(rest):
            raise STAFUnmarshallError('specified length exceeds available data')

        obj = rest[:length]
        rest = rest[length:]

        return (obj, rest)

class ScalarUnmarshaller(Unmarshaller):
    @classmethod
    def unmarshall(cls, data, mode, context):
        if not data.startswith('0') and not data.startswith('S'):
            raise STAFUnmarshallError('bad format for scalar object')

        typ = data[0]
        (obj, rest) = cls.read_clc_obj(data[1:])

        if typ == '0':
            if obj != '':
                raise STAFUnmarshallError('bad format for none object')
            return (None, rest)

        else: # typ == 'S'
            # Possibly do recursive unmarshalling.
            if mode == UNMARSHALL_RECURSIVE:
                obj = unmarshall(obj, mode)

            return (obj, rest)


class MapUnmarshaller(Unmarshaller):
    @classmethod
    def unmarshall(cls, data, mode, context):
        (items, remainder) = cls.read_clc_obj(data)

        result = {}

        while items:
            (key, items) = cls.read_clc_obj(items)
            (val, items) = unmarshall_internal(items, mode, context)

            result[key] = val

        return (result, remainder)

class ListUnmarshaller(Unmarshaller):
    count_matcher = re.compile(r'''^
        (?P<count>\d+)  # Number of elements
        (?P<rest>.*)    # List items
        $''', re.VERBOSE | re.DOTALL)

    @classmethod
    def unmarshall(cls, data, mode, context):
        m = cls.count_matcher.match(data)
        if m is None:
            raise STAFUnmarshallError('bad format for list object')

        (count, rest) = m.group('count', 'rest')
        count = int(count)

        (items, remainder) = cls.read_clc_obj(rest)

        result = []
        for i in range(count):
            (obj, items) = unmarshall_internal(items, mode, context)
            result.append(obj)

        if items != '':
            raise STAFUnmarshallError('unexpected trailing data')

        return (result, remainder)

class MapClassUnmarshaller(Unmarshaller):
    @classmethod
    def unmarshall(cls, data, mode, context):
        (content, remainder) = cls.read_clc_obj(data)
        (class_name, values) = cls.read_clc_obj(content)

        class_def = context.get(class_name)
        if class_def is None:
            raise STAFUnmarshallError('missing map class definition for %r' %
                                      class_name)

        result = class_def.map_class()
        # The ordering and names of the keys are given by class_def.keys.
        for key in class_def.keys:
            (value, values) = unmarshall_internal(values, mode, context)
            result[key] = value

        if values != '':
            raise STAFUnmarshallError('unexpected trailing data')

        return (result, remainder)

class ContextUnmarshaller(Unmarshaller):
    @classmethod
    def unmarshall(cls, data, mode, context):
        (content, remainder) = cls.read_clc_obj(data)
        (context_map, root_data) = unmarshall_internal(content, mode, context)

        class_map = context_map.get('map-class-map', {})

        # Build a map of names to MapClassDefinitions.
        new_context = {}
        for (name, info) in class_map.iteritems():
            class_def = MapClassDefinition(name)
            for item in info['keys']:
                class_def.add_item(item['key'], item['display-name'],
                                   item.get('display-short-name'))

            new_context[name] = class_def

        # Note that we may be forsaking an existing class map in 'context' in
        # favor of new_context. Nested contexts probably shouldn't happen, but
        # if they do this means the objects in the inner context won't be able
        # to reference objects in the outer context. This is probably fine.
        (root_obj, trailing) = unmarshall_internal(root_data, mode, new_context)

        if trailing != '':
            raise STAFUnmarshallError('unexpected trailing data')

        return (root_obj, remainder)
