from __future__ import absolute_import

import io
import string
import uuid

import pytest

import pike.ntstatus
import pike.smb2


@pytest.fixture
def filename():
    return "test_io_{}.bin".format(uuid.uuid4())


@pytest.fixture
def test_buffer():
    def buf(size):
        base = string.printable
        copies = size // len(base) + 1
        return (base * copies).encode("utf-8")[:size]

    return buf


def test_open_write_read_seek(pike_TreeConnect, filename, test_buffer):
    with pike_TreeConnect() as tc:
        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as fh:
            # write a buffer greater than the transact size
            max_write = tc.conn.negotiate_response.max_write_size
            buf = test_buffer(size=max_write * 3)
            fh.write(buf)

            # make sure flush works
            flush_resp = fh.flush()
            assert flush_resp
            assert flush_resp.status == pike.ntstatus.STATUS_SUCCESS

            # the EOF marker should have been updated
            assert fh.end_of_file == len(buf)

            # now we're at the end of file, so read should return empty
            assert fh.read() == b""

            # subsequent reads should also return empty
            assert fh.read() == b""

            # seek backwards to read 8 bytes
            pos = fh.seek(-8, io.SEEK_CUR)
            assert pos == fh.tell()

            tail_buf_8 = fh.read()
            assert len(tail_buf_8) == 8
            assert tail_buf_8 == buf[-8:]
            assert fh.tell() == pos + 8

            # seek to beginning of file
            pos = fh.seek(0, io.SEEK_SET)
            assert pos == 0

            # read to the end
            read_buf = fh.read()
            assert read_buf == buf
            assert fh.tell() == fh.end_of_file

            # seek -256 from the end
            pos = fh.seek(-256, io.SEEK_END)
            assert pos == fh.tell()
            assert pos == fh.end_of_file - 256
            tail_buf_256_16 = fh.read(16)
            assert len(tail_buf_256_16) == 16
            assert tail_buf_256_16 == buf[-256:-240]
            assert fh.tell() == pos + 16

            # seek backwards 512
            pos = fh.seek(-512, io.SEEK_CUR)
            assert pos == fh.tell()
            assert pos == fh.end_of_file - 256 + 16 - 512
            tail_buf_752_256 = fh.read(256)
            assert len(tail_buf_752_256) == 256
            assert tail_buf_752_256 == buf[-752:-496]
            assert fh.tell() == pos + 256


def test_open_not_readable_writable(pike_TreeConnect, filename):
    with pike_TreeConnect() as tc:
        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_READ | pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as rfh:
            assert not rfh.writable()
            # can't flush non-writable streams
            assert rfh.flush() is None

        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as wfh:
            assert not wfh.readable()


def test_update_eof(pike_TreeConnect, filename, test_buffer):
    with pike_TreeConnect() as tc:
        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_READ | pike.smb2.DELETE,
            share=pike.smb2.FILE_SHARE_ALL,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as rfh:
            with tc.chan.create(
                tc.tree,
                filename,
                access=pike.smb2.GENERIC_WRITE,
                share=pike.smb2.FILE_SHARE_ALL,
            ).result() as wfh:
                assert rfh.end_of_file == wfh.end_of_file
                buf = test_buffer(size=256)
                wfh.write(buf)
                # the two handles eof will get out of sync at this point
                assert wfh.end_of_file == len(buf)
                assert rfh.end_of_file != wfh.end_of_file

                # reading to an offset should update the eof, but they're still not equal
                assert rfh.read(128) == buf[:128]
                assert rfh.end_of_file == 128
                assert rfh.end_of_file != wfh.end_of_file

                # reading to end should update the eof, now they're in sync again
                assert rfh.read() == buf[128:]
                assert rfh.end_of_file == wfh.end_of_file


def test_open_write_multiple(pike_TreeConnect, filename, test_buffer):
    with pike_TreeConnect() as tc:
        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as fh:
            # write a buffer greater than the transact size
            max_write = tc.conn.negotiate_response.max_write_size
            buf = test_buffer(256)
            n_ops = 5
            for i in range(n_ops):
                fh.write(buf)
            fh.seek(0)
            for i in range(n_ops):
                assert fh.read(256) == buf
