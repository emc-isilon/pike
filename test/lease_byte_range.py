#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        lease_byte_range.py
#
# Abstract:
#
#        byte range lock tests combined with all lease types.
#
# Authors: Dhanashree Patil, Calsoft (dhanashree.patil@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.test
import array
import random
import time

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class LockLeaseTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(LockLeaseTest, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        self.lease = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.lease2 = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh
        self.none = pike.smb2.SMB2_LEASE_NONE
        self.lock_list = [[(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)],[(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)],[(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK|pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)],[(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK|pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)],[(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]]
        self.lease_list = [self.none, self.r, self.rw, self.rh, self.rwh]

    def test_leasewithbyterange(self):
        i = 1
        num = 1
        for lease_req in self.lease_list:
            for byte_range_lock in self.lock_list:
                print "==============================================="
                print "TestCase", i
                self.lease_byterange(lease_req,byte_range_lock,num )
                i = i+1
                num = num+1

    def lease_byterange(self,lease_req,byte_range_lock,num):
        try:
            print "Setting up the session and tree connect."
            chan, tree = self.tree_connect()
            print "Session set up and tree connect successful."
            buffer = "0123456789012345678901"
            print "Creating a file."
            file1 = chan.create(tree,
                           'lock.txt',
                            access = pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                            share = self.share_all,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            lease_key = self.lease,
                            lease_state = lease_req).result()
            print "File created successfully."
            print "Lease requested : " ,lease_req
            print "Byte range lock requested : ",byte_range_lock
            if "SMB2_LOCKFLAG_UN_LOCK" in str(byte_range_lock):
                expected_result = "STATUS_RANGE_NOT_LOCKED"
            else:
                expected_result = "STATUS_SUCCESS"
            print "Writing into the file."
            bytes_written = chan.write(file1,
                                   0,
                                   buffer)
            print "File write completed."
            print "Verify write operation."
            self.assertEqual(bytes_written, len(buffer))
            print "Write operation verified successfully."
            print "Apply byte range lock on the file."
            returnval = chan.lock(file1, byte_range_lock).result()
            actual_result = returnval.status
            print "Byte range lock applied succesfully."
            print "Closing file handle."
            chan.close(file1)
            print "File handle closed."
        except Exception as e:
            if isinstance(file1, pike.model.Open):
                chan.close(file1)
            actual_result = str(e)
        finally:
            print "Expected result : ",expected_result
            print "Actual result : ",actual_result
            if expected_result in str(actual_result):
                print "test case passed."
            else:
                print "test case failed."

