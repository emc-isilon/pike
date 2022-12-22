#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_query.py
#
# Abstract:
#
#        SMB2_QUERY_INFO command tests with SMB2_0_INFO_FILE type.
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#          Masen Furer (m_github@0x26.net)
#
import pytest

import pike.model
import pike.ntstatus
import pike.smb2
import pike.test


SMB2_0_INFO_FILE = pike.smb2.SMB2_0_INFO_FILE
SMB2_0_INFO_SECURITY = pike.smb2.SMB2_0_INFO_SECURITY
ALL_SEC_INFO = (
    pike.smb2.OWNER_SECURITY_INFORMATION
    | pike.smb2.GROUP_SECURITY_INFORMATION
    | pike.smb2.DACL_SECURITY_INFORMATION
)


@pytest.fixture
def open_file(pike_tmp_path):
    """Helper to open basic file"""
    path = pike_tmp_path / "test.txt"
    with path.create(disposition=pike.smb2.FILE_SUPERSEDE) as handle:
        yield handle
    path.unlink()


@pytest.mark.parametrize(
    "level, info_type, additional_information",
    (
        (pike.smb2.FILE_BASIC_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_STANDARD_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_ALIGNMENT_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_INTERNAL_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_MODE_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_POSITION_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_EA_INFORMATION, SMB2_0_INFO_FILE, None),
        (pike.smb2.FILE_ALL_INFORMATION, SMB2_0_INFO_FILE, None),
        (
            pike.smb2.FILE_SECURITY_INFORMATION,
            SMB2_0_INFO_SECURITY,
            pike.smb2.OWNER_SECURITY_INFORMATION,
        ),
        (
            pike.smb2.FILE_SECURITY_INFORMATION,
            SMB2_0_INFO_SECURITY,
            pike.smb2.GROUP_SECURITY_INFORMATION,
        ),
        (
            pike.smb2.FILE_SECURITY_INFORMATION,
            SMB2_0_INFO_SECURITY,
            pike.smb2.DACL_SECURITY_INFORMATION,
        ),
        (pike.smb2.FILE_SECURITY_INFORMATION, SMB2_0_INFO_SECURITY, ALL_SEC_INFO),
    ),
)
@pytest.mark.parametrize(
    "output_buffer_length, exp_status",
    (
        (4096, pike.ntstatus.STATUS_SUCCESS),
        (
            0,
            [
                pike.ntstatus.STATUS_INFO_LENGTH_MISMATCH,
                pike.ntstatus.STATUS_BUFFER_TOO_SMALL,
            ],
        ),
    ),
)
def test_query_info(
    pike_tree_connect,
    open_file,
    level,
    info_type,
    additional_information,
    output_buffer_length,
    exp_status,
):
    """Perform a QUERY INFO with different info types."""
    with pike.ntstatus.raises(exp_status):
        info = pike_tree_connect.chan.query_file_info(
            open_file,
            level,
            info_type=info_type,
            additional_information=additional_information,
            output_buffer_length=output_buffer_length,
            first_result_only=False,
        )
        assert len(info) == 1


def test_query_sec_desc_0(pike_tree_connect, pike_tmp_path):
    """
    Querying a security descriptor with output buffer size 0 should
    return STATUS_BUFFER_TOO_SMALL and tell us how many bytes are needed
    """
    with (pike_tmp_path / "foo").create() as handle:
        with pike.ntstatus.raises(pike.ntstatus.STATUS_BUFFER_TOO_SMALL) as ntsctx:
            pike_tree_connect.chan.query_file_info(
                handle,
                pike.smb2.FILE_SECURITY_INFORMATION,
                info_type=pike.smb2.SMB2_0_INFO_SECURITY,
                additional_information=(
                    pike.smb2.OWNER_SECURITY_INFORMATION
                    | pike.smb2.DACL_SECURITY_INFORMATION
                ),
                output_buffer_length=0,
                first_result_only=False,
            )
            resp_err = ntsctx.exc.response
            assert resp_err.data_length == 4
            assert resp_err.minimum_buffer_length > 0
