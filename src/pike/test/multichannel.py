#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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
        return (
            chan.connection.client.connect(self.server)
            .negotiate()
            .session_setup(self.creds, bind=chan.session)
        )

    # Open a file, binding session to second channel, and close it there
    def test_open_bind_close(self):
        chan, tree = self.tree_connect()
        handle = chan.create(tree, "hello.txt").result()

        # Open a second channel and bind the session
        chan2 = self.session_bind(chan)

        # Close the handle on the second channel
        chan2.close(handle)

    # Simulate a channel failover during a write and confirm that a
    # stale write sent on the original channel is rejected
    def test_write_fence_reject_stale(self):
        data_stale = b"stale"
        data_fresh = b"fresh"
        chan, tree = self.tree_connect()
        client = chan.connection.client

        # Open a file
        handle = chan.create(
            tree, "hello.txt", disposition=pike.smb2.FILE_SUPERSEDE
        ).result()

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
