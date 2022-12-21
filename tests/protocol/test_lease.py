#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        lease.py
#
# Abstract:
#
#        Lease tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import array
import functools
import random

import pytest

import pike.model
import pike.smb2
import pike.test


pytestmark = [
    pytest.mark.require_dialect(0x210),
    pytest.mark.require_capabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING),
]

share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)
lease1 = array.array("B", (random.randint(0, 255) for _ in range(16)))
lease2 = array.array("B", (random.randint(0, 255) for _ in range(16)))
r = pike.smb2.SMB2_LEASE_READ_CACHING
rw = r | pike.smb2.SMB2_LEASE_WRITE_CACHING
rh = r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
rwh = rw | rh


@pytest.fixture
def lease_file(pike_tmp_path):
    lease_file = pike_tmp_path / "lease.txt"
    lease_file.create = functools.partial(
        lease_file.create,
        share=share_all,
        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
    )
    yield lease_file
    lease_file.unlink()


def test_lease_upgrade_break(lease_file):
    """Upgrade lease from RW to RWH, then break it to R."""
    # Request rw lease
    with lease_file.create(
        lease_key=lease1,
        lease_state=rw,
    ) as handle1:
        assert handle1.lease.lease_state == rw

        with lease_file.create(
            lease_key=lease1,
            lease_state=rwh,
        ) as handle2:
            assert handle2.lease is handle1.lease
            assert handle2.lease.lease_state == rwh

            # On break, voluntarily give up handle caching
            handle2.lease.on_break(
                lambda state: state & ~pike.smb2.SMB2_LEASE_HANDLE_CACHING
            )

            # Break our lease
            with lease_file.create(
                lease_key=lease2,
                lease_state=rwh,
            ) as handle3:
                # First lease should have broken to r
                assert handle2.lease.lease_state == r
                # Should be granted rh on second lease
                assert handle3.lease.lease_state == rh


def test_lease_break_close_ack(pike_tree_connect, lease_file):
    """Close handle associated with lease while a break is in progress."""
    # Request rw lease
    with lease_file.create(
        lease_key=lease1,
        lease_state=rw,
    ) as handle1:
        # Upgrade to rwh
        with lease_file.create(
            lease_key=lease1,
            lease_state=rwh,
        ) as handle2:
            chan, tree = pike_tree_connect
            # Break our lease (async)
            handle3_future = chan.create(
                tree,
                lease_file._path,
                share=share_all,
                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                lease_key=lease2,
                lease_state=rwh,
            )

            # Wait for break
            handle1.lease.future.wait()

            # Close second handle
            chan.close(handle2)

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle3
            chan.close(handle3_future.result())


def test_lease_multiple_connections(pike_TreeConnect, pike_tree_connect, lease_file):
    """Test that a lease can be shared across connections of the same client."""
    # Request rwh lease
    with lease_file.create(
        lease_key=lease1,
        lease_state=rwh,
    ) as handle1:
        assert handle1.lease.lease_state == rwh
        handle1.lease.on_break(lambda state: state)

        with pike_TreeConnect(client=pike_tree_connect.client) as tc2:
            # Request rwh lease to same file on separate connection,
            # which we should get
            with (tc2 / lease_file).create(
                share=share_all,
                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                lease_key=lease1,
                lease_state=rwh,
            ) as handle2:
                assert handle2.lease.lease_state == rwh

                # Leases should be the same object
                assert handle1.lease == handle2.lease
                # but they should be on different sessions and connections
                assert None not in [handle1.tree, handle2.tree]
                assert handle1.tree != handle2.tree
                assert handle1.channel != handle2.channel
                assert handle1.channel.session != handle2.channel.session
                assert handle1.channel.connection != handle2.channel.connection
