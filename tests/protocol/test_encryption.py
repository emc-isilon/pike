#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_encryption.py
#
# Abstract:
#
#        Test SMB3 Encryption and negotiation options
#
# Authors: Masen Furer (masen.furer@dell.com)
#
import pytest

import pike.crypto as crypto
import pike.model as model
import pike.smb2 as smb2

from ..utils import samba_version


pytestmark = [
    pytest.mark.require_dialect(smb2.DIALECT_SMB3_0),
]


@pytest.mark.parametrize(
    "dialect, exp_aes_mode",
    (
        (smb2.DIALECT_SMB3_0, crypto.AES.MODE_CCM),
        pytest.param(
            smb2.DIALECT_SMB3_0_2,
            crypto.AES.MODE_CCM,
            marks=[
                pytest.mark.require_dialect(smb2.DIALECT_SMB3_0_2),
            ],
        ),
        pytest.param(
            smb2.DIALECT_SMB3_1_1,
            crypto.AES.MODE_GCM,
            marks=[
                pytest.mark.require_dialect(smb2.DIALECT_SMB3_1_1),
                pytest.mark.skipif(
                    samba_version(greater=(4, 16)),
                    reason="TODO: BadPacket on samba 4.16+",
                ),
            ],
        ),
    ),
)
def test_smb_3_encryption(pike_TreeConnect, dialect, exp_aes_mode):
    with pike_TreeConnect(
        client=model.Client(dialects=[dialect]),
        encryption=True,
    ) as tc:
        assert tc.conn.negotiate_response.dialect_revision == dialect
        assert tc.chan.session.encryption_context is not None
        assert tc.chan.session.encryption_context.aes_mode == exp_aes_mode
        assert tc.tree.tree_connect_response.parent.parent.transform is not None


@pytest.mark.require_dialect(smb2.DIALECT_SMB3_1_1)
@pytest.mark.skipif(
    samba_version(greater=(4, 16)),
    reason="TODO: BadPacket on samba 4.16+",
)
def test_smb_3_compound(pike_TreeConnect):
    with pike_TreeConnect(encryption=True) as tc:
        assert tc.conn.negotiate_response.dialect_revision == smb2.DIALECT_SMB3_1_1
        assert tc.chan.session.encryption_context is not None
        assert tc.chan.session.encryption_context.aes_mode == crypto.AES.MODE_GCM
        assert tc.tree.tree_connect_response.parent.parent.transform is not None

        create_req = tc.chan.create_request(
            tc.tree,
            "hello.txt",
            access=smb2.GENERIC_WRITE | smb2.DELETE,
            options=smb2.FILE_DELETE_ON_CLOSE,
            maximal_access=True,
        )

        nb_req = create_req.parent.parent
        nb_req.adopt(tc.chan.close_request(model.RelatedOpen).parent)
        resp = tc.conn.transceive(nb_req)
        parent = resp[0].parent
        for smb2_frame in resp:
            assert smb2_frame.parent.transform is not None
            assert smb2_frame.parent is parent
