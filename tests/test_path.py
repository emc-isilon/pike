"""
Tests for pike path-like interface
"""
from __future__ import unicode_literals
from builtins import str

import os
import uuid

import pytest

import pike.model as model
import pike.ntstatus as ntstatus
from pike.path import PikePath
import pike.smb2 as smb2


ACCESS_RWD = smb2.GENERIC_READ | smb2.GENERIC_WRITE | smb2.DELETE


def test_stat_root(pike_tmp_path):
    print(pike_tmp_path.stat())


def test_exists(pike_tmp_path):
    unique_id = str(uuid.uuid4())
    fname = pike_tmp_path / unique_id
    assert not fname.exists()
    with pike_tmp_path._channel.create(
        pike_tmp_path._tree,
        fname._path,
        access=ACCESS_RWD,
        options=smb2.FILE_DELETE_ON_CLOSE,
    ).result() as fh:
        assert fname.exists()
    assert not fname.exists()


def test_iterdir(pike_tmp_path):
    filedata = {name: str(uuid.uuid4()) for name in ["f1", "f2", "f3", "f4"]}
    for f, data in filedata.items():
        (pike_tmp_path / f).write_text(data)
    for fpth in pike_tmp_path.iterdir():
        assert fpth.name in filedata
        assert fpth.read_text() == filedata[fpth.name]


def test_mkdir(pike_tmp_path):
    pth = pike_tmp_path / "foo" / "bar" / "baz"
    pth.mkdir(parents=True, exist_ok=False)
    while pth != pike_tmp_path:
        pth.rmdir()
        pth = pth.parent


def test_write_read(pike_tmp_path):
    test_bytes = b"hola pika" * (1024 * 1024)
    pth = pike_tmp_path / "bar.txt"
    pth.write_bytes(test_bytes)
    assert pth.read_bytes() == test_bytes


def test_open(pike_tmp_path):
    pth = pike_tmp_path / "foo.txt"
    f = pth.open("rw")
    f.write("this is a test test test\n")
    f.write("foo\n\n")
    f.close()
    assert pth.read_bytes() == b"this is a test test test\nfoo\n\n"


def test_relative_to(pike_tmp_path):
    pth = pike_tmp_path / "foo"
    assert str(pth.relative_to(pike_tmp_path)) == "foo"


def test_parents(pike_tmp_path):
    pcs = ["foo", "bar", "baz"]
    pth = pike_tmp_path.joinpath(*pcs)
    parents = pth.parents
    for ix, pc in enumerate(reversed(pcs[:-1])):
        print(parents[ix])
        print(parents[ix].exists())
        assert parents[ix].name == pc


def test_join_from_root(pike_tmp_path, pike_TreeConnect):
    with pike_TreeConnect() as tc2:
        pth = pike_tmp_path / "rehome.txt"
        with pth.open("w") as f:
            f.write("foo the bar\n")
            # now attempt to open the file from the second connection
            with model.pike_status(ntstatus.STATUS_SHARING_VIOLATION):
                from_root = PikePath(tc2.tree).join_from_root(pth)
                print(from_root.read_text())

@pytest.mark.skip("Doesn't work against samba")
def test_symlink(pike_tmp_path):
    buf = "this is my content\n"
    subdir = pike_tmp_path / "subdir"
    subdir.mkdir()
    target = subdir / "target"
    target.write_text(buf)
    link = pike_tmp_path / "link"
    link.symlink_to(target)
    assert link.read_text() == buf
    assert link.resolve() == target
