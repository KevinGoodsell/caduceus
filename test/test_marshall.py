# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

import unittest
import operator

from STAF import (
    unmarshall,
    unmarshall_force,
    STAFUnmarshallError,
    UNMARSHALL_NON_RECURSIVE,
    UNMARSHALL_NONE,
    MapClassDefinition,
)

class Unmarshall(unittest.TestCase):

    def testUnmarshallScalar(self):
        self.assertTrue(unmarshall('@SDT/$0:0:') is None)

        self.assertEqual(unmarshall('@SDT/$S:0:'), '')
        self.assertEqual(unmarshall('@SDT/$S:3:foo'), 'foo')
        self.assertEqual(unmarshall('@SDT/$S:10:   \tab\n   '), '   \tab\n   ')

    def testUnmarshallMap(self):
        self.assertEqual(unmarshall('@SDT/{:0:'), {})
        self.assertEqual(unmarshall('@SDT/{:13::0:@SDT/$0:0:'), {'': None})
        self.assertEqual(unmarshall('@SDT/{:53:'
                                    ':8:some key@SDT/$0:0:'
                                    ':7:another@SDT/$S:11:foo bar baz'),
                         {'some key': None, 'another': 'foo bar baz'})

    def testUnmarshalList(self):
        self.assertEqual(unmarshall('@SDT/[0:0:'), [])
        self.assertEqual(unmarshall('@SDT/[4:42:'
                                    '@SDT/[0:0:'
                                    '@SDT/$0:0:'
                                    '@SDT/$S:3:foo'
                                    '@SDT/{:0:'),
                         [[], None, 'foo', {}])

    def testUnmarshallMapClass(self):
        data = (
            '@SDT/*:1306:'
            '@SDT/{:743::13:map-class-map'
            '@SDT/{:715:'

            # ClassFoo:
            ':8:ClassFoo'
            '@SDT/{:318:'
                ':4:keys'
                '@SDT/[3:274:'
                    '@SDT/{:91:'
                        ':3:key'
                        '@SDT/$S:4:name'
                        ':18:display-short-name'
                        '@SDT/$S:4:Name'
                        ':12:display-name'
                        '@SDT/$S:9:Item Name'
                    '@SDT/{:95:'
                        ':3:key'
                        '@SDT/$S:5:color'
                        ':18:display-short-name'
                        '@SDT/$S:5:Color'
                        ':12:display-name'
                        '@SDT/$S:10:Item Color'
                    '@SDT/{:58:'
                        ':3:key'
                        '@SDT/$S:8:category'
                        ':12:display-name'
                        '@SDT/$S:8:Category'
                ':4:name'
                '@SDT/$S:8:ClassFoo'

            # ClassBar:
            ':8:ClassBar'
            '@SDT/{:353:'
                ':4:keys'
                '@SDT/[3:309:'
                    '@SDT/{:95:'
                        ':3:key'
                        '@SDT/$S:5:fname'
                        ':18:display-short-name'
                        '@SDT/$S:5:First'
                        ':12:display-name'
                        '@SDT/$S:10:First Name'
                    '@SDT/{:92:'
                        ':3:key'
                        '@SDT/$S:5:lname'
                        ':18:display-short-name'
                        '@SDT/$S:4:Last'
                        ':12:display-name'
                        '@SDT/$S:9:Last Name'
                    '@SDT/{:92:'
                        ':3:key'
                        '@SDT/$S:6:number'
                        ':18:display-short-name'
                        '@SDT/$S:6:Number'
                        ':12:display-name'
                        '@SDT/$S:6:Number'
                ':4:name'
                '@SDT/$S:8:ClassBar'

            '@SDT/[8:540:'
                '@SDT/%:54::8:ClassFoo'
                    '@SDT/$S:5:Apple'
                    '@SDT/$S:3:Red'
                    '@SDT/$S:5:Fruit'
                '@SDT/%:62::8:ClassFoo'
                    '@SDT/$S:6:Carrot'
                    '@SDT/$S:6:Orange'
                    '@SDT/$S:9:Vegetable'
                '@SDT/%:70::8:ClassFoo'
                    '@SDT/$S:6:Tomato'
                    '@SDT/$S:3:Red'
                    '@SDT/$S:19:Depends who you ask'

                '@SDT/%:59::8:ClassBar'
                    '@SDT/$S:6:George'
                    '@SDT/$S:10:Washington'
                    '@SDT/$S:1:1'
                '@SDT/%:51::8:ClassBar'
                    '@SDT/$S:4:John'
                    '@SDT/$S:5:Adams'
                    '@SDT/$S:1:2'
                '@SDT/%:57::8:ClassBar'
                    '@SDT/$S:6:Thomas'
                    '@SDT/$S:9:Jefferson'
                    '@SDT/$S:1:3'
                '@SDT/%:54::8:ClassBar'
                    '@SDT/$S:5:James'
                    '@SDT/$S:7:Madison'
                    '@SDT/$S:1:4'
                '@SDT/%:53::8:ClassBar'
                    '@SDT/$S:5:James'
                    '@SDT/$S:6:Monroe'
                    '@SDT/$S:1:5'
        )

        unmarshalled = unmarshall(data)

        self.assertEqual(
            unmarshalled,
            [
                {'name': 'Apple', 'color': 'Red', 'category': 'Fruit'},
                {'name': 'Carrot', 'color': 'Orange', 'category': 'Vegetable'},
                {'name': 'Tomato', 'color': 'Red', 'category': 'Depends who you ask'},

                {'fname': 'George', 'lname': 'Washington', 'number': '1'},
                {'fname': 'John', 'lname': 'Adams', 'number': '2'},
                {'fname': 'Thomas', 'lname': 'Jefferson', 'number': '3'},
                {'fname': 'James', 'lname': 'Madison', 'number': '4'},
                {'fname': 'James', 'lname': 'Monroe', 'number': '5'},
            ]
        )

        for mc in unmarshalled[:3]:
            self.assertEqual(mc.display_name('name'), 'Item Name')
            self.assertEqual(mc.display_short_name('name'), 'Name')

            self.assertEqual(mc.display_name('color'), 'Item Color')
            self.assertEqual(mc.display_short_name('color'), 'Color')

            self.assertEqual(mc.display_name('category'), 'Category')
            self.assertTrue(mc.display_short_name('category') is None)

        for mc in unmarshalled[3:]:
            self.assertEqual(mc.display_name('fname'), 'First Name')
            self.assertEqual(mc.display_short_name('fname'), 'First')

            self.assertEqual(mc.display_name('lname'), 'Last Name')
            self.assertEqual(mc.display_short_name('lname'), 'Last')

            self.assertEqual(mc.display_name('number'), 'Number')
            self.assertEqual(mc.display_short_name('number'), 'Number')

    def testNoUnmarshall(self):
        no_tag = [
            '',
            'foo',
            '@',
            '@SDT',
        ]

        tag = [
            '@SDT/',
            '@SDT/$0:0:',
            '@SDT/$S:3:foo',
            '@SDT/[1:15:@SDT/$S:5:Hello'
        ]

        # Data without a tag should never be unmarshalled:
        for test in no_tag:
            self.assertEqual(unmarshall(test), test)

        # Nothing should be unmarshalled with UnmarshallNone:
        for test in no_tag + tag:
            self.assertEqual(unmarshall(test, UNMARSHALL_NONE), test)

    def testInvalidData(self):
        bad_strings = [
            '',
            '@',
            '@SDT',
            '@SDT/',
            'SDT/$S:0:',

            # Scalars

            # There was previously a bug where the character after $ was read
            # without first checking that it actually existed. This test
            # verifies that the bug is fixed.
            '@SDT/$',
            '@SDT/$J',

            '@SDT/$0',
            '@SDT/$0:',
            '@SDT/$0:0',
            '@SDT/$0:0::',
            '@SDT/$0:1:a',

            '@SDT/$S',
            '@SDT/$S:',
            '@SDT/$S:0',
            '@SDT/$S:1:',
            '@SDT/$S:2:foo',

            # Lists

            '@SDT/[0:10:@SDT/$0:0:',
            '@SDT/[1:0:',
            '@SDT/[0:0:foo',
            '@SDT/[',
            '@SDT/[0',
            '@SDT/[0:',
            '@SDT/[0:0',

            # Maps

            '@SDT/{:1:',
            '@SDT/{:6::3:foo',
            '@SDT/{:9::3:foobar',
            '@SDT/{:10:@SDT/$0:0:',
            '@SDT/{:22::3:foo@SDT/$0:0::3:bar',
            '@SDT/{',
            '@SDT/{:',
            '@SDT/{:0',
        ]

        for s in bad_strings:
            try:
                self.assertRaises(STAFUnmarshallError, unmarshall_force, s)
            except AssertionError as e:
                # Hack the string info into the error.
                e.args = ('STAFUnmarshallError not raised for %r' % s,)
                raise

    def testRecursion(self):
        s = '@SDT/$S:24:@SDT/$S:13:@SDT/$S:3:foo'
        self.assertEqual(unmarshall(s), 'foo')
        self.assertEqual(unmarshall(s, UNMARSHALL_NON_RECURSIVE),
                         '@SDT/$S:13:@SDT/$S:3:foo')

        s = '@SDT/[1:21:@SDT/$S:10:@SDT/[0:0:'
        self.assertEqual(unmarshall(s), [[]])
        self.assertEqual(unmarshall(s, UNMARSHALL_NON_RECURSIVE),
                         ['@SDT/[0:0:'])


class MapClassDefinitionTests(unittest.TestCase):
    def testBasicMapClass(self):
        defn = MapClassDefinition('species')
        defn.add_item('common', 'Common Name', 'Common')
        defn.add_item('genus', 'Genus')
        defn.add_item('species', 'Species')

        # https://en.wikipedia.org/wiki/List_of_moths

        # A few different ways to populate items:
        atlas = defn.map_class()
        atlas['common'] = 'Atlas moth'
        atlas['genus'] = 'Attacus'
        atlas['species'] = 'atlas'

        gypsy = defn.map_class()
        gypsy.update(common='Gypsy moth', species='dispar', genus='Lymantria')

        peppered = defn.map_class(common='Peppered moth', genus='Biston',
                                  species='betularia')

        # Make definition from class:
        defn2 = peppered.definition()
        self.assertEqual(defn.keys, defn2.keys)

        # Use new definition:
        zea = defn2.map_class([('common', 'Corn earworm'),
                               ('genus', 'Helicoverpa'), ('species', 'zea')])

        # Modify:
        it = iter(zea.items())
        zea['common'] = 'Cotton bollworm'
        # Iterators pick up changes during iteration.
        self.assertEqual(next(it), ('common', 'Cotton bollworm'))

        # Invalid modifications:
        self.assertRaises(NotImplementedError, atlas.__delitem__, 'common')
        self.assertRaises(NotImplementedError, atlas.clear)
        self.assertRaises(NotImplementedError, atlas.pop, 'common', None)
        self.assertRaises(NotImplementedError, atlas.popitem)
        self.assertRaises(KeyError, atlas.__setitem__, 'name', 'Mothra')
        self.assertRaises(KeyError, atlas.setdefault, 'name', 'Mothra')
        self.assertRaises(KeyError, atlas.update, name='Mothra')

        # Check key ordering:
        moths = [atlas, gypsy, peppered, zea]
        keys = ['common', 'genus', 'species']
        for moth in moths:
            self.assertEqual(list(moth), keys)
            self.assertEqual(list(moth.keys()), keys)
            self.assertEqual(list(moth.keys()), keys)

        # Check value ordering:
        values = ['Cotton bollworm', 'Helicoverpa', 'zea']
        self.assertEqual(list(zea.values()), values)
        self.assertEqual(list(zea.values()), values)

        # Check item ordering:
        items = [('common', 'Cotton bollworm'), ('genus', 'Helicoverpa'),
                 ('species', 'zea')]
        self.assertEqual(list(zea.items()), items)
        self.assertEqual(list(zea.items()), items)

        # Same stuff for views, if supported.
        if hasattr(dict, 'viewitems'):
            for moth in moths:
                self.assertEqual(list(moth.keys()), keys)
            self.assertEqual(list(zea.values()), values)
            self.assertEqual(list(zea.items()), items)

        # Check long & short display names
        for moth in moths:
            self.assertEqual(moth.display_name('common'), 'Common Name')
            self.assertEqual(moth.display_name('genus'), 'Genus')
            self.assertEqual(moth.display_name('species'), 'Species')

            self.assertEqual(moth.display_short_name('common'), 'Common')
            self.assertTrue(moth.display_short_name('genus') is None)
            self.assertTrue(moth.display_short_name('species') is None)


    def testModifyDefinition(self):
        defn = MapClassDefinition('definition')
        defn.add_item('key1', 'Display Name', 'Short Name')
        defn.add_item('key2', 'Display Name 2')

        mc1 = defn.map_class()

        defn.add_item('key3', 'Display Name 3')

        mc2 = defn.map_class()

        # Map Classes have the right keys:
        self.assertEqual(list(mc1.keys()), ['key1', 'key2'])
        self.assertEqual(list(mc2.keys()), ['key1', 'key2', 'key3'])

        # Definitions from MapClasses have the right keys & display names:
        def1 = mc1.definition()
        self.assertEqual(def1.name, 'definition')
        self.assertEqual(def1.keys, ['key1', 'key2'])
        self.assertEqual(def1.display_name('key1'), 'Display Name')
        self.assertEqual(def1.display_name('key2'), 'Display Name 2')
        self.assertEqual(def1.display_short_name('key1'), 'Short Name')
        self.assertTrue(def1.display_short_name('key2') is None)

        def2 = mc2.definition()
        self.assertEqual(def2.name, 'definition')
        self.assertEqual(def2.keys, ['key1', 'key2', 'key3'])
        self.assertEqual(def2.display_name('key1'), 'Display Name')
        self.assertEqual(def2.display_name('key2'), 'Display Name 2')
        self.assertEqual(def2.display_name('key3'), 'Display Name 3')
        self.assertEqual(def2.display_short_name('key1'), 'Short Name')
        self.assertTrue(def2.display_short_name('key2') is None)
        self.assertTrue(def2.display_short_name('key3') is None)

    def testViews(self):
        if not hasattr(dict, 'viewkeys'):
            print('Skipping view tests')
            return

        defn = MapClassDefinition('class-name')
        defn.add_item('alpha', 'Alpha')
        defn.add_item('beta', 'Beta')
        defn.add_item('gamma', 'Gamma')
        defn.add_item('delta', 'Delta')

        mc = defn.map_class(alpha='the first', beta='the second',
                            gamma='the third', delta='the fourth')
        keys = mc.keys()
        values = mc.values()
        items = mc.items()

        # __len__
        self.assertEqual(len(keys), 4)
        self.assertEqual(len(values), 4)
        self.assertEqual(len(items), 4)

        # __contains__
        self.assertTrue('alpha' in keys)
        self.assertTrue('the second' in values)
        self.assertTrue(('gamma', 'the third') in items)

        self.assertFalse('omega' in keys)
        self.assertFalse('the fifth' in values)
        self.assertFalse(('omega', 'the fifth') in items)

        self.assertTrue('omega' not in keys)
        self.assertTrue('the fifth' not in values)
        self.assertTrue(('omega', 'the fifth') not in items)

        self.assertFalse('alpha' not in keys)
        self.assertFalse('the second' not in values)
        self.assertFalse(('gamma', 'the third') not in items)

        # __and__
        self.assertEqual(
            keys & ['alpha', 'gamma', 'omega'],
            set(['alpha', 'gamma'])
        )
        self.assertEqual(
            items & [('beta', 'the second'), 3],
            set([('beta', 'the second')])
        )

        # __or__
        self.assertEqual(
            keys | ['omega'],
            set(['alpha', 'beta', 'gamma', 'delta', 'omega'])
        )
        self.assertEqual(
            items | [10],
            set([('alpha', 'the first'), ('beta', 'the second'),
                 ('gamma', 'the third'), ('delta', 'the fourth'), 10])
        )

        # __sub__
        self.assertEqual(
            keys - ['beta', 'omega'],
            set(['alpha', 'gamma', 'delta'])
        )
        self.assertEqual(
            items - [('beta', 'the second'), ('omega', 'not there')],
            set([('alpha', 'the first'), ('gamma', 'the third'),
                 ('delta', 'the fourth')])
        )

        # __xor__
        self.assertEqual(
            keys ^ ['beta', 'omega'],
            set(['alpha', 'gamma', 'delta', 'omega'])
        )
        self.assertEqual(
            items ^ [('beta', 'the second'), ('omega', 'the last')],
            set([('alpha', 'the first'), ('gamma', 'the third'),
                 ('delta', 'the fourth'), ('omega', 'the last')])
        )

        # no set ops for value views
        self.assertRaises(TypeError, operator.and_, values, set())
        self.assertRaises(TypeError, operator.or_, values, set())
        self.assertRaises(TypeError, operator.sub, values, set())
        self.assertRaises(TypeError, operator.xor, values, set())

        # no set ops for item views with unhashable values
        mc['delta'] = [1]
        self.assertRaises(TypeError, operator.and_, items, set())
        self.assertRaises(TypeError, operator.or_, items, set())
        self.assertRaises(TypeError, operator.sub, items, set())
        self.assertRaises(TypeError, operator.xor, items, set())

        # Changes during iteration
        value_it = iter(values)
        item_it = iter(items)
        self.assertEqual(next(value_it), 'the first')
        self.assertEqual(next(value_it), 'the second')
        self.assertEqual(next(item_it), ('alpha', 'the first'))
        self.assertEqual(next(item_it), ('beta', 'the second'))
        mc['gamma'] = '3rd'
        self.assertEqual(next(value_it), '3rd')
        self.assertEqual(next(item_it), ('gamma', '3rd'))
        mc['gamma'] = 'Third'
        mc['delta'] = 'Fourth'
        self.assertEqual(next(value_it), 'Fourth')
        self.assertEqual(next(item_it), ('delta', 'Fourth'))

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
