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
#        persistent.py
#
# Abstract:
#
#        Persistent handle tests
#
# Authors: Paul Martin (paul.o.martin@emc.com)
#

import pike.model as model
import pike.smb2 as smb2
import pike.test as test
import pike.ntstatus as ntstatus
import random
import array
import time
import pike.model

# Constants
LEASE_R   = smb2.SMB2_LEASE_READ_CACHING
LEASE_RW  = LEASE_R | smb2.SMB2_LEASE_WRITE_CACHING
LEASE_RH  = LEASE_R | smb2.SMB2_LEASE_HANDLE_CACHING
LEASE_RWH = LEASE_RW | LEASE_RH
SHARE_ALL = smb2.FILE_SHARE_READ | smb2.FILE_SHARE_WRITE | smb2.FILE_SHARE_DELETE

class _testNetworkResiliencyRequestRequest(pike.smb2.NetworkResiliencyRequestRequest):
    def  _encode(self, cur):
        cur.encode_uint32le(self.timeout)
        cur.encode_uint16le(self.reserved)

@test.RequireDialect(smb2.DIALECT_SMB3_0)
@test.RequireCapabilities(smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)
@test.RequireShareCapabilities(smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY)
class Persistent(test.PikeTest):

    def setup(self):
        self.lease_key = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.channel, self.tree = self.tree_connect()

    def create_persistent(self, prev_handle = 0):
        """Helper to create a persistent handle, optionally reconnecting an old one"""
        handle = self.channel.create(
            self.tree,
            "persistent.txt",
            access = smb2.FILE_READ_DATA | smb2.FILE_WRITE_DATA | smb2.DELETE,
            share = SHARE_ALL,
            disposition = smb2.FILE_OPEN_IF,
            options = smb2.FILE_DELETE_ON_CLOSE,
            oplock_level = smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key = self.lease_key,
            lease_state = LEASE_RWH,
            durable = prev_handle,
            persistent = True
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

        handle2 = self.create_persistent(prev_handle = handle1)

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
                access = smb2.FILE_READ_DATA,
                share = SHARE_ALL,
                disposition = smb2.FILE_OPEN).result()

        # Clean up: Reconnect and close file (handle)
        self.channel.connection.close()
        self.channel, self.tree = self.tree_connect()
        handle2 = self.create_persistent(prev_handle = handle1)
        self.assertTrue(handle1)
        self.assertTrue(handle2)
        self.assertEqual(handle1.file_id, handle2.file_id)
        self.channel.close(handle2)

    def test_resiliency_interact_persistent(self):
        handle1 = self.create_persistent()
        timeout = handle1.durable_timeout
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.channel.connection.close()
        print handle1.is_persistent
        print handle1.is_durable

        #  sleeping time < resiliemcy < ca's default 120s
        time.sleep(15)
        self.channel, self.tree = self.tree_connect(client=pike.model.Client())

        # Invalidate handle from separate client
        handle2 = self.channel.create(self.tree,
                                      "persistent.txt",
                                      access=smb2.FILE_READ_DATA,
                                      share=SHARE_ALL,
                                      disposition=pike.smb2.FILE_OPEN)

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()
        handle3 = self.create_persistent(prev_handle=handle1)

        # handle1 and handle3 has the same file_id, and the same persistent status
        # it seams that resilience has not impacted the result of reconnect
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_resiliency_timein_interact_durable(self):
        handle1 = self.create_persistent()
        timeout = 10000
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)

        self.channel.connection.close()

        #  sleeping time < resiliemcy < ca's default 120s
        time.sleep(timeout / 1000.0 - 4.0)  # timeout
        self.channel, self.tree = self.tree_connect()
        handle3 = self.create_persistent(prev_handle=handle1)

        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_timeout_resiliency_interact_durable(self):
        handle1 = self.create_persistent()
        timeout = 10000
        # a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        # self.assertEqual(handle1.lease.lease_state, self.rw)

        self.channel.connection.close()

        # resiliemcy < sleeping time < ca's default 120s
        time.sleep(timeout / 1000.0 + 5.0)  # timeout
        self.channel, self.tree = self.tree_connect()
        handle3 = self.create_persistent(prev_handle=handle1)

        # It seams that resilience timeout has not impacted the result
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_timeout_ca_resiliency_interact_persistent(self):
        handle1 = self.create_persistent()

        # set ca's timeout equals resiliency's timeout
        timeout = handle1.durable_timeout
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.channel.connection.close()

        # resilience's timeout = ca's defaut 120s < sleeping time
        time.sleep(121)

        # timeout, can't get object name
        self.channel, self.tree = self.tree_connect()
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create_persistent(prev_handle=handle1)

    def test_timeout_cav2_interact_persistent(self):
        handle1 = self.create_persistent()

        # set ca's timeout equals resiliency's timeout
        timeout = handle1.durable_timeout + 5000
        a = self.channel.network_resiliency_request(handle1, timeout=timeout)
        self.channel.connection.close()

        # ca's defaut 120s < sleeping time < resilience's timeout
        time.sleep(121)

        self.channel, self.tree = self.tree_connect()

        handle3 = self.create_persistent(prev_handle=handle1)

        # sleeping time longer than ca's default, couldn't get object name, but shoter than resilience' time,so the result is true.
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)

    def test_buffer_too_small(self):
        handle1 = self.create_persistent()

        timeout = 5
        with self.assert_error(pike.ntstatus.STATUS_BUFFER_TOO_SMALL):  # just for onefs
            smb_req = self.channel.request(obj=handle1.tree)
            ioctl_req = pike.smb2.IoctlRequest(smb_req)
            vni_req = _testNetworkResiliencyRequestRequest(ioctl_req)
            ioctl_req.file_id = handle1.file_id
            ioctl_req.flags = pike.smb2.SMB2_0_IOCTL_IS_FSCTL
            vni_req.Timeout = timeout
            vni_req.Reserved = 0
            a = self.channel.connection.transceive(smb_req.parent)[0]

        # self.channel.connection.close()

        self.channel, self.tree = self.tree_connect(client=pike.model.Client())
        handle2 = self.channel.create(self.tree,
                                      "persistent.txt",
                                      access=smb2.FILE_READ_DATA,
                                      share=SHARE_ALL,
                                      disposition=pike.smb2.FILE_OPEN)

        self.channel.connection.close()

        self.channel, self.tree = self.tree_connect()

        # resiliency's buffer too small has not impacted persistent status
        handle3 = self.create_persistent(prev_handle=handle1)
        self.assertTrue(handle1.is_persistent)
        self.assertTrue(handle3.is_persistent)
        self.assertEqual(handle1.file_id, handle3.file_id)
        self.channel.close(handle3)
