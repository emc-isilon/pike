#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_multichannel.py
#
# Abstract:
#
#        Multichannel tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#          Masen Furer (m_github@0x26.net)
#
import pytest

import pike.smb2
import pike.ntstatus


pytestmark = [
    pytest.mark.require_dialect(pike.smb2.DIALECT_SMB3_0),
    pytest.mark.require_capabilities(pike.smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL),
]


def test_open_bind_close(pike_tree_connect, pike_tmp_path):
    """Open a file, bind second channel to session, and close handle in 2nd channel."""
    handle = (pike_tmp_path / "hello.txt").create()
    # Establish second channel to same server
    tc2 = pike_tree_connect.multichannel()
    # Close the handle on the second channel
    tc2.chan.close(handle)


def test_write_fence_reject_stale(pike_tree_connect, pike_tmp_path):
    """
    Simulate a channel failover during a write.

    Confirm that a stale write sent on the original channel is rejected.
    """
    data_stale = b"stale"
    data_fresh = b"fresh"

    # Open a file
    handle = (pike_tmp_path / "hello.txt").create(disposition=pike.smb2.FILE_SUPERSEDE)

    # Open a second channel
    tc2 = pike_tree_connect.multichannel()

    # Pretend channel failover occured
    pike_tree_connect.client.channel_sequence = 1

    # Send write replay
    with tc2.chan.let(flags=pike.smb2.SMB2_FLAGS_REPLAY_OPERATION):
        tc2.chan.write(handle, 0, data_stale)

    # Send normal write
    tc2.chan.write(handle, 0, data_fresh)

    # Send stale write on original channel, which should fail.
    # Spec is ambiguous as to status code, but Windows Server 2012
    # seems to return STATUS_FILE_NOT_AVAILABLE
    with pike.ntstatus.raises(pike.ntstatus.STATUS_FILE_NOT_AVAILABLE):
        with pike_tree_connect.chan.let(channel_sequence=0):
            pike_tree_connect.chan.write(handle, 0, data_stale)

    # Read back data to ensure it is not stale value
    assert tc2.chan.read(handle, len(data_fresh), 0).tobytes() == data_fresh

    # Close handle
    tc2.chan.close(handle)

    # Close second connection
    tc2.conn.close()
