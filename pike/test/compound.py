#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        compound.py
#
# Abstract:
#
#        Compound request tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.ntstatus
import pike.smb2
import pike.test


RelatedOpen = pike.model.RelatedOpen


class CompoundTest(pike.test.PikeTest):

    # Compounded create/close of the same file, with maximal access request
    def test_create_close(self):
        chan, tree = self.tree_connect()

        # Manually assemble a chained request
        nb_req = chan.frame()
        smb_req1 = chan.request(nb_req, obj=tree)
        smb_req2 = chan.request(nb_req, obj=tree)
        create_req = pike.smb2.CreateRequest(smb_req1)
        close_req = pike.smb2.CloseRequest(smb_req2)

        create_req.name = "hello.txt"
        create_req.desired_access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE
        create_req.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL
        create_req.create_disposition = pike.smb2.FILE_OPEN_IF

        max_req = pike.smb2.MaximalAccessRequest(create_req)

        close_req.file_id = pike.smb2.RELATED_FID
        smb_req2.flags |= pike.smb2.SMB2_FLAGS_RELATED_OPERATIONS

        chan.connection.transceive(nb_req)

    # Compound create/query/close
    def test_create_query_close(self):
        chan, tree = self.tree_connect()

        create_req = chan.create_request(
            tree,
            "create_query_close",
            access=(
                pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE
            ),
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        )
        nb_req = create_req.parent.parent
        query_req = chan.query_file_info_request(RelatedOpen(tree))
        nb_req.adopt(query_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        nb_req.adopt(close_req.parent)

        (create_res, query_res, close_res) = chan.connection.transceive(nb_req)

        compare_attributes = [
            "creation_time",
            "change_time",
            "last_access_time",
            "last_write_time",
            "file_attributes",
        ]
        for attr in compare_attributes:
            self.assertEqual(
                getattr(create_res[0], attr), getattr(query_res[0][0], attr)
            )

    # Compound create/write/close & create/read/close
    def test_create_write_close(self):
        filename = "create_write_close"
        buf = b"compounded write"

        chan, tree = self.tree_connect()

        create_req1 = chan.create_request(
            tree, filename, access=pike.smb2.GENERIC_WRITE
        )
        nb_req = create_req1.parent.parent
        write_req = chan.write_request(RelatedOpen(tree), 0, buf)
        nb_req.adopt(write_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        nb_req.adopt(close_req.parent)

        (create_res1, write_res, close_res) = chan.connection.transceive(nb_req)

        create_req2 = chan.create_request(
            tree,
            filename,
            access=(pike.smb2.GENERIC_READ | pike.smb2.DELETE),
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        )
        nb_req = create_req2.parent.parent
        read_req = chan.read_request(RelatedOpen(tree), 1024, 0)
        nb_req.adopt(read_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        nb_req.adopt(close_req.parent)

        (create_res2, read_res, close_res) = chan.connection.transceive(nb_req)

        self.assertEqual(buf, read_res[0].data.tobytes())

    # Compound create/write/close with insufficient access
    def test_create_write_close_access_denied(self):
        filename = "create_write_close_access_denied"

        chan, tree = self.tree_connect()

        create_req1 = chan.create_request(
            tree,
            filename,
            access=(pike.smb2.GENERIC_READ | pike.smb2.DELETE),
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        )
        nb_req = create_req1.parent.parent
        write_req = chan.write_request(RelatedOpen(tree), 0, "Expect fail")
        nb_req.adopt(write_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        nb_req.adopt(close_req.parent)

        with self.assert_error(pike.ntstatus.STATUS_ACCESS_DENIED):
            (create_res1, write_res, close_res) = chan.connection.transceive(nb_req)

    def test_create_failed_and_query(self):
        chan, tree = self.tree_connect()
        name = "create_query_failed"
        test_dir = chan.create(
            tree,
            name,
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
        ).result()

        create_req = chan.create_request(
            tree,
            name,
            access=pike.smb2.GENERIC_READ,
            disposition=pike.smb2.FILE_CREATE,
            options=pike.smb2.FILE_DIRECTORY_FILE,
        )
        nb_req = create_req.parent.parent

        query_req = chan.query_directory_request(RelatedOpen(tree))
        nb_req.adopt(query_req.parent)

        (create_future, query_future) = chan.connection.submit(nb_req)
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
            create_future.result()

        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
            query_future.result()

        chan.close(test_dir)
