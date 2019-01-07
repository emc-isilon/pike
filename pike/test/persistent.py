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
    buf_too_small_error = pike.ntstatus.STATUS_INVALID_PARAMETER

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
        self.channel.close(handle2)

    def test_resiliency_interact_persistent(self):
        chan, tree = self.tree_connect()
        handle1 = self.create_persistent()
        print handle1
        timeout = 100
        # a = chan.network_resiliency_request(handle1, timeout=timeout)
        print handle1.durable_flags
        self.channel.connection.close()

        time.sleep((timeout - 10) / 1000)

        chan2, tree2 = self.tree_connect(client=pike.model.Client())
        # Invalidate handle from separate client
        with self.assert_error(ntstatus.STATUS_FILE_NOT_AVAILABLE):
            handle2 = self.create(chan2,
                                  tree2,
                                  access=smb2.FILE_READ_DATA,
                                  share=SHARE_ALL,
                                  disposition=pike.smb2.FILE_OPEN)
        chan2.connection.close()

        chan3, tree3 = self.tree_connect()
        handle3 = self.create_persistent(chan3,tree3,prev_handle = handle1)
        print handle3.durable_flags
        self.assertEqual(handle2.lease.lease_state, LEASE_RWH)
        chan3.connection.close()

    def test_resiliency_timeout_interact_durable(self):
        chan, tree = self.tree_connect()
        handle1 = self.create(chan, tree)
        timeout = 100
        a = chan.network_resiliency_request(handle1, timeout=timeout)
        self.assertEqual(handle1.lease.lease_state, self.rw)

        # Close the connection
        chan.connection.close()
        time.sleep(timeout / 1000 + 5)  # timeout

        chan2, tree2 = self.tree_connect(client=pike.model.Client())
        # Invalidate handle from separate client
        handle2 = self.create(chan2,
                              tree2,
                              access=smb2.FILE_READ_DATA,
                              share=SHARE_ALL,
                              disposition=pike.smb2.FILE_OPEN)

        self.assertEqual(handle2.lease.lease_state, self.rw)
        chan2.close(handle2)
        chan2.connection.close()
        chan3, tree3 = self.tree_connect()

        # Reconnect should fail(resiliency timeout)
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create(chan3, tree3, durable=handle1)

    def test_buffer_too_small(self):
        chan, tree = self.tree_connect()
        handle1 = self.create(chan,
                              tree)

        timeout = 5
        # with self.assert_error(pike.ntstatus.STATUS_BUFFER_TOO_SMALL):  just for onefs
        with self.assert_error(self.buf_too_small_error):  # for windows plat
            smb_req = chan.request(obj=handle1.tree)
            ioctl_req = pike.smb2.IoctlRequest(smb_req)
            vni_req = _testNetworkResiliencyRequestRequest(ioctl_req)
            ioctl_req.file_id = handle1.file_id
            ioctl_req.flags = pike.smb2.SMB2_0_IOCTL_IS_FSCTL
            vni_req.Timeout = timeout
            vni_req.Reserved = 0
            a = chan.connection.transceive(smb_req.parent)[0]

        self.assertEqual(handle1.lease.lease_state, self.rw)
        chan.connection.close()

        chan2, tree2 = self.tree_connect(client=pike.model.Client())
        handle2 = self.create(chan2,
                              tree2,
                              access=smb2.FILE_READ_DATA,
                              share=SHARE_ALL,
                              disposition=pike.smb2.FILE_OPEN)

        self.assertEqual(handle2.lease.lease_state, self.rw)
        chan2.close(handle2)
        chan2.connection.close()

        chan3, tree3 = self.tree_connect()
        # buffer too small
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
            handle3 = self.create(chan3, tree3, durable=handle1)
