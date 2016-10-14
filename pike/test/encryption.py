#
# Copyright (c) 2016, EMC Corporation
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
#        encryption.py
#
# Abstract:
#
#        Test SMB3 Encryption and negotiation options
#
# Authors: Masen Furer (masen.furer@dell.com)
#

import pike.crypto as crypto
import pike.model as model
import pike.smb2 as smb2
import pike.test

class TestEncryption(pike.test.PikeTest):
    def test_smb_3_0_encryption(self):
        client = model.Client(dialects=[smb2.DIALECT_SMB3_0])
        conn = client.connect(self.server)
        conn.negotiate()
        self.assertEqual(conn.negotiate_response.dialect_revision,
                         smb2.DIALECT_SMB3_0)
        self.assertTrue(conn.negotiate_response.capabilities &
                        smb2.SMB2_GLOBAL_CAP_ENCRYPTION)
        chan = conn.session_setup(self.creds)
        chan.session.encrypt_data = True
        self.assertIsNotNone(chan.session.encryption_context)
        self.assertEqual(chan.session.encryption_context.aes_mode,
                         crypto.AES.MODE_CCM)
        tree = chan.tree_connect(self.share)
        self.assertIsNotNone(tree.tree_connect_response.parent.parent.transform)

    def test_smb_3_0_2_encryption(self):
        client = model.Client(dialects=[smb2.DIALECT_SMB3_0_2])
        conn = client.connect(self.server)
        conn.negotiate()
        self.assertEqual(conn.negotiate_response.dialect_revision,
                         smb2.DIALECT_SMB3_0_2)
        self.assertTrue(conn.negotiate_response.capabilities &
                        smb2.SMB2_GLOBAL_CAP_ENCRYPTION)
        chan = conn.session_setup(self.creds)
        chan.session.encrypt_data = True
        self.assertIsNotNone(chan.session.encryption_context)
        self.assertEqual(chan.session.encryption_context.aes_mode,
                         crypto.AES.MODE_CCM)
        tree = chan.tree_connect(self.share)
        self.assertIsNotNone(tree.tree_connect_response.parent.parent.transform)

    def test_smb_3_1_1_encryption_gcm(self):
        client = model.Client(dialects=[smb2.DIALECT_SMB3_0,
                                        smb2.DIALECT_SMB3_1_1])
        conn = client.connect(self.server)
        conn.negotiate(ciphers=[crypto.SMB2_AES_128_GCM])
        self.assertEqual(conn.negotiate_response.dialect_revision,
                         smb2.DIALECT_SMB3_1_1)
        self.assertFalse(conn.negotiate_response.capabilities &
                        smb2.SMB2_GLOBAL_CAP_ENCRYPTION)
        chan = conn.session_setup(self.creds)
        chan.session.encrypt_data = True
        self.assertIsNotNone(chan.session.encryption_context)
        self.assertEqual(chan.session.encryption_context.aes_mode,
                         crypto.AES.MODE_GCM)
        tree = chan.tree_connect(self.share)
        self.assertIsNotNone(tree.tree_connect_response.parent.parent.transform)

    def test_smb_3_1_1_encryption_ccm(self):
        client = model.Client(dialects=[smb2.DIALECT_SMB3_0,
                                        smb2.DIALECT_SMB3_1_1])
        conn = client.connect(self.server)
        conn.negotiate(ciphers=[crypto.SMB2_AES_128_CCM])
        self.assertEqual(conn.negotiate_response.dialect_revision,
                         smb2.DIALECT_SMB3_1_1)
        self.assertFalse(conn.negotiate_response.capabilities &
                        smb2.SMB2_GLOBAL_CAP_ENCRYPTION)
        chan = conn.session_setup(self.creds)
        chan.session.encrypt_data = True
        self.assertIsNotNone(chan.session.encryption_context)
        self.assertEqual(chan.session.encryption_context.aes_mode,
                         crypto.AES.MODE_CCM)
        tree = chan.tree_connect(self.share)
        self.assertIsNotNone(tree.tree_connect_response.parent.parent.transform)

    def test_smb_3_1_1_compound(self):
        client = model.Client(dialects=[smb2.DIALECT_SMB3_0,
                                        smb2.DIALECT_SMB3_1_1])
        conn = client.connect(self.server)
        conn.negotiate(ciphers=[crypto.SMB2_AES_128_GCM])
        self.assertEqual(conn.negotiate_response.dialect_revision,
                         smb2.DIALECT_SMB3_1_1)
        self.assertFalse(conn.negotiate_response.capabilities &
                        smb2.SMB2_GLOBAL_CAP_ENCRYPTION)
        chan = conn.session_setup(self.creds)
        chan.session.encrypt_data = True
        self.assertIsNotNone(chan.session.encryption_context)
        self.assertEqual(chan.session.encryption_context.aes_mode,
                         crypto.AES.MODE_GCM)
        chan.session.encrypt_data = True
        tree = chan.tree_connect(self.share)
        self.assertIsNotNone(tree.tree_connect_response.parent.parent.transform)

        nb_req = chan.frame()
        smb_req1 = chan.request(nb_req, obj=tree)
        smb_req2 = chan.request(nb_req, obj=tree)
        create_req = smb2.CreateRequest(smb_req1)
        close_req = smb2.CloseRequest(smb_req2)

        create_req.name = 'hello.txt'
        create_req.desired_access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE
        create_req.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL
        create_req.create_disposition = pike.smb2.FILE_OPEN_IF

        max_req = pike.smb2.MaximalAccessRequest(create_req)

        close_req.file_id = smb2.RELATED_FID
        smb_req2.flags |= smb2.SMB2_FLAGS_RELATED_OPERATIONS
        resp = chan.connection.transceive(nb_req)
        parent = resp[0].parent
        self.assertIsNotNone(parent.transform)
        for r in resp:
            self.assertEqual(r.parent, parent)

if __name__ == "__main__":
    pike.test.unittest.main()
