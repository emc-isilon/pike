"""
Tests for pike path-like interface
"""
import os
import uuid

import pytest

import pike.model as model
import pike.ntstatus as ntstatus
from pike.path import PikePath
import pike.smb2 as smb2


ACCESS_RWD = smb2.GENERIC_READ | smb2.GENERIC_WRITE | smb2.DELETE


@pytest.fixture
def test_path(pike_TreeConnect):
    with pike_TreeConnect() as tc:
        test_root = tc / "test_{}".format(uuid.uuid4())
        test_root.mkdir()
        yield test_root


def test_stat_root(test_path):
    print(test_path.stat())


def test_exists(test_path):
    unique_id = str(uuid.uuid4())
    fname = test_path / unique_id
    assert not fname.exists()
    with test_path._channel.create(
        test_path._tree,
        fname._path,
        access=ACCESS_RWD,
        options=smb2.FILE_DELETE_ON_CLOSE,
    ).result() as fh:
        assert fname.exists()
    assert not fname.exists()


def test_iterdir(test_path):
    filedata = {name: str(uuid.uuid4()) for name in ["f1", "f2", "f3", "f4"]}
    for f, data in filedata.items():
        (test_path / f).write_text(data)
    for fpth in test_path.iterdir():
        assert fpth.name in filedata
        assert fpth.read_text() == filedata[fpth.name]


def test_mkdir(test_path):
    pth = test_path / "foo" / "bar" / "baz"
    pth.mkdir(parents=True, exist_ok=False)
    while pth != test_path:
        pth.rmdir()
        pth = pth.parent


def test_write_read(test_path):
    test_bytes = b"hola pika" * (1024 * 1024)
    pth = test_path / "bar.txt"
    pth.write_bytes(test_bytes)
    assert pth.read_bytes() == test_bytes


def test_open(test_path):
    pth = test_path / "foo.txt"
    f = pth.open("rw")
    f.write("this is a test test test\n")
    f.write("foo\n\n")
    f.close()
    assert pth.read_bytes() == b"this is a test test test\nfoo\n\n"


def test_relative_to(test_path):
    pth = test_path / "foo"
    assert str(pth.relative_to(test_path)) == "foo"


def test_parents(test_path):
    pcs = ["foo", "bar", "baz"]
    pth = test_path.joinpath(*pcs)
    parents = pth.parents
    for ix, pc in enumerate(reversed(pcs[:-1])):
        print(parents[ix])
        print(parents[ix].exists())
        assert parents[ix].name == pc


def test_join_from_root(test_path, pike_TreeConnect):
    with pike_TreeConnect() as tc2:
        pth = test_path / "rehome.txt"
        with pth.open("w") as f:
            f.write("foo the bar\n")
            # now attempt to open the file from the second connection
            with model.pike_status(ntstatus.STATUS_SHARING_VIOLATION):
                from_root = PikePath(tc2.tree).join_from_root(pth)
                print(from_root.read_text())

def test_symlink(test_path):
    buf = "this is my content\n"
    subdir = test_path / "subdir"
    subdir.mkdir()
    target = subdir / "target"
    target.write_text(buf)
    link = test_path / "link"
    link.symlink_to(target)
    assert link.read_text() == buf
    assert link.resolve() == target
