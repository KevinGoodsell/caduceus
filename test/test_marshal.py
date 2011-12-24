import unittest

from STAF import (
    unmarshal,
    STAFUnmarshalError,
    unmarshal_non_recursive,
    unmarshal_none,
)

class Unmarshal(unittest.TestCase):

    def testUnmarshalScalar(self):
        self.assertIs(unmarshal('@SDT/$0:0:'), None)

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
        pass
        # XXX Come back to this

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

        # Data without a tag should never be unmarshalled:
        for test in no_tag:
            self.assertEqual(unmarshal(test), test)

        # Nothing should be unmarshalled with UnmarshalNone:
        for test in no_tag + tag:
            self.assertEqual(unmarshal(test, unmarshal_none), test)

    def testInvalidData(self):
        # Scalars:

        # There was previously a bug where the character after $ was read
        # without first checking that it actually existed. This test verifies
        # that the bug is fixed.
        with self.assertRaises(STAFUnmarshalError):
            unmarshal('@SDT/$')

        # XXX Add more tests here.

    def testRecursion(self):
        s = '@SDT/$S:24:@SDT/$S:13:@SDT/$S:3:foo'
        self.assertEqual(unmarshal(s), 'foo')
        self.assertEqual(unmarshal(s, unmarshal_non_recursive),
                         '@SDT/$S:13:@SDT/$S:3:foo')

        s = '@SDT/[1:21:@SDT/$S:10:@SDT/[0:0:'
        self.assertEqual(unmarshal(s), [[]])
        self.assertEqual(unmarshal(s, unmarshal_non_recursive), ['@SDT/[0:0:'])

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
