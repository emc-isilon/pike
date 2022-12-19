#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        durable.py
#
# Abstract:
#
#        Durable handle tests
#
# Authors: Arlene Berry (arlene.berry@emc.com)
#

from builtins import map

import array
import random
import time

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus


# for buffer too small
class InvalidNetworkResiliencyRequestRequest(pike.smb2.NetworkResiliencyRequestRequest):
    def _encode(self, cur):
        cur.encode_uint32le(self.timeout)
        cur.encode_uint16le(self.reserved)


@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class DurableHandleTest(pike.test.PikeTest):
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
    buffer_too_small_error = pike.ntstatus.STATUS_INVALID_PARAMETER

    def create(
        self,
        chan,
        tree,
        durable,
        lease=rwh,
        lease_key=lease1,
        disposition=pike.smb2.FILE_SUPERSEDE,
    ):
        return chan.create(
            tree,
            "durable.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=self.share_all,
            disposition=disposition,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=lease_key,
            lease_state=lease,
            durable=durable,
        ).result()

    def durable_test(self, durable):
        chan, tree = self.tree_connect()

        handle1 = self.create(chan, tree, durable=durable)

        self.assertEqual(handle1.lease.lease_state, self.rwh)
        self.assertTrue(handle1.is_durable)

        chan.close(handle1)

    def durable_reconnect_test(self, durable):
        chan, tree = self.tree_connect()

        handle1 = self.create(chan, tree, durable=durable)

        self.assertEqual(handle1.lease.lease_state, self.rwh)
        self.assertTrue(handle1.is_durable)

        # Close the connection
        chan.connection.close()

        chan2, tree2 = self.tree_connect()

        # Request reconnect
        handle2 = self.create(chan2, tree2, durable=handle1)
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        self.assertTrue(handle2.is_durable)
        chan2.close(handle2)

    def durable_reconnect_fails_client_guid_test(self, durable):
        chan, tree = self.tree_connect()

        handle1 = self.create(chan, tree, durable=durable)
        self.assertTrue(handle1.is_durable)

        self.assertEqual(handle1.lease.lease_state, self.rwh)

        # Close the connection
        chan.connection.close()

        chan2, tree2 = self.tree_connect(client=pike.model.Client())

        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle2 = self.create(chan2, tree2, durable=handle1)

        chan2.connection.close()

        chan3, tree3 = self.tree_connect()

        handle3 = self.create(chan3, tree3, durable=handle1)
        self.assertTrue(handle3.is_durable)

        chan3.close(handle3)

    def durable_invalidate_test(self, durable):
        chan, tree = self.tree_connect()

        handle1 = self.create(chan, tree, durable=durable)
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        self.assertTrue(handle1.is_durable)

        # Close the connection
        chan.connection.close()

        chan2, tree2 = self.tree_connect(client=pike.model.Client())

        # Invalidate handle from separate client
        handle2 = self.create(
            chan2,
            tree2,
            durable=durable,
            lease=self.rw,
            lease_key=self.lease2,
            disposition=pike.smb2.FILE_OPEN,
        )
        self.assertEqual(handle2.lease.lease_state, self.rw)
        chan2.close(handle2)

        chan2.connection.close()

        chan3, tree3 = self.tree_connect()

        # Reconnect should now fail
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create(chan3, tree3, durable=handle1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_reconnect_before_timeout(self, durable=True):
        chan, tree = self.tree_connect()
        handle1 = self.create(chan, tree, durable=durable)
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        self.assertEqual(handle1.is_durable, durable)
        timeout = 100

        a = chan.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)

        # Close the connection
        chan.connection.close()
        time.sleep((timeout - 10) / 1000.0)

        chan2, tree2 = self.tree_connect(client=pike.model.Client())

        handle2 = self.create(
            chan2,
            tree2,
            durable=durable,
            lease=self.rw,
            lease_key=self.lease2,
            disposition=pike.smb2.FILE_OPEN,
        )
        # resiliency interact handle2's lease_status(before rw, now r)
        self.assertEqual(handle2.lease.lease_state, self.r)
        chan2.close(handle2)
        chan2.connection.close()
        chan3, tree3 = self.tree_connect()
        handle3 = self.create(chan3, tree3, durable=handle1)
        self.assertTrue(handle3.is_resilient)

        # cause of the resiliency, handle1.fileid would be equals to handle3's.
        self.assertEqual(handle1.file_id, handle3.file_id)
        chan3.close(handle3)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_reconnect_after_timeout(self, durable=True):
        chan, tree = self.tree_connect()
        handle1 = self.create(chan, tree, durable=durable, lease=self.rwh)
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        self.assertEqual(handle1.is_durable, durable)
        timeout = 100
        a = chan.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)

        # Close the connection
        chan.connection.close()
        time.sleep(timeout / 1000.0 + 5.0)  # timeout

        chan2, tree2 = self.tree_connect(client=pike.model.Client())
        # Invalidate handle from separate client
        handle2 = self.create(
            chan2,
            tree2,
            durable=durable,
            lease=self.rw,
            lease_key=self.lease2,
            disposition=pike.smb2.FILE_OPEN,
        )

        self.assertEqual(handle2.lease.lease_state, self.rw)
        chan2.close(handle2)
        chan2.connection.close()
        chan3, tree3 = self.tree_connect()

        # Reconnect should fail(resiliency timeout)
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create(chan3, tree3, durable=handle1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_buffer_too_small(self, durable=True):
        chan, tree = self.tree_connect()
        handle1 = self.create(chan, tree, durable=durable)
        self.assertEqual(handle1.is_durable, durable)

        timeout = 5
        with self.assert_error(self.buffer_too_small_error):
            smb_req = chan.request(obj=handle1.tree)
            ioctl_req = pike.smb2.IoctlRequest(smb_req)
            # replace with invalid request that has short input buffer
            invalid_nrr_req = InvalidNetworkResiliencyRequestRequest(ioctl_req)
            ioctl_req.file_id = handle1.file_id
            ioctl_req.flags = pike.smb2.SMB2_0_IOCTL_IS_FSCTL
            invalid_nrr_req.timeout = timeout
            invalid_nrr_req.reserved = 0
            a = chan.connection.transceive(ioctl_req.parent.parent)[0]

        self.assertEqual(handle1.lease.lease_state, self.rwh)
        chan.connection.close()

        chan2, tree2 = self.tree_connect(client=pike.model.Client())
        handle2 = self.create(
            chan2,
            tree2,
            durable=durable,
            lease=self.rw,
            lease_key=self.lease2,
            disposition=pike.smb2.FILE_OPEN,
        )

        self.assertEqual(handle2.lease.lease_state, self.rw)
        chan2.close(handle2)
        chan2.connection.close()

        chan3, tree3 = self.tree_connect()
        # buffer too small
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create(chan3, tree3, durable=handle1)

    # the resiliency_upgrade tests start with a non-durable handle
    # and upgrade to resilient handle by use of ioctl
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_upgrade_reconnect_before_timeout(self):
        self.test_resiliency_reconnect_before_timeout(durable=False)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_upgrade_reconnect_after_timeout(self):
        self.test_resiliency_reconnect_after_timeout(durable=False)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_resiliency_upgrade_buffer_too_small(self):
        self.test_resiliency_buffer_too_small(durable=False)

    # Request a durable handle
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_durable(self):
        self.durable_test(True)

    # Reconnect a durable handle after a TCP disconnect
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_durable_reconnect(self):
        self.durable_reconnect_test(True)

    # Reconnecting a durable handle after a TCP disconnect
    # fails with STATUS_OBJECT_NAME_NOT_FOUND if the client
    # guid does not match
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_durable_reconnect_fails_client_guid(self):
        self.durable_reconnect_fails_client_guid_test(True)

    # Breaking the lease of a disconnected durable handle
    # (without HANDLE) invalidates it, so a subsequent
    # reconnect will fail.
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_durable_invalidate(self):
        self.durable_invalidate_test(True)

    # Request a durable handle via V2 context structure
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_durable_v2(self):
        self.durable_test(0)

    # Reconnect a durable handle via V2 context structure
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_durable_reconnect_v2(self):
        self.durable_reconnect_test(0)

    # Reconnecting a durable handle (v2) after a TCP disconnect
    # fails with STATUS_OBJECT_NAME_NOT_FOUND if the client
    # guid does not match
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_durable_reconnect_v2_fails_client_guid(self):
        self.durable_reconnect_fails_client_guid_test(0)

    # Breaking the lease of a disconnected durable handle v2
    # (without HANDLE) invalidates it, so a subsequent
    # reconnect will fail.
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_durable_v2_invalidate(self):
        self.durable_invalidate_test(0)
