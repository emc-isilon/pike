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
#        readwrite.py
#
# Abstract:
#
#        Read and write tests
#
# Authors: Arlene Berry (arlene.berry@emc.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus
import array
import errno
import random
import socket


class ReadWriteTest(pike.test.PikeTest):
    # Test that we can write to a file
    def test_write(self):
        chan, tree = self.tree_connect()
        buffer = "testing123"

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                           'write.txt',
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=share_all,
                           disposition=pike.smb2.FILE_SUPERSEDE,
                           options=pike.smb2.FILE_DELETE_ON_CLOSE,
                           oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()

        bytes_written = chan.write(file,
                                   0,
                                   buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.close(file)

    # Test that a 0-byte write succeeds
    def test_write_none(self):
        chan, tree = self.tree_connect()
        buffer = None

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                           'write.txt',
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=share_all,
                           disposition=pike.smb2.FILE_SUPERSEDE,
                           options=pike.smb2.FILE_DELETE_ON_CLOSE,
                           oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()

        bytes_written = chan.write(file,
                                   0,
                                   buffer)
        self.assertEqual(bytes_written, 0)

        chan.close(file)

    # Test that a 0-byte write triggers access checks
    # (and fails since we do not have write access)
    def test_write_none_access(self):
        chan, tree = self.tree_connect()

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                           'write.txt',
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.DELETE,
                           share=share_all,
                           disposition=pike.smb2.FILE_SUPERSEDE,
                           oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()

        with self.assert_error(pike.ntstatus.STATUS_ACCESS_DENIED):
            chan.write(file, 0, None)

        chan.close(file)

    # Test that 0-byte write does not cause an oplock break
    def test_write_none_oplock(self):
        chan, tree = self.tree_connect()

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                           'write.txt',
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=share_all,
                           disposition=pike.smb2.FILE_SUPERSEDE,
                           options=pike.smb2.FILE_DELETE_ON_CLOSE,
                           oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()

        file2 = chan.create(tree,
                            'write.txt',
                            access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
        self.assertEqual(file2.oplock_level, pike.smb2.SMB2_OPLOCK_LEVEL_II)

        bytes_written = chan.write(file,
                                   0,
                                   None)
        self.assertEqual(bytes_written, 0)

        # We should not receive an oplock break
        with self.assertRaises(pike.model.TimeoutError):
            file2.oplock_future.wait(timeout=0.1)

        chan.close(file)
        chan.close(file2)

    # Test that 0-byte write does not cause a lease break
    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    @pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
    def test_write_none_lease(self):
        chan, tree = self.tree_connect()
        lease1 = array.array('B',map(random.randint, [0]*16, [255]*16))

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                           'write.txt',
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=share_all,
                           disposition=pike.smb2.FILE_SUPERSEDE,
                           oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()

        file2 = chan.create(tree,
                            'write.txt',
                            access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            lease_key=lease1,
                            lease_state=pike.smb2.SMB2_LEASE_READ_CACHING).result()

        bytes_written = chan.write(file, 64, None)
        self.assertEqual(bytes_written, 0)

        # We should not receive a lease break
        with self.assertRaises(pike.model.TimeoutError):
            file2.lease.future.wait(timeout=0.1)

        chan.close(file)
        chan.close(file2)


class WriteReadMaxMtu(pike.test.PikeTest,
                      pike.test.TreeConnectWithDialect):
    invalid_write_status = [
            pike.ntstatus.STATUS_INVALID_PARAMETER,     # windows 2012+
            pike.ntstatus.STATUS_BUFFER_OVERFLOW]       # windows 2008r2 / 7
    invalid_read_status = [
            pike.ntstatus.STATUS_INVALID_PARAMETER,     # windows 2012+
            pike.ntstatus.STATUS_BUFFER_OVERFLOW,       # windows 2008r2 / 7
            pike.ntstatus.STATUS_INVALID_NETWORK_RESPONSE]      # onefs

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
        write_resp = read_resp = None

        with self.tree_connect_with_dialect_and_caps(dialect, caps) as (chan,
                                                                        tree):
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
            self.assertBufferEqual(read_resp.tostring(),
                                   self.write_buf[:max_read_size])
        return write_resp, read_resp

    def gen_writeread_over(self, writeover=0, readover=0, dialect=None, caps=0):
        """
        Send more than the largest write and read the server will accept
        """

        filename = "gen_writeread_over"
        write_resp = read_resp = None

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
        return write_resp, read_resp

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_002)
    def test_wr_2_002(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB2_002)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_002)
    def test_wr_2_002_writeover1(self):
        try:
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_002)
            self.fail("Writing more than max_write_size didn't raise error")
        # special handling is needed here since windows resets the connection
        # instead of checking the size and returning an error
        except pike.model.ResponseError as err:
            if err.response.status not in self.invalid_write_status:
                raise
        except socket.error as err:
            if err.errno != errno.ECONNRESET:
                raise

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_002)
    def test_wr_2_002_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_002)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_wr_2_1(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB2_1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_wr_2_1_writeover1(self):
        with self.assert_error(*self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB2_1)
    def test_wr_2_1_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB2_1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_wr_3_0(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_0)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_wr_3_0_writeover1(self):
        with self.assert_error(*self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
    def test_wr_3_0_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_0_2(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_0_2)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_0_2_writeover1(self):
        with self.assert_error(*self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0_2)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_0_2_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_0_2)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_1_1(self):
        self.gen_writeread_max_mtu(dialect=pike.smb2.DIALECT_SMB3_1_1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_1_1_writeover1(self):
        with self.assert_error(*self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_1_1)

    @pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0_2)
    def test_wr_3_1_1_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    dialect=pike.smb2.DIALECT_SMB3_1_1)

    @pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
    def test_wr_large_mtu(self):
        self.gen_writeread_max_mtu(caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    @pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
    def test_wr_large_mtu_writeover1(self):
        with self.assert_error(*self.invalid_write_status):
            self.gen_writeread_over(writeover=1,
                                    caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)

    @pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
    def test_wr_large_mtu_readover1(self):
        with self.assert_error(*self.invalid_read_status):
            self.gen_writeread_over(readover=1,
                                    caps=pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
