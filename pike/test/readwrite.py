#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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

from builtins import map

import array
import random

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus


class ReadWriteTest(pike.test.PikeTest):
    # Test that we can write to a file
    def test_write(self):
        chan, tree = self.tree_connect()
        buffer = "testing123"

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
        ).result()

        bytes_written = chan.write(file, 0, buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.close(file)

    # Test that a 0-byte write succeeds
    def test_write_none(self):
        chan, tree = self.tree_connect()
        buffer = None

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
        ).result()

        bytes_written = chan.write(file, 0, buffer)
        self.assertEqual(bytes_written, 0)

        chan.close(file)

    # Test that a 0-byte write succeeds
    def test_write_none(self):
        chan, tree = self.tree_connect()
        buffer = None

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
        ).result()

        bytes_written = chan.write(file, 0, buffer)
        self.assertEqual(bytes_written, 0)

        chan.close(file)

    # Test that a 0-byte write triggers access checks
    # (and fails since we do not have write access)
    def test_write_none_access(self):
        chan, tree = self.tree_connect()

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
        ).result()

        with pike.model.pike_status(pike.ntstatus.STATUS_ACCESS_DENIED):
            chan.write(file, 0, None)

        chan.close(file)

    # Test that 0-byte write does not cause an oplock break
    def test_write_none_oplock(self):
        chan, tree = self.tree_connect()

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE,
        ).result()

        file2 = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II,
        ).result()
        self.assertEqual(file2.oplock_level, pike.smb2.SMB2_OPLOCK_LEVEL_II)

        bytes_written = chan.write(file, 0, None)
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
        lease1 = array.array("B", map(random.randint, [0] * 16, [255] * 16))

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        file = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE,
        ).result()

        file2 = chan.create(
            tree,
            "write.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=share_all,
            disposition=pike.smb2.FILE_SUPERSEDE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=lease1,
            lease_state=pike.smb2.SMB2_LEASE_READ_CACHING,
        ).result()

        bytes_written = chan.write(file, 64, None)
        self.assertEqual(bytes_written, 0)

        # We should not receive a lease break
        with self.assertRaises(pike.model.TimeoutError):
            file2.lease.future.wait(timeout=0.1)

        chan.close(file)
        chan.close(file2)
