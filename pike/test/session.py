#
# Copyright (c) 2013, EMC Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
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
