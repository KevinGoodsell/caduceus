# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

import unittest

from STAF import (
    unmarshal,
    unmarshal_force,
    STAFUnmarshalError,
    UNMARSHAL_NON_RECURSIVE,
    UNMARSHAL_NONE,
)

class Unmarshal(unittest.TestCase):

    def testUnmarshalScalar(self):
        self.assertTrue(unmarshal('@SDT/$0:0:') is None)

        self.assertEqual(unmarshal('@SDT/$S:0:'), '')
        self.assertEqual(unmarshal('@SDT/$S:3:foo'), 'foo')
        self.assertEqual(unmarshal('@SDT/$S:10:   \tab\n   '), '   \tab\n   ')

    def testUnmarshalMap(self):
        self.assertEqual(unmarshal('@SDT/{:0:'), {})
        self.assertEqual(unmarshal('@SDT/{:13::0:@SDT/$0:0:'), {'': None})
        self.assertEqual(unmarshal('@SDT/{:53:'
                                   ':8:some key@SDT/$0:0:'
                                   ':7:another@SDT/$S:11:foo bar baz'),
                         {'some key': None, 'another': 'foo bar baz'})

    def testUnmarshalList(self):
        self.assertEqual(unmarshal('@SDT/[0:0:'), [])
        self.assertEqual(unmarshal('@SDT/[4:42:'
                                   '@SDT/[0:0:'
                                   '@SDT/$0:0:'
                                   '@SDT/$S:3:foo'
                                   '@SDT/{:0:'),
                         [[], None, 'foo', {}])

    def testUnmarshalMapClass(self):
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

        unmarshaled = unmarshal(data)

        self.assertEqual(
            unmarshaled,
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

        for mc in unmarshaled[:3]:
            self.assertEqual(mc.display_name('name'), 'Item Name')
            self.assertEqual(mc.display_short_name('name'), 'Name')

            self.assertEqual(mc.display_name('color'), 'Item Color')
            self.assertEqual(mc.display_short_name('color'), 'Color')

            self.assertEqual(mc.display_name('category'), 'Category')
            self.assertTrue(mc.display_short_name('category') is None)

        for mc in unmarshaled[3:]:
            self.assertEqual(mc.display_name('fname'), 'First Name')
            self.assertEqual(mc.display_short_name('fname'), 'First')

            self.assertEqual(mc.display_name('lname'), 'Last Name')
            self.assertEqual(mc.display_short_name('lname'), 'Last')

            self.assertEqual(mc.display_name('number'), 'Number')
            self.assertEqual(mc.display_short_name('number'), 'Number')

    def testNoUnmarshal(self):
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

        # Data without a tag should never be unmarshaled:
        for test in no_tag:
            self.assertEqual(unmarshal(test), test)

        # Nothing should be unmarshaled with UnmarshalNone:
        for test in no_tag + tag:
            self.assertEqual(unmarshal(test, UNMARSHAL_NONE), test)

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
                self.assertRaises(STAFUnmarshalError, unmarshal_force, s)
            except AssertionError, e:
                # Hack the string info into the error.
                e.args = ('STAFUnmarshalError not raised for %r' % s,)
                raise

    def testRecursion(self):
        s = '@SDT/$S:24:@SDT/$S:13:@SDT/$S:3:foo'
        self.assertEqual(unmarshal(s), 'foo')
        self.assertEqual(unmarshal(s, UNMARSHAL_NON_RECURSIVE),
                         '@SDT/$S:13:@SDT/$S:3:foo')

        s = '@SDT/[1:21:@SDT/$S:10:@SDT/[0:0:'
        self.assertEqual(unmarshal(s), [[]])
        self.assertEqual(unmarshal(s, UNMARSHAL_NON_RECURSIVE), ['@SDT/[0:0:'])

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
