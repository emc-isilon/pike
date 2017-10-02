#
# Copyright (c) 2017, Dell EMC Corporation
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
#        invalid_session.py
#
# Abstract:
#
#        SMB2 requests with invalid session id
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#


import pike.model
import pike.ntstatus as nt
import pike.smb2 as smb2
import pike.test


class InvalidSessionTest(pike.test.PikeTest):
    def test_logoff(self):
        conn = pike.model.Client().connect(self.server, self.port).negotiate()

        req = conn.request()
        logoff_req = smb2.LogoffRequest(req)

        # Set invalid session id
        req.session_id = 0xffffffffffffffff

        with self.assert_error(nt.STATUS_USER_SESSION_DELETED):
            conn.transceive(req.parent)[0]

        conn.close()

    def open_file(self, filename):
        self.chan, self.tree = self.tree_connect()
        fh = self.chan.create(
            self.tree,
            filename,
            disposition=smb2.FILE_SUPERSEDE).result()
        return fh


    def test_treeconnect(self):
        chan, tree = self.tree_connect()

        req1 = chan.request(obj=tree)

        tree_con_req1 = smb2.TreeConnectRequest(req1)
        tree_con_req1.path = tree.path

        # Set invalid session id
        req1.session_id = 0xffffffffffffffff

        with self.assert_error(nt.STATUS_USER_SESSION_DELETED):
            chan.connection.transceive(req1.parent)[0]

        chan.connection.close()


    def test_ioctl(self):
        fh = self.open_file("test.txt")

        req1 = self.chan.request(obj=self.tree)

        ioctl_req1 = smb2.IoctlRequest(req1)
        val_req1 = smb2.ValidateNegotiateInfoRequest(ioctl_req1)

        ioctl_req1.flags = smb2.SMB2_0_IOCTL_IS_FSCTL
        ioctl_req1.file_id = fh.file_id
        val_req1.capabilities = self.chan.session.client.capabilities
        val_req1.client_guid = self.chan.session.client.client_guid
        val_req1.security_mode = self.chan.session.client.security_mode
        val_req1.dialects = self.chan.session.client.dialects

        # Set invalid session
        req1.session_id = 0xffffffffffffffff

        with self.assert_error(nt.STATUS_USER_SESSION_DELETED):
            self.chan.connection.transceive(req1.parent)

        self.chan.connection.close()


    def test_oplock_break_ack(self):
        fh = self.open_file("test.txt")

        req1 = self.chan.request(obj=self.tree)

        oplock_ack_req1 = smb2.OplockBreakAcknowledgement(req1)
        oplock_ack_req1.file_id = fh.file_id

        # Set invalid session and tree id
        req1.session_id = 0xffffffffffffffff

        with self.assert_error(nt.STATUS_USER_SESSION_DELETED):
            self.chan.connection.transceive(req1.parent)

        self.chan.close(fh)
        self.chan.connection.close()
