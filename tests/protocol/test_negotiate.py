#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_negotiate.py
#
# Abstract:
#
#        Tests negotiatate responses when requests are sent with a
#        variety of bits set
#
# Authors: Angela Bartholomaus (angela.bartholomaus@emc.com)
#          Paul Martin (paul.o.martin@emc.com)
#          Masen Furer (m_github@0x26.net)
#
import itertools

import pytest

import pike
import pike.crypto as crypto
import pike.smb2 as smb2

from ..utils import samba_version


smb3_caps = [
    smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES,
    smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL,
    smb2.SMB2_GLOBAL_CAP_ENCRYPTION,
    smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING,
]
smb21_caps = [
    smb2.SMB2_GLOBAL_CAP_LARGE_MTU,
    smb2.SMB2_GLOBAL_CAP_LEASING,
]


@pytest.fixture(scope="session")
def share_has_continuous_availability():
    with pike.TreeConnect() as tc:
        capabilities = tc.tree.tree_connect_response.capabilities
        return capabilities & smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY != 0


@pytest.fixture
def negotiate():
    """Negotiate requested dialect on demand."""

    tc = pike.TreeConnect()

    def _negotiate(
        dialect=None, caps=None, hash_algorithms=None, salt=None, ciphers=None
    ):
        if dialect:
            tc.client.dialects = [dialect, smb2.DIALECT_SMB2_002]
        if caps:
            tc.client.capabilities = caps
        return tc.connect(
            hash_algorithms=hash_algorithms, salt=salt, ciphers=ciphers
        ).negotiate_response

    yield _negotiate
    tc.close()


@pytest.fixture
def expect_capabilities(negotiate):
    """Test that cap is advertised by the server if the client advertises it"""

    def _expect(dialect, req_caps=0, exp_caps=None):
        if exp_caps is None:
            exp_caps = req_caps
        assert negotiate(dialect, req_caps).capabilities & exp_caps == exp_caps

    return _expect


@pytest.fixture
def expect_not_capabilities(negotiate):
    """Test that cap is not advertised if we don't ask for it."""

    def _expect(dialect, caps):
        assert negotiate(dialect, 0).capabilities & caps == 0

    return _expect


@pytest.fixture(scope="session", params=smb3_caps)
def smb3_capability(request, share_has_continuous_availability):
    if (
        request.param == smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES
        and not share_has_continuous_availability
    ):
        pytest.skip("Server share does not support CONTINUOUS_AVAILABILITY")
    if request.param == smb2.SMB2_GLOBAL_CAP_DIRECTORY_LEASING and samba_version():
        pytest.skip("Samba does not support DIRECTORY_LEASING")
    return request.param


@pytest.fixture(scope="session")
def many_capabilities():
    caps = 0
    for cap in itertools.chain(smb3_caps, smb21_caps):
        caps |= cap
    return caps


@pytest.mark.require_dialect(smb2.DIALECT_SMB3_0)
def test_smb3_many_capabilities(
    expect_capabilities, many_capabilities, smb3_capability
):
    """generic smb3 cap is advertised if we ask for lots of caps."""
    expect_capabilities(smb2.DIALECT_SMB3_0, many_capabilities, smb3_capability)


@pytest.mark.require_dialect(smb2.DIALECT_SMB3_0)
def test_smb3_caps(expect_capabilities, smb3_capability):
    """generic smb3 cap is advertised if we ask for it."""
    expect_capabilities(smb2.DIALECT_SMB3_0, smb3_capability)


@pytest.mark.require_dialect(smb2.DIALECT_SMB2_1)
@pytest.mark.parametrize("cap", smb21_caps)
def test_smb21_caps(expect_capabilities, cap):
    """generic smb21 cap is advertised if we ask for it."""
    expect_capabilities(smb2.DIALECT_SMB2_1, cap)


@pytest.mark.parametrize("cap", smb3_caps)
def test_smb21_no_advert(expect_not_capabilities, cap):
    """smb3 cap is not advertised if we don't advertise it (SMB 2.1)."""
    expect_not_capabilities(smb2.DIALECT_SMB2_1, cap)


@pytest.mark.parametrize("cap", itertools.chain(smb3_caps, smb21_caps))
def test_smb2_no_advert(expect_not_capabilities, cap):
    """smb3 cap is not advertised to downlevel client."""
    expect_not_capabilities(smb2.DIALECT_SMB2_002, cap)


def test_smb21_always_caps(negotiate):
    negotiate_response = negotiate()
    for cap in smb21_caps:
        assert negotiate_response.capabilities & cap == cap


@pytest.mark.require_dialect(smb2.DIALECT_SMB3_1_1)
def test_preauth_integrity_capabilities(negotiate):
    resp = negotiate(hash_algorithms=[smb2.SMB2_SHA_512])
    if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
        for ctx in resp:
            if isinstance(ctx, smb2.PreauthIntegrityCapabilitiesResponse):
                assert smb2.SMB2_SHA_512 in ctx.hash_algorithms
                assert len(ctx.salt) > 0


@pytest.mark.parametrize(
    "advertise_ciphers, exp_cipher",
    (
        pytest.param(
            [crypto.SMB2_AES_128_CCM],
            crypto.SMB2_AES_128_CCM,
            id="ccm",
        ),
        pytest.param(
            [crypto.SMB2_AES_128_GCM],
            crypto.SMB2_AES_128_GCM,
            id="gcm",
        ),
        pytest.param(
            [crypto.SMB2_AES_128_CCM, crypto.SMB2_AES_128_GCM],
            crypto.SMB2_AES_128_CCM,
            id="both_prefer_ccm",
            marks=[
                pytest.mark.skipif(
                    samba_version(greater=(4, 16)),
                    reason="cipher order not respected on samba 4.16+",
                ),
            ],
        ),
        pytest.param(
            [crypto.SMB2_AES_128_GCM, crypto.SMB2_AES_128_CCM],
            crypto.SMB2_AES_128_GCM,
            id="both_prefer_gcm",
        ),
    ),
)
@pytest.mark.require_dialect(smb2.DIALECT_SMB3_1_1)
def test_encryption_capabilities(negotiate, advertise_ciphers, exp_cipher):
    resp = negotiate(ciphers=advertise_ciphers)
    if resp.dialect_revision >= smb2.DIALECT_SMB3_1_1:
        for ctx in resp:
            if isinstance(ctx, crypto.EncryptionCapabilitiesResponse):
                assert len(ctx.ciphers) == 1
                assert ctx.ciphers[0] == exp_cipher
