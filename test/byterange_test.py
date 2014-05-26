#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        lock.py
#
# Abstract:
#
#        byte range lock tests with different combinations where 2nd lock is expected to fail followed by a cancel request.
#
# Authors: Dhanashree Patil, Calsoft (dhanashree.patil@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

class LockTest(pike.test.PikeTest):
    def test_byterange1(self):
        print "***\ntest_byterange1.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)] #A lock tuple which consistes of offset, lenth and flags)

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

        # Create file, lock
        print "Creating a file."
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks).result()
        print "Byte range lock applied succesfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)

    def test_byterange2(self):
        print "***\n\ntest_byterange2.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)] #A lock tuple which consistes of offset, lenth and flags)
        locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

        # Create file, lock
        print "Creating a file."
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks1).result()
        print "Byte range lock applied successfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks2)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)

    def test_byterange3(self):
        print "***\n\ntest_byterange3.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)] #A lock tuple which consistes of offset, lenth and flags)
        locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
        print "Creating a file."
        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks1).result()
        print "Byte range lock applied successfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks2)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)


    def test_byterange4(self):
        print "***\n\ntest_byterange4.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK|pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]#A lock tuple which consistes of offset, lenth and flags)
        locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
        print "Creating a file."
        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks1).result()
        print "Byte range lock applied successfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks2)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)

    def test_byterange5(self):
        print "***\n\ntest_byterange5.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK|pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]#A lock tuple which consistes of offset, lenth and flags)
        locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
        print "Creating a file."
        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks1).result()
        print "Byte range lock applied successfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response.
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks2)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)

    def test_byterange6(self):
        print "***\n\ntest_byterange6.\n---"
        print "Setting up the session and tree connect."
        chan, tree = self.tree_connect()
        print "Session set up and tree connect successful."
        buffer = "0123456789012345678901"
        locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK|pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]#A lock tuple which consistes of offset, lenth and flags)
        locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE
        print "Creating a file."
        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
        print "File created successfully."
        print "Writing into the file."
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        print "File write completed."
        print "Verify write operation."
        self.assertEqual(bytes_written, len(buffer))
        print "Write operation verified successfully."
        print "Apply byte range lock on the file."
        chan.lock(file1, locks1).result()
        print "Byte range lock applied successfully."
        print "Open another handle on the same file."
        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
        print "Second file handle created successfully."
        # This will block since the lock is already held, so only wait for interim response.
        print "Apply byte range lock on the same range using second file handle."
        lock_future = chan.lock(file2, locks2)
        print "Wait for the response as this request is expected to fail."
        lock_future.wait_interim()
        print "Cancel, wait for response, verify error response."
        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        print "Close file handle 1."
        chan.close(file1)
        print "Close file handle 2."
        chan.close(file2)

