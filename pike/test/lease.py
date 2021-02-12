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

from builtins import map

import array
import random

import pike.model
import pike.smb2
import pike.test


@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class LeaseTest(pike.test.PikeTest):
    share_all = (
        pike.smb2.FILE_SHARE_READ
        | pike.smb2.FILE_SHARE_WRITE
        | pike.smb2.FILE_SHARE_DELETE
    )
    lease1 = array.array("B", map(random.randint, [0] * 16, [255] * 16))
    lease2 = array.array("B", map(random.randint, [0] * 16, [255] * 16))
    r = pike.smb2.SMB2_LEASE_READ_CACHING
    rw = r | pike.smb2.SMB2_LEASE_WRITE_CACHING
    rh = r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
    rwh = rw | rh

    # Upgrade lease from RW to RWH, then break it to R
    def test_lease_upgrade_break(self):
        chan, tree = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rw,
        ).result()

        self.assertEqual(handle1.lease.lease_state, self.rw)

        handle2 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
        ).result()

        self.assertIs(handle2.lease, handle1.lease)
        self.assertEqual(handle2.lease.lease_state, self.rwh)

        # On break, voluntarily give up handle caching
        handle2.lease.on_break(
            lambda state: state & ~pike.smb2.SMB2_LEASE_HANDLE_CACHING
        )

        # Break our lease
        handle3 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease2,
            lease_state=self.rwh,
        ).result()

        # First lease should have broken to r
        self.assertEqual(handle2.lease.lease_state, self.r)
        # Should be granted rh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rh)

        chan.close(handle1)
        chan.close(handle2)
        chan.close(handle3)

    # Close handle associated with lease while a break is in progress
    def test_lease_break_close_ack(self):
        chan, tree = self.tree_connect()
        # Request rw lease
        handle1 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rw,
        ).result()

        # Upgrade to rwh
        handle2 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
        ).result()

        # Break our lease
        handle3_future = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease2,
            lease_state=self.rwh,
        )

        # Wait for break
        handle1.lease.future.wait()

        # Close second handle
        chan.close(handle2)

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle3
        handle3 = handle3_future.result()

        chan.close(handle1)
        chan.close(handle3)

    # Test that a lease can be shared across connections
    def test_lease_multiple_connections(self):
        chan, tree = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(
            tree,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
        ).result()
        self.assertEqual(handle1.lease.lease_state, self.rwh)

        chan2, tree2 = self.tree_connect()

        # Request rwh lease to same file on separate connection,
        # which we should get
        handle2 = chan2.create(
            tree2,
            "lease.txt",
            share=self.share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
        ).result()
        self.assertEqual(handle2.lease.lease_state, self.rwh)

        # Leases should be the same object
        self.assertEqual(handle1.lease, handle2.lease)

        chan2.close(handle2)
        chan.close(handle1)
