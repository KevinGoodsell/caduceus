# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

import time
import unittest

import STAF

class HandleTests(unittest.TestCase):

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
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            pieces = result[0]
            self.assertEqual(pieces['name'], 'test handle')
            self.assertEqual(pieces['state'], 'Registered')


    def testErrors(self):
        h = STAF.Handle('test handle')

        with self.assertRaises(STAF.STAFResultError) as cm:
            h.submit('local', 'doesntexist', 'do magic')
        self.assertEqual(cm.exception.rc, STAF.errors.UnknownService)

        with self.assertRaises(STAF.STAFResultError) as cm:
            h.submit('local', 'ping', 'not a ping command')
        self.assertEqual(cm.exception.rc, STAF.errors.InvalidRequestString)

        h.unregister()

        with self.assertRaises(STAF.STAFResultError) as cm:
            h.submit('local', 'ping', 'ping')
        self.assertEqual(cm.exception.rc, STAF.errors.HandleDoesNotExist)

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

            req = h.submit('local', 'ping', 'ping', h.REQ_FIRE_AND_FORGET)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # No queued result
            with self.assertRaises(STAF.STAFResultError) as cm:
                result = h.submit('local', 'queue', 'get type STAF/RequestComplete')
            self.assertEqual(cm.exception.rc, STAF.errors.NoQueueElement)

            # No retained result
            with self.assertRaises(STAF.STAFResultError) as cm:
                h.submit('local', 'service', ['free request', req])
            self.assertEqual(cm.exception.rc, STAF.errors.RequestNumberNotFound)

            # QUEUE

            req = h.submit('local', 'ping', 'ping', h.REQ_QUEUE)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # Check queued result
            result = h.submit('local', 'queue', 'get type STAF/RequestComplete')
            msg = result['message']
            self.assertEqual(msg['rc'], '0')
            self.assertEqual(msg['requestNumber'], req)
            self.assertEqual(msg['result'], 'PONG')

            # No retained result
            with self.assertRaises(STAF.STAFResultError) as cm:
                h.submit('local', 'service', ['free request', req])
            self.assertEqual(cm.exception.rc, STAF.errors.RequestNumberNotFound)

            # RETAIN

            req = h.submit('local', 'ping', 'ping', h.REQ_RETAIN)
            self.assertTrue(req.isdigit())

            time.sleep(2)

            # No queued result
            with self.assertRaises(STAF.STAFResultError) as cm:
                result = h.submit('local', 'queue', 'get type STAF/RequestComplete')
            self.assertEqual(cm.exception.rc, STAF.errors.NoQueueElement)

            # Check retained result
            result = h.submit('local', 'service', ['free request', req])
            self.assertEqual(result['rc'], '0')
            self.assertEqual(result['result'], 'PONG')

            # QUEUE AND RETAIN

            req = h.submit('local', 'ping', 'ping', h.REQ_QUEUE_RETAIN)
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
