#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        querydirectory.py
#
# Abstract:
#
#        Query directory tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus


class QueryDirectoryTest(pike.test.PikeTest):
    # Enumerate directory at FILE_DIRECTORY_INFORMATION level.
    # Test for presence of . and .. entries
    def test_file_directory_info(self):

        chan, tree = self.tree_connect()
        root = chan.create(
            tree,
            "",
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
            share=pike.smb2.FILE_SHARE_READ,
        ).result()

        names = [info.file_name for info in chan.enum_directory(root)]

        self.assertIn(".", names)

        chan.close(root)

    # Querying for a specific filename twice
    # on the same handle succeeds the first time and
    # fails with STATUS_NO_MORE_FILES the second.
    def test_specific_name(self):
        chan, tree = self.tree_connect()
        name = "hello.txt"

        hello = chan.create(
            tree,
            name,
            access=pike.smb2.GENERIC_WRITE | pike.smb2.GENERIC_READ | pike.smb2.DELETE,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()

        root = chan.create(
            tree,
            "",
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
            share=pike.smb2.FILE_SHARE_READ,
        ).result()

        query1 = chan.query_directory(root, file_name=name)

        with self.assert_error(pike.ntstatus.STATUS_NO_MORE_FILES):
            chan.query_directory(root, file_name=name)

        chan.close(hello)
        chan.close(root)

    def test_file_id_both_directory_information(self):

        chan, tree = self.tree_connect()
        root = chan.create(
            tree,
            "",
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
            share=pike.smb2.FILE_SHARE_READ,
        ).result()

        result = chan.query_directory(
            root, file_information_class=pike.smb2.FILE_ID_BOTH_DIR_INFORMATION
        )
        names = [info.file_name for info in result]
        self.assertIn(".", names)
        self.assertIn("..", names)

        valid_file_ids = [info.file_id >= 0 for info in result]
        self.assertNotIn(False, valid_file_ids)

        chan.close(root)

    def test_restart_scan(self):

        chan, tree = self.tree_connect()
        root = chan.create(
            tree,
            "",
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
            share=pike.smb2.FILE_SHARE_READ,
        ).result()

        result = chan.query_directory(root)
        names = [info.file_name for info in result]
        self.assertIn(".", names)

        result = chan.query_directory(
            root, flags=pike.smb2.SL_RESTART_SCAN, file_name="*"
        )
        names = [info.file_name for info in result]
        self.assertIn(".", names)

        chan.close(root)
