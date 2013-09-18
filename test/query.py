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
#        query.py
#
# Abstract:
#
#        SMB2_QUERY_INFO command tests with SMB2_0_INFO_FILE type.
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

from pike.test import unittest

class QueryTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(QueryTest, self).__init__(*args, **kwargs)
        self.chan = None
        self.tree = None
        
    def open_file(self):
        """Helper to open basic file"""
        self.chan, self.tree = self.tree_connect()
        return self.chan.create(self.tree, "test.txt", disposition=pike.smb2.FILE_SUPERSEDE).result()

    def basic_test(self, level):
        """Helper to perform a basic query test"""
        handle = self.open_file()
        info = self.chan.query_file_info(handle, level)
        self.chan.close(handle)

    # The following tests simply try each info level
    def test_query_file_basic_info(self):
        self.basic_test(pike.smb2.FILE_BASIC_INFORMATION)

    def test_query_file_standard_info(self):
        self.basic_test(pike.smb2.FILE_STANDARD_INFORMATION)

    def test_query_file_alignment_info(self):
        self.basic_test(pike.smb2.FILE_ALIGNMENT_INFORMATION)

    def test_query_file_internal_info(self):
        self.basic_test(pike.smb2.FILE_INTERNAL_INFORMATION)

    def test_query_file_mode_info(self):
        self.basic_test(pike.smb2.FILE_MODE_INFORMATION)

    def test_query_file_position_info(self):
        self.basic_test(pike.smb2.FILE_POSITION_INFORMATION)

    def test_query_file_ea_info(self):
        self.basic_test(pike.smb2.FILE_EA_INFORMATION)

    def test_query_file_all_info(self):
        self.basic_test(pike.smb2.FILE_ALL_INFORMATION)

    # Querying a security descriptor with output buffer size 0 should
    # return STATUS_BUFFER_TOO_SMALL and tell us how many bytes are needed
    def test_query_sec_desc_0(self):
        handle = self.open_file()
        smb2_req = self.chan.request(obj=handle)
        query_req = pike.smb2.QueryInfoRequest(smb2_req)
        query_req.info_type = pike.smb2.SMB2_0_INFO_SECURITY
        query_req.additional_information = pike.smb2.OWNER_SECURITY_INFORMATION | pike.smb2.DACL_SECURITY_INFORMATION
        query_req.output_buffer_length = 0
        query_req.file_id = handle.file_id

        with self.assert_error(pike.ntstatus.STATUS_BUFFER_TOO_SMALL) as cm:
            self.chan.connection.transceive(smb2_req.parent)

        err = cm.response[0]

        self.assertEqual(err.byte_count, 4)
        self.assertTrue(err.error_data > 0)
