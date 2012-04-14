# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
STAF data type marshaling.
'''

import re

from ._errors import STAFError

class STAFUnmarshalError(STAFError):
    pass

UNMARSHAL_RECURSIVE     = 'unmarshal-recursive'
UNMARSHAL_NON_RECURSIVE = 'unmarshal-non-recursive'
UNMARSHAL_NONE          = 'unmarshal-none'

marker = '@SDT/'

def unmarshal(data, mode=UNMARSHAL_RECURSIVE):
    '''
    Try to unmarshal the string in 'data'. 'mode' determines how unmarshaling
    is done.

    'mode' can be one of the following:

        UNMARSHAL_RECURSIVE (default) - Tries to recursively unmarshal any
        string result.

        UNMARSHAL_NON_RECURSIVE - leaves string results as they are, doesn't
        attept further unmarshaling.

        UNMARSHAL_NONE - doesn't do any unmarshaling.

    Returns 'data' if it doesn't appear to be a marshaled object, or if 'mode'
    is UNMARSHAL_NONE.
    '''
    try:
        return unmarshal_force(data, mode)
    except STAFUnmarshalError:
        return data

def unmarshal_force(data, mode=UNMARSHAL_RECURSIVE):
    '''
    Same as unmarshal, but raises STAFUnmarshalError if unmarshaling isn't
    possible.
    '''
    if mode == UNMARSHAL_NONE:
        return data

    (obj, remainder) = unmarshal_internal(data, mode)

    if remainder != '':
        raise STAFUnmarshalError('unexpected trailing data')

    return obj

# Special classes for dealing with STAF Map Class types. Unmarshaled map
# classes will instances of MapClass, which is derived from dict and can be used
# as a dict. It also provides display_name() and display_short_name() to access
# those attributes if desired.

class MapClassDefinition(object):
    '''
    Represents a map class definition, which provides the set of key names and
    long and short display names for the map. This is accessible as the
    'definition' field on a MapClass instance.
    '''

    def __init__(self, name):
        self.name = name
        self.keys = []
        self._names = {} # {'key' : ('display name', 'short display name')}

    def add_item(self, key, display_name, display_short_name=None):
        self.keys.append(key)
        self._names[key] = (display_name, display_short_name)

    def display_name(self, key):
        return self._names[key][0]

    def display_short_name(self, key):
        return self._names[key][1]

class MapClass(dict):
    '''
    Represents a map class instance. This is a dict and can be accessed the same
    way. It also has 'display_name' and 'display_short_name' methods for getting
    the display names for a key.
    '''

    def __init__(self, definition, *args, **kwargs):
        super(MapClass, self).__init__(*args, **kwargs)

        self.definition = definition

    def display_name(self, key):
        return self.definition.display_name(key)

    def display_short_name(self, key):
        return self.definition.display_short_name(key)

    # Overrides to preserve ordering on item access.

    def __iter__(self):
        return iter(self.definition.keys)

    def iterkeys(self):
        return iter(self.definition.keys)

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        for key in self.definition.keys:
            yield self[key]

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for key in self.definition.keys:
            yield (key, self[key])

    def items(self):
        return list(self.iteritems())

    # The default dict repr is would be fine, but the order of the fields is
    # kind of important for MapClass instances.
    def __repr__(self):
        items = []
        for (k, v) in self.iteritems():
            items.append('%r: %r' % (k, v))

        return '{%s}' % ', '.join(items)

    # NOTE: Python 2.7 adds viewitems(), viewkeys(), and viewvalues(). These
    # aren't supported here because it would be tricky to make them work and
    # they aren't really useful in MapClasses that aren't expected to have items
    # added/removed. Because the inherited versions from dict won't work as
    # expected, disable them.

    def viewitems(self):
        raise NotImplementedError('viewitems is not supported in MapClass')

    def viewkeys(self):
        raise NotImplementedError('viewkeys is not supported in MapClass')

    def viewvalues(self):
        raise NotImplementedError('viewvalues is not supported in MapClass')


def unmarshal_internal(data, mode, context=None):
    if context is None:
        context = {}

    if not data.startswith(marker):
        raise STAFUnmarshalError('missing marshaled data marker')

    sym_index = len(marker)
    try:
        symbol = data[sym_index]
        rest = data[sym_index+1:]
    except IndexError:
        raise STAFUnmarshalError('incomplete marshaled data')

    unmarshaler = get_unmarshaler(symbol)
    if unmarshaler is None:
        raise STAFUnmarshalError('unrecognized data type indicator')

    return unmarshaler.unmarshal(rest, mode, context)

def get_unmarshaler(symbol):
    if symbol == '$':
        return ScalarUnmarshaler
    elif symbol == '{':
        return MapUnmarshaler
    elif symbol == '[':
        return ListUnmarshaler
    elif symbol == '%':
        return MapClassUnmarshaler
    elif symbol == '*':
        return ContextUnmarshaler
    else:
        return None

class Unmarshaler(object):
    '''
    Base class for all unmarshalers.
    '''
    clc_matcher = re.compile(
        r'''^
        :(?P<len>\d+):  # Colon-length-colon
        (?P<rest>.*)    # Data
        $''', re.VERBOSE | re.DOTALL)

    @classmethod
    def unmarshal(cls, data, mode, context):
        raise NotImplementedError()

    @classmethod
    def read_clc_obj(cls, data):
        '''
        Read a colon-length-colon denoted object from data. That is, a colon,
        integer length, colon, and finally a sequence of characters of the given
        length. Returns a tuple of the object and everything that's left in
        data. Raises STAFUnmarshalError if the format is not as expected.
        '''
        m = cls.clc_matcher.match(data)
        if m is None:
            raise STAFUnmarshalError('bad format for colon-length-colon object')

        (length, rest) = m.group('len', 'rest')
        length = int(length)

        if length > len(rest):
            raise STAFUnmarshalError('specified length exceeds available data')

        obj = rest[:length]
        rest = rest[length:]

        return (obj, rest)

class ScalarUnmarshaler(Unmarshaler):
    @classmethod
    def unmarshal(cls, data, mode, context):
        if not data.startswith('0') and not data.startswith('S'):
            raise STAFUnmarshalError('bad format for scalar object')

        typ = data[0]
        (obj, rest) = cls.read_clc_obj(data[1:])

        if typ == '0':
            if obj != '':
                raise STAFUnmarshalError('bad format for none object')
            return (None, rest)

        else: # typ == 'S'
            # Possibly do recursive unmarshaling.
            if mode == UNMARSHAL_RECURSIVE:
                obj = unmarshal(obj, mode)

            return (obj, rest)


class MapUnmarshaler(Unmarshaler):
    @classmethod
    def unmarshal(cls, data, mode, context):
        (items, remainder) = cls.read_clc_obj(data)

        result = {}

        while items:
            (key, items) = cls.read_clc_obj(items)
            (val, items) = unmarshal_internal(items, mode, context)

            result[key] = val

        return (result, remainder)

class ListUnmarshaler(Unmarshaler):
    count_matcher = re.compile(r'''^
        (?P<count>\d+)  # Number of elements
        (?P<rest>.*)    # List items
        $''', re.VERBOSE | re.DOTALL)

    @classmethod
    def unmarshal(cls, data, mode, context):
        m = cls.count_matcher.match(data)
        if m is None:
            raise STAFUnmarshalError('bad format for list object')

        (count, rest) = m.group('count', 'rest')
        count = int(count)

        (items, remainder) = cls.read_clc_obj(rest)

        result = []
        for i in range(count):
            (obj, items) = unmarshal_internal(items, mode, context)
            result.append(obj)

        if items != '':
            raise STAFUnmarshalError('unexpected trailing data')

        return (result, remainder)

class MapClassUnmarshaler(Unmarshaler):
    @classmethod
    def unmarshal(cls, data, mode, context):
        (content, remainder) = cls.read_clc_obj(data)
        (class_name, values) = cls.read_clc_obj(content)

        class_def = context.get(class_name)
        if class_def is None:
            raise STAFUnmarshalError('missing map class definition for %r' %
                                     class_name)

        result = MapClass(class_def)
        # The ordering and names of the keys are given by class_def.keys.
        for key in class_def.keys:
            (value, values) = unmarshal_internal(values, mode, context)
            result[key] = value

        if values != '':
            raise STAFUnmarshalError('unexpected trailing data')

        return (result, remainder)

class ContextUnmarshaler(Unmarshaler):
    @classmethod
    def unmarshal(cls, data, mode, context):
        (content, remainder) = cls.read_clc_obj(data)
        (context_map, root_data) = unmarshal_internal(content, mode, context)

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
        (root_obj, trailing) = unmarshal_internal(root_data, mode, new_context)

        if trailing != '':
            raise STAFUnmarshalError('unexpected trailing data')

        return (root_obj, remainder)
