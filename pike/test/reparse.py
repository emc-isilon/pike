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
#       reparse.py
#
# Abstract:
#
#       Set/Get reparse point tests
#
# Authors: Masen Furer (masen.furer@emc.com)
#

import pike.model
import pike.test

share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

class TestReparsePoint(pike.test.PikeTest):
    def test_set_get_reparse_point(self):
        chan, tree = self.tree_connect()

        target = "target"

        link = chan.create(tree,
                           "symlink",
                           pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           options=pike.smb2.FILE_OPEN_REPARSE_POINT | \
                                   pike.smb2.FILE_DELETE_ON_CLOSE).result()
        chan.set_symlink(link, target, pike.smb2.SYMLINK_FLAG_RELATIVE)
        result = chan.get_symlink(link)
        self.assertEqual(result[0][0].reparse_data.substitute_name, target)
        chan.close(link)

    def test_symbolic_link_error_response(self):
        chan, tree = self.tree_connect()

        target = "target"

        link = chan.create(tree,
                           "symlink",
                           pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=share_all,
                           options=pike.smb2.FILE_OPEN_REPARSE_POINT | \
                                   pike.smb2.FILE_DELETE_ON_CLOSE).result()
        chan.set_symlink(link, target, pike.smb2.SYMLINK_FLAG_RELATIVE)
        try:
            chan.create(tree, "symlink", share=share_all).result()
        except pike.model.ResponseError as err:
            self.assertEqual(err.response.status, pike.ntstatus.STATUS_STOPPED_ON_SYMLINK)
            self.assertEqual(err.response[0][0].error_data.substitute_name, target)
            self.assertEqual(err.response[0][0].error_data.print_name, target)
        chan.close(link)

