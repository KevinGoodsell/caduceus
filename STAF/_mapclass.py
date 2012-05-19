# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
Special classes for dealing with STAF Map Class types. Unmarshalled map classes
will be instances of MapClass, which is derived from dict and can be used as a
dict. It also provides display_name() and display_short_name() to access those
attributes if desired.
'''

class View(object):
    '''
    Base class for MapClass views.
    '''
    def __init__(self, mc):
        self._mc = mc

    def __len__(self):
        return len(self._mc)

class SetLikeView(View):
    '''
    Base class for MapClass key views and item views (those that support set
    operations).
    '''
    def __and__(self, other):
        return set(self).intersection(other)

    def __or__(self, other):
        return set(self).union(other)

    def __xor__(self, other):
        return set(self).symmetric_difference(other)

    def __sub__(self, other):
        return set(self).difference(other)

class KeyView(SetLikeView):
    '''
    Class for MapClass key views.
    '''
    def __contains__(self, val):
        return val in self._mc

    def __iter__(self):
        return iter(self._mc._keys)

class ItemView(SetLikeView):
    '''
    Class for MapClass item views.
    '''
    def __contains__(self, val):
        (key, value) = val
        return key in self._mc and self._mc[key] == value

    def __iter__(self):
        for key in self._mc._keys:
            yield (key, self._mc[key])

class ValueView(View):
    '''
    Class for MapClass value views.
    '''
    def __contains__(self, val):
        return val in list(self)

    def __iter__(self):
        for key in self._mc._keys:
            yield self._mc[key]

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

    def setdefault(self, key, default=None):
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

        super(MapClass, self).update(as_dict)

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

    if hasattr(dict, 'viewitems'):
        def viewitems(self):
            return ItemView(self)

        def viewkeys(self):
            return KeyView(self)

        def viewvalues(self):
            return ValueView(self)

        add_docstring(viewitems)
        add_docstring(viewkeys)
        add_docstring(viewvalues)

    add_docstring(__iter__)
    add_docstring(iterkeys)
    add_docstring(keys)
    add_docstring(itervalues)
    add_docstring(values)
    add_docstring(iteritems)
    add_docstring(items)
    add_docstring(__repr__)
