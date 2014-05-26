#
# copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        lease_desired_access.py
#
# Abstract:
#
#        Valid combinations of Lease(5) combined with Desired Access
# values used in single create request. For each Valid bit of Lease,
# different bits of "desired access" is tried, and handle
# creation is checked. There are 45 test cases.
#
# Author(s): Abhilasha Bhardwaj (abhilasha.bhardwaj@calsoftinc.com)
#
import pike.smb2
import pike.test
import random
import array
import sys

@pike.test.RequireDialect(0x210)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LEASING)
class TestLease(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(TestLease, self).__init__(*args, **kwargs)
        self.share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE\
            | pike.smb2.FILE_SHARE_DELETE
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh
        self.none = pike.smb2.SMB2_LEASE_NONE
        # Desired accesses
        self.read_a = pike.smb2.FILE_READ_DATA
        self.write_a = pike.smb2.FILE_WRITE_DATA
        self.delete_a = pike.smb2.DELETE
        self.append_a = pike.smb2.FILE_APPEND_DATA
        self.generic_read_a = pike.smb2.GENERIC_READ
        self.generic_write_a = pike.smb2.GENERIC_WRITE
        self.generic_execute_a = pike.smb2.GENERIC_EXECUTE
        self.generic_all_a = pike.smb2.GENERIC_ALL
        self.max_allowed_a = pike.smb2.MAXIMUM_ALLOWED
        # Define a lease list of valid combinations
        self.lease_list = [self.none, self.r, self.rw, self.rh, self.rwh]
        # Define a list of desired access.
        self.access_list = [self.read_a, self.write_a, self.delete_a,
                            self.append_a, self.generic_read_a,
                            self.generic_write_a, self.generic_execute_a,
                            self.generic_all_a, self.max_allowed_a]
        self.tc = 1
        self.num = 1
        self.fail_count, self.pass_count = 0, 0

    def test_lease(self):
        for lease_req in self.lease_list:
            for desired_access in self.access_list:
                print "==============================================="
                print "TestCase {0} - Verify server response when {1} Lease \
is requested with {2} Desired Access".format(self.tc, lease_req, desired_access)
                lease = array.array('B', map(random.randint, [0]*16, [255]*16))
                self.lease_file(lease_req, desired_access, lease, self.num)
                self.tc = self.tc + 1
                self.num = self.num + 1
        print "\n\nTest cases passed:", self.pass_count
        print "Test cases failed:", self.fail_count

    def lease_file(self, lease_req, desired_access, lease, num):
        chan, tree = self.tree_connect()
        try:
            print "\nCreate a file with Lease bit set."
            print "Creating session and tree connect..."
            handle1 = chan.create(tree,
                              'lease_' + str(num) + '.txt',
                              share=self.share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                              access=desired_access,
                              disposition=pike.smb2.FILE_SUPERSEDE,
                              lease_key=lease,
                              lease_state=lease_req).result()
            print "File created."
            print "\nLease requested", lease_req
            print "Lease obtained", handle1.lease.lease_state
            try:
                print "\nValidate lease obtained on the file."
                self.assertEqual(handle1.lease.lease_state, lease_req)
                print "Lease granted. Validation successfully done."
                print "\nTest Case has PASSED!"
                self.pass_count = self.pass_count + 1
            except Exception as e:
                print "Lease Rejected", str(e)
                print "\nTest Case has FAILED"
                self.fail_count = self.fail_count + 1
        except Exception as e:
            print "HANDLE- Handle creation failed, exiting...", str(e)
            sys.exit()
            chan.close(handle1)
            print "File closed after test case failed."
            #handle1 closed
