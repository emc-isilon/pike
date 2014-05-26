#
# copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        lease_oplock_test.py
#
# Abstract:
#
#        Lease and oplock combination tests. 
#   Lease break (downgrade) tests with two create handle requests,
#   the first Handle is created with different bits of LEASES set and
#   the second handle is created with different bits of Oplock. 
#   There are total 3 Lease bits, the script checks the creation 
#   of first handle with the total 8 combinations of these bits, 
#   which is then followed by a second create request with the 
#   4 different Oplock levels. 
#   There are two functions in the script. 
#   test_lease_break:
#   Total test cases using this function are 32.
#   test_lease_break_no_handle_lease:
#   Total test cases using this function are 32. These test cases 
#   check for  lease break after voluntarily giving up Handle Lease 
#   obtained in the first create request. 
#
# Authors: Abhilasha Bhardwaj
#
import pike.test
import random
import array
import sys

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class LeaseTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(LeaseTest, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ |\
            pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
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
        # Lease used to create first handle
        lease_list = [self.none, self.r, self.w, self.h, self.rw, self.rh,
                      self.wh, self.rwh]
        temp_handle1_lease = []
        [temp_handle1_lease.extend([l_value] * 4) for l_value in lease_list]
        self.handle1_lease = temp_handle1_lease
        # oplock used to create second handle
        oplock_list = [self.oplock_none, self.oplock_level2,
                       self.oplock_exclusive, self.oplock_batch]
        self.handle2_oplock = [op_value for op_value in oplock_list]*8
        # expected lease granted for first handle. Valid lease requests are granted.
        self.handle1_lease_exp = [
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r,
            self.none, self.none, self.none, self.none,
            self.none, self.none, self.none, self.none,
            self.rw, self.rw, self.rw, self.rw,
            self.rh, self.rh, self.rh, self.rh,
            self.none, self.none, self.none, self.none,
            self.rwh, self.rwh, self.rwh, self.rwh]
        # expected lease after lease break. Exclusive lease is revoked and downgraded
        # to shared lease by the server on recieving a create on the same file.
        # Break is called on exclusive leases: RW and RWH.
        self.handle1_exp_break = [
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r,
            self.none, self.none, self.none, self.none,
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r,
            self.rh, self.rh, self.rh, self.rh,
            self.none, self.none, self.none, self.none,
            self.rh, self.rh, self.rh, self.rh]
        # expected lease after lease break - voluntarily giving up handle caching.
        # this impacts the exclusive lease : RWH in particular. RH and LEVEL2 oplock
        # can't co-exist. So, on volutarily giving up Handle Caching, the lease on
        # first handle is downgraded to R and a LEVEL2 oplock is successfully granted
        # in second create as opposed to when Handle lease is not given up and
        # OPLOCK_LEVEL_NONE is granted for every OPLOCK Request in second create. 
        self.handle1_exp_break_no_handle = [
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r,
            self.none, self.none, self.none, self.none,
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r,
            self.rh, self.rh, self.rh, self.rh,
            self.none, self.none, self.none, self.none,
            self.r, self.r, self.r, self.r]
        # expected oplocks granted for second handle
        self.handle2_oplock_exp = [
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_none]
        # expected oplock when Handle Lease is given up
        self.handle2_oplock_exp_no_handle_lease = [
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_none,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2,
            self.oplock_none, self.oplock_level2,
            self.oplock_level2, self.oplock_level2]

        LeaseTest.tc = 1
        LeaseTest.pass_count, LeaseTest.fail_count =  0, 0
 
    def test_lease_break(self):
        for i in range(0, 32):
            print "==========================================="
            print "TestCase {0} - Verify server response when Lease \
requested in first create is {1} and Oplock requested in second Create is \
{2}".format(LeaseTest.tc, self.handle1_lease[i], self.handle2_oplock[i])
            chan, tree = self.tree_connect()
            lease = array.array('B', map(random.randint, [0]*16, [255]*16))
            try:
                print "\nCreate file with Lease bit set."
                print "Creating session and tree connect..."
                handle1 = chan.create(tree,
                            'LeaseOplockTest.txt',
                            share=self.share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE, 
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            lease_key=lease,
                            lease_state=self.handle1_lease[i]).result()
                print "File created."
                #Handle1 created
                print "HANDLE1: LEASE"
                print "Requested-", self.handle1_lease[i]
                print "Expected-", self.handle1_lease_exp[i]
                print "Obtained-", handle1.lease.lease_state
                # Break the Lease obtained when second Create request comes.
                #handle1.lease.on_break(lambda state: state)
                handle1.lease.on_break(lambda state: state)
                try:
                    print "\nValidate Lease obtained through first create."
                    self.assertEqual(handle1.lease.lease_state,
                                     self.handle1_lease_exp[i])
                    print "Lease in first create validated."
                #HANDLE1: Lease granted
                except Exception as e:
                    print "Lease validation in first create failed."
                    print "HANDLE1- Test case FAILED", str(e)
                    LeaseTest.tc = LeaseTest.tc + 1
                    LeaseTest.fail_count = LeaseTest.fail_count + 1
                    chan.close(handle1)
                    continue
            except Exception as e:
                print "HANDLE1- Create failed.", str(e)
                sys.exit()
            try:
                print "-------------------------------------------"
                print "Second Create request on the existing file with oplock."
                print "Creating session and tree connect..."
                handle2 = chan.create(tree,
                            'LeaseOplockTest.txt',
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            share=self.share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            oplock_level=self.handle2_oplock[i]).result()
                print "Create request completed"
                print "HANDLE2: OPLOCK"
                print "Requested-", self.handle2_oplock[i]
                print "Expected-", self.handle2_oplock_exp[i]
                print "Obtained-", handle2.oplock_level
                print "\nHANDLE1: LEASE obtained after break", handle1.lease.lease_state
                #"Handle2 created"
                try:
                    print "\nValidate Oplock obtained through second create."
                    self.assertEqual(handle2.oplock_level,
                                     self.handle2_oplock_exp[i])
                    print "Oplock in second create validated."
                    #print "HANDLE2- Oplock granted"
                    print "Validate Lease state on first handle, after second create"
                    self.assertEqual(handle1.lease.lease_state,
                                     self.handle1_exp_break[i])
                    print "Lease on first handle, after recieving second create validated."
                    print "\nTest case has PASSED!"
                    LeaseTest.pass_count = LeaseTest.pass_count + 1
                except Exception as e:
                    print "Validation failed."
                    print "\nTest case has FAILED!", str(e)
                    LeaseTest.fail_count = LeaseTest.fail_count + 1
                chan.close(handle2)
            #"handle2 closed"
                chan.close(handle1)
            #"handle1 closed"
                LeaseTest.tc = LeaseTest.tc + 1
            except Exception:
                print "HANDLE2 creation failed"
                chan.close(handle1)
                sys.exit()

    def test_lease_break_no_handle_lease(self):
        print "\n\n==========================================="
        print "TESTS GIVING UP HANDLE LEASE VOLUNTARILY"
        for i in range(0, 32):
            print "==========================================="
            print "TestCase {0} - Verify server response when Lease \
requested in first create is {1} and Oplock requested in second Create is \
{2}".format(LeaseTest.tc, self.handle1_lease[i], self.handle2_oplock[i])
            chan, tree = self.tree_connect()
            lease = array.array('B', map(random.randint, [0]*16, [255]*16))
            try:
                print "\nCreate file with Lease bit set."
                print "Creating session and tree connect..."
                handle1 = chan.create(tree,
                            'LeaseOplockTest.txt',
                            share=self.share_all,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_DELETE_ON_CLOSE,
                            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            lease_key=lease,
                            lease_state=self.handle1_lease[i]).result()
                print "File created."
                #Handle1 created
                print "\nHANDLE1: LEASE"
                print "Requested-", self.handle1_lease[i]
                print "Expected-", self.handle1_lease_exp[i]
                print "Obtained-", handle1.lease.lease_state
                # voluntarily give up Handle caching
                handle1.lease.on_break(lambda state: state &
                                       ~pike.smb2.SMB2_LEASE_HANDLE_CACHING)
                try:
                    print "\nValidate Lease obtained through first create."
                    self.assertEqual(handle1.lease.lease_state,
                                     self.handle1_lease_exp[i])
                    print "Lease in first create validated."
                #HANDLE1: Lease granted
                except Exception as e:
                    print "Validation failed."
                    print "HANDLE1- Test case FAILED", str(e)
                    LeaseTest.tc = LeaseTest.tc + 1
                    LeaseTest.fail_count = LeaseTest.fail_count + 1
                    chan.close(handle1)
                    continue
            except Exception as e:
                print "HANDLE1- Create failed.", str(e)
                sys.exit()
            try:
                print "\n----------------------------------------------"
                print "Second Create request on the existing file with oplock."
                print "Creating session and tree connect..."
                handle2 = chan.create(tree,
                            'LeaseOplockTest.txt',
                            access=pike.smb2.GENERIC_READ |
                            pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
                            share=self.share_all,
                            disposition=pike.smb2.FILE_OPEN,
                            oplock_level=self.handle2_oplock[i]).result()
                print "Create request completed."
                print "HANDLE2: OPLOCK"
                print "Requested-", self.handle2_oplock[i]
                print "Expected-", self.handle2_oplock_exp_no_handle_lease[i]
                print "Obtained-", handle2.oplock_level
                print "\nHANDLE1: LEASE obtained after break", handle1.lease.lease_state
                #print "Handle2 create
                try:
                    print "\nValidate Oplock obtained through second create."
                    self.assertEqual(handle2.oplock_level,
                         self.handle2_oplock_exp_no_handle_lease[i])
                    print "Oplock in second create validated."
                    print "Validate Lease state on first handle after second create"
                    self.assertEqual(handle1.lease.lease_state,
                         self.handle1_exp_break_no_handle[i])
                #print "HANDLE2- Lease granted"
                    print "Lease on first handle after recieving second create validated."
                    print "\nTest case has PASSED!"
                    LeaseTest.pass_count = LeaseTest.pass_count + 1
                except Exception as e:
                    print "Validation failed."
                    print "\nTest case FAILED!" , str(e)
                    LeaseTest.fail_count = LeaseTest.fail_count + 1
                chan.close(handle2)
                #"handle2 closed"
                chan.close(handle1)
                #"handle1 closed"
                LeaseTest.tc = LeaseTest.tc + 1
            except Exception:
                print "HANDLE2 creation failed"
                chan.close(handle1)
                sys.exit()
        print "\n\nTest cases passed:", LeaseTest.pass_count
        print "Test cases failed:", LeaseTest.fail_count
