# coding=utf-8
#
# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

import unittest

from STAF import (
    add_privacy_delimiters,
    remove_privacy_delimiters,
    mask_private_data,
    escape_privacy_delimiters,
)

class PrivateData(unittest.TestCase):
    def testAddDelims(self):
        # Basic delimiter addition
        self.assertEqual(add_privacy_delimiters(''), '')
        self.assertEqual(add_privacy_delimiters('foo'), '!!@foo@!!')
        wierd_chars = '`~!@#$%^&*()[{}]\\|=/?+\'",<>.;:'
        self.assertEqual(add_privacy_delimiters(wierd_chars),
                         '!!@' + wierd_chars + '@!!')

        # Unicode, using some latin-1 and braile chars
        text = u'¿ÀÁÂÃÄÅÆÇ⠑⠒⠓'
        self.assertEqual(add_privacy_delimiters(text), u'!!@' + text + u'@!!')

        # Double-application has no effect:
        self.assertEqual(add_privacy_delimiters(add_privacy_delimiters('foo')),
                         '!!@foo@!!')

        # Inner delimiters are escaped:
        self.assertEqual(add_privacy_delimiters('@!!-!!@-@!!'),
                         '!!@^@!!-^!!@-^@!!@!!')

    def testEscapeDelims(self):
        self.assertEqual(escape_privacy_delimiters('!!@@!!'), '^!!@^@!!')
        self.assertEqual(escape_privacy_delimiters('@!!!!@'), '^@!!^!!@')

        self.assertEqual(escape_privacy_delimiters('foo @!! @@!! !!@ !!!@ bar'),
                         'foo ^@!! @^@!! ^!!@ !^!!@ bar')

        self.assertEqual(escape_privacy_delimiters('foo'), 'foo')
        self.assertEqual(escape_privacy_delimiters(''), '')

    def testRemoveDelims(self):
        # No delims
        self.assertEqual(remove_privacy_delimiters(''), '')
        self.assertEqual(remove_privacy_delimiters('foo'), 'foo')

        # Individual delims aren't touched, only matched pairs.
        self.assertEqual(remove_privacy_delimiters('@!!'), '@!!')
        self.assertEqual(remove_privacy_delimiters('!!@'), '!!@')

        # Reversed delims aren't detected, they have to be in the right order.
        self.assertEqual(remove_privacy_delimiters('@!!!!@'), '@!!!!@')

        # Basic removal
        self.assertEqual(remove_privacy_delimiters('!!@@!!'), '')
        self.assertEqual(remove_privacy_delimiters('!!@ @!!'), ' ')
        self.assertEqual(remove_privacy_delimiters('!!@ a b c d @!!'),
                         ' a b c d ')
        self.assertEqual(remove_privacy_delimiters('foo!!@bar@!!baz'),
                         'foobarbaz')

        # Removal with unicode (mixed character length)
        self.assertEqual(remove_privacy_delimiters(u'¿ÀÁA!!@ÂÃAÄÅ@!!ÆAÇ⠑⠒⠓'),
                         u'¿ÀÁAÂÃAÄÅÆAÇ⠑⠒⠓')

        # Multi-level delims with un-escaping
        nested = 'foo !!@ bar ^!!@ baz ^^@!! quux ^@!! more @!! blah'
        self.assertEqual(remove_privacy_delimiters(nested),
                         'foo  bar  baz @!! quux  more  blah')
        self.assertEqual(remove_privacy_delimiters(nested, 1),
                         'foo  bar !!@ baz ^@!! quux @!! more  blah')
        self.assertEqual(remove_privacy_delimiters(nested, 2),
                         'foo  bar  baz @!! quux  more  blah')
        self.assertEqual(remove_privacy_delimiters(nested, 3),
                         'foo  bar  baz @!! quux  more  blah')

    def testMaskPrivateData(self):
        self.assertEqual(mask_private_data(''), '')
        self.assertEqual(mask_private_data('foo'), 'foo')
        self.assertEqual(mask_private_data('!!@@!!'), '******')
        self.assertEqual(mask_private_data('!!@secrets@!!'),
                         '*************')
        self.assertEqual(mask_private_data('My password is !!@magicbeans@!!!'),
                         'My password is ****************!')
        self.assertEqual(mask_private_data('!!@ No closing delim'),
                         '!!@ No closing delim')


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
