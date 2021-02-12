#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        session.py
#
# Abstract:
#
#        Session setup tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.test


class SessionTest(pike.test.PikeTest):
    # Log off a session
    def test_session_logoff(self):
        chan, tree = self.tree_connect()
        chan.logoff()

    def test_session_multiplex(self):
        chan, tree = self.tree_connect()
        chan2 = chan.connection.session_setup(self.creds)
        chan3 = chan.connection.session_setup(self.creds)
        self.assertEqual(chan.connection, chan2.connection)
        self.assertEqual(chan2.connection, chan3.connection)
        self.assertNotEqual(chan.session, chan2.session)
        self.assertNotEqual(chan2.session, chan3.session)
        self.assertNotEqual(chan.session.session_id, chan2.session.session_id)
        self.assertNotEqual(chan2.session.session_id, chan3.session.session_id)
        self.assertNotEqual(chan.session.session_key, chan2.session.session_key)
        self.assertNotEqual(chan2.session.session_key, chan3.session.session_key)
        tree2 = chan2.tree_connect(self.share)
        tree3 = chan3.tree_connect(self.share)
        chan3.logoff()
        chan2.logoff()
        chan.logoff()
