#
# copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        oplock_lease_test.py
#
# Abstract:
#       Oplock break (downgrade) tests with two create handle requests,
#   the first Handle is created with different bits of OPLOCK set and
#   the second handle is created with SMB2_OPLOCK_LEVEL_LEASE.
#   There are 4 oplock bits, the script checks the creation of first 
#   handle with these combinations, which is then followed by 
#   second create request with all the 8 possible combinations of leases. 
#   The total test cases thus are 32.
#
# Author(s): Abhilasha Bhardwaj (abhilasha.bhardwaj@calsoftinc.com)
#
import pike.test
import random
import array
import pike.model
import sys

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class OplockLeaseTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(OplockLeaseTest, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE |\
            pike.smb2.FILE_SHARE_DELETE
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh
        self.none = pike.smb2.SMB2_LEASE_NONE
        self.w = pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.h = pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.wh = self.w | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        #Define oplocks
        self.oplock_exclusive = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
        self.oplock_level2 = pike.smb2.SMB2_OPLOCK_LEVEL_II
        self.oplock_none = pike.smb2.SMB2_OPLOCK_LEVEL_NONE
        self.oplock_batch = pike.smb2.SMB2_OPLOCK_LEVEL_BATCH
        # handle1_oplock - oplock used to create first handle
        oplock_list = [self.oplock_none, self.oplock_level2,
                       self.oplock_exclusive, self.oplock_batch]
        temp_handle1_oplock = []
        [temp_handle1_oplock.extend([o_value]*8) for o_value in oplock_list]
        self.handle1_oplock = temp_handle1_oplock
        # handle2_lease - Lease used to create second handle
        lease_list = [self.none, self.r, self.w, self.h,
                      self.rw, self.rh, self.wh, self.rwh]
        self.handle2_lease = [l_value for l_value in lease_list]*4
        # List of expected oplocks that should be granted for first handle
        # Oplock request type is valid and hence is granted for each 
        # request in handle1. Hence, requested = granted.
        # handle1_oplock = handle1_oplock_exp
        self.handle1_oplock_exp = self.handle1_oplock
        # list of expected lease that should be granted for second handle
        self.handle2_lease_exp = [
            self.none, self.r, self.none, self.none,
            self.r, self.rh, self.none, self.rh,
            self.none, self.r, self.none, self.none,
            self.r, self.r, self.none, self.r,
            self.none, self.r, self.none, self.none,
            self.r, self.r, self.none, self.r,
            self.none, self.r, self.none, self.none,
            self.r, self.r, self.none, self.r]
        # list of expected oplocks after break. Any exclusive right on the file
        # is revoked from first handle.
        self.handle1_oplock_break = [
            self.oplock_none, self.oplock_none, self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_none, self.oplock_none, self.oplock_none,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2,
            self.oplock_level2, self.oplock_level2, self.oplock_level2, self.oplock_level2]                                    

    def test_oplock_lease_break(self):
        tc = 1
        pass_count, fail_count=0, 0
        for i in range(0, 32):
            print "==========================================="
            print "TestCase {0} - Verify server response when Oplock in first create is {1} \
and Lease in second Create is {2}".format(tc, self.handle1_oplock[i], self.handle2_lease[i])
            print "==========================================="
            chan, tree = self.tree_connect()
            lease = array.array('B', map(random.randint, [0]*16, [255]*16))
            try:
                print "\nCreate a file with Oplock bit set."
                print "Creating session and tree connect..."
                handle1 = chan.create(tree,
                               'OplockLeaseTest.txt',
                               access=pike.smb2.FILE_READ_DATA |
                               pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                               share=self.share_all,
                               options=pike.smb2.FILE_DELETE_ON_CLOSE,
                               disposition=pike.smb2.FILE_SUPERSEDE,
                               oplock_level=self.handle1_oplock[i]).result()
                print "File created."
                print "HANDLE1: OPLOCK BEFORE BREAK:"
                print "Requested-", self.handle1_oplock[i]
                print "Expected-", self.handle1_oplock_exp[i]
                print "Obtained-", handle1.oplock_level
                if handle1.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE or\
                   handle1.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_BATCH:
                   handle1.on_oplock_break(lambda level: level)
                #print "Handle1 created"
                try:
                    print "Validate Oplock obtained on first handle."
                    self.assertEqual(handle1.oplock_level,
                                     self.handle1_oplock_exp[i])
                    print "Oplock on first handle validated."
                    #print "HANDLE1- Oplock granted"
                except Exception as e:
                    print "Validation on oplock on first handle failed", str(e)
                    print "\n Test case failed."
                    fail_count = fail_count + 1
                    tc = tc + 1
                    chan.close(handle1)
                    continue
            except Exception as e:
                print "HANDLE1- Create failed.", str(e)
                sys.exit()
            try:
                print "--------------------------------------------------------"
                print "Second create request on existing file with Lease bit set."
                print "Creating session and tree connect..."
                handle2 = chan.create(tree,
                               'OplockLeaseTest.txt',
                               share=self.share_all,
                               oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                               disposition=pike.smb2.FILE_OPEN,
                               access=pike.smb2.FILE_READ_DATA |
                               pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                               lease_key=lease,
                               lease_state=self.handle2_lease[i]).result()
                print "Create request completed."
                #Handle2 created
                print "HANDLE2: LEASE"
                print "Requested-", self.handle2_lease[i]
                print "Eexpected-", self.handle2_lease_exp[i]
                print "Obtained-", handle2.lease.lease_state
                # Check Handle1 state after oplock_break is done
                print "HANDLE1: OPLOCK FINAL STATE:"
                print "Expected-", self.handle1_oplock_break[i]
                print "Obtained-", handle1.oplock_level
                try:
                    print "Validate Oplock on first handle after second create request."
                    self.assertEqual(handle1.oplock_level,
                                     self.handle1_oplock_break[i])
                    print "Oplock final state validated."
                except Exception as e:
                    print "\nOplock Break Failed. Validation failed.", str(e)
                try:
                    print "Validate Lease obtained in second create request."
                    self.assertEqual(handle2.lease.lease_state,
                                     self.handle2_lease_exp[i])
                    print "Lease in second create request validated."
                    print "\nTest case has PASSED!"
                    pass_count = pass_count + 1
                except Exception as e:
                    print "\nValidation of Lease n second create failed. Test case FAILED!", str(e)
                    fail_count = fail_count + 1
                chan.close(handle2)
            #"handle2 closed"
                chan.close(handle1)
            #"handle1 closed"
                tc = tc + 1
            except Exception as e:
                print "HANDLE2- Create failed", str(e)
                chan.close(handle1)
                sys.exit()
        print "\n\nTest cases passed:", pass_count
        print "Test cases failed:", fail_count
