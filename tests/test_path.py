"""
Tests for pike path-like interface
"""
from __future__ import absolute_import, unicode_literals
from builtins import str

import io
import os
import uuid

import pytest

import pike.io
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


def test_is_file(pike_tmp_path):
    unique_id = str(uuid.uuid4())
    fname = pike_tmp_path / unique_id
    assert not fname.exists()
    assert not fname.is_file()
    assert not fname.is_symlink()
    fname.touch()
    assert fname.exists()
    assert fname.is_file()
    assert not fname.is_dir()
    assert not fname.is_symlink()
    fname.unlink()


def test_is_dir(pike_tmp_path):
    unique_id = str(uuid.uuid4())
    dname = pike_tmp_path / unique_id
    assert not dname.exists()
    assert not dname.is_dir()
    assert not dname.is_symlink()
    dname.mkdir()
    assert dname.exists()
    assert dname.is_dir()
    assert not dname.is_file()
    assert not dname.is_symlink()
    dname.rmdir()


def test_glob(pike_tmp_path):
    a_files = ["a1", "a2", "a3"]
    b_files = ["b1", "b2", "b3"]
    for f in a_files + b_files:
        (pike_tmp_path / f).touch()

    a_glob = list(pike_tmp_path.glob("a*"))
    assert len(a_glob) == len(a_files)
    for f in a_glob:
        assert f.name in a_files

    b_glob = list(pike_tmp_path.glob("b*"))
    assert len(b_glob) == len(b_files)
    for f in b_glob:
        assert f.name in b_files

    glob2 = list(pike_tmp_path.glob("*2"))
    assert len(glob2) == 2
    for f in glob2:
        assert f.name in ("a2", "b2")


def test_glob_invalid(pike_tmp_path):
    with pytest.raises(ValueError):
        list(pike_tmp_path.glob("**/foo"))

    with pytest.raises(NotImplementedError):
        pike_tmp_path.rglob("foo")


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
    pth.mkdir(exist_ok=True)
    while pth != pike_tmp_path:
        pth.rmdir()
        pth = pth.parent


def test_write_read(pike_tmp_path):
    test_bytes = b"hola pika" * (1024 * 1024)
    pth = pike_tmp_path / "bar.txt"
    pth.write_bytes(test_bytes)
    assert pth.read_bytes() == test_bytes


def test_open_w_r_a_x(pike_tmp_path):
    buf = "this is a test test test\nfoo\n\n"
    pth = pike_tmp_path / "foo.txt"
    with pth.open("w") as f:
        assert isinstance(f.buffer, io.BufferedWriter)
        assert f.writable()
        assert not f.readable()
        assert f.buffer.raw.create_request.create_disposition == smb2.FILE_SUPERSEDE
        f.write(buf)
    assert pth.read_bytes() == buf.encode("utf-8")
    with pth.open("r") as f:
        assert isinstance(f.buffer, io.BufferedReader)
        assert f.readable()
        assert not f.writable()
        assert f.buffer.raw.create_request.create_disposition == smb2.FILE_OPEN
        assert f.read() == buf
    with pth.open("a") as f:
        assert isinstance(f.buffer, io.BufferedWriter)
        assert f.writable()
        assert not f.readable()
        assert f.buffer.raw.create_request.create_disposition == smb2.FILE_OPEN_IF
        assert f.tell() == f.buffer.raw.end_of_file
        f.write("appended")
    assert pth.read_text().endswith("appended")
    with model.pike_status(ntstatus.STATUS_OBJECT_NAME_COLLISION):
        f = pth.open("x")
    pth.unlink()
    with pth.open("x") as f:
        f.write("exclusive access")
    assert pth.read_text() == "exclusive access"


@pytest.mark.parametrize("primary_mode", ("r", "w", "a", "rb", "wb", "ab"))
@pytest.mark.parametrize(
    "buffering", (pytest.param(-1, id="buffered"), pytest.param(0, id="raw"))
)
def test_open_plus(pike_tmp_path, primary_mode, buffering):
    buf = "this is a read/write test case\n"
    pth = pike_tmp_path / "foo.txt"
    if "r" in primary_mode:
        pth.touch()
    with pth.open(primary_mode + "+", buffering=buffering) as f:
        if "b" in primary_mode:
            buf = buf.encode("utf-8")
        if buffering == 0 and "b" in primary_mode:
            assert isinstance(f, pike.io.Open)
        elif "b" in primary_mode:
            assert isinstance(f, io.BufferedRandom)
        else:
            assert isinstance(f, io.TextIOWrapper)
            assert isinstance(f.buffer, io.BufferedRandom)
        assert f.readable()
        assert f.writable()
        f.write(buf)
        f.seek(0)
        assert f.read() == buf


def test_relative_to(pike_tmp_path):
    pth = pike_tmp_path / "foo"
    assert str(pth.relative_to(pike_tmp_path)) == "foo"


def test_rename(pike_tmp_path):
    orig_file = pike_tmp_path / "orig"
    new_file = pike_tmp_path / "new"

    orig_file.touch()
    assert orig_file.is_file()
    assert not new_file.exists()

    orig_file.rename(new_file)
    assert not orig_file.exists()
    assert new_file.is_file()


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


@pytest.mark.nosamba
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
    assert link.readlink()._path == target._path
    link.unlink()
    assert not link.exists()
    assert target.exists()


@pytest.mark.nosamba
def test_symlink_dir(pike_tmp_path):
    buf = "this is my content\n"
    subdir = pike_tmp_path / "subdir"
    subdir.mkdir()
    target = subdir / "target"
    target.write_text(buf)
    link = pike_tmp_path / "link"
    link.symlink_to(subdir)
    assert (link / target.name).read_text() == buf
    assert (link / target.name).resolve() == target
    assert link.resolve() == subdir
    assert link.readlink()._path == subdir._path


@pytest.mark.nosamba
def test_symlink_relative(pike_tmp_path):
    buf = "this is my content\n"
    subdir = pike_tmp_path / "subdir"
    subdir.mkdir()
    subdir_a2 = pike_tmp_path / "subdir2" / "a1" / "a2"
    subdir_a2.mkdir(parents=True)
    target = subdir / "target"
    target.write_text(buf)
    link = subdir_a2 / "link"
    link.symlink_to(target)
    assert link.read_text() == buf
    assert link.resolve() == target
    assert (
        link.readlink()._path == link.parent._path + "\\..\\..\\..\\..\\" + target._path
    )


@pytest.mark.nosamba
def test_symlink_chain(pike_tmp_path):
    buf = "this is my content\n"
    subdir = pike_tmp_path / "subdir"
    subdir.mkdir()
    subdir_a1 = pike_tmp_path / "subdir2" / "a1"
    subdir_a1.mkdir(parents=True)
    subdir_a2 = subdir_a1 / "a2"
    subdir_a2.mkdir()
    subdir_a3 = subdir_a2 / "a3"
    subdir_a3.mkdir()
    target = subdir / "target"
    target.write_text(buf)
    link = subdir_a3 / "link"
    link.symlink_to(subdir)
    link2 = subdir_a1 / "link2"
    link2.symlink_to(link)
    link = subdir_a2 / "link3"
    link.symlink_to(link2)
    link2 = subdir_a3 / "link4"
    link2.symlink_to(link)
    link = subdir_a1 / "link5"
    link.symlink_to(link2)
    assert (link / target.name).read_text() == buf
    assert (link / target.name).resolve() == target


def test_samefile(pike_tmp_path, pike_TreeConnect):
    f1 = pike_tmp_path / "f1"
    with pike_TreeConnect() as tc2:
        f1_2 = PikePath(tc2.tree).join_from_root(f1)
        assert f1_2.drive != f1.drive
        # when the file doesn't exist, it is not considered samefile
        assert not f1.samefile(f1_2)
        f1.touch()
        assert f1.samefile(f1_2)
        assert f1_2.samefile(f1)


def test_unlink(pike_tmp_path):
    fname = pike_tmp_path / str(uuid.uuid4())
    with model.pike_status(ntstatus.STATUS_OBJECT_NAME_NOT_FOUND):
        fname.unlink()
    fname.unlink(missing_ok=True)
    fname.touch()
    assert fname.is_file()
    fname.unlink()
    assert not fname.exists()
    fname.unlink(missing_ok=True)
