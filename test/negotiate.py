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
#        negotiate.py
#
# Abstract:
#
#        Tests negotiatate responses when requests are sent with a 
#        variety of bits set
#
# Authors: Angela Bartholomaus (angela.bartholomaus@emc.com)
#          Paul Martin (paul.o.martin@emc.com)
#

import pike.model as model
import pike.smb2 as smb2
import pike.test as test
import random
import array

class CapTest(test.PikeTest):
    def setup(self):
        self.conn = model.Client().connect(self.server, self.port)
        self.client = self.conn.client

    def teardown(self):
        self.conn.close()

    def negotiate(self, dialect, caps):
        """Negotiate requested dialect"""
        self.client.dialects = [dialect, smb2.DIALECT_SMB2_002]
        self.client.capabilities = caps
        self.conn.negotiate()

        if self.conn.negotiate_response.dialect_revision != dialect:
            self.skipTest("Dialect required: %s" % dialect)

        return self.conn

    def positive_cap(self, dialect, req_caps=0, exp_caps=None)
        """Test that cap is advertised by the server if the client advertises it"""
        if exp_caps is None:
            exp_caps = req_caps
        conn = self.negotiate(dialect, caps)
        self.assertEqual(conn.negotiate_response.capabilities & exp_caps, exp_caps)

    def negative_cap(self, dialect, cap):
        """Test that cap is not advertised if we don't advertise it"""
        conn = self.negotiate(dialect, 0)
        self.assertEqual(conn.negotiate_response.capabilities & cap, 0)

    def downlevel_cap(self, cap):
        """Test that cap is not advertised to downlevel dialect even if we advertise it"""
        conn = self.negotiate(smb2.DIALECT_SMB2_002, cap)
        self.assertEqual(conn.negotiate_response.capabilities & cap, 0)

class CapPersistent(CapTest):
    # persistent cap is advertised if we ask for it
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

    # persistent cap is advertised if we ask for lots of caps
    def test_smb3_many_capabilities(self):
        advertise_caps = \
                smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL | \
                smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES | \
                smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING | \
                smb2.SMB2_GLOBAL_CAP_ENCRYPTION 
        self.positive_cap(smb2.DIALECT_SMB3_0,
                          advertise_caps,
                          smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

    # persistent cap is not advertised if we don't advertise it
    def test_smb3_no_advert(self):
        self.negative_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

    # persistent cap is not advertised if we don't advertise it (SMB 2.1)
    def test_downlevel_no_advert(self):
        self.negative_cap(smb2.DIALECT_SMB2_1, smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

    # persistent cap is not advertised to downlevel client
    def test_downlevel(self):
        self.downlevel_cap(smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

class CapMultichannel(CapTest):
    # multichannel cap is advertised if we ask for it
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

    # multichannel cap is advertised if we ask for lots of caps
    def test_smb3_many_capabilities(self):
        advertise_caps = \
                smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL | \
                smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES | \
                smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING | \
                smb2.SMB2_GLOBAL_CAP_ENCRYPTION 
        self.positive_cap(smb2.DIALECT_SMB3_0,
                          advertise_caps,
                          smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

    # multichannel cap is not advertised if we don't advertise it
    def test_smb3_no_advert(self):
        self.negative_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

    # multichannel cap is not advertised if we don't advertise it (SMB 2.1)
    def test_downlevel_no_advert(self):
        self.negative_cap(smb2.DIALECT_SMB2_1, smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

    # multichannel cap is not advertised to downlevel client
    def test_downlevel(self):
        self.downlevel_cap(smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

class CapMulticredit(CapTest):
    # largemtu cap is advertised if we ask for it
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    # largemtu cap is advertised if we ask for lots of caps
    def test_smb3_many_capabilities(self):
        advertise_caps = \
                smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL | \
                smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES | \
                smb2.SMB2_GLOBAL_CAP_LARGE_MTU | \
                smb2.SMB2_GLOBAL_CAP_ENCRYPTION 
        self.positive_cap(smb2.DIALECT_SMB3_0,
                          advertise_caps,
                          smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    # largemtu cap is advertised if we ask for it
    def test_smb21(self):
        self.positive_cap(smb2.DIALECT_SMB2_1, smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    # multicredit cap is not advertised to downlevel client
    def test_downlevel(self):
        self.downlevel_cap(smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
