# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
STAF data type marshalling.
'''

import re

from ._errors import STAFError
from ._mapclass import MapClassDefinition

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
