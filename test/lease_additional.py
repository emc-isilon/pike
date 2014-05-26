#-----------------------------------------------------------------------------
#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:       lease_additional.py
# Purpose:
#
# Abstract:
#
#        Runs SMB lease tests in a distributed fashion with the given arguments.
#        Instead of using multiple clients, multiple sessions have been created
#        on the same client.
#
# Author:      Sagar Naik, Calsoft (sagar.naik@calsoftinc.com)
#
#-----------------------------------------------------------------------------

#!/usr/bin/env python


"""
Runs SMB lease tests in a distributed fashion with the given arguments.
Instead of using multiple clients, multiple sessions have been created
on the same client.
"""

import pike.model
import pike.smb2
import pike.test
import random
import array
import time

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class AdditionalLeaseTests(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(AdditionalLeaseTests, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        self.lease1 = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.lease2 = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.lease3 = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
        self.n = pike.smb2.SMB2_LEASE_NONE
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh
        self.buffer = "testing123"
        self.lock1 = [(12, 34, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock2 = [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock3 = [(1234, 56, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock4 = [(56, 56, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock5 = [(234, 56, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock6 = [(2345, 67, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock7 = [(3456, 78, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock8 = [(4567, 89, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        self.lock9 = [(5678, 90, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]

    def test_tc01_2_opener(self):
        """
        2 clients open the same file requesting leases
        """
        print "-------------------------------------"
        print "TC01: 2 clients open the same file requesting leases."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rw).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        print "Open file handle 2 with rwh lease request"

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)

        # First lease should have broken to r
        self.assertEqual(handle1.lease.lease_state, self.r)
        print "read caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc02_3_opener(self):
        """
        3 clients open the same file requesting leases
        """
        print "-------------------------------------"
        print "TC02: 3 clients open the same file requesting leases."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        print "Open file handle 2 with rwh lease request"

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)

        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for all file handles"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"
        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc03_2_openers_write(self):
        """
        2 clients open the same file requesting
        leases and write to the file.
        """
        print "-------------------------------------"
        print "TC03: 2 clients open the same file requesting leases and write to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_test_2_openers_write.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_test_2_openers_write.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        bytes_written = chan1.write(handle2,
                                   11,
                                   self.buffer)
        chan.close(handle1)
        print "Closed first file handle"

        try:
            handle2 = chan1.create(tree1,
                              'lease_test_2_openers_write.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        except Exception as e:
            print "Create handle failed with error :", str(e)

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan.logoff()

    def test_tc04_3_openers_write(self):
        """
        3 clients open the same file requesting
        leases and write to the file.
        """
        print "-------------------------------------"
        print "TC04: 3 clients open the same file requesting leases and write to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        bytes_written = chan1.write(handle2,
                                   11,
                                   self.buffer)

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to None
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc05_2_openers_read(self):
        """
        2 clients open the same file requesting
        leases and read from the file
        """
        print "-------------------------------------"
        print "TC05: 2 clients open the same file requesting leases and read from the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc06_3_openers_read(self):
        """
        3 clients open the same file requesting
        leases and read from the file
        """
        print "-------------------------------------"
        print "TC06: 3 clients open the same file requesting leases and read from the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for all file handles"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"
        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc07_3_openers_one_writer(self):
        """
        3 clients open the same file requesting
        leases and only one writes to the file.
        """
        print "-------------------------------------"
        print "TC07: 3 clients open the same file requesting leases and only one writes to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to None
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the third client gets a read and handle
        # caching lease.

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc08_2_openers_read_write(self):
        """
        2 clients open the same file requesting
        leases, read and write data from/to the file.
        """
        print "-------------------------------------"
        print "TC08: 2 clients open the same file requesting leases, read and write data from/to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"
        # Observe that the write goes on the wire as a 4Kbytes (the
        # allocation size) block and that the lease's state remains
        # unchanged.

        # Second  handle
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan1.write(handle2,
                                   0,
                                   self.buffer)
        print "Verified write operation on second file handle"
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc09_3_openers_read_write(self):
        """
        3 clients open the same file requesting
        leases, read and write data from/to the file.
        """
        print "-------------------------------------"
        print "TC09: 3 clients open the same file requesting leases, read and write data from/to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"
        # Observe that the write goes on the wire as a 4Kbytes (the
        # allocation size) block and that the lease's state remains
        # unchanged.

        # Second  handle
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan1.write(handle2,
                                   0,
                                   self.buffer)
        print "Verified write operation on second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc10_3_openers_read_one_writer(self):
        """
        3 clients open the same file requesting
        leases, read and only one writes data from/to the file.
        """
        print "-------------------------------------"
        print "TC010: 3 clients open the same file requesting leases, read and only one writes data from/to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"
        # Observe that the write goes on the wire as a 4Kbytes (the
        # allocation size) block and that the lease's state remains
        # unchanged.

        # Second  handle
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second and third clients.

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Close the file from second client.
        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Should be granted rh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc11_2_openers_lock(self):
        """
        2 clients open the same file requesting
        leases and lock 3 different ranges on the file
        """
        print "-------------------------------------"
        print "TC011: 2 clients open the same file requesting leases and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second handle
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        chan1.lock(handle2, self.lock4).result(timeout=120)
        print "Verified Exclusive Lock operation on second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc12_2_openers_lock_contend(self):
        """
        2 clients open the same file requesting
        leases and lock 3 different ranges (contending) on the
        file.
        """
        print "-------------------------------------"
        print "TC012: 2 clients open the same file requesting leases and lock 3 different ranges (contending) on the file."
        expected_status = 'STATUS_LOCK_NOT_GRANTED'
        actual_status   = 'STATUS_SUCCESS'
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted no lease on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc13_3_openers_lock(self):
        """
        3 clients open the same file requesting
        leases and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC013: 3 clients open the same file requesting leases and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_test_3_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_test_3_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        chan1.lock(handle2, self.lock4).result(timeout=120)
        print "Verified Exclusive Lock operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_test_3_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Close the file from first and second client.
        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_test_3_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc14_3_openers_lock_contend(self):
        """
        3 clients open the same file requesting
        leases and lock 3 different ranges (contending) on the file.
        """
        print "-------------------------------------"
        print "TC014: 3 clients open the same file requesting leases and lock 3 different ranges (contending) on the file."
        expected_status = 'STATUS_LOCK_NOT_GRANTED'
        actual_status   = 'STATUS_SUCCESS'
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_test_3_openers_lock_contend.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_test_3_openers_lock_contend.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.

        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Should be granted no lease on first handle
        self.assertEqual(handle1.lease.lease_state, self.n)

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_test_3_openers_lock_contend.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rh on second lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"
        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc16_3_openers_one_locker(self):
        """
        3 clients open the same file requesting
        leases and only one locks 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC016: 3 clients open the same file requesting leases and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rh on second lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Close the file from firstclient.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second and third client.

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the second and third client gets a read and
        # handle caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc17_2_openers_read_lock(self):
        """
        2 clients open the same file requesting
        leases, read data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC017: 2 clients open the same file requesting leases, read data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Should be granted rh on first client
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc18_2_openers_read_lock_contend(self):
        """
        2 clients open the same file requesting
        leases, read data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC018: 2 clients open the same file requesting leases, read data and lock 3 different ranges (contending) on the file."
        read_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        lock_expected_status = 'STATUS_LOCK_NOT_GRANTED'
        actual_status   = 'STATUS_SUCCESS'
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from second client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Read request on Second handle"

        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(read_expected_status, actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(read_expected_status, actual_status)
        print "Verified read operation on second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(lock_expected_status, actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Should be granted n lease on first handle
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc19_3_openers_read_lock(self):
        """
        3 clients open the same file requesting
        leases, read data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC019: 3 clients open the same file requesting leases, read data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Should be granted rh on first client
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from anywhere in the file.
        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        # Close the file from first and second client.
        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc20_3_openers_read_lock_contend(self):
        """
        3 clients open the same file requesting
        leases, read data and lock 3 different ranges (contending) on the file.
        """
        print "-------------------------------------"
        print "TC020: 3 clients open the same file requesting leases, read data and lock 3 different ranges (contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        read_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        lock_expected_status = 'STATUS_LOCK_NOT_GRANTED'
        actual_status   = 'STATUS_SUCCESS'
        lock_actual_status   = 'STATUS_SUCCESS'

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Should be granted rh on first client
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from a location in the file that overlaps
        # existing locked ranges from third client. Observe that
        # the read fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Read request on Third handle"

        try:
            data2 = chan2.read(handle3, 3456, 1234)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(read_expected_status, actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        # Read data from the same location as on step above.
        try:
            data2 = chan2.read(handle3, 3456, 1234)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(read_expected_status, actual_status)
        print "Verified read operation on third file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # second client. Observe that the lock from third client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        # Read data from anywhere in the file.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on third file handle"

        # Should be granted no lease on first and second handle
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Close the file from first and second client.
        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc21_3_openers_read_one_locker(self):
        """
        3 clients open the same file requesting
        leases, read data and only one locks 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC021: 3 clients open the same file requesting leases, read data and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from anywhere in the file.
        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second and third clients.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the second and third client gets a read and
        # handle caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc22_2_openers_write_lock(self):
        """
        2 clients open the same file requesting
        leases, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC022: 2 clients open the same file requesting leases, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan1.write(handle2,
                                   0,
                                   self.buffer)
        print "Verified write operation on second file handle"

        # Should be granted n on first client
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc23_2_openers_write_lock_contend(self):
        """
        2 clients open the same file requesting
        leases, write data and lock 3 different ranges (contending) on the file.
        """
        print "-------------------------------------"
        print "TC023: 2 clients open the same file requesting leases, write data and lock 3 different ranges (contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        write_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        actual_status   = 'STATUS_SUCCESS'
        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Write a small amount (less than 1Kbyte) of data from
        # second client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Write request on Second handle"

        try:
            bytes_written = chan1.write(handle2,
                                        35,
                                        self.buffer)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(write_expected_status, actual_status)
        print "Verified write operation on second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc24_3_openers_write_lock(self):
        """
        3 clients open the same file requesting
        leases, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC024: 2 clients open the same file requesting leases, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Request rwh lease from 3rd client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a no caching lease.
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan2.write(handle3,
                                        234,
                                        self.buffer)
        print "Verified write operation on third file handle"

        # Close the file from first and second client.
        chan.close(handle1)
        print "Closed first file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc25_3_openers_write_lock_contend(self):
        """
        3 clients open the same file requesting
        leases, write data and lock 3 different ranges (contending) on the file.
        """
        print "-------------------------------------"
        print "TC025: 2 clients open the same file requesting leases, write data and lock 3 different ranges (contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        write_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        lock_expected_status = 'STATUS_LOCK_NOT_GRANTED'
        write_actual_status   = 'STATUS_SUCCESS'
        lock_actual_status   = 'STATUS_SUCCESS'

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Request rwh lease from 3rd client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a no caching lease.
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Write a small amount (less than 1Kbyte) of data from
        # third client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Write Request on Third Handle"

        try:
            bytes_written = chan2.write(handle3,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on first file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # first client.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on first file handle"

        # Close the file from first and second client.
        chan.close(handle1)
        print "Closed first file handle"
        chan1.close(handle2)
        print "Closed second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc26_3_openers_write_one_locker(self):
        """
        3 clients open the same file requesting
        leases, write data and only one locks 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC026: 2 clients open the same file requesting leases, write data and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Request rwh lease from 3rd client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a no caching lease.
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Write a small amount (less than 1Kbyte) of data anywhere
        # on the file.
        bytes_written = chan2.write(handle3,
                                        234,
                                        self.buffer)
        print "Verified write operation on third file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second and third clients.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the second and third clients get a read
        # and handle caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Close the file from second client.
        chan1.close(handle2)
        print "Closed second file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc27_2_openers_read_write_lock(self):
        """
        2 clients open the same file requesting
        leases, read data, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC027: 2 clients open the same file requesting leases, read data, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Write a small amount (less than 1Kbyte) of data on the
        # file to the same location where the read above.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"


        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        bytes_written = chan.write(handle1,
                                   234,
                                   self.buffer)

        # Should be granted rh on first client
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc28_2_openers_read_write_lock_contend(self):
        """
        2 clients open the same file requesting
        leases, read data, write data and lock 3 different
        ranges (contending)  on the file.
        """
        print "-------------------------------------"
        print "TC028: 2 clients open the same file requesting leases, read data, write data and lock 3 different ranges (contending)  on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        actual_status   = 'STATUS_SUCCESS'

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests_contend.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Write a small amount (less than 1Kbyte) of data on the
        # file to the same location where the read above.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests_contend.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from second client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Read Request on Second Handle"

        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        # Read data from the same location as on step above.
        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified read operation on second file handle"

        # Write a given number of bytes to the file from second
        # client on a location in the file that overlaps existing
        # locked ranges. Observe that the write fails with
        # STATUS_FILE_LOCK_CONFLICT.
        try:
            bytes_written = chan1.write(handle2,
                                        125,
                                        self.buffer)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified write operation on second file handle"

        # Should be granted n on first client
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Observe whether the second client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"
        chan.logoff()
        chan1.logoff()

    def test_tc29_3_openers_read_write_lock(self):
        """
        3 clients open the same file requesting
        leases, read data, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC029: 3 clients open the same file requesting leases, read data, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Write a small amount (less than 1Kbyte) of data on the
        # file to the same location where the read above.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Request rwh lease on third client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from anywhere in the file.
        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on third file handle"

        # Write a small amount (less than 1Kbyte) of data on the
        # file to the same location where the read above.
        bytes_written = chan2.write(handle3,
                                   3456,
                                   self.buffer)
        print "Verified write operation on third file handle"

        # Should be granted n on first client
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Close the file from first and second clients.
        chan.close(handle1)
        print "Closed first file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc30_3_openers_read_write_lock_contend(self):
        """
        3 clients open the same file requesting
        leases, read data, write data and lock 3 different ranges (contending) on the file.
        """
        print "-------------------------------------"
        print "TC030: 3 clients open the same file requesting leases, read data, write data and lock 3 different ranges (contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        actual_status   = 'STATUS_SUCCESS'

        # Request rwh lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Write a small amount (less than 1Kbyte) of data on the
        # file to the same location where the read above.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Request rwh lease on third client
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from third client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Read Request on Third Handle"

        try:
            data2 = chan2.read(handle3, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        # Read data from the same location as on step above.
        try:
            data2 = chan2.read(handle3, 3456, 901)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified read operation on second file handle"

        # Write a given number of bytes to the file from third
        # client on a location in the file that overlaps existing
        # locked ranges. Observe that the write fails with
        # STATUS_FILE_LOCK_CONFLICT.
        try:
            bytes_written = chan2.write(handle3,
                                        125,
                                        self.buffer)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified write operation on first file handle"

        # Should be granted n on first client
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read and handle
        # caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 3 with rwh lease request"

        # Observe whether the third client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()

    def test_tc31_2_openers_req_r_share_r(self):
        """
        2 clients open the same file requesting
        leases and reading (r) with read sharing (sr) options.
        """
        print "-------------------------------------"
        print "TC031: 2 clients open the same file requesting leases and reading (r) with read sharing (sr) options."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_READ_DATA,
                              share=pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_READ_DATA,
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_READ_DATA,
                              share=pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc32_2_openers_req_w_share_w(self):
        """
        2 clients open the same file requesting
        leases and writing (w) with write sharing (sw) options.
        """
        print "-------------------------------------"
        print "TC032: 2 clients open the same file requesting leases and writing (w) with write sharing (sw) options."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_WRITE_DATA,
                              share=pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_WRITE_DATA,
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_WRITE_DATA,
                              share=pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc33_2_openers_req_a_share_w(self):
        """
        2 clients open the same file requesting
        leases and appending (a) with write sharing (sw) options.
        """
        print "-------------------------------------"
        print "TC033: 2 clients open the same file requesting leases and appending (a) with write sharing (sw) options."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Request rw lease
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_APPEND_DATA,
                              share=pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_APPEND_DATA,
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.FILE_APPEND_DATA,
                              share=pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc34_2_openers_req_d_share_d(self):
        """
        2 clients open the same file requesting
        leases and deletion (r) with delete sharing (sd) options.
        """
        print "-------------------------------------"
        print "TC034: 2 clients open the same file requesting leases and deletion (r) with delete sharing (sd) options."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting no caching (this is done
        # by the redirector), delete access and delete sharing from
        # first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access=pike.smb2.DELETE,
                              share=pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.n).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Open file requesting no caching (this is done by the
        # redirector), delete access from the
        # second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.DELETE,
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.n).result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access=pike.smb2.DELETE,
                              share=pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc35_2_openers_req_rw_share_r(self):
        """
        2 clients open the same file one for RW
        access and share R the other for R access and share R.
        """
        print "-------------------------------------"
        print "TC035: 2 clients open the same file one for RW access and share R the other for R access and share R."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, read and write access and read sharing
        # from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, read access and read sharing from the second
        # client.
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc36_2_openers_req_ra_share_r(self):
        """
        2 clients open the same file one for RA
        access and share R the other for R access and share R.
        """
        print "-------------------------------------"
        print "TC036: 2 clients open the same file one for RA access and share R the other for R access and share R."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, read and append access and read
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_APPEND_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, read access and read sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"


        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc37_2_openers_req_rd_share_r(self):
        """
        2 clients open the same file one for RD
        access and share R the other for R access and share R.
        """
        print "-------------------------------------"
        print "TC037: 2 clients open the same file one for RD access and share R the other for R access and share R."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, read and delete access and read
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA | pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, read access and read sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = pike.smb2.FILE_SHARE_READ,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"


        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc38_2_openers_req_wr_share_w(self):
        """
        2 clients open the same file one for WR
        access and share W the other for W access and share W.
        """
        print "-------------------------------------"
        print "TC038: 2 clients open the same file one for WR access and share W the other for W access and share W."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, write and read access and write
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, write access and write sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"


        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc39_2_openers_req_wa_share_w(self):
        """
        2 clients open the same file one for WA
        access and share W the other for W access and share W.
        """
        print "-------------------------------------"
        print "TC039: 2 clients open the same file one for WA access and share W the other for W access and share W."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, write and append access and write
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_APPEND_DATA | pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, write access and write sharing from the second
        # client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First and second handle should get rh lease
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.

        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 2 with rwh lease request"


        # Should be granted rwh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc40_2_openers_req_wd_share_w(self):
        """
        2 clients open the same file one for WD
        access and share W the other for W access and share W.
        """
        print "-------------------------------------"
        print "TC040: 2 clients open the same file one for WD access and share W the other for W access and share W."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, write and delete access and write
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE | pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, write access and write sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = pike.smb2.FILE_SHARE_WRITE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"


        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc41_2_openers_req_dr_share_d(self):
        """
        2 clients open the same file one for DR
        access and share D the other for D access and share D.
        """
        print "-------------------------------------"
        print "TC041: 2 clients open the same file one for DR access and share D the other for D access and share D."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, delete and read access and delete
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA | pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, delete access and delete sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc42_2_openers_req_dw_share_d(self):
        """
        2 clients open the same file one for DW
        access and share D the other for D access and share D.
        """
        print "-------------------------------------"
        print "TC042: 2 clients open the same file one for DW access and share D the other for D access and share D."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, delete and write access and delete
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, delete access and delete sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc43_2_openers_req_da_share_d(self):
        """
        2 clients open the same file one for DA
        access and share D the other for D access and share D.
        """
        print "-------------------------------------"
        print "TC043: 2 clients open the same file one for DA access and share D the other for D access and share D."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, delete and append access and delete
        # sharing from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_APPEND_DATA | pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, delete access and delete sharing from the second
        # client. Observe whether the second client gets sharing
        # violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = pike.smb2.FILE_SHARE_DELETE,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on second lease
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc44_2_openers_req_r_no_sharing(self):
        """
        2 clients open the same file for
        reading (r) with no sharing (contending).
        """
        print "-------------------------------------"
        print "TC044: 2 clients open the same file for reading (r) with no sharing (contending)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, read access and no sharing from first
        # client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Attempt to open file requesting lease for read, handle
        # and write caching, read access and no sharing from the
        # second client. Observe whether the second client gets
        # sharing violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.

        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_READ_DATA,
                              share = 0,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc45_2_openers_req_w_no_sharing(self):
        """
        2 clients open the same file for
        writing (w) with no sharing (contending).
        """
        print "-------------------------------------"
        print "TC045: 2 clients open the same file for writing (w) with no sharing (contending)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, write access and no sharing from first
        # client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Attempt to open file requesting lease for read, handle
        # and write caching, write access and no sharing from the
        # second client. Observe whether the second client gets
        # sharing violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_WRITE_DATA,
                              share = 0,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc46_2_openers_req_a_no_sharing(self):
        """
        2 clients open the same file for
        appending (a) with no sharing (contending).
        """
        print "-------------------------------------"
        print "TC046: 2 clients open the same file for appending (w) with no sharing (contending)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, append access and no sharing from first
        # client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_APPEND_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Attempt to open file requesting lease for read, handle
        # and write caching, append access and no sharing from the
        # second client. Observe whether the second client gets
        # sharing violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_APPEND_DATA,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.FILE_APPEND_DATA,
                              share = 0,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc47_2_openers_req_d_no_sharing(self):
        """
        2 clients open the same file for
        deletion (d) with no sharing (contending).
        """
        print "-------------------------------------"
        print "TC047: 2 clients open the same file for deletion (d) with no sharing (contending)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_SHARING_VIOLATION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, delete access and no sharing from first
        # client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Attempt to open file requesting lease for read, handle
        # and write caching, delete access and no sharing from the
        # second client. Observe whether the second client gets
        # sharing violation error (STATUS_SHARING_VIOLATION).
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = 0,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "status sharing violation message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.DELETE,
                              share = 0,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc48_2_openers_1st_opi_2nd_opn(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses OPEN (opn).
        """
        print "-------------------------------------"
        print "TC048: 2 clients open the same file one uses OPEN_IF (opi) the other uses OPEN (opn)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc49_2_openers_1st_opi_2nd_opi(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses OPEN_IF (opi).
        """
        print "-------------------------------------"
        print "TC049: 2 clients open the same file one uses OPEN_IF (opi) the other uses OPEN_IF (opi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc50_2_openers_1st_opi_2nd_crt(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses CREATE (crt).
        """
        print "-------------------------------------"
        print "TC050: 2 clients open the same file one uses OPEN_IF (opi) the other uses CREATE (crt)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_OBJECT_NAME_COLLISION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and CREATE
        # disposition from second client.
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_CREATE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e)

        self.assertIn(expected_status, actual_status)
        print "STATUS_OBJECT_NAME_COLLISION message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc51_2_openers_1st_opi_2nd_sup(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses SUPERSEDE (sup).
        """
        print "-------------------------------------"
        print "TC051: 2 clients open the same file one uses OPEN_IF (opi) the other uses SUPERSEDE (sup)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and SUPERSEDE
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc52_2_openers_1st_opi_2nd_ovw(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses OVERWRITE (ovw).
        """
        print "-------------------------------------"
        print "TC052: 2 clients open the same file one uses OPEN_IF (opi) the other uses OVERWRITE (ovw)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OVERWRITE (ovw)
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc53_2_openers_1st_opi_2nd_ovi(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses OVERWRITE_IF (ovi).
        """
        print "-------------------------------------"
        print "TC053: 2 clients open the same file one uses OPEN_IF (opi) the other uses OVERWRITE_IF (ovi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and  OVERWRITE_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc54_2_openers_1st_sup_2nd_opn(self):
        """
        2 clients open the same file one uses
        SUPERSEDE (sup) the other uses OPEN (opn).
        """
        print "-------------------------------------"
        print "TC054: 2 clients open the same file one uses SUPERSEDE (sup) the other uses OPEN (opn)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc55_2_openers_1st_sup_2nd_opi(self):
        """
        2 clients open the same file one uses
        SUPERSEDE (sup) the other uses OPEN_IF (opi).
        """
        print "-------------------------------------"
        print "TC055: 2 clients open the same file one uses SUPERSEDE (sup) the other uses OPEN_IF (opi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc56_2_openers_1st_sup_2nd_crt(self):
        """
        2 clients open the same file one uses
        SUPERSEDE (sup) the other uses CREATE (crt).
        """
        print "-------------------------------------"
        print "TC056: 2 clients open the same file one uses SUPERSEDE (sup) the other uses CREATE (crt)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_OBJECT_NAME_COLLISION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and CREATE
        # disposition from second client.
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_CREATE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e)

        self.assertIn(expected_status, actual_status)
        print "STATUS_OBJECT_NAME_COLLISION message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc57_2_openers_1st_sup_2nd_sup(self):
        """
        2 clients open the same file one uses
        SUPERSEDE (sup) the other uses SUPERSEDE (sup).
        """
        print "-------------------------------------"
        print "TC057: 2 clients open the same file one uses SUPERSEDE (sup) the other uses SUPERSEDE (sup)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and SUPERSEDE
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc58_2_openers_1st_sup_2nd_ovw(self):
        """
        2 clients open the same file one uses
        SUPERSEDE (sup) the other uses OVERWRITE (ovw).
        """
        print "-------------------------------------"
        print "TC058: 2 clients open the same file one uses SUPERSEDE (sup) the other uses OVERWRITE (ovw)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OVERWRITE (ovw)
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc59_2_openers_1st_sup_2nd_ovi(self):
        """
        2 clients open the same file one uses
        OPEN_IF (opi) the other uses OVERWRITE_IF (ovi).
        """
        print "-------------------------------------"
        print "TC059: 2 clients open the same file one uses SUPERSEDE (sup) the other uses OVERWRITE_IF (ovi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and SUPERSEDE (sup) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and  OVERWRITE_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc60_2_openers_1st_ovw_2nd_opn(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses OPEN (opn).
        """
        print "-------------------------------------"
        print "TC060: 2 clients open the same file one uses OVERWRITE (ovw) the other uses OPEN (opn)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc61_2_openers_1st_ovw_2nd_opi(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses OPEN_IF (opi).
        """
        print "-------------------------------------"
        print "TC061: 2 clients open the same file one uses OVERWRITE (ovw) the other uses OPEN_IF (opi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc62_2_openers_1st_ovw_2nd_crt(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses CREATE (crt).
        """
        print "-------------------------------------"
        print "TC062: 2 clients open the same file one uses OVERWRITE (ovw) the other uses CREATE (crt)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_OBJECT_NAME_COLLISION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and CREATE
        # disposition from second client.
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_CREATE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e)

        self.assertIn(expected_status, actual_status)
        print "STATUS_OBJECT_NAME_COLLISION message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc63_2_openers_1st_ovw_2nd_sup(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses SUPERSEDE (sup).
        """
        print "-------------------------------------"
        print "TC063: 2 clients open the same file one uses OVERWRITE (ovw) the other uses SUPERSEDE (sup)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and SUPERSEDE
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc64_2_openers_1st_ovw_2nd_ovw(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses OVERWRITE (ovw).
        """
        print "-------------------------------------"
        print "TC064: 2 clients open the same file one uses OVERWRITE (ovw) the other uses OVERWRITE (ovw)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OVERWRITE (ovw)
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc65_2_openers_1st_ovw_2nd_ovi(self):
        """
        2 clients open the same file one uses
        OVERWRITE (ovw) the other uses OVERWRITE_IF (ovi).
        """
        print "-------------------------------------"
        print "TC065: 2 clients open the same file one uses OVERWRITE (ovw) the other uses OVERWRITE_IF (ovi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE (ovw) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and  OVERWRITE_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc66_2_openers_1st_ovi_2nd_opn(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses OPEN (opn).
        """
        print "-------------------------------------"
        print "TC066: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses OPEN (opn)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc67_2_openers_1st_ovi_2nd_opi(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses OPEN_IF (opi).
        """
        print "-------------------------------------"
        print "TC067: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses OPEN_IF (opi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc68_2_openers_1st_ovi_2nd_crt(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses CREATE (crt).
        """
        print "-------------------------------------"
        print "TC068: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses CREATE (crt)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        expected_status = 'STATUS_OBJECT_NAME_COLLISION'
        actual_status   = 'STATUS_SUCCESS'

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and CREATE
        # disposition from second client.
        try:
            handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_CREATE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
            # Wait for break
            handle1.lease.future.wait()

            # Now ack break
            handle1.lease.on_break(lambda state: state)

            # Wait for handle2
            handle2 = handle2.result(timeout=120)
        except Exception as e:
            actual_status = str(e)

        self.assertIn(expected_status, actual_status)
        print "STATUS_OBJECT_NAME_COLLISION message is given while opening second file handle"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the third client.
        handle3 = chan2.create(tree2,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease3,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle3.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan2.close(handle3)
        print "Closed third file handle"

        chan.logoff()
        chan2.logoff()

    def test_tc69_2_openers_1st_ovi_2nd_sup(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses SUPERSEDE (sup).
        """
        print "-------------------------------------"
        print "TC069: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses SUPERSEDE (sup)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and SUPERSEDE
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc70_2_openers_1st_ovi_2nd_ovw(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses OVERWRITE (ovw).
        """
        print "-------------------------------------"
        print "TC070: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses OVERWRITE (ovw)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OVERWRITE (ovw)
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc71_2_openers_1st_ovi_2nd_ovi(self):
        """
        2 clients open the same file one uses
        OVERWRITE_IF (ovi) the other uses OVERWRITE_IF (ovi).
        """
        print "-------------------------------------"
        print "TC071: 2 clients open the same file one uses OVERWRITE_IF (ovi) the other uses OVERWRITE_IF (ovi)."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OVERWRITE_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and  OVERWRITE_IF
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OVERWRITE_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc72_2_openers_set_basic_info(self):
        """
        LOFT MCSN OSFIS Two clients open the same file and set
        FILE_BASIC_INFORMATION.
        """
        print "-------------------------------------"
        print "TC072: 2 clients open the same file and set FILE_BASIC_INFORMATION."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Retrieves the current FILE_BASIC_INFORMATION.
        try:
            info=chan.query_file_info(handle1,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 1"

        # Set FILE_BASIC_INFORMATION changing the "FileAttributes"
        # field only
        info.basic_information.file_attributes = "R,H,S"
        chan.set_file_info(handle1,info)
        print "Changed the FileAttributes field in FILE_BASIC_INFORMATION"

        # Set FILE_BASIC_INFORMATION changing the "CreationTime"
        # field only.
        info.basic_information.creation_time = "Tue Oct 25 16:10:32.7481797 2011"
        chan.set_file_info(handle1,info)
        print "Changed the CreationTime field in FILE_BASIC_INFORMATION"

        # Open file requesting lease for read, handle and write
        # caching, generic read and generic write access and OPEN
        # disposition from second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Retrieves the current information.
        try:
            info1=chan1.query_file_info(handle2,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 2"

        # Set FILE_BASIC_INFORMATION changing the "FileAttributes"
        # field only from first client.
        info1.basic_information.file_attributes = "A"
        chan1.set_file_info(handle2,info1)
        print "Changed the FileAttributes field in FILE_BASIC_INFORMATION"

        # Set FILE_BASIC_INFORMATION changing the "CreationTime"
        # field only.
        info1.basic_information.creation_time = "Tue Oct 24 16:10:32.7481797 2011"
        chan1.set_file_info(handle2,info1)
        print "Changed the CreationTime field in FILE_BASIC_INFORMATION"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc73_2_openers_set_disp_info(self):
        """
        LOFT MCSN OSFIS Two clients open the same file and set
        FILE_DISPOSITION_INFORMATION.
        """
        print "-------------------------------------"
        print "TC073: 2 clients open the same file and set FILE_DISPOSITION_INFORMATION."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Retrieves the current information.
        try:
            info=chan.query_file_info(handle1,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 1"

        # Set FILE_DISPOSITION_INFORMATION changing the
        # "DeletePending" field to "True".
        info.standard_information.delete_pending = True
        chan.set_file_info(handle1,info)
        print "Changed the DeletePending field in FILE_DISPOSITION_INFORMATION to True"

        # Observe that the SET_INFORMATION command goes on the wire
        # and that the leases state remains unchanged.

        # Set FILE_DISPOSITION_INFORMATION changing the
        # "DeletePending" field back to "False".
        info.standard_information.delete_pending = False
        chan.set_file_info(handle1,info)
        print "Changed the DeletePending field in FILE_DISPOSITION_INFORMATION to False"

        # Observe that the SET_INFORMATION command goes on the wire
        # and that the leases state remains unchanged.

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Retrieves the current information.
        try:
            info1=chan1.query_file_info(handle2,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 2"

        # Set FILE_DISPOSITION_INFORMATION changing the
        # "DeletePending" field to "True" once more.
        info1.standard_information.delete_pending = True
        chan1.set_file_info(handle2,info1)
        print "Changed the DeletePending field in FILE_DISPOSITION_INFORMATION to True"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc74_2_openers_set_alloc_info(self):
        """
        LOFT MCSN OSFIS Two clients open the same file and set
        FILE_ALLOCATION_INFORMATION.
        """
        print "-------------------------------------"
        print "TC074: 2 clients open the same file and set FILE_ALLOCATION_INFORMATION."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Retrieves the current information.
        try:
            info=chan.query_file_info(handle1,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 1"

        # Set FILE_ALLOCATION_INFORMATION changing the
        # "AllocationSize" field to 65536.
        info.standard_information.allocation_size = 65536
        chan.set_file_info(handle1,info)
        print "Changed the AllocationSize field to 65536 in FILE_ALLOCATION_INFORMATION"

        # Observe that the SET_INFORMATION command goes on the wire
        # and that the leases state remains unchanged.

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Retrieves the current information.
        try:
            info1=chan1.query_file_info(handle2,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 2"

        # Set FILE_ALLOCATION_INFORMATION changing the
        # "AllocationSize" field to 16384.
        info1.standard_information.allocation_size = 16384
        chan1.set_file_info(handle2,info1)
        print "Changed the AllocationSize field to 16384 in FILE_ALLOCATION_INFORMATION"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for third file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc75_2_openers_set_eof_info(self):
        """
        LOFT MCSN OSFIS Two clients open the same file and set
        FILE_END_OF_FILE_INFORMATION.
        """
        print "-------------------------------------"
        print "TC075: 2 clients open the same file and set FILE_END_OF_FILE_INFORMATION."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()

        # Open an unopened file requesting lease for read, handle
        # and write caching, generic read and generic write access
        # and OPEN_IF (ovi) disposition from first client.
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # First lease should be rwh
        self.assertEqual(handle1.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for first file handle"

        # Retrieves the current information.
        try:
            info=chan.query_file_info(handle1,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 1"

        # Set FILE_END_OF_FILE_INFORMATION changing the
        # "EndOfFile" field to 65536.
        info.standard_information.end_of_file = 65536
        chan.set_file_info(handle1,info)
        print "Changed the EndOfFile field to 65536 in FILE_ALLOCATION_INFORMATION"

        # Observe that the SET_INFORMATION command goes on the wire
        # and that the leases state remains unchanged.

        # Open file requesting lease for read, handle and write
        # caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)
        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        try:
            info1=chan1.query_file_info(handle2,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            print 'Querying general attributes of file ...FAILED :',str(e)
        print "Retrieved the current FILE_ALL_INFORMATION on file handle 2"

        # Set FILE_END_OF_FILE_INFORMATION changing the "EndOfFile"
        # field to 16384.
        info1.standard_information.end_of_file = 16384
        chan1.set_file_info(handle2,info1)
        print "Changed the EndOfFile field to 16384 in FILE_ALLOCATION_INFORMATION"

        # Close the file from first client.
        chan.close(handle1)
        print "Closed first file handle"

        # Open file again requesting lease for read, handle and
        # write caching from the second client.
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
                              share = self.share_all,
                              disposition=pike.smb2.FILE_OPEN_IF,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 2 with rwh lease request"

        # Should be granted rwh on third cliant
        self.assertEqual(handle2.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for second file handle"

        chan1.close(handle2)
        print "Closed second file handle"

        chan.logoff()
        chan1.logoff()

    def test_tc76_10_openers(self):
        """
        Ten clients open the same file requesting
        leases.
        """
        print "-------------------------------------"
        print "TC076: Ten clients open the same file requesting leases."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"


        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc77_10_openers_read(self):
        """
        Ten clients open the same file requesting
        leases and read from the file.
        """
        print "-------------------------------------"
        print "TC077: Ten clients open the same file requesting leases and read from the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"
        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc78_10_openers_write(self):
        """
        Ten clients open the same file requesting
        leases and write to the file.
        """
        print "-------------------------------------"
        print "TC078: Ten clients open the same file requesting leases and write to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Write a given number of bytes to the file from second
        # client.
        bytes_written = chan1.write(handle2,
                                   11,
                                   self.buffer)
        print "Verified write operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Write a given number of bytes to the file from third
        # client.
        bytes_written = chan2.write(handle3,
                                   21,
                                   self.buffer)
        print "Verified write operation on third file handle"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.

        print "Open file handles 4 to 10 with rwh lease request"

        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan3.write(handle4,
                                   30,
                                   self.buffer)
        print "Verified write operation on 4th file handle"

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   40,
                                   self.buffer)
        print "Verified write operation on 5th file handle"

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   50,
                                   self.buffer)
        print "Verified write operation on 6th file handle"

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   60,
                                   self.buffer)
        print "Verified write operation on 7th file handle"

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   70,
                                   self.buffer)
        print "Verified write operation on 8th file handle"

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   80,
                                   self.buffer)
        print "Verified write operation on 9th file handle"

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   90,
                                   self.buffer)
        print "Verified write operation on 10th file handle"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc79_10_openers_one_writer(self):
        """
        Ten clients open the same file requesting
        leases and only one writes to the file.
        """
        print "-------------------------------------"
        print "TC079: Ten clients open the same file requesting leases and only one writes to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc80_10_openers_read_write(self):
        """
        Ten clients open the same file requesting
        leases, read and write data from/to the file.
        """
        print "-------------------------------------"
        print "TC080: Ten clients open the same file requesting leases, read and write data from/to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   100,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Write a given number of bytes to the file from second
        # client.
        bytes_written = chan1.write(handle2,
                                   11,
                                   self.buffer)
        print "Verified write operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Read data from anywhere in the file from third client.
        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Write a given number of bytes to the file from third
        # client.
        bytes_written = chan2.write(handle3,
                                   21,
                                   self.buffer)
        print "Verified write operation on third file handle"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 4 with rwh lease request"

        # Read data from anywhere in the file from fourth client.
        data3 = chan3.read(handle4, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data3 = chan3.read(handle4, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on 4th file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        bytes_written = chan3.write(handle4,
                                   30,
                                   self.buffer)
        print "Verified write operation on 4th file handle"

        print "Open file handles 5 to 10 with rwh lease request"

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   40,
                                   self.buffer)
        print "Verified write operation on 5th file handle"

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   50,
                                   self.buffer)
        print "Verified write operation on 6th file handle"

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   60,
                                   self.buffer)
        print "Verified write operation on 7th file handle"

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   70,
                                   self.buffer)
        print "Verified write operation on 8th file handle"

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   80,
                                   self.buffer)
        print "Verified write operation on 9th file handle"

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   90,
                                   self.buffer)
        print "Verified write operation on 10th file handle"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc81_10_openers_read_one_writer(self):
        """
        Ten clients open the same file requesting
        leases, read and only one writes data from/to the file.
        """
        print "-------------------------------------"
        print "TC081: Ten clients open the same file requesting leases, read and only one writes data from/to the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).
        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).
        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for second file handle"

        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for third file handle"

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.rh)
        self.assertEqual(handle5.lease.lease_state, self.rh)
        self.assertEqual(handle6.lease.lease_state, self.rh)
        self.assertEqual(handle7.lease.lease_state, self.rh)
        self.assertEqual(handle8.lease.lease_state, self.rh)
        self.assertEqual(handle9.lease.lease_state, self.rh)
        self.assertEqual(handle10.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc82_10_openers_lock(self):
        """
        Ten clients open the same file requesting
        leases and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC082: Ten clients open the same file requesting leases and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_test_10_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_test_10_openers_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_test_10_openers_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handle 10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc83_10_openers_lock_contend(self):
        """
        Ten clients open the same file requesting
        leases and lock 3 different ranges (contending) on the
        file.
        """
        print "-------------------------------------"
        print "TC083: Ten clients open the same file requesting leases and lock 3 different ranges (contending) on the file."
        expected_status = 'STATUS_LOCK_NOT_GRANTED'
        actual_status   = 'STATUS_SUCCESS'
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Should be granted no lease on first handle
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # first client. Observe that the lock from third client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            actual_status = str(e[1])

        self.assertEqual(expected_status, actual_status)

        # Lock 3 different ranges exclusively (different than those
        # locked by the other two clients) on the file from third
        # client.
        chan2.lock(handle3, self.lock7).result(timeout=120)
        chan2.lock(handle3, self.lock8).result(timeout=120)
        chan2.lock(handle3, self.lock9).result(timeout=120)
        print "Verified Exclusive Lock operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handle 10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc84_10_openers_one_locker(self):
        """
        Ten clients open the same file requesting
        leases and only one locks 3 different ranges on the file
        """
        print "-------------------------------------"
        print "TC084: Ten clients open the same file requesting leases and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted no on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Should be granted no on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc85_10_openers_read_lock(self):
        """
        Ten clients open the same file requesting
        leases, read data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC085: Ten clients open the same file requesting leases, read data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        # Read data from anywhere in the file from third client.
        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data2 = chan2.read(handle3, len(self.buffer), 0)
        self.assertEqual(self.buffer, data2.tostring())
        print "Verified read operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handle 10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc86_10_openers_read_lock_contend(self):
        """
        Ten clients open the same file requesting
        leases, read data and lock 3 different ranges (contending)
        on the file.
        """
        print "-------------------------------------"
        print "TC086: Ten clients open the same file requesting leases, read data and lock 3 different ranges (contending) on the file."
        read_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        expected_status = 'STATUS_LOCK_NOT_GRANTED'
        read_actual_status   = 'STATUS_SUCCESS'
        lock_actual_status   = 'STATUS_SUCCESS'
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from second client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Read Request on Second Handle"

        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)
        print "Verified read operation on second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "No lease is granted for the file handles 1 to 3"

        # Read data from third client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            data2 = chan2.read(handle3, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)
        print "Verified read operation on third file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # first client. Observe that the lock from third client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "No lease is granted for all file handles from 1 to 9"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"


        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "No lease is granted for file handle10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc87_10_openers_read_one_locker(self):
        """
        Ten clients open the same file requesting
        leases, read data and only one locks 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC087: Ten clients open the same file requesting leases, read data and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Observe that there is no upgrade break notification sent
        # to the client with the last open.
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handle 10"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc88_10_openers_write_lock(self):
        """
        Ten clients open the same file requesting
        leases, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC088: Ten clients open the same file requesting leases, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_test_10_openers_write_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_test_10_openers_write_lock.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Write a given number of bytes to the file from second
        # client.
        bytes_written = chan1.write(handle2,
                                   211,
                                   self.buffer)
        print "Verified write operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        # Write a given number of bytes to the file from third
        # client.
        bytes_written = chan2.write(handle3,
                                   221,
                                   self.buffer)
        print "Verified write operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.
        handle4 = chan3.create(tree3,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle5 = chan4.create(tree4,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle6 = chan5.create(tree5,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle7 = chan6.create(tree6,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle8 = chan7.create(tree7,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle9 = chan8.create(tree8,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        handle10 = chan9.create(tree9,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Open file handles 4 to 10 with rwh lease request"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_test_10_openers_write_lock.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc89_10_openers_write_lock_contend(self):
        """
        Ten clients open the same file requesting
        leases, write data and lock 3 different ranges(contending) on the file.
        """
        print "-------------------------------------"
        print "TC089: Ten clients open the same file requesting leases, / write data and lock 3 different ranges (contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        lock_expected_status = 'STATUS_LOCK_NOT_GRANTED'
        write_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        lock_actual_status   = 'STATUS_SUCCESS'
        write_actual_status   = 'STATUS_SUCCESS'

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)
        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "No lease is granted for second file handle"

        # Write a small amount (less than 1Kbyte) of data from
        # second client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Write Request on Second Handle"

        try:
            bytes_written = chan1.write(handle2,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Should be granted no lease on first handle
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        # Write a small amount (less than 1Kbyte) of data from
        # third client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            bytes_written = chan2.write(handle3,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on third file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.

        print "Open file handles 4 to 10 with rwh lease request"

        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan3.write(handle4,
                                   230,
                                   self.buffer)

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   240,
                                   self.buffer)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   250,
                                   self.buffer)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   260,
                                   self.buffer)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   270,
                                   self.buffer)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   280,
                                   self.buffer)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   290,
                                   self.buffer)

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no
        # lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for all file handles from 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc90_10_openers_write_one_locker(self):
        """
        Ten clients open the same file requesting
        leases, write data and only one locks 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC090: Ten clients open the same file requesting leases, write data and only one locks 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        bytes_written = chan1.write(handle2,
                                        211,
                                        self.buffer)
        print "Verified write operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        bytes_written = chan2.write(handle3,
                                        221,
                                        self.buffer)
        print "Verified write operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.

        print "Open file handles 4 to 10 with rwh lease request"

        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan3.write(handle4,
                                   230,
                                   self.buffer)
        print "Verified write operation on 4th file handle"

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   240,
                                   self.buffer)
        print "Verified write operation on 5th file handle"

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   250,
                                   self.buffer)
        print "Verified write operation on 6th file handle"

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   260,
                                   self.buffer)
        print "Verified write operation on 7th file handle"

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   270,
                                   self.buffer)
        print "Verified write operation on 8th file handle"

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   280,
                                   self.buffer)
        print "Verified write operation on 9th file handle"

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   290,
                                   self.buffer)
        print "Verified write operation on 10th file handle"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc91_10_openers_read_write_lock(self):
        """
        Ten clients open the same file requesting
        leases, read data, write data and lock 3 different ranges on the file.
        """
        print "-------------------------------------"
        print "TC091: Ten clients open the same file requesting leases, read data, write data and lock 3 different ranges on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)

        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Write a given number of bytes to the file from second
        # client.
        bytes_written = chan1.write(handle2,
                                   211,
                                   self.buffer)
        print "Verified write operation on second file handle"

        # Read data from anywhere in the file from second client.
        data1 = chan1.read(handle2, len(self.buffer), 0)
        self.assertEqual(self.buffer, data1.tostring())
        print "Verified read operation on second file handle"

        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache).

        # Lock 3 different ranges exclusively (different than those
        # locked by the first client) on the file from second
        # client.
        chan1.lock(handle2, self.lock4).result(timeout=120)
        chan1.lock(handle2, self.lock5).result(timeout=120)
        chan1.lock(handle2, self.lock6).result(timeout=120)
        print "Verified Exclusive Lock operation on second file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted rh on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted rh on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        # Write a given number of bytes to the file from third
        # client.
        bytes_written = chan2.write(handle3,
                                   221,
                                   self.buffer)
        print "Verified write operation on third file handle"

        # Lock 3 different ranges exclusively (different than those
        # locked by the other two clients) on the file from third
        # client.
        chan2.lock(handle3, self.lock7).result(timeout=120)
        chan2.lock(handle3, self.lock8).result(timeout=120)
        chan2.lock(handle3, self.lock9).result(timeout=120)
        print "Verified Exclusive Lock operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.

        print "Open file handles 4 to 10 with rwh lease request"

        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan3.write(handle4,
                                   230,
                                   self.buffer)
        print "Verified write operation on 4th file handle"

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   240,
                                   self.buffer)
        print "Verified write operation on 5th file handle"

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   250,
                                   self.buffer)
        print "Verified write operation on 6th file handle"

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   260,
                                   self.buffer)
        print "Verified write operation on 7th file handle"

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   270,
                                   self.buffer)
        print "Verified write operation on 8th file handle"

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   280,
                                   self.buffer)
        print "Verified write operation on 9th file handle"

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   290,
                                   self.buffer)
        print "Verified write operation on 10th file handle"

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get read and
        # handle caching lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "no lease is granted for file handles 4 to 10"

        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for the 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()

    def test_tc92_10_openers_read_write_lock_contend(self):
        """
        Ten clients open the same file requesting
        leases, read data, write data and lock 3 different ranges(contending) on the file.
        """
        print "-------------------------------------"
        print "TC092: Ten clients open the same file requesting leases, read data, write data and lock 3 different ranges(contending) on the file."
        chan, tree = self.tree_connect()
        chan1, tree1 = self.tree_connect()
        chan2,  tree2 = self.tree_connect()
        lock_expected_status = 'STATUS_LOCK_NOT_GRANTED'
        write_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        read_expected_status = 'STATUS_FILE_LOCK_CONFLICT'
        lock_actual_status   = 'STATUS_SUCCESS'
        write_actual_status   = 'STATUS_SUCCESS'
        read_actual_status   = 'STATUS_SUCCESS'

        # Request rw lease from first client
        handle1 = chan.create(tree,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease1,
                              lease_state = self.rwh).result(timeout=120)

        print "Open file handle 1 with rwh lease request"

        # Write a given number of bytes to the file.
        bytes_written = chan.write(handle1,
                                   0,
                                   self.buffer)
        print "Verified write operation on first file handle"

        # Read data from anywhere in the file.
        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())

        # Wait 3 seconds.
        time.sleep(3)

        data = chan.read(handle1, len(self.buffer), 0)
        self.assertEqual(self.buffer, data.tostring())
        print "Verified read operation on first file handle"
        # Observe that the read doesn't go on the wire (the data is
        # being read from the client's cache)

        # Lock 3 different ranges exclusively on the file.
        chan.lock(handle1, self.lock1).result(timeout=120)
        chan.lock(handle1, self.lock2).result(timeout=120)
        chan.lock(handle1, self.lock3).result(timeout=120)
        print "Verified Exclusive Lock operation on first file handle"

        # Break our lease
        handle2 = chan1.create(tree1,
                              'lease_tests.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              lease_key = self.lease2,
                              lease_state = self.rwh)

        # Wait for break
        handle1.lease.future.wait()

        # Now ack break
        handle1.lease.on_break(lambda state: state)

        # Wait for handle2
        handle2 = handle2.result(timeout=120)
        print "Open file handle 2 with rwh lease request"

        # First lease should have broken to rh
        self.assertEqual(handle1.lease.lease_state, self.rh)
        print "read, handle caching lease is granted for first file handle"

        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        print "no lease is granted for second file handle"

        # Write a small amount (less than 1Kbyte) of data from
        # second client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.

        print "Send Write Request on Second Handle"

        try:
            bytes_written = chan1.write(handle2,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on second file handle"

        # Read data from second client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        try:
            data1 = chan1.read(handle2, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)
        print "Verified read operation on second file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # second client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan1.lock(handle2, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on second file handle"

        # Should be granted no lease on first handle
        self.assertEqual(handle1.lease.lease_state, self.n)
        print "no lease is granted for first file handle"

        # Open file requesting lease for read, handle and write
        # caching from the third client.
        handle3 = chan2.create(tree2,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Open file handle 3 with rwh lease request"

        # First lease should have broken to n
        self.assertEqual(handle1.lease.lease_state, self.n)
        # Should be granted n on second lease
        self.assertEqual(handle2.lease.lease_state, self.n)
        # Should be granted n on third lease
        self.assertEqual(handle3.lease.lease_state, self.n)
        print "no lease is granted for file handles 1, 2 and 3"

        # Write a small amount (less than 1Kbyte) of data from
        # third client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            bytes_written = chan2.write(handle3,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on third file handle"

        # Read data from third client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            data2 = chan2.read(handle3, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        try:
            data2 = chan2.read(handle3, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)
        print "Verified read operation on third file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # third client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan2.lock(handle3, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on third file handle"

        chan3, tree3 = self.tree_connect()
        chan4, tree4 = self.tree_connect()
        chan5,  tree5 = self.tree_connect()
        chan6, tree6 = self.tree_connect()
        chan7, tree7 = self.tree_connect()
        chan8,  tree8 = self.tree_connect()
        chan9,  tree9 = self.tree_connect()

        # Open file requesting lease for read, handle and write
        # caching from all other clients.
        # Write a given number of bytes to the file from the other
        # clients.
        handle4 = chan3.create(tree3,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)
        print "Open file handle 4 with rwh lease request"

        # Write a small amount (less than 1Kbyte) of data from
        # 4th client on a location in the file that overlaps
        # existing locked ranges from first client. Observe that
        # the write fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            bytes_written = chan3.write(handle4,
                                        35,
                                        self.buffer)
        except Exception as e:
            write_actual_status = str(e[1])

        self.assertEqual(write_expected_status, write_actual_status)
        print "Verified write operation on 4th file handle"

        # Read data from 4th client from a location in the file
        # that overlaps existing locked ranges. Observe that the
        # read fails with STATUS_FILE_LOCK_CONFLICT.
        try:
            data3 = chan3.read(handle4, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)

        # Wait 3 seconds.
        time.sleep(3)

        try:
            data3 = chan3.read(handle4, 3456, 901)
        except Exception as e:
            read_actual_status = str(e[1])

        self.assertEqual(read_expected_status, read_actual_status)
        print "Verified read operation on 4th file handle"

        # Attempt to obtain a non-blocking exclusive lock from
        # 4th client on one of the ranges already locked by the
        # first client. Observe that the lock from second client is
        # revoked with STATUS_LOCK_NOT_GRANTED.
        try:
            chan3.lock(handle4, [(123, 45, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]).result(timeout=120)
        except Exception as e:
            lock_actual_status = str(e[1])

        self.assertEqual(lock_expected_status, lock_actual_status)
        print "Verified Exclusive Lock operation on 4th file handle"

        print "Open file handles 5 to 10 with rwh lease request"

        handle5 = chan4.create(tree4,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan4.write(handle5,
                                   240,
                                   self.buffer)

        handle6 = chan5.create(tree5,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan5.write(handle6,
                                   250,
                                   self.buffer)

        handle7 = chan6.create(tree6,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan6.write(handle7,
                                   260,
                                   self.buffer)

        handle8 = chan7.create(tree7,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan7.write(handle8,
                                   270,
                                   self.buffer)

        handle9 = chan8.create(tree8,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan8.write(handle9,
                                   280,
                                   self.buffer)

        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        bytes_written = chan9.write(handle10,
                                   290,
                                   self.buffer)

        # Observe whether no lease breaks were sent to any of the
        # other seven clients.

        # Observe whether all other clients only get no
        # caching lease.
        self.assertEqual(handle4.lease.lease_state, self.n)
        self.assertEqual(handle5.lease.lease_state, self.n)
        self.assertEqual(handle6.lease.lease_state, self.n)
        self.assertEqual(handle7.lease.lease_state, self.n)
        self.assertEqual(handle8.lease.lease_state, self.n)
        self.assertEqual(handle9.lease.lease_state, self.n)
        self.assertEqual(handle10.lease.lease_state, self.n)
        print "No lease is granted for all file handles"


        # Close the file from all clients except one.
        chan.close(handle1)
        chan1.close(handle2)
        chan2.close(handle3)
        chan3.close(handle4)
        chan4.close(handle5)
        chan5.close(handle6)
        chan6.close(handle7)
        chan7.close(handle8)
        chan8.close(handle9)
        print "Closed file handles from 1 to 9"

        # Open file again requesting lease for read, handle and
        # write caching from the last client.
        handle10 = chan9.create(tree9,
                                'lease_tests.txt',
                                share=self.share_all,
                                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                lease_key = self.lease3,
                                lease_state = self.rwh).result(timeout=120)

        print "Re-Open file handle 10 with rwh lease request"

        # Observe whether the last client gets a read, handle and
        # write caching lease.
        self.assertEqual(handle10.lease.lease_state, self.rwh)
        print "read, write, handle caching lease is granted for 10th file handle"

        # Close the file from the last client.
        chan9.close(handle10)
        print "Closed the 10th file handle"

        chan.logoff()
        chan1.logoff()
        chan2.logoff()
        chan3.logoff()
        chan4.logoff()
        chan5.logoff()
        chan6.logoff()
        chan7.logoff()
        chan8.logoff()
        chan9.logoff()
