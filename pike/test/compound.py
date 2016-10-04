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
#        compound.py
#
# Abstract:
#
#        Compound request tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test
import random
import array

class CompoundTest(pike.test.PikeTest):

    # Compounded create/close of the same file, with maximal access request
    def test_create_close(self):
        chan, tree = self.tree_connect()

        # Manually assemble a chained request
        nb_req = chan.frame()
        smb_req1 = chan.request(nb_req, obj=tree)
        smb_req2 = chan.request(nb_req, obj=tree)
        create_req = pike.smb2.CreateRequest(smb_req1)
        close_req = pike.smb2.CloseRequest(smb_req2)
        
        create_req.name = 'hello.txt'
        create_req.desired_access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE
        create_req.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL
        create_req.create_disposition = pike.smb2.FILE_OPEN_IF
        
        max_req = pike.smb2.MaximalAccessRequest(create_req)
        
        close_req.file_id = pike.smb2.RELATED_FID
        smb_req2.flags |= pike.smb2.SMB2_FLAGS_RELATED_OPERATIONS
        
        chan.connection.transceive(nb_req)
