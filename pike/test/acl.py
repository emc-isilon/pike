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
#        acl.py
#
# Abstract:
#
#        SMB2/3 ACL set/get testing.
#
#
import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

from pike.test import unittest


class SecTest(pike.test.PikeTest):

    def __init__(self, *args, **kwargs):
        super(SecTest, self).__init__(*args, **kwargs)
        self.chan = None
        self.tree = None
        self.sec_info = (pike.smb2.OWNER_SECURITY_INFORMATION |
                         pike.smb2.GROUP_SECURITY_INFORMATION |
                         pike.smb2.DACL_SECURITY_INFORMATION)
        self.sec_info_owner = pike.smb2.OWNER_SECURITY_INFORMATION
        self.sec_info_group = pike.smb2.GROUP_SECURITY_INFORMATION
        self.sec_info_dacl = pike.smb2.DACL_SECURITY_INFORMATION

    def open_file(self):
        """Helper to open basic file"""
        self.chan, self.tree = self.tree_connect()
        return self.chan.create(self.tree, "test_sec.txt",
                                options=pike.smb2.FILE_DELETE_ON_CLOSE,
                                access=(pike.smb2.READ_CONTROL |
                                        pike.smb2.WRITE_OWNER |
                                        pike.smb2.DELETE |
                                        pike.smb2.WRITE_DAC),
                                disposition=pike.smb2.FILE_SUPERSEDE).result()

    def test_set_sec_same(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info) as file_info:
            file_info.clone_from(info)
        self.chan.close(handle)

    def test_set_sec_owner(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_owner) as file_info:
            file_info.clone_from(info, ["owner_sid"])
        self.chan.close(handle)

    def test_set_sec_group(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_group) as file_info:
            file_info.clone_from(info, ["group_sid"])
        self.chan.close(handle)

    def test_set_sec_dacl(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_dacl) as file_info:
            file_info.clone_from(info, ["dacl"])
        self.chan.close(handle)

    def test_set_sec_dacl_partial_copy(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_dacl) as file_info:
            file_info.clone_from(info, [])
            aces = info.dacl.children
            new_dacl = pike.smb2.NT_ACL()
            new_dacl.acl_revision = pike.smb2.ACL_REVISION
            new_dacl.append(aces[0])
            file_info.dacl = new_dacl
        self.chan.close(handle)

    def test_set_sec_dacl_append_ace(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_dacl) as file_info:
            file_info.clone_from(info, [])
            aces = info.dacl.children
            new_dacl = info.dacl.clone()
            file_info.dacl = new_dacl
            # append a modified ace
            template_ace = aces[0].clone(new_parent=None)
            template_ace.sid.identifier_authority = 5
            template_ace.sid.sub_authority = [18]
            file_info.dacl.append(template_ace)
        self.chan.close(handle)

    def test_set_sec_dacl_new(self):
        handle = self.open_file()
        info = self.chan.query_file_info(
            handle, pike.smb2.FILE_SECURITY_INFORMATION,
            info_type=pike.smb2.SMB2_0_INFO_SECURITY,
            additional_information=self.sec_info)
        with self.chan.set_file_info(
                handle,
                pike.smb2.FileSecurityInformation,
                additional_information=self.sec_info_dacl) as file_info:
            file_info.clone_from(info, [])
            aces = info.dacl.children
            #generate a new NT_ACL object
            new_dacl = pike.smb2.NT_ACL()
            new_dacl.acl_revision = pike.smb2.ACL_REVISION
            #keep the original aces
            new_dacl._entries = aces
            # append a cloned ace then modify it
            template_ace = aces[0].clone(new_parent=new_dacl)
            template_ace.sid.identifier_authority = 5
            template_ace.sid.sub_authority = [18]
            file_info.dacl = new_dacl
        self.chan.close(handle)
