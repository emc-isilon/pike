#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        ioctl.py
#
# Abstract:
#
#        Test IOCTLs
#
# Authors: Ki Anderson (kimberley.anderson@emc.com)
#          Paul Martin (paul.o.martin@emc.com)
#          Steve Leef (steven.leef@dell.com)
#

import pike.model as model
import pike.smb2 as smb2
import pike.test as test
import pike.ntstatus


class ValidateNegotiateInfo(test.PikeTest):
    def __init__(self, *args, **kwds):
        super(ValidateNegotiateInfo, self).__init__(*args, **kwds)
        self.set_client_dialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_0_2)

    # VALIDATE_NEGOTIATE_INFO fsctl succeeds for SMB3
    @test.RequireDialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_0_2)
    def test_validate_negotiate_smb3(self):
        self.set_client_dialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_0_2)
        chan, tree = self.tree_connect()
        chan.validate_negotiate_info(tree)


class QueryNetworkInterfaceInfo(test.PikeTest):
    def __init__(self, *args, **kwds):
        super(QueryNetworkInterfaceInfo, self).__init__(*args, **kwds)
        self.set_client_dialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_1_1)

    @test.RequireDialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_1_1)
    def test_query_interface_info_smb3(self):
        self.set_client_dialect(smb2.DIALECT_SMB3_0, smb2.DIALECT_SMB3_1_1)
        chan, tree = self.tree_connect()
        try:
            chan.query_network_interface_info(tree)
        except model.ResponseError as err:
            self.assertEqual(err.response.status, pike.ntstatus.STATUS_SUCCESS)
