#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_changenotify.py
#
# Abstract:
#
#        Change Notify tests
#
# Authors: Masen Furer <masen.furer@emc.com>
#
import pytest

import pike.ntstatus
import pike.smb2


@pytest.fixture
def directory_for_notify(pike_tmp_path):
    with pike_tmp_path.create(
        access=pike.smb2.GENERIC_READ,
        options=pike.smb2.FILE_DIRECTORY_FILE,
        share=pike.smb2.FILE_SHARE_READ,
    ) as handle:
        yield handle


def test_change_notify_file_name(
    pike_tree_connect, pike_tmp_path, directory_for_notify
):
    chan, tree = pike_tree_connect

    change_notify_future = chan.change_notify(
        handle=directory_for_notify,
        completion_filter=pike.smb2.SMB2_NOTIFY_CHANGE_FILE_NAME,
    )

    # create a file on the share to trigger the notification
    file_to_create = pike_tmp_path / "change_notify.txt"
    file_to_create.touch()
    file_to_create.unlink()

    # collect the change notify response
    change_notify_result = change_notify_future.result()[0]

    # expect one notification, for the file add
    assert len(change_notify_result.notifications) == 1
    notification = change_notify_result.notifications[0]
    assert notification.filename == file_to_create.name
    assert notification.action == pike.smb2.SMB2_ACTION_ADDED


def test_change_notify_cancel(pike_tree_connect, directory_for_notify):
    chan, tree = pike_tree_connect

    cn_future = chan.change_notify(directory_for_notify)
    # close the handle for the outstanding notify
    chan.close(directory_for_notify)

    smb2_resp = cn_future.result()
    # [MS-SMB2] 3.3.5.10 - The Server MUST send an SMB2 CHANGE_NOTIFY Response with
    # STATUS_NOTIFY_CLEANUP status code for all pending CHANGE_NOTIFY requests
    # associated with the FileId that is closed.
    assert smb2_resp.status == pike.ntstatus.STATUS_NOTIFY_CLEANUP
    notify_resp = smb2_resp[0]
    # The response should contain no FileNotifyInformation structs
    assert len(notify_resp) == 0
