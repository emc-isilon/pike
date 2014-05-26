#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        multiple_lease_key_test.py
#
# Abstract:
#
#        Multiple Lease key tests. Lease break tests with two create 
#   handle requests using two different lease keys. 
#   Create first handle with Lease bit set and with all possible 
#   combinations. Create second handle with a different lease
#   key and with all the 8 possible combinations of leases.
#   The total test cases thus are 64.
#
# Authors: Abhilasha Bhardwaj (abhilasha.bhardwaj@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.test
import random
import array
import sys

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class LeaseTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(LeaseTest, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        self.lease1 = array.array('B',map(random.randint, [0]*16, [255]*16))
        self.lease2 = array.array('B',map(random.randint, [0]*16, [255]*16))
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
        # handle1 lease expected before break. The lease is granted when it is valid lease,
        # i.e. one of none, R, RH, RW, RWH and rejected to NONE otherwise.
        self.handle1_lease_exp = [ self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                   self.r, self.r, self.r, self.r, self.r, self.r, self.r, self.r,
                                   self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                   self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                   self.rw, self.rw, self.rw, self.rw, self.rw, self.rw, self.rw, self.rw,
                                   self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh,
                                   self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                   self.rwh, self.rwh, self.rwh, self.rwh, self.rwh, self.rwh, self.rwh, self.rwh]
        # handle1 lease expected after lease break. After break, exclusive access (RW or RWH) is denied to 
        # any client.
        self.handle1_lease_break_exp = [self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                        self.r, self.r, self.r, self.r, self.r, self.r, self.r, self.r,
                                        self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                        self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                        self.r, self.r, self.r, self.r, self.r, self.r, self.r, self.r,
                                        self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh,
                                        self.none, self.none, self.none, self.none, self.none, self.none, self.none, self.none,
                                        self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh, self.rh]
        # handle2 lease expected. This lease request results in breaking the first client's exclusive access 
        # on the file already opened in Handle1.
        self.handle2_lease_exp = [self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,
                                  self.none, self.r, self.none, self.none, self.r, self.rh, self.none, self.rh,]

    def test_lease_upgrade_break(self):
        chan, tree = self.tree_connect()
        tc = 1
        pass_count, fail_count = 0, 0
        for i in range(0, 64):
            print "\n==========================================="
            print "TestCase {0} - Verify server response when Lease in \
first create is {1} and Lease in second Create is {2}\
".format((i+1), self.handle1_lease[i], self.handle2_lease[i])
            try:
                print "Create file with lease bit set"
                print "Creating session and tree connect..."
                handle1 = chan.create(tree,
                                      'MultipleLeaseKey.txt',
                                      share=self.share_all,
                                      access=pike.smb2.GENERIC_READ |
                                      pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,                              
                                      oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                      disposition=pike.smb2.FILE_SUPERSEDE,
                                      options=pike.smb2.FILE_DELETE_ON_CLOSE,
                                      lease_key = self.lease1,
                                      lease_state = self.handle1_lease[i]).result()
                print "File created."
                print "\nHANDLE1: LEASE BEFORE BREAK:"
                print "Requested-", self.handle1_lease[i]
                print "Expected-", self.handle1_lease_exp[i]
                print "Obtained-", handle1.lease.lease_state
                try:
                    print "validate lease obtained in first create."
                    self.assertEqual(self.handle1_lease_exp[i], handle1.lease.lease_state) 
                    print "Lease in first create validated."
                except Exception as e:
                    print "Lease in first create validation failed."
                    print "HANDLE1- Test case FAILED", str(e)
                    fail_count = fail_count + 1
                    tc = tc + 1
                    chan.close(handle1)
                    continue
                handle1.lease.on_break(lambda state: state)
            except Exception as e:
                print "HANDLE1- Create failed.", str(e)
                chan.close(handle1)
                sys.exit()            
        # Break our lease
            try:
                print "Second Create Request on existing file with different lease key."
                print "Creating session and tree connect..."
                handle2 = chan.create(tree,
                                      'MultipleLeaseKey.txt',
                                      share=self.share_all,
                                      disposition=pike.smb2.FILE_OPEN,
                                      access=pike.smb2.GENERIC_READ |
                                      pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,                              
                                      oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                      lease_key = self.lease2,
                                      lease_state = self.handle2_lease[i]).result()
                print "Second create request completed."
                print "HANDLE2: LEASE"
                print "Requested-", self.handle2_lease[i]
                print "Eexpected-", self.handle2_lease_exp[i]
                print "Obtained-", handle2.lease.lease_state
                # Check Handle1 state after lease_break is done
                print "HANDLE1: LEASE FINAL STATE:"
                print "Expected-", self.handle1_lease_break_exp[i]
                print "Obtained-", handle1.lease.lease_state
                try:
                    print "Validate Lease obtained in second create."
                    self.assertEqual(self.handle2_lease_exp[i], handle2.lease.lease_state)
                    print "Lease in second create validated."
                except Exception as e:
                    print "Lease in second create validation failed.", str(e)
                    print "\nTest case has failed."
                    fail_count = fail_count + 1
                    tc = tc + 1                    
                try:
                    print "Validate first Lease state after second create request."
                    self.assertEqual(self.handle1_lease_break_exp[i], handle1.lease.lease_state)
                    print "Lease state on First handle after second create request validated."
                    print "\nTest case has passed!"
                    pass_count = pass_count + 1
                except Exception as e:
                    print "HANDLE1- Lease validation after second create failed", str(e)
                    print "\nTest case has failed."
                    fail_count = fail_count + 1
                    tc = tc + 1
                chan.close(handle2)
                chan.close(handle1)                
            except Exception as e:
                print "HANDLE2- Create Failed.", str(e)
                chan.close(handle1)
                sys.exit()
        print "\n\nTest cases passed:", pass_count
        print "Test cases failed:", fail_count            
