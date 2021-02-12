"""
Tests for pike path-like interface
"""
import uuid

import pike.smb2 as smb2


ACCESS_RWD = smb2.GENERIC_READ | smb2.GENERIC_WRITE | smb2.DELETE


def test_stat_root(pike_TreeConnect):
    with pike_TreeConnect() as tc:
        print(tc.tree.pathlike.stat())


def test_exists(pike_TreeConnect):
    unique_id = str(uuid.uuid4())
    with pike_TreeConnect() as tc:
        fname = tc.tree.pathlike / unique_id
        assert not fname.exists()
        with tc.chan.create(tc.tree, unique_id, access=ACCESS_RWD, options=smb2.FILE_DELETE_ON_CLOSE).result() as fh:
            assert fname.exists()
        assert not fname.exists()

def test_iterdir(pike_TreeConnect):
    with pike_TreeConnect() as tc:
        print(list(tc.tree.pathlike.iterdir()))


def test_mkdir(pike_TreeConnect):
    with pike_TreeConnect() as tc:
        pth = tc.tree.pathlike / "foo" / "bar" / "baz"
        pth.mkdir(parents=True, exist_ok=False)

