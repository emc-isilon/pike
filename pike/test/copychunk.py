#
# Copyright (c) 2015-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        copychunk.py
#
# Abstract:
#
#        Tests for server side copy
#
# Authors: Avi Bhandari (avi.bahndari@emc.com)
#          Masen Furer (masen.furer@emc.com)
#

from __future__ import division
from builtins import chr
from builtins import range
from builtins import str
from builtins import zip

import array
import random

import pike.ntstatus
import pike.smb2
import pike.test

share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)
access_rwd = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
access_wd = pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

SIMPLE_CONTENT = "Hello"
SIMPLE_5_CHUNKS = [
    (0, 0, 4000),
    (4000, 4000, 4000),
    (8000, 8000, 4000),
    (12000, 12000, 4000),
    (16000, 16000, 4000),
]
SIMPLE_5_CHUNKS_LEN = 20000


def _gen_test_buffer(length):
    # XXX: refactor and push up into helper/util module
    pattern = "".join([chr(x) for x in range(ord(" "), ord("~"))])
    buf = (pattern * ((length // len(pattern)) + 1))[:length]
    return buf.encode("ascii")


def _gen_random_test_buffer(length):
    # XXX: refactor and push up into helper/util module
    buf = ""
    random_str_seq = "0123456789" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i in range(0, length):
        if i % length == 0 and i != 0:
            buf += "-"
        # XXX: accidentally quadratic str concat
        buf += str(random_str_seq[random.randint(0, len(random_str_seq) - 1)])
    return buf.encode("ascii")


###
# Main test
###


class TestServerSideCopy(pike.test.PikeTest):
    # these values are valid for Windows -- other servers may need to adjust
    bad_resume_key_error = pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND
    max_number_of_chunks = 256
    max_chunk_size = 1048576
    max_data_size = 16777216

    def setUp(self):
        self.chan, self.tree = self.tree_connect()
        self.other_chan_list = []

    def tearDown(self):
        self._clean_up_other_channels()
        self.chan.tree_disconnect(self.tree)
        self.chan.logoff()

    def _create_and_write(self, filename, content):
        """ create / overwrite filename with content """
        fh1 = self.chan.create(
            self.tree,
            filename,
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
        ).result()
        # get the max size of write per request
        max_write_size = min(
            self.chan.connection.negotiate_response.max_write_size, self.max_chunk_size
        )
        total_len = len(content)
        this_offset = 0
        writes = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + max_write_size < total_len:
                length = max_write_size
            else:
                length = total_len - this_offset
            writes.append((offset, length))
            this_offset += max_write_size
        num_of_writes = len(writes)
        bytes_written = 0
        for the_offset, the_length in writes:
            bytes_written += self.chan.write(
                fh1, the_offset, content[the_offset : (the_offset + the_length)]
            )
        self.chan.close(fh1)

    def _open_src_dst(
        self,
        src_filename,
        dst_filename,
        src_access=None,
        src_disp=None,
        src_options=None,
        dst_access=None,
        dst_disp=None,
        dst_options=None,
    ):
        if src_access is None:
            src_access = pike.smb2.FILE_READ_DATA | pike.smb2.DELETE
        if dst_access is None:
            dst_access = access_rwd
        if src_disp is None:
            src_disp = pike.smb2.FILE_OPEN
        if dst_disp is None:
            dst_disp = pike.smb2.FILE_SUPERSEDE
        if src_options is None:
            src_options = pike.smb2.FILE_DELETE_ON_CLOSE
        if dst_options is None:
            dst_options = pike.smb2.FILE_DELETE_ON_CLOSE

        if src_filename == dst_filename:
            src_options = 0  # if we're opening the same file, only delete one
        fh_src = self.chan.create(
            self.tree,
            src_filename,
            access=src_access,
            share=share_all,
            disposition=src_disp,
            options=src_options,
        ).result()

        fh_dst = self.chan.create(
            self.tree,
            dst_filename,
            access=dst_access,
            share=share_all,
            disposition=dst_disp,
            options=dst_options,
        ).result()
        return (fh_src, fh_dst)

    def _get_readable_handler(self, filename):
        fh_read = self.chan.create(
            self.tree,
            filename,
            access=pike.smb2.FILE_READ_DATA,
            share=share_all,
            options=0,
        ).result()
        return fh_read

    def _clean_up_other_channels(self):
        """
        clean up chan tree filehandles during failure
        """
        if self.other_chan_list:
            for info in self.other_chan_list:
                for fh in info["filehandles"]:
                    info["channel"].close(fh)
                info["channel"].tree_disconnect(info["tree"])
                info["channel"].logoff()
            self.other_chan_list = []

    def _prepare_source_file(self):
        """
        generate a five chunks file as source file for resume_key request
        """
        src_filename = "src_copy_chunk_rk.txt"
        self._create_and_write(src_filename, SIMPLE_CONTENT)

    def _read_big_file(self, file_handle, total_len, add_offset=0):
        """ read large file and return in string """
        max_read_size = self.chan.connection.negotiate_response.max_read_size
        reads = []
        this_offset = 0
        while this_offset < total_len:
            offset = this_offset
            if this_offset + max_read_size < total_len:
                length = max_read_size
            else:
                length = total_len - this_offset
            reads.append((offset, length))
            this_offset += max_read_size
        num_of_reads = len(reads)
        read_list = []
        for the_offset, the_length in reads:
            read_list.append(
                self.chan.read(
                    file_handle, the_length, the_offset + add_offset
                ).tobytes()
            )
        return b"".join(read_list)

    def _gen_16mega_file(self, filename):
        """
        use multiple server side copy to generate a 16M sourcefile
        """
        file_64k = "temp_src_file_64k.txt"
        file_1m = "temp_src_file_1m.txt"
        block_64k = _gen_test_buffer(65536)
        self._create_and_write(file_64k, block_64k)
        list_offset_64k = [i * 65536 for i in range(16)]
        chunks_64k_1m = list(zip([0] * 16, list_offset_64k, [65536] * 16))
        list_offset_1m = [i * 1048576 for i in range(16)]
        chunks_1m_16m = list(zip([0] * 16, list_offset_1m, [1048576] * 16))
        fh_64k = self.chan.create(
            self.tree,
            file_64k,
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_OPEN,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        fh_1m = self.chan.create(
            self.tree,
            file_1m,
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        fh_16m = self.chan.create(
            self.tree,
            filename,
            access=access_rwd,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=0,
        ).result()
        self.chan.copychunk(fh_64k, fh_1m, chunks_64k_1m)
        self.chan.copychunk(fh_1m, fh_16m, chunks_1m_16m)
        self.chan.close(fh_64k)
        self.chan.close(fh_1m)
        self.chan.close(fh_16m)

    def _gen_random_chunks_on_para(self, random_chunk_size=False, random_offset=False):
        """
        generate random chunks for chunkcopy operation
        copy length is always randomized, chunk_size and offset can be fixed by flags
        """

        if random_chunk_size:
            chunk_sz = random.randrange(1, self.max_chunk_size + 1)
        else:
            chunk_sz = self.max_chunk_size
        total_len = random.randrange(1, 16 * chunk_sz)
        if random_offset:
            dst_offset = random.randrange(1, 4294967295 - total_len)
        else:
            dst_offset = 0
        this_offset = 0
        chunks = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, offset + dst_offset, length))
            this_offset += chunk_sz
        self.logger.info(
            "chunks generated, total_length is %d, chunk_size is %d, dst_offset is %lu"
            % (total_len, chunk_sz, dst_offset)
        )
        return chunks

    def _prepare_before_ssc_copy(self, filepair, write_thru=False):
        if write_thru:
            my_options = pike.smb2.FILE_WRITE_THROUGH
        else:
            my_options = 0
        num_sess = len(filepair)
        for i in range(0, num_sess):
            chan, tree = self.tree_connect()
            fh_src = chan.create(
                tree, filepair[i][0], access=access_rwd, share=share_all
            ).result()

            fh_dst = chan.create(
                tree,
                filepair[i][1],
                access=access_rwd,
                share=share_all,
                options=my_options,
            ).result()
            resume_key = chan.resume_key(fh_src)[0][0].resume_key
            self.other_chan_list.append(
                {
                    "channel": chan,
                    "tree": tree,
                    "filehandles": [fh_src, fh_dst],
                    "resume_key": resume_key,
                }
            )

    def _submit_ssc_async_request(self, chan, file_handle, resume_key, chunks):
        """
        submit ssc request with resume_key as input parameter
        return the future object for later check
        """
        smb_req = chan.request(obj=file_handle.tree)
        ioctl_req = pike.smb2.IoctlRequest(smb_req)
        copychunk_req = pike.smb2.CopyChunkCopyRequest(ioctl_req)

        ioctl_req.max_output_response = 16384
        ioctl_req.file_id = file_handle.file_id
        ioctl_req.flags |= pike.smb2.SMB2_0_IOCTL_IS_FSCTL
        copychunk_req.source_key = resume_key
        copychunk_req.chunk_count = len(chunks)

        for source_offset, target_offset, length in chunks:
            chunk = pike.smb2.CopyChunk(copychunk_req)
            chunk.source_offset = source_offset
            chunk.target_offset = target_offset
            chunk.length = length

        future = chan.connection.submit(ioctl_req.parent.parent)
        return future

    def _submit_ssc_async_request_in_other_channels(self, index, chunks):
        chan = self.other_chan_list[index]["channel"]
        fh_dst = self.other_chan_list[index]["filehandles"][1]
        resume_key = self.other_chan_list[index]["resume_key"]

        return self._submit_ssc_async_request(chan, fh_dst, resume_key, chunks)

    def generic_ssc_test_case(
        self, block, number_of_chunks, total_offset=0, write_flag=False
    ):
        """
        copy block in number_of_chunks, offset the destination copy by total_offset
        """
        src_filename = "src_copy_chunk_offset.txt"
        dst_filename = "dst_copy_chunk_offset.txt"
        self._create_and_write(src_filename, block)

        total_len = len(block)
        chunk_sz = (total_len // number_of_chunks) + 1
        this_offset = 0

        chunks = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, offset + total_offset, length))
            this_offset += chunk_sz

        if write_flag:
            dst_access = access_wd
        else:
            dst_access = access_rwd

        fh_src, fh_dst = self._open_src_dst(
            src_filename, dst_filename, dst_access=dst_access
        )

        result = self.chan.copychunk(fh_src, fh_dst, chunks, write_flag=write_flag)

        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read each file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tobytes()
        self.assertBufferEqual(src_buf, block)
        fh_dst_read = self._get_readable_handler(dst_filename)
        dst_buf = self.chan.read(fh_dst_read, total_len, total_offset).tobytes()
        self.assertBufferEqual(dst_buf, block)

        self.chan.close(fh_dst_read)
        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def test_copy_small_file(self):
        block = b"Hello"
        num_of_chunks = 1
        self.generic_ssc_test_case(block, num_of_chunks)

    def test_copy_big_file(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 1
        self.generic_ssc_test_case(block, num_of_chunks)

    def test_copy_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        self.generic_ssc_test_case(block, num_of_chunks)

    def test_copy_max_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 16
        self.generic_ssc_test_case(block, num_of_chunks)

    def test_offset_copy_small_file(self):
        block = b"Hello"
        num_of_chunks = 1
        offset = 64
        self.generic_ssc_test_case(block, num_of_chunks, offset)

    def test_offset_copy_big_file(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 1
        offset = 64
        self.generic_ssc_test_case(block, num_of_chunks, offset)

    def test_offset_copy_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        offset = 64
        self.generic_ssc_test_case(block, num_of_chunks, offset)

    def test_copy_write_small_file(self):
        block = b"Hello"
        num_of_chunks = 1
        self.generic_ssc_test_case(block, num_of_chunks, write_flag=True)

    def test_copy_write_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        self.generic_ssc_test_case(block, num_of_chunks, write_flag=True)

    def test_copy_write_max_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 16
        self.generic_ssc_test_case(block, num_of_chunks, write_flag=True)

    def generic_ssc_same_file_test_case(self, block, number_of_chunks, total_offset=0):
        """
        duplicate block in number_of_chunks to the same file,
        the copy will be total_offset from the current end of file
        """
        filename = "src_copy_chunk_same.txt"
        self._create_and_write(filename, block)

        total_len = len(block)
        chunk_sz = (total_len // number_of_chunks) + 1
        this_offset = 0

        chunks = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, offset + total_len + total_offset, length))
            this_offset += chunk_sz

        fh_src, fh_dst = self._open_src_dst(
            filename, filename, dst_disp=pike.smb2.FILE_OPEN_IF
        )

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read the file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tobytes()
        self.assertBufferEqual(src_buf, block)
        if total_offset > 0:
            offs_buf = self.chan.read(fh_src, total_offset, total_len).tobytes()
            self.assertBufferEqual(offs_buf, b"\x00" * total_offset)
        dst_buf = self.chan.read(fh_src, total_len, total_len + total_offset).tobytes()
        self.assertBufferEqual(dst_buf, block)

        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def test_same_small_file(self):
        block = b"Hello"
        num_of_chunks = 1
        self.generic_ssc_same_file_test_case(block, num_of_chunks)

    def test_same_big_file(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 1
        self.generic_ssc_same_file_test_case(block, num_of_chunks)

    def test_same_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        self.generic_ssc_same_file_test_case(block, num_of_chunks)

    def test_same_offset_small_file(self):
        block = b"Hello"
        num_of_chunks = 1
        offset = 64
        self.generic_ssc_same_file_test_case(block, num_of_chunks, offset)

    def test_same_offset_big_file(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 1
        offset = 64
        self.generic_ssc_same_file_test_case(block, num_of_chunks, offset)

    def test_same_offset_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        offset = 64
        self.generic_ssc_same_file_test_case(block, num_of_chunks, offset)

    def generic_ssc_overlap_test_case(
        self, block, number_of_chunks, overlap_each_block=0
    ):
        """
        copy block in number_of_chunks, each destination block offset will be overlapped
        over the previous block by overlap_each_block bytes
        """
        src_filename = "src_copy_chunk_overlap.txt"
        dst_filename = "dst_copy_chunk_overlap.txt"
        self._create_and_write(src_filename, block)

        total_len = len(block)
        chunk_sz = (total_len // number_of_chunks) + 1
        this_offset = 0

        chunks = []
        src_block = array.array("B", block)
        dst_block = array.array("B", block)
        while this_offset < total_len:
            offset = dst_offset = this_offset
            if offset - overlap_each_block > 0:
                dst_offset = offset - overlap_each_block
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, dst_offset, length))
            dst_block[dst_offset : dst_offset + length] = src_block[
                offset : offset + length
            ]
            this_offset += chunk_sz
        dst_len = dst_offset + length
        dst_block = dst_block[:dst_len].tobytes()

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read each file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tobytes()
        self.assertBufferEqual(src_buf, block)
        dst_buf = self.chan.read(fh_dst, dst_len, 0).tobytes()
        self.assertBufferEqual(dst_buf, dst_block)

        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def test_overlap_multiple_chunks(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 10
        overlap = 64
        self.generic_ssc_overlap_test_case(block, num_of_chunks, overlap)

    def test_overlap_16_chunks_1024_overlap(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 16
        overlap = 1024
        self.generic_ssc_overlap_test_case(block, num_of_chunks, overlap)

    def test_overlap_15_chunks_4096_overlap(self):
        block = _gen_test_buffer(65535)
        num_of_chunks = 15
        overlap = 4096
        self.generic_ssc_overlap_test_case(block, num_of_chunks, overlap)

    def generic_ssc_negative_test_case(
        self,
        src_access=None,
        dst_access=None,
        src_disp=None,
        dst_disp=None,
        src_options=None,
        dst_options=None,
        src_brl=None,
        dst_brl=None,
        exp_error=None,
    ):
        block = b"Hello"
        total_len = len(block)
        src_filename = "src_negative.txt"
        dst_filename = "dst_negative.txt"
        self._create_and_write(src_filename, block)

        fh_src, fh_dst = self._open_src_dst(
            src_filename,
            dst_filename,
            src_access=src_access,
            src_disp=src_disp,
            src_options=src_options,
            dst_access=dst_access,
            dst_disp=dst_disp,
            dst_options=dst_options,
        )
        close_handles = []
        if src_brl or dst_brl:
            chan2, tree2 = self.tree_connect()
            if src_brl:
                fh_src_other = chan2.create(
                    tree2, src_filename, access=access_rwd, share=share_all
                ).result()
                chan2.lock(
                    fh_src_other, [(0, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
                ).result()
                close_handles.append((chan2, fh_src_other))
            if dst_brl:
                fh_dst_other = chan2.create(
                    tree2, dst_filename, access=access_rwd, share=share_all
                ).result()
                chan2.lock(
                    fh_dst_other, [(3, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
                ).result()
                close_handles.append((chan2, fh_dst_other))
        if exp_error is None:
            exp_error = pike.ntstatus.STATUS_SUCCESS
        try:
            with self.assert_error(exp_error):
                result = self.chan.copychunk(fh_src, fh_dst, [(0, 0, 5)])
        finally:
            for chan, fh in close_handles:
                chan.close(fh)
            self.chan.close(fh_src)
            self.chan.close(fh_dst)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_neg_src_exc_brl(self):
        """
        Initiate copychunk when another handle has an exclusive BRL on the
        source file (win 8 / 2012)
        """
        self.generic_ssc_negative_test_case(
            src_brl=True, exp_error=pike.ntstatus.STATUS_FILE_LOCK_CONFLICT
        )

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_neg_dst_exc_brl(self):
        """
        Initiate copychunk when another handle has an exclusive BRL on the
        destination file (win 8 / 2012)
        """
        self.generic_ssc_negative_test_case(
            dst_brl=True, exp_error=pike.ntstatus.STATUS_FILE_LOCK_CONFLICT
        )

    def test_neg_src_no_read(self):
        """
        Try to copychunk with no read access on the source file
        """
        self.generic_ssc_negative_test_case(
            src_access=pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED,
        )

    def test_neg_dst_no_read(self):
        """
        Try to copychunk with no read access on the destination file
        """
        self.generic_ssc_negative_test_case(
            dst_access=pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED,
        )

    def test_neg_dst_no_write(self):
        """
        Try to copychunk with no write access on the destination file
        """
        self.generic_ssc_negative_test_case(
            dst_access=pike.smb2.FILE_READ_DATA | pike.smb2.DELETE,
            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED,
        )

    def test_neg_dst_is_a_dir(self):
        """
        Try to copychunk with destination file being a directory
        """
        self.generic_ssc_negative_test_case(
            dst_options=pike.smb2.FILE_DIRECTORY_FILE | pike.smb2.FILE_DELETE_ON_CLOSE,
            dst_disp=pike.smb2.FILE_OPEN_IF,
            exp_error=pike.ntstatus.STATUS_INVALID_DEVICE_REQUEST,
        )

    def generic_multiple_resume_key_test_case(self, sess_num):
        """
        multiple session resume key test
        """
        src_filename = "src_copy_chunk_rk.txt"
        content = "resume key test"
        rk_list = []

        for i in range(sess_num):
            chan, tree = self.tree_connect()
            fh_1 = chan.create(
                tree, src_filename, access=access_rwd, share=share_all
            ).result()
            chan.write(fh_1, 0, content)
            resume_key_1_1 = chan.resume_key(fh_1)[0][0].resume_key
            resume_key_1_2 = chan.resume_key(fh_1)[0][0].resume_key
            fh_2 = chan.create(
                tree, src_filename, access=access_rwd, share=share_all
            ).result()
            resume_key_2_1 = chan.resume_key(fh_2)[0][0].resume_key
            resume_key_2_2 = chan.resume_key(fh_2)[0][0].resume_key
            self.other_chan_list.append(
                {"channel": chan, "tree": tree, "filehandles": [fh_1, fh_2]}
            )
            try:
                # for same file handler, resume_key should be same
                self.assertEqual(resume_key_1_1, resume_key_1_2)
                self.assertEqual(resume_key_2_1, resume_key_2_2)
                # for different file handler in same session
                self.assertNotEqual(resume_key_1_1, resume_key_2_1)
                # for different file hander and different session
                self.assertNotIn(resume_key_1_1, rk_list)
                self.assertNotIn(resume_key_2_1, rk_list)
            except AssertionError:
                self.error(
                    "resume key check failed on session index {0}".format(i),
                    exc_info=True,
                )
                raise
            else:
                rk_list += [resume_key_1_1, resume_key_2_1]

    def test_multiple_resume_key(self):
        """
        test multiple sessions requesting resume_key for same
        file, also test within one session, multiple requests
        for same file
        """
        self.generic_multiple_resume_key_test_case(sess_num=3)

    def generic_negative_resume_key_test_case(self, resume_key, exp_error=None):
        """
        negative test for invalid resume key handling case
        """
        src_filename = "src_copy_chunk_rk.txt"
        dst_filename = "dst_copy_chunk_rk.txt"

        chunks = [(0, 0, len(SIMPLE_CONTENT))]
        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)

        if exp_error is None:
            exp_error = pike.ntstatus.STATUS_SUCCESS
        try:
            with self.assert_error(exp_error):
                result = self.chan.copychunk(fh_src, fh_dst, chunks, resume_key)
        finally:
            self.chan.close(fh_src)
            self.chan.close(fh_dst)

    def test_other_resume_key(self):
        """
        negative test for multiple sessions acquiring resume key
        for same file one session uses other session's resume key
        to perform the server side copy
        """
        self._prepare_source_file()
        chan_2, tree_2 = self.tree_connect()
        src_filename = "src_copy_chunk_rk.txt"
        fh_src_2 = chan_2.create(
            tree_2, src_filename, access=access_rwd, share=share_all
        ).result()
        self.other_chan_list.append(
            {"channel": chan_2, "tree": tree_2, "filehandles": [fh_src_2]}
        )
        other_key = chan_2.resume_key(fh_src_2)[0][0].resume_key

        self.generic_negative_resume_key_test_case(
            other_key, exp_error=self.bad_resume_key_error
        )

    def test_bogus_resume_key(self):
        """
        negative test for single session does not acquire resume_key
        but generate one bogus resume_key to perform the server side copy
        """
        self._prepare_source_file()
        import array

        bogus_key = array.array("B", [255] * 24)
        self.generic_negative_resume_key_test_case(
            bogus_key, exp_error=self.bad_resume_key_error
        )

    def basic_ssc_random_test_case(self, chunks, src_options=0):
        """
        given chunks, perform server side copy accordingly
        """
        src_filename = "src_copy_chunk_random.txt"
        dst_filename = "dst_copy_chunk_random.txt"

        fh_src, fh_dst = self._open_src_dst(
            src_filename, dst_filename, src_options=src_options
        )

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        copy_len = chunks[-1][0] + chunks[-1][2]
        dst_offset = chunks[0][1]
        self.assertEqual(result[0][0].chunks_written, len(chunks))
        self.assertEqual(result[0][0].total_bytes_written, copy_len)

        # read each file and verify the result
        src_buf = self._read_big_file(fh_src, copy_len)
        dst_buf = self._read_big_file(fh_dst, copy_len, add_offset=dst_offset)
        self.assertBufferEqual(dst_buf, src_buf)

        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def generic_ssc_random_test_case_loop(self, **kwargs):
        """
        test loop for certain random parameters
        """
        src_filename = "src_copy_chunk_random.txt"
        self._gen_16mega_file(src_filename)
        iter_num = 3
        for i in range(iter_num):
            self.logger.info("iter %d, parameters flags are %s" % (i, kwargs))
            chunks = self._gen_random_chunks_on_para(**kwargs)
            if i == (iter_num - 1):
                src_options = pike.smb2.FILE_DELETE_ON_CLOSE
            else:
                src_options = 0
            self.basic_ssc_random_test_case(chunks, src_options=src_options)

    def test_random_copy_length(self):
        self.generic_ssc_random_test_case_loop(random_chunk_size=False)

    def test_random_chunk_size(self):
        self.generic_ssc_random_test_case_loop(random_chunk_size=True)

    def test_random_file_offset(self):
        self.generic_ssc_random_test_case_loop(
            random_chunk_size=False, random_offset=True
        )

    def test_random_all(self):
        self.generic_ssc_random_test_case_loop(
            random_chunk_size=True, random_offset=True
        )

    def generic_ssc_compound_test_case(self):
        """
        test copychunk request inside one compound smb message
        1st chunkcopy from src to dst file
        2nd read half of the dst file
        3rd read the other half of the dst file
        4st close the open
        """
        src_filename = "src_ssc_chunk_cp.txt"
        dst_filename = "dst_ssc_chunk_cp.txt"
        block = _gen_test_buffer(SIMPLE_5_CHUNKS_LEN)
        self._create_and_write(src_filename, block)
        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)
        ioctl_req = self.chan.copychunk_request(fh_src, fh_dst, SIMPLE_5_CHUNKS)
        nb_req = ioctl_req.parent.parent
        read_req1 = self.chan.read_request(
            pike.model.RelatedOpen(self.tree), SIMPLE_5_CHUNKS_LEN // 2, 0
        )
        nb_req.adopt(read_req1.parent)
        read_req2 = self.chan.read_request(
            pike.model.RelatedOpen(self.tree),
            SIMPLE_5_CHUNKS_LEN // 2,
            SIMPLE_5_CHUNKS_LEN // 2,
        )
        nb_req.adopt(read_req2.parent)
        close_req = self.chan.close_request(pike.model.RelatedOpen(self.tree))
        nb_req.adopt(close_req.parent)

        (ssc_res, read1_res, read2_res, close_res) = self.chan.connection.transceive(
            nb_req
        )

        self.assertEqual(ssc_res[0][0].chunks_written, len(SIMPLE_5_CHUNKS))
        self.assertEqual(ssc_res[0][0].total_bytes_written, SIMPLE_5_CHUNKS_LEN)
        dst_buf = read1_res[0].data.tobytes() + read2_res[0].data.tobytes()
        self.assertBufferEqual(dst_buf, block)
        self.chan.close(fh_src)

    def test_ssc_in_compound_req(self):
        self.generic_ssc_compound_test_case()

    def generic_mchan_ssc_test_case(self):
        """
        Interaction with multiple channel feature:
        reqeust resume key in one channel
        copy chunk in another channel with the resume key
        """
        src_filename = "src_copy_chunk_mc.txt"
        dst_filename = "dst_copy_chunk_mc.txt"
        block = _gen_test_buffer(SIMPLE_5_CHUNKS_LEN)
        self._create_and_write(src_filename, block)
        chan2 = (
            self.chan.connection.client.connect(self.server)
            .negotiate()
            .session_setup(self.creds, bind=self.chan.session)
        )

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)
        resume_key = self.chan.resume_key(fh_src)[0][0].resume_key
        result = chan2.copychunk(fh_src, fh_dst, SIMPLE_5_CHUNKS, resume_key)

        self.assertEqual(result[0][0].chunks_written, len(SIMPLE_5_CHUNKS))
        self.assertEqual(result[0][0].total_bytes_written, SIMPLE_5_CHUNKS_LEN)

        # read each file and verify the result
        src_buf = self.chan.read(fh_src, SIMPLE_5_CHUNKS_LEN, 0).tobytes()
        self.assertBufferEqual(src_buf, block)
        dst_buf = chan2.read(fh_dst, SIMPLE_5_CHUNKS_LEN, 0).tobytes()
        self.assertBufferEqual(dst_buf, block)
        self.chan.close(fh_src)
        self.chan.close(fh_dst)
        chan2.connection.close()

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    @pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_MULTI_CHANNEL)
    def test_ssc_in_multchannel(self):
        self.generic_mchan_ssc_test_case()

    def generic_multiple_ssc_test_case(
        self, filepair, chunks, blocks, write_thru=False, num_iter=1
    ):
        """
        server side copy in multiple sessions, multiple iterations
        with filepair, chunks, blocks, write_through flag as input
        parameters
        """
        num_sess = len(filepair)
        results = [None] * num_sess * num_iter
        ssc_futures = [None] * num_sess * num_iter

        self._prepare_before_ssc_copy(filepair, write_thru=write_thru)

        # for loop to submit requests in short time
        for it in range(num_iter):
            for i in range(num_sess):
                chunk_break = list(zip(*chunks))
                dst_list = [x + filepair[i][2] for x in chunk_break[1]]
                newchunks = list(zip(chunk_break[0], dst_list, chunk_break[2]))
                ssc_futures[
                    it * num_sess + i
                ] = self._submit_ssc_async_request_in_other_channels(i, newchunks)

        # collect asychronized results
        for i in range(num_sess * num_iter):
            results[i] = ssc_futures[i][0].result()
            copy_len = chunks[-1][0] + chunks[-1][2]
            self.assertEqual(results[i][0][0].chunks_written, len(chunks))
            self.assertEqual(results[i][0][0].total_bytes_written, copy_len)
            if i < num_sess:
                dst_buf = (
                    self.other_chan_list[i]["channel"]
                    .read(
                        self.other_chan_list[i]["filehandles"][1],
                        copy_len,
                        filepair[i][2],
                    )
                    .tobytes()
                )
                self.assertBufferEqual(dst_buf, blocks[i])

    def test_multiple_ssc_file(self):
        """
        server side copy with certain iterations in certain number
        of sessions
        """
        num_sess = 5
        num_iter = 3
        # file pair element {src_filename, dst_filename, dst_offset}
        filepair = []
        blocks = []
        for i in range(0, num_sess):
            src_filename = "src_multiple_session" + str(i) + ".txt"
            dst_filename = "dst_multiple_session" + str(i) + ".txt"
            filepair.append((src_filename, dst_filename, 0))
            block = _gen_random_test_buffer(SIMPLE_5_CHUNKS_LEN)
            self._create_and_write(src_filename, block)
            blocks.append(block)
        self.logger.info(
            "start multiple session test, session number is %d iteration number is %d"
            % (num_sess, num_iter)
        )
        self.generic_multiple_ssc_test_case(
            filepair, SIMPLE_5_CHUNKS, blocks, num_iter=num_iter
        )

    def test_multiple_ssc_same_source_file(self):
        """
        multiple server side copy operation which shares the same
        source file
        """
        num_sess = 5
        num_iter = 3
        # file pair element {src_filename, dst_filename, dst_offset}
        filepair = []
        blocks = []
        for i in range(0, num_sess):
            src_filename = "src_multiple_session_same_source.txt"
            dst_filename = "dst_multiple_session" + str(i) + ".txt"
            filepair.append((src_filename, dst_filename, 0))
            if i == 0:
                block = _gen_random_test_buffer(SIMPLE_5_CHUNKS_LEN)
                self._create_and_write(src_filename, block)
        blocks = [block] * num_sess
        self.logger.info(
            "ssc same source multiple session test, session number is %d iteration number is %d"
            % (num_sess, num_iter)
        )
        self.generic_multiple_ssc_test_case(
            filepair, SIMPLE_5_CHUNKS, blocks, num_iter=num_iter
        )

    def test_multiple_ssc_same_dest_file(self):
        """
        multiple server side copy operation which shares the same
        destination file but with different destination offset
        """
        num_sess = 5
        num_iter = 3
        # file pair element {src_filename, dst_filename, dst_offset}
        filepair = []
        blocks = []
        for i in range(0, num_sess):
            src_filename = "src_multiple_session" + str(i) + ".txt"
            dst_filename = "dst_multiple_session_same_dest.txt"
            filepair.append((src_filename, dst_filename, 0 + i * SIMPLE_5_CHUNKS_LEN))
            block = _gen_random_test_buffer(SIMPLE_5_CHUNKS_LEN)
            self._create_and_write(src_filename, block)
            blocks.append(block)
        self.logger.info(
            "ssc same dest multiple session test, session number is %d iteration number is %d"
            % (num_sess, num_iter)
        )
        self.generic_multiple_ssc_test_case(
            filepair, SIMPLE_5_CHUNKS, blocks, num_iter=num_iter
        )

    def test_multiple_ssc_file_with_writethrough_flag(self):
        """
        multiple server side copy operation which write_through
        flag set when creating the destination file handle
        """
        num_sess = 3
        num_iter = 1
        # file pair element {src_filename, dst_filename, dst_offset}
        filepair = []
        blocks = []
        for i in range(0, num_sess):
            src_filename = "src_multiple_session" + str(i) + ".txt"
            dst_filename = "dst_multiple_session" + str(i) + ".txt"
            filepair.append((src_filename, dst_filename, 0))
            block = _gen_random_test_buffer(SIMPLE_5_CHUNKS_LEN)
            self._create_and_write(src_filename, block)
            blocks.append(block)
        self.logger.info(
            "ssc test with write_through set, session number is %d iteration number is %d"
            % (num_sess, num_iter)
        )
        self.generic_multiple_ssc_test_case(
            filepair, SIMPLE_5_CHUNKS, blocks, write_thru=True, num_iter=num_iter
        )

    def generic_ssc_boundary_test_case(
        self, block, chunks, exp_error=None, ssc_res=[0, 0, 0]
    ):
        """
        check situation that one of the chunks which contain numbers cross the value
        of end of file or maximum values system can support
        """
        src_filename = "src_copy_chunk_cross_offset.txt"
        dst_filename = "dst_copy_chunk_cross_offset.txt"
        self._create_and_write(src_filename, block)

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)
        resume_key = self.chan.resume_key(fh_src)[0][0].resume_key
        future = self._submit_ssc_async_request(self.chan, fh_dst, resume_key, chunks)

        if exp_error is None:
            exp_error = pike.ntstatus.STATUS_SUCCESS
        try:
            with self.assert_error(exp_error):
                result = future[0].result()
        finally:
            self.chan.close(fh_src)
            self.chan.close(fh_dst)

        ioctl_resp = future[0].response.response.children[0]
        self.assertIsInstance(ioctl_resp.ioctl_output, pike.smb2.CopyChunkCopyResponse)
        chunks_written = ioctl_resp.children[0].chunks_written
        chunk_bytes_written = ioctl_resp.children[0].chunk_bytes_written
        total_bytes_written = ioctl_resp.children[0].total_bytes_written
        self.assertEqual(chunks_written, ssc_res[0])
        self.assertEqual(chunk_bytes_written, ssc_res[1])
        self.assertEqual(total_bytes_written, ssc_res[2])

    def test_neg_cross_offset_basic(self):
        block = _gen_test_buffer(4096)
        chunks = [(10, 0, 4096)]
        self.generic_ssc_boundary_test_case(
            block, chunks, exp_error=pike.ntstatus.STATUS_INVALID_VIEW_SIZE
        )

    def test_neg_cross_offset_second_chunk(self):
        block = _gen_test_buffer(8192)
        chunks = [(0, 0, 4096), (4097, 4096, 4096)]
        exp_res = [1, 0, 4096]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_VIEW_SIZE,
            ssc_res=exp_res,
        )

    def test_neg_cross_offset_fifth_chunk(self):
        block = _gen_test_buffer(20480)
        chunks = [
            (0, 0, 4096),
            (4096, 4096, 4096),
            (8192, 8192, 4096),
            (12288, 12288, 4096),
            (16386, 16384, 4096),
        ]
        exp_res = [4, 0, 16384]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_VIEW_SIZE,
            ssc_res=exp_res,
        )

    def test_neg_cross_max_chunks(self):
        """
        request contains 300 chunks
        """
        block = _gen_test_buffer(30000)
        chunks = [(0, 0, 100)] * 300
        exp_res = [self.max_number_of_chunks, self.max_chunk_size, self.max_data_size]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_PARAMETER,
            ssc_res=exp_res,
        )

    def test_neg_cross_chunk_size(self):
        """
        request with chunk size in first chunk larger
        than the maximum chunk size
        """
        block = _gen_test_buffer(1048577)
        chunks = [(0, 0, 1048577)]
        exp_res = [self.max_number_of_chunks, self.max_chunk_size, self.max_data_size]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_PARAMETER,
            ssc_res=exp_res,
        )

    def test_neg_cross_second_chunk_size(self):
        """
        request with second chunk chunk size larger
        than the maximum chunk size
        """
        block = _gen_test_buffer(2097153)
        chunks = [(0, 0, 1048576), (1048576, 1048576, 1048577)]
        exp_res = [self.max_number_of_chunks, self.max_chunk_size, self.max_data_size]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_PARAMETER,
            ssc_res=exp_res,
        )

    def test_neg_cross_chunk_size_allf(self):
        """
        request with chunk size in one chunk all f
        """
        block = _gen_test_buffer(1048577)
        chunks = [(0, 0, 4294967295)]
        exp_res = [self.max_number_of_chunks, self.max_chunk_size, self.max_data_size]
        self.generic_ssc_boundary_test_case(
            block,
            chunks,
            exp_error=pike.ntstatus.STATUS_INVALID_PARAMETER,
            ssc_res=exp_res,
        )
