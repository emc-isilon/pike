#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_compound.py
#
# Abstract:
#
#        Compound request tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#          Masen Furer (m_github@0x26.net)
#
import pytest

from pike.model import RelatedOpen
import pike.ntstatus
import pike.smb2


def test_create_close(pike_tree_connect):
    """Compounded create/close of the same file, with maximal access request."""
    chan, tree = pike_tree_connect

    create_req = chan.create_request(
        tree,
        "hello.txt",
        access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
        attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL,
        disposition=pike.smb2.FILE_OPEN_IF,
        maximal_access=True,
    )
    nb_req = create_req.parent.parent
    nb_req.adopt(chan.close_request(RelatedOpen).parent)
    resp = pike_tree_connect.conn.transceive(nb_req)
    assert len(resp) == 2


def test_create_query_close(pike_tree_connect):
    """Compound create/query/close."""
    chan, tree = pike_tree_connect

    create_req = chan.create_request(
        tree,
        "create_query_close",
        access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
        options=pike.smb2.FILE_DELETE_ON_CLOSE,
    )
    nb_req = create_req.parent.parent
    nb_req.adopt(chan.query_file_info_request(RelatedOpen).parent)
    nb_req.adopt(chan.close_request(RelatedOpen(tree)).parent)

    resp = pike_tree_connect.conn.transceive(nb_req)
    assert len(resp) == 3
    (create_res, query_res, close_res) = resp

    compare_attributes = [
        "creation_time",
        "change_time",
        "last_access_time",
        "last_write_time",
        "file_attributes",
    ]
    for attr in compare_attributes:
        assert getattr(create_res[0], attr) == getattr(query_res[0][0], attr)


def test_create_write_close(pike_tree_connect):
    """Compound create/write/close & create/read/close."""
    filename = "create_write_close"
    buf = b"compounded write"

    chan, tree = pike_tree_connect

    create_req1 = chan.create_request(
        tree,
        filename,
        access=pike.smb2.GENERIC_WRITE,
    )
    nb_req = create_req1.parent.parent
    nb_req.adopt(chan.write_request(RelatedOpen(tree), 0, buf).parent)
    nb_req.adopt(chan.close_request(RelatedOpen(tree)).parent)

    resp1 = chan.connection.transceive(nb_req)
    assert len(resp1) == 3

    create_req2 = chan.create_request(
        tree,
        filename,
        access=(pike.smb2.GENERIC_READ | pike.smb2.DELETE),
        options=pike.smb2.FILE_DELETE_ON_CLOSE,
    )
    nb_req = create_req2.parent.parent
    nb_req.adopt(chan.read_request(RelatedOpen(tree), 1024, 0).parent)
    nb_req.adopt(chan.close_request(RelatedOpen(tree)).parent)

    resp2 = pike_tree_connect.conn.transceive(nb_req)
    assert len(resp2) == 3
    (create_res2, read_res, close_res) = resp2

    assert buf == read_res[0].data.tobytes()


@pytest.mark.parametrize(
    "submit_method",
    ["submit", "transceive"],
)
def test_create_write_close_access_denied(pike_tree_connect, submit_method):
    """Compound create/write/close with insufficient access"""
    filename = "create_write_close_access_denied"
    chan, tree = pike_tree_connect

    create_req1 = chan.create_request(
        tree,
        filename,
        access=(pike.smb2.GENERIC_READ | pike.smb2.DELETE),
        options=pike.smb2.FILE_DELETE_ON_CLOSE,
    )
    nb_req = create_req1.parent.parent
    nb_req.adopt(chan.write_request(RelatedOpen(tree), 0, b"Expect fail").parent)
    nb_req.adopt(chan.close_request(RelatedOpen).parent)

    if submit_method == "transceive":
        with pike.ntstatus.raises(pike.ntstatus.STATUS_ACCESS_DENIED) as ntsctx:
            _ = pike_tree_connect.conn.transceive(nb_req)
        resp_err = ntsctx.exc.response
        assert resp_err.status == pike.ntstatus.STATUS_ACCESS_DENIED
    elif submit_method == "submit":
        (create_future, write_future, close_future) = pike_tree_connect.conn.submit(
            nb_req
        )
        assert create_future.result()
        with pike.ntstatus.raises(pike.ntstatus.STATUS_ACCESS_DENIED):
            write_future.result()
        assert close_future.result()
    else:
        pytest.fail("Unhandled submit method: {}".format(submit_method))


@pytest.fixture
def top_level_directory(pike_tmp_path):
    path = pike_tmp_path / "top_level"
    with path.create(
        access=(pike.smb2.GENERIC_READ | pike.smb2.DELETE),
        options=pike.smb2.FILE_DIRECTORY_FILE | pike.smb2.FILE_DELETE_ON_CLOSE,
    ):
        yield path


def test_create_failed_and_query(pike_tree_connect, top_level_directory):
    chan, tree = pike_tree_connect

    create_req = chan.create_request(
        tree,
        top_level_directory._path,
        access=pike.smb2.GENERIC_READ,
        disposition=pike.smb2.FILE_CREATE,
        options=pike.smb2.FILE_DIRECTORY_FILE,
    )
    nb_req = create_req.parent.parent
    nb_req.adopt(chan.query_directory_request(RelatedOpen(tree)).parent)

    (create_future, query_future) = pike_tree_connect.conn.submit(nb_req)

    with pike.ntstatus.raises(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
        create_future.result()

    with pike.ntstatus.raises(pike.ntstatus.STATUS_OBJECT_NAME_COLLISION):
        query_future.result()
