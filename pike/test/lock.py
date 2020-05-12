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
#        lock.py
#
# Abstract:
#
#        Lock tests
#
# Authors: Arlene Berry (arlene.berry@emc.com)
#

from builtins import range
import pike.model
import pike.smb2
import pike.test
import pike.ntstatus

class LockTest(pike.test.PikeTest):
    # Take a basic byte-range lock
    def test_lock(self):
        chan, tree = self.tree_connect()
        buffer = "0123456789012345678901"
        locks = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        file = chan.create(tree,
                              'lock.txt',
                              access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                              share=share_all,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              options=pike.smb2.FILE_DELETE_ON_CLOSE).result()
       
        bytes_written = chan.write(file,
                                   0,
                                   buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.lock(file, locks).result()
        
        chan.close(file)

    # Test that pending lock request can be cancelled, yielding STATUS_CANCELLED
    def test_cancel(self):
        chan, tree = self.tree_connect()
        buffer = "0123456789012345678901"
        locks = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
       
        bytes_written = chan.write(file1,
                                   0,
                                   buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.lock(file1, locks).result()

        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()

        # This will block since the lock is already held, so only wait for interim response
        lock_future = chan.lock(file2, locks)
        lock_future.wait_interim()

        # Cancel, wait for response, verify error response
        with self.assert_error(pike.ntstatus.STATUS_CANCELLED):
            chan.cancel(lock_future).result()
        
        chan.close(file1)
        chan.close(file2)

    def test_deny_write(self):
        chan, tree = self.tree_connect()
        buffer = "0123456789012345678901"
        lock_offset = 8
        lock_size = 8
        locks = [(lock_offset, lock_size, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
       
        bytes_written = chan.write(file1, 0, buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.lock(file1, locks).result()

        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()

        cases = ((offset,size) for offset in range(0, 16) for size in range(0, 16))

        for (offset,size) in cases:
            if ranges_intersect(offset, offset+size, lock_offset, lock_offset + lock_size):
                with self.assert_error(pike.ntstatus.STATUS_FILE_LOCK_CONFLICT):
                    chan.write(file2, offset, 'a' * size)

        chan.close(file1)
        chan.close(file2)

    def test_allow_zero_byte_write(self):
        chan, tree = self.tree_connect()
        buffer = "0123456789012345678901"
        lock_offset = 8
        lock_size = 8
        locks = [(lock_offset, lock_size, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE

        # Create file, lock
        file1 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE).result()
       
        bytes_written = chan.write(file1, 0, buffer)
        self.assertEqual(bytes_written, len(buffer))

        chan.lock(file1, locks).result()

        # Open file again (with delete on close)
        file2 = chan.create(tree,
                            'lock.txt',
                            access=access,
                            share=share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE).result()

        chan.write(file2, lock_offset + 1, None)

        chan.close(file1)
        chan.close(file2)

def range_contains(a1, a2, b):
    return b >= a1 and b < a2

def ranges_intersect(a1, a2, b1, b2):
    return a2 > a1 and b2 > b1 and \
        (range_contains(a1, a2, b1) or range_contains(a1, a2, b2-1) or \
         range_contains(b1, b2, a1) or range_contains(b1, b2, a2-1))
            
