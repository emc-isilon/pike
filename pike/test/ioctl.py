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
