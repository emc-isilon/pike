#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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

share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)


class TestReparsePoint(pike.test.PikeTest):
    def test_set_get_reparse_point(self):
        chan, tree = self.tree_connect()

        target = "target"

        link = chan.create(
            tree,
            "symlink",
            pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
            options=pike.smb2.FILE_OPEN_REPARSE_POINT | pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        chan.set_symlink(link, target, pike.smb2.SYMLINK_FLAG_RELATIVE)
        result = chan.get_symlink(link)
        self.assertEqual(result[0][0].reparse_data.substitute_name, target)
        chan.close(link)

    def test_symbolic_link_error_response(self):
        chan, tree = self.tree_connect()

        target = "target"

        link = chan.create(
            tree,
            "symlink",
            pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
            share=share_all,
            options=pike.smb2.FILE_OPEN_REPARSE_POINT | pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        chan.set_symlink(link, target, pike.smb2.SYMLINK_FLAG_RELATIVE)
        try:
            chan.create(tree, "symlink", share=share_all).result()
        except pike.model.ResponseError as err:
            self.assertEqual(
                err.response.status, pike.ntstatus.STATUS_STOPPED_ON_SYMLINK
            )
            self.assertEqual(err.response[0][0].error_data.substitute_name, target)
            self.assertEqual(err.response[0][0].error_data.print_name, target)
        chan.close(link)
