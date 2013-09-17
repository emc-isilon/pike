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
import random
import array

# Constants
LEASE_R   = smb2.SMB2_LEASE_READ_CACHING
LEASE_RW  = LEASE_R | smb2.SMB2_LEASE_WRITE_CACHING
LEASE_RH  = LEASE_R | smb2.SMB2_LEASE_HANDLE_CACHING
LEASE_RWH = LEASE_RW | LEASE_RH
SHARE_ALL = smb2.FILE_SHARE_READ | smb2.FILE_SHARE_WRITE | smb2.FILE_SHARE_DELETE

@test.RequireDialect(smb2.DIALECT_SMB3_0)
@test.RequireCapabilities(smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)
class Persistent(test.PikeTest):
    def setup(self):
        self.lease_key = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.channel, self.tree = self.tree_connect()

    def create_persistent(self, prev_handle = 0):
        """Helper to create a persistent handle, optionally reconnecting an old one"""
        return self.channel.create(
            self.tree,
            "persistent.txt",
            access = smb2.FILE_READ_DATA | smb2.FILE_WRITE_DATA | smb2.DELETE,
            share = SHARE_ALL,
            disposition = smb2.FILE_SUPERSEDE,
            options = smb2.FILE_DELETE_ON_CLOSE,
            oplock_level = smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key = self.lease_key,
            lease_state = LEASE_RWH,
            durable = prev_handle,
            persistent = True
            ).result()

    # Opening a persistent handle grants persistent flag
    def test_create(self):
        handle = self.create_persistent()
        self.assertEqual(handle.durable_flags, smb2.SMB2_DHANDLE_FLAG_PERSISTENT)

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

        with self.assertRaises(smb2.ErrorResponse) as cm:
            # Perform a failing second open
            self.channel.create(
                self.tree,
                "persistent.txt",
                access = smb2.FILE_READ_DATA,
                share = SHARE_ALL,
                disposition = smb2.FILE_OPEN).result()
        self.assertEqual(cm.exception.parent.status, smb2.STATUS_FILE_NOT_AVAILABLE)

        # Clean up: Reconnect and close file (handle)
        self.channel.connection.close()
        self.channel, self.tree = self.tree_connect()
        handle2 = self.create_persistent(prev_handle = handle1)
        self.channel.close(handle2)
