#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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

import pike.crypto as crypto
import pike.smb2 as smb2
import pike.test as test


class CapTest(test.PikeTest):
    def setup(self):
        # determine max capability and apply Required decorators
        self.chan, self.tree = self.tree_connect()
        self.max_dialect = self.chan.connection.negotiate_response.dialect_revision
        self.capabilities = self.chan.connection.negotiate_response.capabilities
        self.share_caps = self.tree.tree_connect_response.capabilities
        self.chan.logoff()
        self.chan.connection.close()

        self.client = self.default_client
        self.conn = self.client.connect(self.server, self.port)

    def teardown(self):
        self.conn.close()

    def negotiate(self, dialect, caps):
        """Negotiate requested dialect"""
        self.client.dialects = [dialect, smb2.DIALECT_SMB2_002]
        self.client.capabilities = caps
        self.conn.negotiate()

        return self.conn

    def positive_cap(self, dialect, req_caps=0, exp_caps=None):
        """Test that cap is advertised by the server if the client advertises it"""
        if exp_caps is None:
            exp_caps = req_caps
        conn = self.negotiate(dialect, req_caps)
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
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    @test.RequireShareCapabilities(smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY)
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)

    # persistent cap is advertised if we ask for lots of caps
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    @test.RequireShareCapabilities(smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY)
    def test_smb3_many_capabilities(self):
        advertise_caps = (
            smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL
            | smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES
            | smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING
            | smb2.SMB2_GLOBAL_CAP_ENCRYPTION
        )
        self.positive_cap(
            smb2.DIALECT_SMB3_0, advertise_caps, smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES
        )

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
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)

    # multichannel cap is advertised if we ask for lots of caps
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    def test_smb3_many_capabilities(self):
        advertise_caps = (
            smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL
            | smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES
            | smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING
            | smb2.SMB2_GLOBAL_CAP_ENCRYPTION
        )
        self.positive_cap(
            smb2.DIALECT_SMB3_0, advertise_caps, smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL
        )

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
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    def test_smb3(self):
        self.positive_cap(smb2.DIALECT_SMB3_0, smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    # largemtu cap is advertised if we ask for lots of caps
    @test.RequireDialect(smb2.DIALECT_SMB3_0)
    def test_smb3_many_capabilities(self):
        advertise_caps = (
            smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL
            | smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES
            | smb2.SMB2_GLOBAL_CAP_LARGE_MTU
            | smb2.SMB2_GLOBAL_CAP_ENCRYPTION
        )
        self.positive_cap(
            smb2.DIALECT_SMB3_0, advertise_caps, smb2.SMB2_GLOBAL_CAP_LARGE_MTU
        )

    # largemtu cap is advertised if we ask for it
    def test_smb21(self):
        self.positive_cap(smb2.DIALECT_SMB2_1, smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    # multicredit cap is not advertised to downlevel client
    def test_downlevel(self):
        self.downlevel_cap(smb2.SMB2_GLOBAL_CAP_LARGE_MTU)


@test.RequireDialect(smb2.DIALECT_SMB3_1_1)
class NegotiateContext(test.PikeTest):
    def negotiate(self, *args, **kwds):
        self.client = self.default_client
        self.conn = self.client.connect(self.server, self.port)
        return self.conn.negotiate(*args, **kwds).negotiate_response

    def test_preauth_integrity_capabilities(self):
        resp = self.negotiate(hash_algorithms=[smb2.SMB2_SHA_512])
        if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            for ctx in resp:
                if isinstance(ctx, smb2.PreauthIntegrityCapabilitiesResponse):
                    self.assertIn(smb2.SMB2_SHA_512, ctx.hash_algorithms)
                    self.assertGreater(len(ctx.salt), 0)

    def test_encryption_capabilities_both_prefer_ccm(self):
        resp = self.negotiate(
            ciphers=[crypto.SMB2_AES_128_CCM, crypto.SMB2_AES_128_GCM]
        )
        if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            for ctx in resp:
                if isinstance(ctx, crypto.EncryptionCapabilitiesResponse):
                    self.assertEqual(len(ctx.ciphers), 1)
                    self.assertIn(crypto.SMB2_AES_128_CCM, ctx.ciphers)

    def test_encryption_capabilities_both_prefer_gcm(self):
        resp = self.negotiate(
            ciphers=[crypto.SMB2_AES_128_GCM, crypto.SMB2_AES_128_CCM]
        )
        if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            for ctx in resp:
                if isinstance(ctx, crypto.EncryptionCapabilitiesResponse):
                    self.assertEqual(len(ctx.ciphers), 1)
                    self.assertIn(crypto.SMB2_AES_128_GCM, ctx.ciphers)

    def test_encryption_capabilities_ccm(self):
        resp = self.negotiate(ciphers=[crypto.SMB2_AES_128_CCM])
        if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            for ctx in resp:
                if isinstance(ctx, crypto.EncryptionCapabilitiesResponse):
                    self.assertEqual(len(ctx.ciphers), 1)
                    self.assertIn(crypto.SMB2_AES_128_CCM, ctx.ciphers)

    def test_encryption_capabilities_gcm(self):
        resp = self.negotiate(ciphers=[crypto.SMB2_AES_128_GCM])
        if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            for ctx in resp:
                if isinstance(ctx, crypto.EncryptionCapabilitiesResponse):
                    self.assertEqual(len(ctx.ciphers), 1)
                    self.assertIn(crypto.SMB2_AES_128_GCM, ctx.ciphers)
