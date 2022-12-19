#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        set.py
#
# Abstract:
#
#        SMB2_SET_INFO command tests with SMB2_0_INFO_FILE type.
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#

import datetime

import pike.model
import pike.smb2
import pike.nttime
import pike.test


class SetTest(pike.test.PikeTest):
    def open_file(self):
        self.chan, self.tree = self.tree_connect()
        return self.chan.create(
            self.tree, "test.txt", disposition=pike.smb2.FILE_SUPERSEDE
        ).result()

    # Set timestamps and file attributes with FILE_BASIC_INFORMATION
    def test_set_file_basic_info(self):
        handle = self.open_file()
        now = pike.nttime.NtTime(datetime.datetime.now())

        with self.chan.set_file_info(
            handle, pike.smb2.FileBasicInformation
        ) as file_info:
            file_info.last_write_time = now
            file_info.last_access_time = now

        with self.chan.set_file_info(
            handle, pike.smb2.FileBasicInformation
        ) as file_info:
            file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY

        with self.chan.set_file_info(
            handle, pike.smb2.FileBasicInformation
        ) as file_info:
            file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL

        self.chan.close(handle)

    # Set file cursor position with FILE_POSITION_INFORMATION
    def test_set_file_position_info(self):
        handle = self.open_file()

        with self.chan.set_file_info(
            handle, pike.smb2.FilePositionInformation
        ) as file_info:
            file_info.current_byte_offset = 100

        self.chan.close(handle)

    # Set file mode with FILE_MODE_INFORMATION
    def test_set_file_mode_info(self):
        handle = self.open_file()

        with self.chan.set_file_info(
            handle, pike.smb2.FileModeInformation
        ) as file_info:
            file_info.mode = pike.smb2.FILE_SEQUENTIAL_ONLY

        self.chan.close(handle)

    # Set file name with FILE_RENAME_INFORMATION
    def test_set_file_name(self):
        self.chan, self.tree = self.tree_connect()
        handle = self.chan.create(
            self.tree,
            "test.txt",
            disposition=pike.smb2.FILE_SUPERSEDE,
            access=pike.smb2.DELETE,
        ).result()

        with self.chan.set_file_info(
            handle, pike.smb2.FileRenameInformation
        ) as file_info:
            file_info.replace_if_exists = 1
            file_info.file_name = "renamed.txt"

        self.chan.close(handle)

        # open the renamed file for delete and ensure that it exists
        handle2 = self.chan.create(
            self.tree,
            "renamed.txt",
            disposition=pike.smb2.FILE_OPEN,  # fail if doesn't exist
            access=pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        self.chan.close(handle2)
