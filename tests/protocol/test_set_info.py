#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_set_info.py
#
# Abstract:
#
#        SMB2_SET_INFO command tests with SMB2_0_INFO_FILE type.
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#          Masen Furer (m_github@0x26.net)
#

import datetime

import pytest

import pike.model
import pike.smb2
import pike.ntstatus
import pike.nttime
import pike.test

from ..utils import samba_version


now = pike.nttime.NtTime(datetime.datetime.now())
Same = object()


@pytest.fixture
def chan(pike_tree_connect):
    return pike_tree_connect.chan


@pytest.fixture
def open_file_rw_attributes(pike_tmp_path):
    with (pike_tmp_path / "test.txt").create(
        access=pike.smb2.FILE_READ_ATTRIBUTES | pike.smb2.FILE_WRITE_ATTRIBUTES,
        disposition=pike.smb2.FILE_SUPERSEDE,
    ) as handle:
        yield handle


@pytest.fixture
def open_file_delete(pike_tmp_path):
    with (pike_tmp_path / "test.txt").create(
        access=pike.smb2.DELETE,
        disposition=pike.smb2.FILE_SUPERSEDE,
    ) as handle:
        yield handle


@pytest.mark.parametrize(
    "set_attributes, exp_values",
    (
        pytest.param(
            {"last_write_time": now},
            Same,
            id="last_write_time",
        ),
        pytest.param(
            {"last_access_time": now},
            Same,
            id="last_access_time",
        ),
        pytest.param(
            {"file_attributes": pike.smb2.FILE_ATTRIBUTE_READONLY},
            Same,
            marks=[
                pytest.mark.skipif(
                    samba_version(greater=(4, 16)),
                    reason="STATUS_NOT_SUPPORTED on samba 4.16+",
                ),
            ],
            id="file_attributes",
        ),
        pytest.param(
            {"file_attributes": pike.smb2.FILE_ATTRIBUTE_NORMAL},
            Same,
            id="file_attributes_normal",
        ),
        pytest.param(
            {
                "last_write_time": now,
                "last_access_time": now,
            },
            Same,
            id="last_write_time+last_access_time",
        ),
        pytest.param(
            {
                "last_write_time": now,
                "last_access_time": now,
                "creation_time": now,
                "change_time": now,
            },
            Same,
            id="last_write_time+last_access_time+creation_time+change_time",
        ),
    ),
)
def test_set_file_basic_info(chan, open_file_rw_attributes, set_attributes, exp_values):
    """Set timestamps and file attributes with FILE_BASIC_INFORMATION."""
    with chan.set_file_info(
        open_file_rw_attributes, pike.smb2.FileBasicInformation
    ) as file_info:
        for attribute, value in set_attributes.items():
            setattr(file_info, attribute, value)

    if exp_values is Same:
        exp_values = set_attributes

    info = chan.query_file_info(
        open_file_rw_attributes,
        pike.smb2.FILE_BASIC_INFORMATION,
        first_result_only=False,
    )
    assert len(info) == 1
    for attribute, exp_value in exp_values.items():
        assert getattr(info[0], attribute) == exp_value


def test_set_file_position_info(chan, open_file_rw_attributes):
    """Set file cursor position with FILE_POSITION_INFORMATION."""
    with chan.set_file_info(
        open_file_rw_attributes, pike.smb2.FilePositionInformation
    ) as file_info:
        file_info.current_byte_offset = 100

    info = chan.query_file_info(
        open_file_rw_attributes,
        pike.smb2.FILE_POSITION_INFORMATION,
        first_result_only=False,
    )
    assert info[0].current_byte_offset == 100
    assert len(info) == 1


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(
            pike.smb2.FILE_SEQUENTIAL_ONLY,
            marks=[
                pytest.mark.skipif(
                    samba_version(greater=(4, 16)),
                    reason="Set mode not respected on samba 4.16+",
                ),
            ],
        ),
        pytest.param(
            pike.smb2.FILE_WRITE_THROUGH,
            marks=[
                pytest.mark.skipif(
                    samba_version(greater=(4, 16)),
                    reason="STATUS_INVALID_PARAMETER on samba 4.16+",
                ),
            ],
        ),
    ],
)
def test_set_file_mode_info(chan, open_file_rw_attributes, mode):
    """Set file mode with FILE_MODE_INFORMATION."""
    with chan.set_file_info(
        open_file_rw_attributes, pike.smb2.FileModeInformation
    ) as file_info:
        file_info.mode = mode

    info = chan.query_file_info(
        open_file_rw_attributes,
        pike.smb2.FILE_MODE_INFORMATION,
        first_result_only=False,
    )
    assert info[0].mode & mode == mode


@pytest.fixture
def target_file_name():
    return "renamed.txt"


@pytest.fixture(params=[True, False])
def target_file_name_exists(request, pike_tree_connect, target_file_name):
    if request.param:
        target = pike_tree_connect / target_file_name
        target.touch()
        yield request.param
        if target.exists():
            target.unlink()
    else:
        yield request.param


@pytest.mark.parametrize(
    "replace_if_exists",
    [True, False],
)
def test_set_file_name(
    pike_tree_connect,
    pike_tmp_path,
    open_file_delete,
    replace_if_exists,
    target_file_name,
    target_file_name_exists,
):
    """Set file name with FILE_RENAME_INFORMATION."""
    chan, tree = pike_tree_connect
    exp_status = None
    if target_file_name_exists and not replace_if_exists:
        exp_status = pike.ntstatus.STATUS_OBJECT_NAME_COLLISION

    with pike.ntstatus.raises(exp_status):
        with chan.set_file_info(
            open_file_delete,
            pike.smb2.FileRenameInformation,
        ) as file_info:
            file_info.replace_if_exists = replace_if_exists
            file_info.file_name = target_file_name

    chan.close(open_file_delete)

    # open the renamed file for delete and ensure that it exists
    with chan.create(
        tree,
        target_file_name,
        disposition=pike.smb2.FILE_OPEN,  # fail if doesn't exist
        access=pike.smb2.DELETE,
        options=pike.smb2.FILE_DELETE_ON_CLOSE,
    ).result():
        pass
    assert not (pike_tmp_path / target_file_name).exists()
