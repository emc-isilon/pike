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
import random
import array


def adopt(new_parent, obj):
    """
    obj is adopted by new_parent
    """
    new_parent.append(obj)
    obj.parent = new_parent
    if isinstance(obj, pike.smb2.Smb2):
        obj.flags |= pike.smb2.SMB2_FLAGS_RELATED_OPERATIONS


class RelatedOpen(pike.model.Tree):
    """
    Shim to insert the RELATED_FID into the request
    """
    def __init__(self, tree=None):
        self.tree_id = tree.tree_id
        self.file_id = pike.smb2.RELATED_FID
        self.encrypt_data = tree.encrypt_data if tree is not None else False


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

        create_req.name = 'hello.txt'
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
                access=(pike.smb2.GENERIC_READ |
                        pike.smb2.GENERIC_WRITE |
                        pike.smb2.DELETE),
                options=pike.smb2.FILE_DELETE_ON_CLOSE)
        nb_req = create_req.parent.parent
        query_req = chan.query_file_info_request(RelatedOpen(tree))
        adopt(nb_req, query_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        adopt(nb_req, close_req.parent)

        (create_res,
         query_res,
         close_res) = chan.connection.transceive(nb_req)

        compare_attributes = [
                "creation_time",
                "change_time",
                "last_access_time",
                "last_write_time",
                "file_attributes"]
        for attr in compare_attributes:
            self.assertEqual(getattr(create_res[0], attr),
                             getattr(query_res[0][0], attr))

    # Compound create/write/close & create/read/close
    def test_create_write_close(self):
        filename = "create_write_close"
        buf = "compounded write"

        chan, tree = self.tree_connect()

        create_req1 = chan.create_request(
                tree,
                filename,
                access=pike.smb2.GENERIC_WRITE)
        nb_req = create_req1.parent.parent
        write_req = chan.write_request(RelatedOpen(tree), 0, buf)
        adopt(nb_req, write_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        adopt(nb_req, close_req.parent)

        (create_res1,
         write_res,
         close_res) = chan.connection.transceive(nb_req)

        create_req2 = chan.create_request(
                tree,
                filename,
                access=(pike.smb2.GENERIC_READ |
                        pike.smb2.DELETE),
                options=pike.smb2.FILE_DELETE_ON_CLOSE)
        nb_req = create_req2.parent.parent
        read_req = chan.read_request(RelatedOpen(tree), 1024, 0)
        adopt(nb_req, read_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        adopt(nb_req, close_req.parent)

        (create_res2,
         read_res,
         close_res) = chan.connection.transceive(nb_req)

        self.assertEqual(buf, read_res[0].data.tostring())

    # Compound create/write/close with insufficient access
    def test_create_write_close_access_denied(self):
        filename = "create_write_close_access_denied"

        chan, tree = self.tree_connect()

        create_req1 = chan.create_request(
                tree,
                filename,
                access=(pike.smb2.GENERIC_READ |
                        pike.smb2.DELETE),
                options=pike.smb2.FILE_DELETE_ON_CLOSE)
        nb_req = create_req1.parent.parent
        write_req = chan.write_request(RelatedOpen(tree), 0, "Expect fail")
        adopt(nb_req, write_req.parent)

        close_req = chan.close_request(RelatedOpen(tree))
        adopt(nb_req, close_req.parent)

        with self.assert_error(pike.ntstatus.STATUS_ACCESS_DENIED):
            (create_res1,
             write_res,
             close_res) = chan.connection.transceive(nb_req)

    def test_create_failed_and_query(self):
        chan, tree = self.tree_connect()
        name = "create_query_failed"
        test_dir = chan.create(tree,
                               name,
                               access=pike.smb2.GENERIC_READ,
                               options=pike.smb2.FILE_DIRECTORY_FILE).result()

        create_req = chan.create_request(
                tree,
                name,
                access=pike.smb2.GENERIC_READ,
                disposition=pike.smb2.FILE_CREATE,
                options=pike.smb2.FILE_DIRECTORY_FILE)
        nb_req = create_req.parent.parent

        query_req = chan.query_directory_request(RelatedOpen(tree))
        adopt(nb_req, query_req.parent)

        (create_future, query_future) = chan.connection.submit(nb_req)
        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
            create_future.result()

        with self.assert_error(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
            query_future.result()

        chan.close(test_dir)
