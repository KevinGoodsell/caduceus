import re

from STAF import Handle

# XXX There's supposed to be one top-level exception class, but that won't work
# if it's the current STAFError because it's too tied to RC.
class STAFUnmarshalError(Exception):
    pass

marker = '@SDT/'

def unmarshal(data, mode):
    if mode == Handle.UnmarshalNone or not data.startswith(marker):
        return data

    (obj, remainder) = unmarshal_internal(data, mode)

    if remainder != '':
        raise STAFUnmarshalError('unexpected trailing data')

    return obj

# Special classes for dealing with STAF Map Class types. Unmarshalled map
# classes will instances of MapClass, which is derived from dict and can be used
# as a dict. It also provides display_name() and display_short_name() to access
# those attributes if desired.

class MapClassDefinition(object):
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
    def __init__(self, definition, *args, **kwargs):
        super(MapClass, self).__init__(*args, **kwargs)

        self.definition = definition

    def display_name(self, key):
        return self.definition.display_name(key)

    def display_short_name(self, key):
        return self.definition.display_short_name(key)

def unmarshal_internal(data, mode, context=None):
    if context is None:
        context = {}

    if not data.startswith(marker):
        raise STAFUnmarshalError('missing marshalled data marker')

    sym_index = len(marker)
    try:
        symbol = data[sym_index]
        rest = data[sym_index+1:]
    except IndexError:
        raise STAFUnmarshalError('incomplete marshalled data')

    unmarshaller = get_unmarshaller(symbol)
    if unmarshaller is None:
        raise STAFUnmarshalError('unrecognized data type indicator')

    return unmarshaller.unmarshal(rest, mode, context)

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

class ScalarUnmarshaller(Unmarshaller):
    matcher = re.compile(
        r'''^
        (?P<type>[S0])  # Type indicator (string or none)
        :(?P<len>\d+):  # Colon-length-colon
        (?P<rest>.*)    # Value
        $''', re.VERBOSE | re.DOTALL)

    @classmethod
    def unmarshal(cls, data, mode, context):
        typ = data[0]
        (obj, rest) = cls.read_clc_obj(data[1:])

        if typ == '0':
            if obj != '':
                raise STAFUnmarshalError('bad format for none object')
            return (None, rest)

        elif typ == 'S':
            # Possibly do recursive unmarshalling.
            if mode == Handle.UnmarshalRecursive:
                obj = unmarshal(obj, mode)

            return (obj, rest)

        raise STAFUnmarshalError('bad format for scalar object')

class MapUnmarshaller(Unmarshaller):
    @classmethod
    def unmarshal(cls, data, mode, context):
        (items, remainder) = cls.read_clc_obj(data)

        result = {}

        while items:
            (key, items) = cls.read_clc_obj(items)
            (val, items) = unmarshal_internal(items, mode, context)

            result[key] = val

        return (result, remainder)

class ListUnmarshaller(Unmarshaller):
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

class MapClassUnmarshaller(Unmarshaller):
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

class ContextUnmarshaller(Unmarshaller):
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
