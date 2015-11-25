#
# Copyright (c) 2015, EMC Corporation
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
#        copychunk.py
#
# Abstract:
#
#        Tests for server side copy
#
# Authors: Avi Bhandari (avi.bahndari@emc.com)
#          Masen Furer (masen.furer@emc.com)
#

import pike.ntstatus
import pike.smb2
import pike.test

share_all = pike.smb2.FILE_SHARE_READ | \
            pike.smb2.FILE_SHARE_WRITE | \
            pike.smb2.FILE_SHARE_DELETE
access_rwd = pike.smb2.FILE_READ_DATA | \
             pike.smb2.FILE_WRITE_DATA | \
             pike.smb2.DELETE

# Max values

SERVER_SIDE_COPY_MAX_NUMBER_OF_CHUNKS = 16
SERVER_SIDE_COPY_MAX_CHUNK_SIZE = 1048576
SERVER_SIDE_COPY_MAX_DATA_SIZE = 16777216

def _gen_test_buffer(length):
    pattern = "".join([ chr(x) for x in xrange(ord(' '), ord('~'))])
    buf = (pattern * (length / (len(pattern)) + 1))[:length]
    return buf

###
# Main test
###
class TestServerSideCopy(pike.test.PikeTest):

    def setUp(self):
        self.chan, self.tree = self.tree_connect()

    def tearDown(self):
        self.chan.tree_disconnect(self.tree)
        self.chan.logoff()

    def _create_and_write(self, filename, content):
        """ create / overwrite filename with content """
        fh1 = self.chan.create(self.tree,
                               filename,
                               access=access_rwd,
                               share=share_all,
                               disposition=pike.smb2.FILE_SUPERSEDE).result()

        bytes_written = self.chan.write(fh1, 0, content)
        self.chan.close(fh1)

    def _open_src_dst(self, src_filename, dst_filename,
                      src_access=None,
                      src_disp=None,
                      src_options=None,
                      dst_access=None,
                      dst_disp=None,
                      dst_options=None):
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
            src_options = 0     # if we're opening the same file, only delete one
        fh_src = self.chan.create(self.tree,
                                  src_filename,
                                  access=src_access,
                                  share=share_all,
                                  disposition=src_disp,
                                  options=src_options).result()

        fh_dst = self.chan.create(self.tree,
                                  dst_filename,
                                  access=dst_access,
                                  share=share_all,
                                  disposition=dst_disp,
                                  options=dst_options).result()
        return (fh_src, fh_dst)

    def generic_ssc_test_case(self, block, number_of_chunks, total_offset=0):
        """
        copy block in number_of_chunks, offset the destination copy by total_offset
        """
        src_filename = "src_copy_chunk_offset.txt"
        dst_filename = "dst_copy_chunk_offset.txt"
        self._create_and_write(src_filename, block)

        total_len = len(block)
        chunk_sz = (total_len / number_of_chunks) + 1
        this_offset = 0

        chunks = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, offset+total_offset, length))
            this_offset += chunk_sz

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read each file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tostring()
        self.assertBufferEqual(src_buf, block)
        dst_buf = self.chan.read(fh_dst, total_len, total_offset).tostring()
        self.assertBufferEqual(dst_buf, block)

        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def test_copy_small_file(self):
        block = "Hello"
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
        block = "Hello"
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

    def generic_ssc_same_file_test_case(self, block, number_of_chunks, total_offset=0):
        """
        duplicate block in number_of_chunks to the same file,
        the copy will be total_offset from the current end of file
        """
        filename = "src_copy_chunk_same.txt"
        self._create_and_write(filename, block)

        total_len = len(block)
        chunk_sz = (total_len / number_of_chunks) + 1
        this_offset = 0

        chunks = []
        while this_offset < total_len:
            offset = this_offset
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, offset+total_len+total_offset, length))
            this_offset += chunk_sz

        fh_src, fh_dst = self._open_src_dst(filename, filename,
                                            dst_disp=pike.smb2.FILE_OPEN_IF)

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read the file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tostring()
        self.assertBufferEqual(src_buf, block)
        if total_offset > 0:
            offs_buf = self.chan.read(fh_src, total_offset, total_len).tostring()
            self.assertBufferEqual(offs_buf, "\x00"*total_offset)
        dst_buf = self.chan.read(fh_src, total_len, total_len+total_offset).tostring()
        self.assertBufferEqual(dst_buf, block)

        self.chan.close(fh_src)
        self.chan.close(fh_dst)

    def test_same_small_file(self):
        block = "Hello"
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
        block = "Hello"
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

    def generic_ssc_overlap_test_case(self, block, number_of_chunks, overlap_each_block=0):
        """
        copy block in number_of_chunks, each destination block offset will be overlapped
        over the previous block by overlap_each_block bytes
        """
        src_filename = "src_copy_chunk_overlap.txt"
        dst_filename = "dst_copy_chunk_overlap.txt"
        self._create_and_write(src_filename, block)

        total_len = len(block)
        chunk_sz = (total_len / number_of_chunks) + 1
        this_offset = 0

        chunks = []
        src_block = list(block)
        dst_block = list(block)
        while this_offset < total_len:
            offset = dst_offset = this_offset
            if offset - overlap_each_block > 0:
                dst_offset = offset - overlap_each_block
            if this_offset + chunk_sz < total_len:
                length = chunk_sz
            else:
                length = total_len - this_offset
            chunks.append((offset, dst_offset, length))
            dst_block[dst_offset:dst_offset+length] = \
                    src_block[offset:offset+length]
            this_offset += chunk_sz
        dst_len = dst_offset+length
        dst_block = "".join(dst_block[:dst_len])

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename)

        result = self.chan.copychunk(fh_src, fh_dst, chunks)
        self.assertEqual(result[0][0].chunks_written, number_of_chunks)
        self.assertEqual(result[0][0].total_bytes_written, total_len)

        # read each file and verify the result
        src_buf = self.chan.read(fh_src, total_len, 0).tostring()
        self.assertBufferEqual(src_buf, block)
        dst_buf = self.chan.read(fh_dst, dst_len, 0).tostring()
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
