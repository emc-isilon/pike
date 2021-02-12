#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        queryondiskid.py
#
# Abstract:
#
#        Query On Disk Id CreateContext tests
#
# Authors: Masen Furer <masen.furer@emc.com>
#

import array

import pike.model
import pike.smb2
import pike.test

share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)
access_rwd = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE
null_fid = array.array("B", [0] * 32)


class TestQueryOnDiskID(pike.test.PikeTest):
    test_files = [
        "qfid_file.bin",
        "qfid_same_file.bin",
        "qfid_diff_file1.bin",
        "qfid_diff_file2.bin",
    ]

    def extract_file_id(self, response):
        """
        Pull out the Query On Disk ID file_id field and return it
        """
        create_res = qfid_res = None
        for child in response:
            if isinstance(child, pike.smb2.CreateResponse):
                create_res = child
                break
        self.assertIsNotNone(
            create_res,
            "response didn't contain a " "CreateResponse: {0}".format(response),
        )
        for child in create_res:
            if isinstance(child, pike.smb2.QueryOnDiskIDResponse):
                qfid_res = child
                break
        self.assertIsNotNone(
            qfid_res,
            "CreateResponse didn't contain a "
            "QueryOnDiskIDResponse: {0}".format(create_res),
        )
        return qfid_res.file_id

    def test_qfid_functional(self):
        """
        Sending a QFid request should ellicit a success response
        """

        chan, tree = self.tree_connect()
        open_future = chan.create(
            tree,
            "qfid_file.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh = open_future.result()
        fid = self.extract_file_id(open_future.request_future.result())
        self.assertNotEqual(fid, null_fid, "On disk file_id was null")

    def test_qfid_same_file(self):
        """
        Opening the same file from different sessions should return the same id
        """

        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        open_future1 = chan1.create(
            tree1,
            "qfid_same_file.bin",
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh1 = open_future1.result()
        fid1 = self.extract_file_id(open_future1.request_future.result())
        open_future2 = chan2.create(
            tree2,
            "qfid_same_file.bin",
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_OPEN,
            query_on_disk_id=True,
        )
        fh2 = open_future2.result()
        fid2 = self.extract_file_id(open_future2.request_future.result())
        self.assertNotEqual(fid1, null_fid, "On disk file_id was null")
        self.assertEqual(fid1, fid2, "On disk file_id for same file didn't match")

    def test_qfid_diff_file(self):
        """
        Opening a different file from different sessions should NOT return
        the same id
        """

        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        open_future1 = chan1.create(
            tree1,
            "qfid_diff_file1.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh1 = open_future1.result()
        fid1 = self.extract_file_id(open_future1.request_future.result())
        open_future2 = chan2.create(
            tree2,
            "qfid_diff_file2.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh2 = open_future2.result()
        fid2 = self.extract_file_id(open_future2.request_future.result())
        self.assertNotEqual(fid1, null_fid, "On disk file_id was null")
        self.assertNotEqual(
            fid1, fid2, "On disk file_id for different files was the same"
        )

    def test_qfid_same_file_seq(self):
        """
        Opening the same file name after closing the first file should return
        the same on disk id
        """

        chan, tree = self.tree_connect()
        open_future = chan.create(
            tree,
            "qfid_file.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_SUPERSEDE,
            query_on_disk_id=True,
        )
        fh = open_future.result()
        fid = self.extract_file_id(open_future.request_future.result())
        self.assertNotEqual(fid, null_fid, "On disk file_id was null")
        first_fid = fid
        chan.close(fh)

        open_future = chan.create(
            tree,
            "qfid_file.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_OPEN,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh = open_future.result()
        fid = self.extract_file_id(open_future.request_future.result())
        self.assertNotEqual(fid, null_fid, "On disk file_id was null")
        self.assertEqual(fid, first_fid, "Subsequent open returns different file id")

    def test_qfid_same_file_seq_delete(self):
        """
        Opening the same file name after deleting the first file should return
        a different on disk id
        """

        chan, tree = self.tree_connect()
        open_future = chan.create(
            tree,
            "qfid_file.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh = open_future.result()
        fid = self.extract_file_id(open_future.request_future.result())
        self.assertNotEqual(fid, null_fid, "On disk file_id was null")
        first_fid = fid
        chan.close(fh)

        open_future = chan.create(
            tree,
            "qfid_file.bin",
            access=access_rwd,
            disposition=pike.smb2.FILE_CREATE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            query_on_disk_id=True,
        )
        fh = open_future.result()
        fid = self.extract_file_id(open_future.request_future.result())
        self.assertNotEqual(fid, null_fid, "On disk file_id was null")
        self.assertNotEqual(
            fid, first_fid, "Subsequent open after delete returns same file id"
        )
