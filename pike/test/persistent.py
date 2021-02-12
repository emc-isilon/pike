#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        persistent.py
#
# Abstract:
#
#        Persistent handle tests
#
# Authors: Paul Martin (paul.o.martin@emc.com)
#

from builtins import map

import array
import random
import time

import pike.model
import pike.smb2 as smb2
import pike.test as test
import pike.ntstatus as ntstatus

# Constants
LEASE_R = smb2.SMB2_LEASE_READ_CACHING
LEASE_RW = LEASE_R | smb2.SMB2_LEASE_WRITE_CACHING
LEASE_RH = LEASE_R | smb2.SMB2_LEASE_HANDLE_CACHING
LEASE_RWH = LEASE_RW | LEASE_RH
SHARE_ALL = smb2.FILE_SHARE_READ | smb2.FILE_SHARE_WRITE | smb2.FILE_SHARE_DELETE


class InvalidNetworkResiliencyRequestRequest(pike.smb2.NetworkResiliencyRequestRequest):
    def _encode(self, cur):
        cur.encode_uint32le(self.timeout)
        cur.encode_uint16le(self.reserved)


@test.RequireDialect(smb2.DIALECT_SMB3_0)
@test.RequireCapabilities(smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)
@test.RequireShareCapabilities(smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY)
class Persistent(test.PikeTest):
    def setup(self):
        self.lease_key = array.array("B", map(random.randint, [0] * 16, [255] * 16))
        self.channel, self.tree = self.tree_connect()

    def create_persistent(self, prev_handle=0):
        """Helper to create a persistent handle, optionally reconnecting an old one"""
        handle = self.channel.create(
            self.tree,
            "persistent.txt",
            access=smb2.FILE_READ_DATA | smb2.FILE_WRITE_DATA | smb2.DELETE,
            share=SHARE_ALL,
            disposition=smb2.FILE_OPEN_IF,
            options=smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease_key,
            lease_state=LEASE_RWH,
            durable=prev_handle,
            persistent=True,
        ).result()
        self.assertEqual(handle.durable_flags, smb2.SMB2_DHANDLE_FLAG_PERSISTENT)

        return handle

    # Opening a persistent handle grants persistent flag
    def test_create(self):
        handle = self.create_persistent()
        self.channel.close(handle)

    # Reconnecting a persistent handle after TCP disconnect works and preserves lease
    def test_reconnect(self):
        # Do a persistent open, drop connection, reconnect
        handle1 = self.create_persistent()
        self.channel.connection.close()
        self.channel, self.tree = self.tree_connect()

        handle2 = self.create_persistent(prev_handle=handle1)

        # Was the original lease state granted in the response?
        self.assertEqual(handle2.lease.lease_state, LEASE_RWH)

        self.channel.close(handle2)

    # Opening a file with a disconnected persistent handle fails with
    # STATUS_FILE_NOT_AVAILABLE
    def test_open_while_disconnected(self):
        # Do a persistent open, drop connection, reconnect
        handle1 = self.create_persistent()
        self.channel.connection.close()
        self.channel, self.tree = self.tree_connect()

        with self.assert_error(ntstatus.STATUS_FILE_NOT_AVAILABLE):
            # Perform a failing second open
            self.channel.create(
                self.tree,
                "persistent.txt",
                access=smb2.FILE_READ_DATA,
                share=SHARE_ALL,
                disposition=smb2.FILE_OPEN,
            ).result()

        # Clean up: Reconnect and close file (handle)
        self.channel.connection.close()
        self.channel, self.tree = self.tree_connect()
        handle2 = self.create_persistent(prev_handle=handle1)
        self.assertEqual(handle1.file_id, handle2.file_id)
        self.channel.close(handle2)

    def test_resiliency_same_timeout_reconnect_before_timeout(self):
        handle1 = self.create_persistent()
        self.assertTrue(handle1.is_persistent)
        timeout = handle1.durable_timeout
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)
        self.channel.connection.close()

        #  sleeping time = resiliemcy < ca's default 120s
        time.sleep(min(handle1.durable_timeout / 1000.0, 1))
        self.channel, self.tree = self.tree_connect(client=pike.model.Client())

        # Invalidate handle from separate client
        with self.assert_error(ntstatus.STATUS_FILE_NOT_AVAILABLE):
            handle2 = self.channel.create(
                self.tree,
                "persistent.txt",
                access=smb2.FILE_READ_DATA,
                share=SHARE_ALL,
                disposition=pike.smb2.FILE_OPEN,
            ).result()

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()
        handle3 = self.create_persistent(prev_handle=handle1)

        # handle1 and handle3 has the same file_id, and the same persistent status
        # it seams that resilience has not impacted the result of reconnect
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertTrue(handle3.is_resilient)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_resiliency_reconnect_before_timeout(self):
        handle1 = self.create_persistent()
        self.assertTrue(handle1.is_persistent)
        timeout = 4000
        wait_time = timeout / 1000.0 * 0.5
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)

        self.channel.connection.close()

        #  sleeping time < resiliemcy < ca's default 120s
        time.sleep(wait_time)

        self.channel, self.tree = self.tree_connect(client=pike.model.Client())
        with self.assert_error(ntstatus.STATUS_FILE_NOT_AVAILABLE):
            handle2 = self.channel.create(
                self.tree,
                "persistent.txt",
                access=smb2.FILE_READ_DATA,
                share=SHARE_ALL,
                disposition=pike.smb2.FILE_OPEN,
            ).result()

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()
        handle3 = self.create_persistent(prev_handle=handle1)

        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertTrue(handle3.is_resilient)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_resiliency_reconnect_after_timeout(self):
        handle1 = self.create_persistent()
        self.assertTrue(handle1.is_persistent)
        timeout = 2000
        wait_time = timeout / 1000.0 * 1.1
        # ensure that the wait_time is _less_ than the granted timeout
        # to confirm that the resiliency request updates the timeout
        self.assertLess(wait_time, handle1.durable_timeout)
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)
        self.channel.connection.close()

        # resiliemcy < sleeping time < ca's default 120s
        time.sleep(wait_time)

        self.channel, self.tree = self.tree_connect(client=pike.model.Client())

        # Because resiliency timeout, so another opener:handle2 break the persistent
        handle2 = self.channel.create(
            self.tree,
            "persistent.txt",
            access=smb2.FILE_READ_DATA,
            share=SHARE_ALL,
            disposition=pike.smb2.FILE_OPEN,
        )
        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()
        # Because resiliency timeout, other opener has broken the persistent, so reconnect would fail
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create_persistent(prev_handle=handle1)

    def test_resiliency_same_timeout_reconnect_after_timeout(self):
        handle1 = self.create_persistent()
        self.assertTrue(handle1.is_persistent)

        # set ca's timeout equals resiliency's timeout
        timeout = handle1.durable_timeout
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.assertTrue(handle1.is_resilient)
        self.channel.connection.close()

        # resilience's timeout = ca's defaut 120s < sleeping time
        time.sleep(handle1.durable_timeout / 1000.0 + 1)

        # timeout, can't get object name
        self.channel, self.tree = self.tree_connect()
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create_persistent(prev_handle=handle1)

    def test_buffer_too_small(self):
        handle1 = self.create_persistent()
        self.assertTrue(handle1.is_persistent)

        timeout = 5
        with self.assert_error(pike.ntstatus.STATUS_BUFFER_TOO_SMALL):  # just for onefs
            smb_req = self.channel.request(obj=handle1.tree)
            ioctl_req = pike.smb2.IoctlRequest(smb_req)
            vni_req = InvalidNetworkResiliencyRequestRequest(ioctl_req)
            ioctl_req.file_id = handle1.file_id
            ioctl_req.flags = pike.smb2.SMB2_0_IOCTL_IS_FSCTL
            vni_req.Timeout = timeout
            vni_req.Reserved = 0
            a = self.channel.connection.transceive(ioctl_req.parent.parent)[0]

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect(client=pike.model.Client())
        with self.assert_error(ntstatus.STATUS_FILE_NOT_AVAILABLE):
            handle2 = self.channel.create(
                self.tree,
                "persistent.txt",
                access=smb2.FILE_READ_DATA,
                share=SHARE_ALL,
                disposition=pike.smb2.FILE_OPEN,
            ).result()

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()

        # resiliency's buffer too small has not impacted persistent status
        handle3 = self.create_persistent(prev_handle=handle1)
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertFalse(handle3.is_resilient)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)
