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
#        querydirectory.py
#
# Abstract:
#
#        Query directory tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

from contextlib import contextmanager

class QueryDirectoryTest(pike.test.PikeTest):
    # Enumerate directory at FILE_DIRECTORY_INFORMATION level.
    # Test for presence of . and .. entries
    def test_file_directory_info(self):

        chan, tree = self.tree_connect()
        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()

        names = map(lambda info: info.file_name, chan.enum_directory(root))

        self.assertIn('.', names)

        chan.close(root)

    # Querying for a specific filename twice
    # on the same handle succeeds the first time and
    # fails with STATUS_NO_MORE_FILES the second.
    def test_specific_name(self):
        chan, tree = self.tree_connect()
        name = 'hello.txt'

        hello = chan.create(tree,
                            name,
                            access=pike.smb2.GENERIC_WRITE | pike.smb2.GENERIC_READ | pike.smb2.DELETE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()

        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()

        query1 = chan.query_directory(root, file_name=name)

        with self.assert_error(pike.ntstatus.STATUS_NO_MORE_FILES):
            chan.query_directory(root, file_name=name)

        chan.close(hello)
        chan.close(root)

    def test_file_id_both_directory_information(self):

        chan, tree = self.tree_connect()
        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()

        result = chan.query_directory(root, file_information_class=pike.smb2.FILE_ID_BOTH_DIR_INFORMATION)
        names = map(lambda info: info.file_name, result)
        self.assertIn('.', names)
        self.assertIn('..', names)

        valid_file_ids = map(lambda info: info.file_id >= 0, result)
        self.assertNotIn(False, valid_file_ids)

        chan.close(root)

    def test_restart_scan(self):

        chan, tree = self.tree_connect()
        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()

        result = chan.query_directory(root)
        names = map(lambda info: info.file_name, result)
        self.assertIn('.', names)

        result = chan.query_directory(root,
                                      flags=pike.smb2.SL_RESTART_SCAN,
                                      file_name='*')
        names = map(lambda info: info.file_name, result)
        self.assertIn('.', names)

        chan.close(root)


class TreeConnectWithDialect(object):
    @contextmanager
    def tree_connect_with_dialect_and_caps(self, dialect=None, caps=0):
        self.client = pike.model.Client(capabilities=caps)
        if dialect is not None:
            self.client.dialects = [dialect]
        self.conn = self.client.connect(self.server, self.port)
        self.conn.negotiate()
        chan = self.conn.session_setup(self.creds)
        tree = chan.tree_connect(self.share)
        try:
            yield chan, tree
        finally:
            if chan.connection.connected:
                chan.logoff()
                chan.connection.close()


class QueryDirectoryTestMaxMtu(pike.test.PikeTest, TreeConnectWithDialect):
    root_dir_name = "mtu_transport_query_dir"
    filename_prefix = "A" * 200
    filename_pattern = "{0}.test.{{0:05}}".format(filename_prefix)
    payload_size = 65536
    n_entries = 0
    filenames = []
    dataset_created = False

    def create_dataset(self):
        if QueryDirectoryTestMaxMtu.dataset_created:
            return
        # 66 bytes is the struct size of FILE_DIRECTORY_INFORMATION
        self.n_entries = (self.payload_size /
                     ((len(self.filename_pattern) - 1) * 2 + 66)) + 1
        self.info("Creating {0} files to fill {1} bytes".format(
                        self.n_entries,
                        self.payload_size))

        chan, tree = self.tree_connect()
        with self.get_test_root(chan, tree) as root_handle:
            pass            # ensure the test root dir is created
        # Creates files within the root directory.
        remaining_files = self.n_entries
        while remaining_files > 0:
            batch_futures = []
            batch_size = 30
            if remaining_files < batch_size:
                batch_size = remaining_files
            for ix in xrange(batch_size):
                filename = self.filename_pattern.format(remaining_files)
                path = "{0}\\{1}".format(self.root_dir_name, filename)
                batch_futures.append((filename, chan.create(tree, path)))
                remaining_files -= 1
            for filename, fu in batch_futures:
                fh = fu.result()
                chan.close(fh)
                self.filenames.append(filename)
        chan.logoff()
        QueryDirectoryTestMaxMtu.dataset_created = True

    def setUp(self):
        self.create_dataset()

    @contextmanager
    def get_test_root(self, chan, tree):
        root_handle = chan.create(
            tree,
            self.root_dir_name,
            access=pike.smb2.GENERIC_READ,
            options=pike.smb2.FILE_DIRECTORY_FILE,
            share=pike.smb2.FILE_SHARE_READ |\
                  pike.smb2.FILE_SHARE_WRITE |\
                  pike.smb2.FILE_SHARE_DELETE).result()
        try:
            yield root_handle
        finally:
            chan.close(root_handle)

    # Enumerate directory at FILE_DIRECTORY_INFORMATION level using the maximum transfer size.
    def gen_file_directory_info_max_mtu(self, dialect=None, caps=0):
        """
        Enumerate directory at FILE_DIRECTORY_INFORMATION level using the maximum transfer size.
        """

        with self.tree_connect_with_dialect_and_caps(dialect, caps) as (chan, tree):
            # Retrieves the maximum transaction size to determine how big the command's payload can be (MTU).
            max_trans_size = chan.connection.negotiate_response.max_transact_size

            # Enumerates the root directory and validates that the expected files are present in it.
            with self.get_test_root(chan, tree) as root_handle:
                dir_query = chan.query_directory(
                    root_handle,
                    file_information_class=pike.smb2.FILE_DIRECTORY_INFORMATION,
                    flags=0,
                    file_index=0,
                    file_name='{0}*'.format(self.filename_prefix),
                    output_buffer_length=self.payload_size)

                transaction_size = dir_query[-1].end - dir_query[0].start
                self.info("Transaction size for query: {0}/{1}".format(
                                transaction_size, max_trans_size))
                self.info("Dir entries returned: {0}/{1}".format(
                                len(dir_query), self.n_entries))
                self.assertLessEqual(transaction_size,
                                     max_trans_size)

    def test_file_directory_info_max_mtu(self):
        self.gen_file_directory_info_max_mtu()

    def test_file_directory_info_max_mtu_2_002(self):
        self.gen_file_directory_info_max_mtu(dialect=pike.smb2.DIALECT_SMB2_002)

    def test_file_directory_info_max_mtu_large_mtu(self):
        self.gen_file_directory_info_max_mtu(caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

class WriteReadMaxMtu(pike.test.PikeTest, TreeConnectWithDialect):
    invalid_write_status = pike.ntstatus.STATUS_INVALID_PARAMETER
    invalid_read_status = pike.ntstatus.STATUS_INVALID_PARAMETER
    invalid_read_status = pike.ntstatus.STATUS_INVALID_NETWORK_RESPONSE     # onefs only

    write_buf = None

    def setUp(self):
        if WriteReadMaxMtu.write_buf is None:
            with self.tree_connect_with_dialect_and_caps() as (chan, tree):
                max_sz = max(chan.connection.negotiate_response.max_read_size,
                             chan.connection.negotiate_response.max_write_size)
                WriteReadMaxMtu.write_buf = "%" * max_sz

    def pump_credits(self, chan, fh, size):
        """
        do small write operations on the file, but request enough credits to
        satisfy a write of `size`
        """
        n_credits = size / 65536 + (1 if size % 65536 > 0 else 0)
        if chan.connection.credits >= n_credits:
            return

        self.info("pumping credits from {0} to {1}".format(
                        chan.connection.credits,
                        n_credits))
        while chan.connection.credits < n_credits:
            with chan.let(credit_request=n_credits):
                chan.write(fh, 0, "A")

    def gen_writeread_max_mtu(self, dialect=None, caps=0):
        """
        Send the largest write and read the server will accept
        """

        filename = "gen_writeread_max_mtu"

        with self.tree_connect_with_dialect_and_caps(dialect, caps) as (chan, tree):
            max_read_size = chan.connection.negotiate_response.max_read_size
            max_write_size = chan.connection.negotiate_response.max_write_size
            self.info("Write {0} / Read {1}".format(
                            max_write_size,
                            max_read_size))
            fh = chan.create(
                        tree,
                        filename,
                        access=pike.smb2.GENERIC_ALL | pike.smb2.DELETE,
                        options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
            self.pump_credits(chan, fh, max_write_size)
            write_resp = chan.write(fh, 0, self.write_buf[:max_write_size])
            self.pump_credits(chan, fh, max_read_size)
            read_resp = chan.read(fh, max_read_size, 0)
            self.assertBufferEqual(read_resp.tostring(), self.write_buf[:max_read_size])

    def gen_writeread_over(self, writeover=0, readover=0, dialect=None, caps=0):
        """
        Send more than the largest write and read the server will accept
        """

        filename = "gen_writeread_over"

        with self.tree_connect_with_dialect_and_caps(dialect, caps) as (chan, tree):
            fh = chan.create(
                        tree,
                        filename,
                        access=pike.smb2.GENERIC_ALL | pike.smb2.DELETE,
                        options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
            if writeover:
                max_write_size = chan.connection.negotiate_response.max_write_size
                write_size = max_write_size + writeover
                over_buf = "%" * writeover
                self.info("Write {0} (over {1})".format(write_size, writeover))
                self.pump_credits(chan, fh, write_size)
                write_resp = chan.write(fh, 0, self.write_buf + over_buf)
            if readover:
                max_read_size = chan.connection.negotiate_response.max_read_size
                read_size = max_read_size + readover
                self.info("Read {0} (over {1})".format(read_size, readover))
                self.pump_credits(chan, fh, read_size)
                read_resp = chan.read(fh, read_size, 0)

    def test_wr_2_002(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB2_002)

    def test_wr_2_002_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_002)

    def test_wr_2_002_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_002)

    def test_wr_2_1(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB2_1)

    def test_wr_2_1_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_1)

    def test_wr_2_1_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_1)

    def test_wr_3_0(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_0)

    def test_wr_3_0_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0)

    def test_wr_3_0_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0)

    def test_wr_3_0_2(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_0_2)

    def test_wr_3_0_2_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0_2)

    def test_wr_3_0_2_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0_2)

    def test_wr_3_1_1(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_1_1)

    def test_wr_3_1_1_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_1_1)

    def test_wr_3_1_1_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_1_1)

    def test_wr_large_mtu(self):
        self.gen_writeread_max_mtu(caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    def test_wr_large_mtu_writeover1(self):
        with self.assert_error(self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    def test_wr_large_mtu_readover1(self):
        with self.assert_error(self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
