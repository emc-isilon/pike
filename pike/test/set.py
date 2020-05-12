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
        return self.chan.create(self.tree, "test.txt", disposition=pike.smb2.FILE_SUPERSEDE).result()

    # Set timestamps and file attributes with FILE_BASIC_INFORMATION
    def test_set_file_basic_info(self):
        handle = self.open_file()
        now = pike.nttime.NtTime(datetime.datetime.now())

        with self.chan.set_file_info(handle, pike.smb2.FileBasicInformation) as file_info:
            file_info.last_write_time = now
            file_info.last_access_time = now

        with self.chan.set_file_info(handle, pike.smb2.FileBasicInformation) as file_info:
            file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY

        with self.chan.set_file_info(handle, pike.smb2.FileBasicInformation) as file_info:
            file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL

        self.chan.close(handle)

    # Set file cursor position with FILE_POSITION_INFORMATION
    def test_set_file_position_info(self):
        handle = self.open_file()
        
        with self.chan.set_file_info(handle, pike.smb2.FilePositionInformation) as file_info:
            file_info.current_byte_offset = 100

        self.chan.close(handle)

    # Set file mode with FILE_MODE_INFORMATION
    def test_set_file_mode_info(self):
        handle = self.open_file()

        with self.chan.set_file_info(handle, pike.smb2.FileModeInformation) as file_info:
            file_info.mode = pike.smb2.FILE_SEQUENTIAL_ONLY

        self.chan.close(handle)

    # Set file name with FILE_RENAME_INFORMATION
    def test_set_file_name(self):
        self.chan, self.tree = self.tree_connect()
        handle = self.chan.create(self.tree, "test.txt",
                                  disposition=pike.smb2.FILE_SUPERSEDE,
                                  access=pike.smb2.DELETE).result()

        with self.chan.set_file_info(handle, pike.smb2.FileRenameInformation) as file_info:
            file_info.replace_if_exists = 1
            file_info.file_name = "renamed.txt"

        self.chan.close(handle)

        # open the renamed file for delete and ensure that it exists
        handle2 = self.chan.create(self.tree, "renamed.txt",
                                   disposition=pike.smb2.FILE_OPEN,     # fail if doesn't exist
                                   access=pike.smb2.DELETE,
                                   options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        self.chan.close(handle2)

