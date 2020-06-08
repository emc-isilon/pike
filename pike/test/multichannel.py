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
#        multichannel.py
#
# Abstract:
#
#        Multichannel tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

@pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)
class MultiChannelTest(pike.test.PikeTest):
    def session_bind(self, chan):
        return chan.connection.client.connect(self.server).negotiate().session_setup(self.creds, bind=chan.session)

    # Open a file, binding session to second channel, and close it there
    def test_open_bind_close(self):
        chan, tree = self.tree_connect()
        handle = chan.create(tree, 'hello.txt').result()

        # Open a second channel and bind the session
        chan2 = self.session_bind(chan)
    
        # Close the handle on the second channel
        chan2.close(handle)

    # Simulate a channel failover during a write and confirm that a
    # stale write sent on the original channel is rejected
    def test_write_fence_reject_stale(self):
        data_stale = b'stale'
        data_fresh = b'fresh'
        chan, tree = self.tree_connect()
        client = chan.connection.client
        
        # Open a file
        handle = chan.create(tree, 'hello.txt', disposition=pike.smb2.FILE_SUPERSEDE).result()

        # Open a second channel
        chan2 = self.session_bind(chan)

        # Pretend channel failover occured
        client.channel_sequence = 1

        # Send write replay
        with chan2.let(flags=pike.smb2.SMB2_FLAGS_REPLAY_OPERATION):
            chan2.write(handle, 0, data_stale)

        # Send normal write
        chan2.write(handle, 0, data_fresh)

        # Send stale write on original channel, which should fail.
        # Spec is ambiguous as to status code, but Windows Server 2012
        # seems to return STATUS_FILE_NOT_AVAILABLE
        with self.assert_error(pike.ntstatus.STATUS_FILE_NOT_AVAILABLE):
            with chan.let(channel_sequence=0):
                chan.write(handle, 0, data_stale)

        # Read back data to ensure it is not stale value
        result = chan2.read(handle, len(data_fresh), 0).tobytes()
        self.assertEquals(result, data_fresh)

        # Close handle
        chan2.close(handle)

        # Close second connection
        chan2.connection.close()
