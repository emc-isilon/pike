#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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
import pike.ntstatus
import pike.smb2
import pike.test


class QueryTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(QueryTest, self).__init__(*args, **kwargs)
        self.chan = None
        self.tree = None

    def open_file(self):
        """Helper to open basic file"""
        self.chan, self.tree = self.tree_connect()
        return self.chan.create(
            self.tree, "test.txt", disposition=pike.smb2.FILE_SUPERSEDE
        ).result()

    def basic_test(
        self, level, info_type=pike.smb2.SMB2_0_INFO_FILE, additional_information=None
    ):
        """Helper to perform a basic query test"""
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle,
            level,
            info_type=info_type,
            additional_information=additional_information,
        )
        self.chan.close(handle)

    def mismatch_test(self, level, size):
        """Helper to perform a test size mismatch"""
        handle = self.open_file()

        with self.assert_error(pike.ntstatus.STATUS_INFO_LENGTH_MISMATCH):
            self.chan.query_file_info(handle, level, output_buffer_length=size)
        self.chan.close(handle)

    # The following tests simply try each info level
    def test_query_file_basic_info(self):
        self.basic_test(pike.smb2.FILE_BASIC_INFORMATION)

    def test_query_file_sec_info_owner(self):
        sec_info = pike.smb2.OWNER_SECURITY_INFORMATION
        self.basic_test(
            pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=sec_info,
        )

    def test_query_file_sec_info_group(self):
        sec_info = pike.smb2.GROUP_SECURITY_INFORMATION
        self.basic_test(
            pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=sec_info,
        )

    def test_query_file_sec_info_dacl(self):
        sec_info = pike.smb2.DACL_SECURITY_INFORMATION
        self.basic_test(
            pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=sec_info,
        )

    def test_query_file_sec_info_all(self):
        sec_info = (
            pike.smb2.OWNER_SECURITY_INFORMATION
            + pike.smb2.GROUP_SECURITY_INFORMATION
            + pike.smb2.DACL_SECURITY_INFORMATION
        )

        self.basic_test(
            pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=sec_info,
        )

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

    def test_mismatch_0_file_basic_info(self):
        self.mismatch_test(pike.smb2.FILE_BASIC_INFORMATION, 0)

    def test_mismatch_0_file_standard_info(self):
        self.mismatch_test(pike.smb2.FILE_STANDARD_INFORMATION, 0)

    def test_mismatch_0_file_alignment_info(self):
        self.mismatch_test(pike.smb2.FILE_ALIGNMENT_INFORMATION, 0)

    def test_mismatch_0_file_internal_info(self):
        self.mismatch_test(pike.smb2.FILE_INTERNAL_INFORMATION, 0)

    def test_mismatch_0_file_mode_info(self):
        self.mismatch_test(pike.smb2.FILE_MODE_INFORMATION, 0)

    def test_mismatch_0_file_position_info(self):
        self.mismatch_test(pike.smb2.FILE_POSITION_INFORMATION, 0)

    def test_mismatch_0_file_ea_info(self):
        self.mismatch_test(pike.smb2.FILE_EA_INFORMATION, 0)

    def test_mismatch_0_file_all_info(self):
        self.mismatch_test(pike.smb2.FILE_ALL_INFORMATION, 0)

    # Querying a security descriptor with output buffer size 0 should
    # return STATUS_BUFFER_TOO_SMALL and tell us how many bytes are needed
    def test_query_sec_desc_0(self):
        handle = self.open_file()
        smb2_req = self.chan.request(obj=handle)
        query_req = pike.smb2.QueryInfoRequest(smb2_req)
        query_req.info_type = pike.smb2.SMB2_0_INFO_SECURITY
        query_req.additional_information = (
            pike.smb2.OWNER_SECURITY_INFORMATION | pike.smb2.DACL_SECURITY_INFORMATION
        )
        query_req.output_buffer_length = 0
        query_req.file_id = handle.file_id

        with self.assert_error(pike.ntstatus.STATUS_BUFFER_TOO_SMALL) as cm:
            self.chan.connection.transceive(smb2_req.parent)

        err = cm.response[0]

        self.assertEqual(err[0].data_length, 4)
        self.assertTrue(err[0].minimum_buffer_length > 0)
