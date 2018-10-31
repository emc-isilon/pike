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
access_wd =  pike.smb2.FILE_WRITE_DATA | \
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

    def _chunkcopy_with_resume_key(self, chan, chunks, dst_file, resume_key):
        smb_req = chan.request(obj=dst_file.tree)
        ioctl_req = pike.smb2.IoctlRequest(smb_req)
        copychunk_req = pike.smb2.CopyChunkCopyRequest(ioctl_req)

        ioctl_req.max_output_response = 16384
        ioctl_req.file_id = dst_file.file_id
        ioctl_req.flags |= pike.smb2.IoctlFlags.SMB2_0_IOCTL_IS_FSCTL
        copychunk_req.source_key = resume_key
        copychunk_req.chunk_count = len(chunks)

        for source_offset, target_offset, length in chunks:
            chunk = pike.smb2.CopyChunk(copychunk_req)
            chunk.source_offset = source_offset
            chunk.target_offset = target_offset
            chunk.length = length
        result = chan.connection.transceive(ioctl_req.parent.parent)[0]
        return result     

    def _convert_fileid_to_resume_key(self, file_handle):
        import struct
        import array
        manual_key = array.array('B')
        file_id = file_handle.file_id
        tmp_first_pack = struct.pack('<Q',file_id[0])
        tmp_second_pack = struct.pack('<Q',file_id[1])
        tmp_first_list = list(struct.unpack('BBBBBBBB', tmp_first_pack))
        tmp_second_list = list(struct.unpack('BBBBBBBB', tmp_second_pack))
        padding = [0, 0, 0, 0, 0, 0, 0, 0]
        manual_key.fromlist(tmp_first_list)
        manual_key.fromlist(tmp_second_list)
        manual_key.fromlist(padding)
        return manual_key

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

    def generic_ssc_negative_test_case(self, src_access=None, dst_access=None,
                                             src_disp=None, dst_disp=None,
                                             src_options=None, dst_options=None,
                                             src_brl=None, dst_brl=None,
                                       exp_error=None):
        block = "Hello"
        total_len = len(block)
        src_filename = "src_negative.txt"
        dst_filename = "dst_negative.txt"
        self._create_and_write(src_filename, block)

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename,
                                            src_access=src_access,
                                            src_disp=src_disp,
                                            src_options=src_options,
                                            dst_access=dst_access,
                                            dst_disp=dst_disp,
                                            dst_options=dst_options)
        close_handles = []
        if src_brl or dst_brl:
            chan2, tree2 = self.tree_connect()
            if src_brl:
                fh_src_other = chan2.create(tree2,
                                            src_filename,
                                            access=access_rwd,
                                            share=share_all).result()
                chan2.lock(fh_src_other,
                           [( 0, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK )]).result()
                close_handles.append((chan2, fh_src_other))
            if dst_brl:
                fh_dst_other = chan2.create(tree2,
                                            dst_filename,
                                            access=access_rwd,
                                            share=share_all).result()
                chan2.lock(fh_dst_other,
                           [( 3, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK )]).result()
                close_handles.append((chan2, fh_dst_other))
        if exp_error is None:
            exp_error = pike.ntstatus.STATUS_SUCCESS
        try:
            with self.assert_error(exp_error):
                result = self.chan.copychunk(fh_src, fh_dst, [(0,0,5)])
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
        self.generic_ssc_negative_test_case(src_brl=True,
                                            exp_error=pike.ntstatus.STATUS_FILE_LOCK_CONFLICT)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_neg_dst_exc_brl(self):
        """
        Initiate copychunk when another handle has an exclusive BRL on the
        destination file (win 8 / 2012)
        """
        self.generic_ssc_negative_test_case(dst_brl=True,
                                            exp_error=pike.ntstatus.STATUS_FILE_LOCK_CONFLICT)

    def test_neg_src_no_read(self):
        """
        Try to copychunk with no read access on the source file
        """
        self.generic_ssc_negative_test_case(src_access=pike.smb2.FILE_WRITE_DATA | \
                                                       pike.smb2.DELETE,
                                            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED)
        
    def test_neg_dst_no_read(self):
        """
        Try to copychunk with no read access on the destination file
        """
        self.generic_ssc_negative_test_case(dst_access=pike.smb2.FILE_WRITE_DATA | \
                                                       pike.smb2.DELETE,
                                            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED)

    def test_neg_dst_no_write(self):
        """
        Try to copychunk with no write access on the destination file
        """
        self.generic_ssc_negative_test_case(dst_access=pike.smb2.FILE_READ_DATA | \
                                                       pike.smb2.DELETE,
                                            exp_error=pike.ntstatus.STATUS_ACCESS_DENIED)

    def test_neg_dst_is_a_dir(self):
        """
        Try to copychunk with destination file being a directory
        """
        self.generic_ssc_negative_test_case(dst_options=pike.smb2.FILE_DIRECTORY_FILE | \
                                                        pike.smb2.FILE_DELETE_ON_CLOSE,
                                            dst_disp=pike.smb2.FILE_OPEN_IF,
                                            exp_error=pike.ntstatus.STATUS_INVALID_DEVICE_REQUEST)

    def generic_resume_key_test_case(self, req_num = 1, neg = False,\
                                     neg_type = None, exp_error=None,
                                     same_sess=False):
        """
        Resume key specific test including basic, multiple reqeusts, negative test
        """
        src_filename = "src_copy_chunk_rk.txt"
        dst_filename = "dst_copy_chunk_rk.txt"
        block = _gen_test_buffer(20000)
        self._create_and_write(src_filename, block)


        chunks = [(0, 0, 4000), (4000, 4000, 4000),\
          (8000, 8000, 4000), (12000, 12000, 4000), \
          (16000, 16000, 4000)]

        if neg_type == "src_no_read":
            src_access = access_wd
        else:
            src_access = None

        fh_src, fh_dst = self._open_src_dst(src_filename, dst_filename,\
                                            src_access = src_access)
        close_handles = []
        resume_key_list = []

        # multiple resume_key requests cases
        if req_num > 1:
            # same session to issue multiple resume_key requets
            if same_sess == False:
                for i in range(2, (req_num+1)):
                    chan2, tree2 = self.tree_connect()
                    fh_src_2 = chan2.create(tree2,
                                    src_filename,
                                    access=access_rwd,
                                    share=share_all).result()
                    fh_dst_2 = chan2.create(tree2,
                                    dst_filename,
                                    access=access_rwd,
                                    share=share_all).result()
                    resume_key_other = chan2.resume_key(fh_src_2)[0][0].resume_key
                    close_handles.append((chan2, tree2, fh_src_2, fh_dst_2))
                    result = self._chunkcopy_with_resume_key(chan2, chunks,\
                                                             fh_dst_2, resume_key_other)
                    self.assertEqual(result[0][0].chunks_written, 5)
                    self.assertEqual(result[0][0].total_bytes_written, 20000)
            # multiple sessions to issue multiple resume_key requests
            else:
                for i in range(2, (req_num+1)):
                    fh_src_2, fh_dst_2 = self._open_src_dst(src_filename,\
                                                            dst_filename,\
                                                            src_options = 0,\
                                                            dst_options = 0)
                    resume_key_other = self.chan.resume_key(fh_src_2)[0][0].resume_key
                    resume_key_list.append(resume_key_other)
                    result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                             fh_dst_2, resume_key_other)
                    self.assertEqual(result[0][0].chunks_written, 5)
                    self.assertEqual(result[0][0].total_bytes_written, 20000)
                    self.chan.close(fh_src_2)
                    self.chan.close(fh_dst_2)
         


        if neg == False:
            resume_key = self.chan.resume_key(fh_src)[0][0].resume_key
            result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                     fh_dst, resume_key)
            self.assertEqual(result[0][0].chunks_written, 5)
            self.assertEqual(result[0][0].total_bytes_written, 20000)

            # read each file and verify the result
            src_buf = self.chan.read(fh_src, 20000, 0).tostring()
            self.assertBufferEqual(src_buf, block)
            dst_buf = self.chan.read(fh_dst, 20000, 0).tostring()
            self.assertBufferEqual(dst_buf, block)
        else:
            try:
                with self.assert_error(exp_error):
                    if neg_type == "other_key":
                        try:
                            assert req_num > 1
                        except AssertionError:
                            raise Exception("in case of test_other_resume_key "
                                           "we need req_num at least two")

                        result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                                 fh_dst, resume_key_other)
                    if neg_type == "manual_key":
                        manual_key = self._convert_fileid_to_resume_key(fh_src)
                        result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                                 fh_dst, manual_key)
                    if neg_type == "bogus_key":
                        import array
                        bogus_key = array.array('B', [255]*24)
                        result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                                 fh_dst, bogus_key)
                    if neg_type == "src_no_read":
                        resume_key = self.chan.resume_key(fh_src)[0][0].resume_key
                        result = self._chunkcopy_with_resume_key(self.chan, chunks,\
                                                                 fh_dst, resume_key)
                    if neg_type == "ssc_disable":
                        resume_key = self.chan.resume_key(fh_src)[0][0].resume_key
            finally:
                pass

        for chan_other, tree, fh_src_2, fh_dst_2 in close_handles:
            chan_other.close(fh_src_2)
            chan_other.close(fh_dst_2)
            chan_other.tree_disconnect(tree)
            chan_other.logoff()

        self.chan.close(fh_src)
        self.chan.close(fh_dst)



    def test_resume_key_by_copychunk(self):
        """
        a typical ssc test first request for a resume key
        then use the resume key for chunk copy
        """
        self.generic_resume_key_test_case()

    def test_multiple_resume_key_diff_sessions(self):
        """
        test multple sessions each acquiring a resume_key
        of same file to perform the server side copy
        """
        self.generic_resume_key_test_case(req_num=2)

    def test_multiple_resume_key_same_sessions(self):
        """
        test in same session, for multiple opens of same file 
        each acquiring a resume_key to perform the server side copy
        """
        self.generic_resume_key_test_case(req_num=5, same_sess=True)

    def test_other_resume_key(self):
        """
        negative test for multiple sessions acquiring resume key
        for same file one session uses other session's resume key
        to perform the server side copy
        """
        self.generic_resume_key_test_case(req_num=2, neg=True,\
                                          neg_type="other_key",\
                                          exp_error=pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND)

    def test_manual_resume_key(self):
        """
        negative test for single session does not acquire resume_key
        but self-generate one resume_key by file_id to perform the 
        server side copy
        """
        self.generic_resume_key_test_case(req_num=1, neg=True,\
                                          neg_type="manual_key",\
                                          exp_error=pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND)

    def test_bogus_resume_key(self):
        """
        negative test for single session does not acquire resume_key
        but generate one bogus resume_key to perform the server side copy
        """
        self.generic_resume_key_test_case(req_num=1, neg=True,\
                                          neg_type="bogus_key",\
                                          exp_error=pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND)

    def test_src_no_read_resume_key(self):
        """
        negative test for single session the source file handle does not
        apply for read permission then send the resume_key request for it
        """
        self.generic_resume_key_test_case(req_num=1, neg=True,\
                                          neg_type="src_no_read",\
                                          exp_error=pike.ntstatus.STATUS_ACCESS_DENIED)

    def test_ssc_disable_resume_key(self):
        """
        negative test for globally disabled ssc then
        perform the resume key  ioctl reqeust
        """
        self.generic_resume_key_test_case(req_num=1, neg=True,\
                                          neg_type="ssc_disable",\
                                          exp_error=pike.ntstatus.STATUS_INVALID_DEVICE_REQUEST)