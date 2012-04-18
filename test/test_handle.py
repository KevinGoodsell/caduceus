# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

from __future__ import with_statement

import time
import unittest

import STAF

class HandleTests(unittest.TestCase):

    def assertSTAFResultError(self, rc, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.fail('STAFResultError not raised')
        except STAF.STAFResultError, exc:
            self.assertEqual(exc.rc, rc)

    def testBasicHandle(self):
        with STAF.Handle('test handle') as h:
            result = h.submit('local', 'ping', 'ping')
            self.assertEqual(result, 'PONG')

            result = h.submit('local', 'ping', ['ping'])
            self.assertEqual(result, 'PONG')

            result = h.submit('local', 'service', 'list')
            services = dict((s['name'], s) for s in result)
            # There's not much reason to check all these, so just pick a few.
            self.assertEqual(services['DELAY'],
                             {'name': 'DELAY', 'executable': None,
                              'library': '<Internal>'})
            self.assertEqual(services['DIAG'],
                             {'name': 'DIAG', 'executable': None,
                              'library': '<Internal>'})
            self.assertEqual(services['ECHO'],
                             {'name': 'ECHO', 'executable': None,
                              'library': '<Internal>'})

            # Submit using a list
            result = h.submit('local', 'handle',
                              ['list handles name', 'test handle', 'long'])
            self.assertTrue(isinstance(result, list))
            self.assertEqual(len(result), 1)
            pieces = result[0]
            self.assertEqual(pieces['name'], 'test handle')
            self.assertEqual(pieces['state'], 'Registered')

            self.assertTrue(h.is_registered())

        self.assertFalse(h.is_registered())


    def testErrors(self):
        h = STAF.Handle('test handle')

        self.assertSTAFResultError(STAF.errors.UnknownService,
                h.submit, 'local', 'doesntexist', 'do magic')

        self.assertSTAFResultError(STAF.errors.InvalidRequestString,
                h.submit, 'local', 'ping', 'not a ping command')

        h.unregister()

        self.assertSTAFResultError(STAF.errors.HandleDoesNotExist,
                h.submit, 'local', 'ping', 'ping')

        # Unregistering a second time should not produce an error.
        h.unregister()


    def testStaticHandle(self):
        with STAF.Handle('helper') as helper:
            self.assertFalse(helper.is_static())

            handle_num = helper.submit('local', 'handle',
                                       'create handle name static-test')
            handle_num = int(handle_num)
            h = STAF.Handle(handle_num)
            self.assertTrue(h.is_static())

            self.assertEqual(h.submit('local', 'ping', 'ping'), 'PONG')

            # Unregistering a static handle does nothing.
            h.unregister()
            self.assertEqual(h.submit('local', 'ping', 'ping'), 'PONG')

            # Delete the static handle
            helper.submit('local', 'handle',
                          ['delete handle', str(h.handle_num())])


    def testSyncModes(self):
        with STAF.Handle('test handle') as h:

            # FIRE AND FORGET

            req = h.submit('local', 'ping', 'ping', STAF.REQ_FIRE_AND_FORGET)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # No queued result
            self.assertSTAFResultError(STAF.errors.NoQueueElement,
                    h.submit, 'local', 'queue', 'get type STAF/RequestComplete')

            # No retained result
            self.assertSTAFResultError(STAF.errors.RequestNumberNotFound,
                    h.submit, 'local', 'service', ['free request', req])

            # QUEUE

            req = h.submit('local', 'ping', 'ping', STAF.REQ_QUEUE)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # Check queued result
            result = h.submit('local', 'queue', 'get type STAF/RequestComplete')
            msg = result['message']
            self.assertEqual(msg['rc'], '0')
            self.assertEqual(msg['requestNumber'], req)
            self.assertEqual(msg['result'], 'PONG')

            # No retained result
            self.assertSTAFResultError(STAF.errors.RequestNumberNotFound,
                    h.submit, 'local', 'service', ['free request', req])

            # RETAIN

            req = h.submit('local', 'ping', 'ping', STAF.REQ_RETAIN)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # No queued result
            self.assertSTAFResultError(STAF.errors.NoQueueElement,
                    h.submit, 'local', 'queue', 'get type STAF/RequestComplete')

            # Check retained result
            result = h.submit('local', 'service', ['free request', req])
            self.assertEqual(result['rc'], '0')
            self.assertEqual(result['result'], 'PONG')

            # QUEUE AND RETAIN

            req = h.submit('local', 'ping', 'ping', STAF.REQ_QUEUE_RETAIN)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # Check queued result
            result = h.submit('local', 'queue', 'get type STAF/RequestComplete')
            msg = result['message']
            self.assertEqual(msg['rc'], '0')
            self.assertEqual(msg['requestNumber'], req)
            self.assertEqual(msg['result'], 'PONG')

            # Check retained result
            result = h.submit('local', 'service', ['free request', req])
            self.assertEqual(result['rc'], '0')
            self.assertEqual(result['result'], 'PONG')


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
