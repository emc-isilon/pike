#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        lease_test.py
#
# Abstract:
#
#       Lease break (upgrade-downgrade) tests with two create handle requests.
#	There are 8 combinations of leases, the script checks the creation
#	of first handle with all possible (valid and invalid) combinations,
#	which is followed by second create request with all possible combinations
#	of leases. The total test cases thus are 64.
#
# Authors: Abhilasha Bhardwaj (abhilasha.bhardwaj@calsoftinc.com)
#
import pike.smb2
import pike.test
import random
import array
import sys
import unittest
@pike.test.RequireDialect(pike.smb2.Dialect.DIALECT_SMB2_002)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class TestLease(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(TestLease, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | \
            pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh
        self.none = pike.smb2.SMB2_LEASE_NONE
        self.w = pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.h = pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.wh = self.w | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        # Define a lease list of all possible combinations
        lease_list = [self.none, self.r, self.w, self.h,
                       self.rw, self.rh, self.wh, self.rwh]
        # 64 elements of the list created using list comprehension logic.
        # For complete check on combinations of leases in two create requests,
        # for each distinct element in the list "handle1_lease", "handle2_lease"
        # checks it against each possible value of lease.
        temp_handle1_lease = []
        [temp_handle1_lease.extend([l_value]*8) for l_value in lease_list]
        # lease requested with first create request.
        self.handle1_lease = temp_handle1_lease
        # lease requested with second create request.
        self.handle2_lease = [l_value for l_value in lease_list]*8
        # expected lease in the first create. Lease is granted when it is valid lease,
        # i.e. one of none, R, RH, RW, RWH and rejected to NONE otherwise.
        self.handle1_lease_exp = [self.none, self.none, self.none, self.none,
                                  self.none, self.none, self.none, self.none,
                                  self.r, self.r, self.r, self.r,
                                  self.r, self.r, self.r, self.r,
                                  self.none, self.none, self.none, self.none,
                                  self.none, self.none, self.none, self.none,
                                  self.none, self.none, self.none, self.none,
                                  self.none, self.none, self.none, self.none,
                                  self.rw, self.rw, self.rw, self.rw,
                                  self.rw, self.rw, self.rw, self.rw,
                                  self.rh, self.rh, self.rh, self.rh,
                                  self.rh, self.rh, self.rh, self.rh,
                                  self.none, self.none, self.none, self.none,
                                  self.none, self.none, self.none, self.none,
                                  self.rwh, self.rwh, self.rwh, self.rwh,
                                  self.rwh, self.rwh, self.rwh, self.rwh]

        # expected lease in the second create. Lease is granted if it is a valid lease,
        # and also is an upgrade request on the previous lease granted with the same
        # lease key, i.e. handle1_lease_exp.
        self.handle2_lease_exp = [self.none, self.r, self.none, self.none,
                                  self.rw, self.rh, self.none, self.rwh,
                                  self.r, self.r, self.r, self.r,
                                  self.rw, self.rh, self.r, self.rwh,
                                  self.none, self.r, self.none, self.none,
                                  self.rw, self.rh, self.none, self.rwh,
                                  self.none, self.r, self.none, self.none,
                                  self.rw, self.rh, self.none, self.rwh,
                                  self.rw, self.rw, self.rw, self.rw,
                                  self.rw, self.rw, self.rw, self.rwh,
                                  self.rh, self.rh, self.rh, self.rh,
                                  self.rh, self.rh, self.rh, self.rwh,
                                  self.none, self.r, self.none, self.none,
                                  self.rw, self.rh, self.none, self.rwh,
                                  self.rwh, self.rwh, self.rwh, self.rwh,
                                  self.rwh, self.rwh, self.rwh, self.rwh]

    def test_lease_break(self):
        tc = 1   # tc is number of test cases
        pass_count, fail_count=0,0
        for i in range(0, 64):
            print "==========================================="
            print "TestCase {0} - Verify server response when Lease in \
first create is {1} and Lease in second Create is {2}\
".format(tc, self.handle1_lease[i], self.handle2_lease[i])
            chan, tree = self.tree_connect()
            lease = array.array('B', map(random.randint, [0]*16, [255]*16))
            try:
                print "\nCreate file with Lease bit set."
                print "Creating session and tree connect..."
                handle1 = chan.create(tree,
                            'SingleLeaseKey.txt',
                            share=self.share_all,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE,
                            lease_key=lease,
                            lease_state=self.handle1_lease[i]).result()
                print "File created."
            #Handle1 created
                print "HANDLE1: LEASE"
                print "Requested-", self.handle1_lease[i]
                print "Expected-", self.handle1_lease_exp[i]
                print "Obtained-", handle1.lease.lease_state
                try:
                    print "Validate Lease obtained in first create."
                    self.assertEqual(handle1.lease.lease_state,
                                     self.handle1_lease_exp[i])
                    print "Lease in first create validated."
                #HANDLE1: Lease granted
                except Exception as e:
                    # If lease is not granted then second create
                    # is skipped, and Test case is marked as Failed.
                    print "Validation of Lease in first create failed."
                    print "\nTest case has FAILED!\n"
                    fail_count = fail_count + 1
                    tc = tc + 1
                    chan.close(handle1)
                    continue
            except Exception as e:
                print "HANDLE1- Create failed, exiting...", str(e)
                sys.exit()
            try:
                print "-----------------------------------------------------"
                print "Create request on an existing file with lease bit set."
                print "Creating session and tree connect..."
                handle2 = chan.create(tree,
                            'SingleLeaseKey.txt',
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            disposition=pike.smb2.FILE_OPEN,
                            share=self.share_all,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            lease_key=lease,
                            lease_state=self.handle2_lease[i]).result()
                print "Create completed."
                print "HANDLE2: LEASE"
                print "Requested-", self.handle2_lease[i]
                print "Expected-", self.handle2_lease_exp[i]
                print "Obtained-", handle2.lease.lease_state
                print "HANDLE1: After Second create"
                print "Expected", self.handle2_lease_exp[i]
                print "Obtained", handle1.lease.lease_state
                #Handle2 created
                try:
                    print "Validate Lease obtained in second create."
                    self.assertEqual(handle2.lease.lease_state,
                                     self.handle2_lease_exp[i])
                    #HANDLE2- Lease granted
                    print "Lease in second create validated."
                    print "Validate Lease on first handle after second create."
                    self.assertEqual(handle1.lease.lease_state,
                                     self.handle2_lease_exp[i])
                    print "Final Lease on first create validated."
                    print "\nTest case has PASSED!\n"
                    pass_count = pass_count + 1
                except Exception:
                    print "\nTest case has FAILED!\n"
                    fail_count = fail_count + 1
                chan.close(handle2)
            #handle2 closed
                chan.close(handle1)
            #handle1 closed
                tc = tc + 1
            except Exception:
                print "HANDLE2 creation failed, exiting..."
                chan.close(handle1)
                sys.exit()
        print "\n\nTest cases passed:", pass_count
        print "Test cases failed:", fail_count
