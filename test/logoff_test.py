#
# copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        logoff_test.py
#
# Abstract:
#
#        SMB2_LOGOFF command tests
#
# Author(s): Lingaraj Gowdar (lingaraj.gowdar@calsoftinc.com)
#
import pike.model
import pike.smb2
import pike.test
import utils
import array
import random


class LogoffTest(pike.test.PikeTest):
    def test_01_valid_inputs(self):
        """
        Logoff session using valid parameters. Test case should PASS successfully with valid inputs.
        """
        try:
            print "\n------------------LOGOFF_TEST01-------------------------------------"
            print "TC 01 - Testing SMB2_LOGOFF with valid inputs"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan, structure_size=4, reserved=0)
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 01 Passed"

    def test_02_invalid_structureSize(self):
        """
        Logoff session with structure size less than valid structure size. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST02-------------------------------------"
            print "TC 02 - Testing SMB2_LOGOFF for structureSize less than valid structureSize"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan, structure_size=2, reserved=0)
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Unexpected success. Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 02 Passed"

    def test_03_invalid_structureSize(self):
        """
        Logoff session with structure size greater than valid structure size. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST03-------------------------------------"
            print "TC 03 - Testing SMB2_LOGOFF for structureSize greater than valid structureSize"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan, structure_size=95, reserved=0)
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Unexpected success. Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 03 Passed"

    def test_04_invalid_reserved_value(self):
        """
        Logoff session with reserved value greater than ZERO. Test case should PASS as reserved value is ignored by server.
        """
        try:
            print "\n------------------LOGOFF_TEST04-------------------------------------"
            print "TC 04 - Testing SMB2_LOGOFF for reserved value greater than zero."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan, structure_size=4, reserved=10)
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 04 Passed"

    def test_05_consecutive_logoff_requests(self):
        """
        Logoff the session. Send second logoff request using the same session id. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST05-------------------------------------"
            print "TC 05 - Testing SMB2_LOGOFF for consecutive logoff requests."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending first Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res1 = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending second Logoff request..."
            logoff_req2 = conv_obj.logoff(chan)
            res2 = conv_obj.transceive(chan, logoff_req2)
            actual_status = str(res2[0].status)
            print "Unexpected success. Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 05 Passed"

    def test_06_closing_file_handle(self):
        """
        Create file and logoff the session. Send close request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        close request completes successfully, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST06-------------------------------------"
            print "TC 06 - Testing SMB2_LOGOFF followed by closing file handle."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST06 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST06").result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Closing file handle"
            close_res = chan.close(file_handle)
            actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File handle closed successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 06 Passed"

    def test_07_create_open_request(self):
        """
        Create file and logoff the session. Send create open request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        file is opened successfully, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST07-------------------------------------"
            print "TC 07 - Create file LOGOFF_TEST07 and Logoff the session. Send create open request for LOGOFF_TEST07 file."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST07 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST07").result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending create Open request on the file LOGOFF_TEST07"
            file_handle2 = chan.create(tree, "LOGOFF_TEST07", disposition=pike.smb2.FILE_OPEN).result()
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File LOGOFF_TEST07 opened."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 07 Passed"

    def test_08_read_request(self):
        """
        Create file and logoff the session. Send read request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        data is read successfully from the file, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST08-------------------------------------"
            print "TC 08 - Create file LOGOFF_TEST08 and Logoff the session. Send read request on the LOGOFF_TEST08 file."
            buffer = "testing123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST08 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST08").result()
            print "File created."
            print "Sending write request..."
            bytes_written = chan.write(file_handle, 0, buffer)
            if bytes_written == len(buffer):
                print "Written data onto the file"
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending read request..."
            conv_obj = utils.Convenience()
            read_packet = conv_obj.read(chan, file_handle)
            read_res = conv_obj.transceive(chan, read_packet)
            actual_status = str(read_res[0].status)
            print "Unexpected success. Successfully read data from the file"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 08 Passed"

    def test_09_write_request(self):
        """
        Create file and logoff the session. Send write request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        write is successful, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST09-------------------------------------"
            print "TC 09 - Create file LOGOFF_TEST09 and Logoff the session. Send write request on the LOGOFF_TEST09 file."
            buffer = "testing123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST09 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST09").result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending write request..."
            bytes_written = chan.write(file_handle, 0, buffer)
            actual_status = "STATUS_SUCCESS"
            print "Unexpected success. Written data onto the file"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 09 Passed"

    def test_10_tree_connect_request(self):
        """
        Logoff the session. Send tree connect request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        tree connection is successful, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST10-------------------------------------"
            print "TC 10 - Testing LOGOFF followed by tree connect request for the previous session."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending tree connect request..."
            tree_res = chan.tree_connect(self.share)
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. Tree connection successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 10 Passed"

    def test_11_tree_disconnect_request(self):
        """
        Logoff the session. Send tree disconnect request using the same session id. Test case should FAIL.
        Since test case is expected to fail, the actual status is set to STATUS_SUCCESS in the test case if the
        tree disconnection is successful, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST11-------------------------------------"
            print "TC 11 - Testing LOGOFF followed by tree disconnect request for the previous session."
            buffer = "testing 123"
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Tree connection successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending tree disconnect request..."
            tree_discon_res = chan.tree_disconnect(tree)
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. Tree disconnect successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 11 Passed"

    def test_12_query_file_info_request(self):
        """
        Create file and logoff the session. Send query file info request using the same session id. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST12-------------------------------------"
            print "TC 12 - Testing LOGOFF followed by query file info request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Tree connection successful."
            print "Create a file LOGOFF_TEST12 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST12").result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Querying file info on LOGOFF_TEST12 file"
            info = chan.query_file_info(file_handle, pike.smb2.FILE_ALL_INFORMATION)
            actual_status = str(info.status)
            print "Unexpected success. Query file info on LOGOFF_TEST12 done."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 12 Passed"

    def test_13_durable_open(self):
        """
        Create file with RWH lease and durable set, logoff the session. Using same session, send create open request.
        Create open should fail as the session was already logged off. Since test case is expected to fail, the actual
        status is set to STATUS_SUCCESS in the test case if the file is opened successfully, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST13-------------------------------------"
            print "TC 13 - Create file LOGOFF_TEST13 with durable set and Logoff the session.\
 Send create open request on LOGOFF_TEST13 file."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST13 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan, tree, "LOGOFF_TEST13",
                                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        lease_key=lease1,
                                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING,
                                                        durable=True)
            file_handle = create_tmp1.result()
            create_result = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending create Open request on the file LOGOFF_TEST13..."
            file_handle2 = chan.create(tree, "LOGOFF_TEST13",
                                       access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                       share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                       disposition=pike.smb2.FILE_OPEN).result()
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File open successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 13 Passed"

    def test_14_invalid_session_id(self):
        """
        Logoff session using invalid session ID. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST14-------------------------------------"
            print "TC 14 - Testing SMB2_LOGOFF with invalid session id."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            logoff_req[0].session_id = 1234561234567
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Unexpected success. Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 14 Passed"

    def test_15_invalid_tree_id(self):
        """
        Logoff session using invalid tree ID. Test case should PASS.
        """
        try:
            print "\n------------------LOGOFF_TEST15-------------------------------------"
            print "TC 15 - Testing SMB2_LOGOFF with invalid tree id."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            logoff_req[0].tree_id = 123324124
            res = conv_obj.transceive(chan, logoff_req)
            actual_status = str(res[0].status)
            print "Session logged off successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 15 Passed"

    def test_16_shared_lock(self):
        """
        Create file, Lock file with SHARED_LOCK and logoff the session.
        With new session, send create open request,try to lock with EXCLUSIVE_LOCK on same locked
        byte ranges. Second lock should be granted as there were no locks on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST16-------------------------------------"
            print "TC 16 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK and Logoff the session.\
 With new session try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST16 for testing"
            file_handle1 = chan1.create(tree, "LOGOFF_TEST16").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST16 for testing"
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST16", disposition=pike.smb2.FILE_OPEN).result()
            print "File LOGOFF_TEST16 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with exclusive lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 16 Passed"

    def test_17_exclusive_lock(self):
        """
        Create file, Lock file with EXCLUSIVE_LOCK and logoff the session.
        With new session, send create open request,try to lock with EXCLUSIVE_LOCK on same locked
        byte ranges. Second lock should be granted as there were no locks on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST17-------------------------------------"
            print "TC 17 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and Logoff the session.\
 With new session try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST17 for testing"
            file_handle1 = chan1.create(tree, "LOGOFF_TEST17").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with exclusive lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST17 for testing"
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST17", disposition=pike.smb2.FILE_OPEN).result()
            print "File LOGOFF_TEST17 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with exclusive lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 17 Passed"

    def test_18_shared_lock(self):
        """
        Create file, Lock file with SHARED_LOCK|FAIL_IMMEDIATELY and logoff the session.
        With new session, send create open request,try to lock with EXCLUSIVE_LOCK on same locked
        byte ranges. Second lock should be granted as there were no locks on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST18-------------------------------------"
            print "TC 18 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and Logoff the session.\
 With new session try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST18 for testing"
            file_handle1 = chan1.create(tree, "LOGOFF_TEST18").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST18 for testing"
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST18", disposition=pike.smb2.FILE_OPEN).result()
            print "File LOGOFF_TEST18 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with exclusive lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 18 Passed"

    def test_19_exclusive_lock(self):
        """
        Create file, Lock file with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY and logoff the session.
        With new session, send create open request,try to lock with EXCLUSIVE_LOCK on same locked
        byte ranges. Second lock should be granted as there were no locks on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST19-------------------------------------"
            print "TC 19 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and Logoff the session.\
 With new session try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST19 for testing"
            file_handle1 = chan1.create(tree, "LOGOFF_TEST19").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with exclusive lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST18 for testing"
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST18", disposition=pike.smb2.FILE_OPEN).result()
            print "File LOGOFF_TEST18 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with exclusive lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 19 Passed"

    def test_20_unlock(self):
        """
        Create file, Lock file with EXCLUSIVE_LOCK and logoff the session. With new session, send create open request,
        try to unlock the locked byte ranges. Second lock should fail as currently there is no lock on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST20-------------------------------------"
            print "TC 20 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and Logoff the session.\
 With new session try to unlock same byte ranges."
            expected_status = "STATUS_RANGE_NOT_LOCKED"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST20 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST20").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK..."
            lock_res1 = chan.lock(file_handle, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST18 for testing"
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST20", disposition=pike.smb2.FILE_OPEN).result()
            print "File LOGOFF_TEST20 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_UN_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "Unexpected success. Unlocked requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 20 Passed"

    def test_21_unlock(self):
        """
        Create file, Lock file with SHARED_LOCK and logoff the session. Try to unlock file on same locked
        byte ranges using the same session. Unlock should fail as the session is not present.
        """
        try:
            print "\n------------------LOGOFF_TEST21-------------------------------------"
            print "TC 21 - Lock file LOGOFF_TEST21 with SMB2_LOCKFLAG_SHARED_LOCK and Logoff the session.\
 Send unlock request on same byte ranges."
            expected_status = "STATUS_FILE_CLOSED"
            locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
            locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST21 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST21").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK..."
            lock_res1 = chan.lock(file_handle, locks1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending Lock request with SMB2_LOCKFLAG_UN_LOCK flag..."
            lock_res2 = chan.lock(file_handle, locks2).result()
            actual_status = str(lock_res2.status)
            print "Unexpected success. Unlocked requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 21 Passed"

    def test_22_oplock_level_none(self):
        """
        Create file with oplock NONE, logoff the session. With new session, send create open request with EXCLUSIVE oplock.
        EXCLUSIVE oplock should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST22-------------------------------------"
            print "TC 22 - Create file LOGOFF_TEST22 with SMB2_OPLOCK_LEVEL_NONE and send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST22 for testing"
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST22",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_NONE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST22 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST22",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 22 Passed"

    def test_23_oplock_level_2(self):
        """
        Create file with LEVEL_II oplock, logoff the session. With new session, send create open request with EXCLUSIVE oplock.
        EXCLUSIVE oplock should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST23-------------------------------------"
            print "TC 23 - Create file LOGOFF_TEST23 with SMB2_OPLOCK_LEVEL_II and send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST23 for testing"
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST23",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
            print "File created with SMB2_OPLOCK_LEVEL_II."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST23 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST23",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 23 Passed"

    def test_24_oplock_level_exclusive(self):
        """
        Create file with EXCLUSIVE oplock, logoff the session. With new session, send create open request with EXCLUSIVE oplock.
        EXCLUSIVE oplock should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST24-------------------------------------"
            print "TC 24 - Create file LOGOFF_TEST24 with SMB2_OPLOCK_LEVEL_EXCLUSIVE and send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST24 for testing"
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST24",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()
            print "File created with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST24 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST24",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 24 Passed"

    def test_25_oplock_level_batch(self):
        """
        Create file with BATCH oplock, logoff the session. With new session, send create open request with EXCLUSIVE oplock.
        EXCLUSIVE oplock should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST25-------------------------------------"
            print "TC 25 - Create file LOGOFF_TEST25 with SMB2_OPLOCK_LEVEL_BATCH and send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST25 for testing"
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST25",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH).result()
            print "File created with SMB2_OPLOCK_LEVEL_BATCH."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST25 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST25",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 25 Passed"

    def test_26_rwh_lease(self):
        """
        Create file with RWH lease, logoff the session. With new session, send create open request with RWH lease.
        RWH lease should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST26-------------------------------------"
            print "TC 26 - Create file LOGOFF_TEST26 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RWH, send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST26 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST26",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RWH lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST26 for testing oplock level with RWH Lease."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST26",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 26 Passed"

    def test_27_rw_lease(self):
        """
        Create file with RW lease, logoff the session. With new session, send create open request with RWH lease.
        RWH lease should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST27-------------------------------------"
            print "TC 27 - Create file LOGOFF_TEST27 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RW, send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST27 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST27",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RW lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST27 for testing oplock level with RWH Lease."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST27",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 27 Passed"

    def test_28_rh_lease(self):
        """
        Create file with RH lease, logoff the session. With new session, send create open request with RWH lease.
        RWH lease should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST28-------------------------------------"
            print "TC 28 - Create file LOGOFF_TEST28 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RH, send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST28 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST28",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RH lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST28 for testing oplock level with RWH Lease."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST28",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 28 Passed"

    def test_29_lease_none(self):
        """
        Create file with lease NONE, logoff the session. With new session, send create open request with RWH lease.
        RWH lease should be granted for the second create open request.
        """
        try:
            print "\n------------------LOGOFF_TEST29-------------------------------------"
            print "TC 29 - Create file LOGOFF_TEST29 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=NONE, send logoff request."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST29 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan1.create(tree1, "LOGOFF_TEST29",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and lease state NONE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Open file LOGOFF_TEST29 for testing oplock level with RWH Lease."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan2.create(tree2, "LOGOFF_TEST29",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 29 Passed"

    def test_30_multiple_tree_connect(self):
        """
        After session setup, send multiple tree connect requests and logoff the session. Try disconnecting any previous tree connection.
        Test case should FAIL. Since test case is expected to fail, the actual status is set to STATUS_SUCCESS, if the tree disconnection
        is successful, which is unexpected success.
        """
        try:
            print "\n------------------LOGOFF_TEST30-------------------------------------"
            print "TC 30 - Send multiple tree connect requests to connect to share,\
 send LOGOFF request followed by tree disconnect request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful"
            print "Sending second tree connect request..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connectoin is successful"
            print "Sending third tree connect request..."
            tree3 = chan.tree_connect(self.share)
            print "Third tree connection is successful"
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully"
            print "Sending tree disconnect request for third tree connect..."
            chan.tree_disconnect(tree3)
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. Tree disconnection successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 30 Passed"

    def test_31_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, logoff the session.
        With new session, send create open request with durable reconnect. Durable reconnect should be successful.
        Actual status will be set to STATUS_SUCCESS only if the durable reconnect is successful.
        """
        try:
            print "\n------------------LOGOFF_TEST31-------------------------------------"
            print "TC 31 - Create file LOGOFF_TEST31 with durable set and SMB2_OPLOCK_LEVEL_BATCH, Logoff the session.\
 Send create open request with durable reconnect for LOGOFF_TEST31 file."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST31 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST31',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST31"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST31',
                                                        access=pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST31 opened."
            actual_status = str(create_result2.status)
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 31 Passed"

    def test_32_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, logoff the session. With new session send create
        open request with oplock lease and durable reconnect set. Durable reconnect should fail as
        durable reconnect with oplock lease is giving STATUS_OBJECT_NAME_NOT_FOUND error.
        Actual status will be set to STATUS_SUCCESS only if the durable reconnect is successful.
        """
        try:
            print "\n------------------LOGOFF_TEST32-------------------------------------"
            print "TC 32 - Create file LOGOFF_TEST32 with durable set and SMB2_OPLOCK_LEVEL_BATCH, Logoff the session.\
 Send create open request with durable reconnect for LOGOFF_TEST32 file with SMB2_OPLOCK_LEVEL_LEASE."
            expected_status = "STATUS_OBJECT_NAME_NOT_FOUND"
            print "Expected status: ", expected_status
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST32 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            self.lease2 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            self.r = pike.smb2.SMB2_LEASE_READ_CACHING
            self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
            self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            self.rwh = self.rw | self.rh
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST32',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST32"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST32',
                                                        access=pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                                        lease_key=self.lease1,
                                                        lease_state=self.rwh,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "File LOGOFF_TEST32 opened."
            print "Unexpected success. Durable reconnect validation has passed."
            actual_status = str(create_result2.status)
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 32 Passed"

    def test_33_flush(self):
        """
        Create file and logoff the session. Send flush request using the same session id. Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST33-------------------------------------"
            print "TC 33 - Create file LOGOFF_TEST33 and Logoff the session. Send flush request on the LOGOFF_TEST33 file."
            buffer = "testing 123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST33 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST33").result()
            print "File created."
            print "Sending write request..."
            bytes_written = chan.write(file_handle, 0, buffer)
            if bytes_written == len(buffer):
                print "Written data onto the file"
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending flush request..."
            flush_packet = conv_obj.flush(chan, tree, file_id=file_handle.file_id)
            res1 = conv_obj.transceive(chan, flush_packet)
            actual_status = str(res1[0].status)
            print "Unexpected success. Flush request successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 33 Passed"

    def test_34_echo(self):
        """
        After session setup and tree connection, logoff the session. send echo request. Test case should PASS.
        """
        try:
            print "\n------------------LOGOFF_TEST34-------------------------------------"
            print "TC 34 - Create file LOGOFF_TEST34 and Logoff the session. Send echo request."
            buffer = "testing 123"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res1 = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending echo request..."
            echo_packet = conv_obj.echo(chan)
            res2 = conv_obj.transceive(chan, echo_packet)
            actual_status = str(res2[0].status)
            print "Echo request successfully processed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 34 Passed"

    def test_35_query_directory(self):
        """
        Create file and logoff the session. Send query directory request using the same session id. Test case should FAIL.
        Actual status will be set to STATUS_SUCCESS only if the file name is present in query directory information.
        """
        try:
            print "\n------------------LOGOFF_TEST35-------------------------------------"
            print "TC 35 - Testing LOGOFF followed by query directory request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Tree connection successful."
            print "Create a file LOGOFF_TEST35 for testing"
            dir_handle = chan.create(tree, "LOGOFF_TEST35", options=pike.smb2.FILE_DIRECTORY_FILE).result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Querying directory information on LOGOFF_TEST35."
            names = map(lambda info: info.file_name, chan.query_directory(dir_handle))
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. Querying directory information on LOGOFF_TEST35 done."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 35 Passed"

    def test_36_set_info(self):
        """
        Create file and logoff the session. Send set_info request using the same session id. Test case should FAIL.
        Actual status will be set to STATUS_SUCCESS only if file attribute is changed using the set command.
        """
        try:
            print "\n------------------LOGOFF_TEST36-------------------------------------"
            print "TC 36 - Testing LOGOFF followed by set info request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Tree connection successful."
            print "Create a file LOGOFF_TEST36 for testing"
            file_handle = chan.create(tree, "LOGOFF_TEST36", disposition=pike.smb2.FILE_SUPERSEDE).result()
            print "File created."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Sending set_info request on LOGOFF_TEST36."
            requested_file_attr = pike.smb2.FILE_ATTRIBUTE_READONLY
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = requested_file_attr
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File attribute information set on LOGOFF_TEST36."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 36 Passed"

    def test_37_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, Lock file with SHARED_LOCK and logoff the session.
        With new session, send create open request with durable reconnect, try to lock with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY on same locked
        byte ranges. Second lock should fail as the same handle already have SHARED lock on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST37-------------------------------------"
            print "TC 37 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK and Logoff the session.\
 With new session try to lock with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY using durable reconnect on same byte ranges."
            expected_status = "STATUS_LOCK_NOT_GRANTED"
            print "Expected status: ", expected_status
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST37 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST37',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST37"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST37',
                                                        access=pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST37 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 37 Passed"

    def test_38_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, Lock file with EXCLUSIVE_LOCK and logoff the session.
        With new session, send create open request with durable reconnect, try to lock with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY on same locked
        byte ranges. Second lock should fail as the same handle already have EXCLUSIVE lock on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST38-------------------------------------"
            print "TC 38 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and Logoff the session.\
 With new session try to lock with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY using durable reconnect on same byte ranges."
            expected_status = "STATUS_LOCK_NOT_GRANTED"
            print "Expected status: ", expected_status
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST38 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST38',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST38"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST38',
                                                        access=pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST38 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 38 Passed"

    def test_39_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, Lock file with SHARED_LOCK|FAIL_IMMEDIATELY and logoff the session.
        With new session, send create open request with durable reconnect, try to lock with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY on same locked
        byte ranges. Second lock should fail as the same handle already have SHARED lock on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST39-------------------------------------"
            print "TC 39 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and Logoff the session.\
 With new session try to lock with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY using durable reconnect on same byte ranges."
            expected_status = "STATUS_LOCK_NOT_GRANTED"
            print "Expected status: ", expected_status
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST39 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST39',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST39"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST39',
                                                        access=pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST39 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 39 Passed"

    def test_40_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, Lock file with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY and logoff the session.
        With new session, send create open request with durable reconnect, try to lock with EXCLUSIVE_LOCK|FAIL_IMMEDIATELY on same locked
        byte ranges. Second lock should fail as the same handle already have EXCLUSIVE lock on the file.
        """
        try:
            print "\n------------------LOGOFF_TEST40-------------------------------------"
            print "TC 40 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and Logoff the session.\
 With new session try to lock with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY using durable reconnect on same byte ranges."
            expected_status = "STATUS_LOCK_NOT_GRANTED"
            print "Expected status: ", expected_status
            lock = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST40 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST40',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST40"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST40',
                                                        access=pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST40 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 40 Passed"

    def test_41_durable_reconnect(self):
        """
        Create file with BATCH oplock and durable set, Lock file with EXCLUSIVE_LOCK and logoff the session.
        With new session, send create open request with durable reconnect, try to unlock file on same locked
        byte ranges. Unlock should be successfully processed.
        """
        try:
            print "\n------------------LOGOFF_TEST41-------------------------------------"
            print "TC 41 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and Logoff the session.\
 With new session try to unlock same byte ranges with durable reconnect on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]
            print "Creating first session and tree connect..."
            chan1, tree1 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST41 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan1, tree1, 'LOGOFF_TEST41',
                                                        access=pike.smb2.GENERIC_READ,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan1.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending Logoff request..."
            logoff_req = conv_obj.logoff(chan1)
            res = conv_obj.transceive(chan1, logoff_req)
            print "Session logged off successfully."
            print "Creating second session and tree connect..."
            chan2, tree2 = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending create Open request with durable reconnect on the file LOGOFF_TEST41"
            create_tmp2, create_resp2 = conv_obj.create(chan2, tree2,
                                                        'LOGOFF_TEST41',
                                                        access=pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        durable=file_handle1)
            file_handle2 = create_tmp2.result()
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            print "File LOGOFF_TEST41 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_UN_LOCK flag..."
            lock_res2 = chan2.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "Unlocked requested byte ranges."
            print "Closing file handle..."
            chan2.close(file_handle2)
            print "Second file handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 41 Passed"

    def test_42_oplock_level_none(self):
        """
        Create file with oplock NONE, logoff the session. With same session, send create open request with EXCLUSIVE oplock.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST42-------------------------------------"
            print "TC 42 - Create file LOGOFF_TEST42 with SMB2_OPLOCK_LEVEL_NONE and send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST42 for testing"
            file_handle1 = chan.create(tree, "LOGOFF_TEST42",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_NONE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST42 for testing oplock level with EXCLUSIVE after logoff."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "LOGOFF_TEST42",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 42 Passed"

    def test_43_oplock_level_2(self):
        """
        Create file with LEVEL_II oplock, logoff the session. With same session, send create open request with EXCLUSIVE oplock.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST43-------------------------------------"
            print "TC 43 - Create file LOGOFF_TEST43 with SMB2_OPLOCK_LEVEL_II and send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST43 for testing"
            file_handle1 = chan.create(tree, "LOGOFF_TEST43",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
            print "File created with SMB2_OPLOCK_LEVEL_II."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST43 for testing oplock level with EXCLUSIVE after logoff."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "LOGOFF_TEST43",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 43 Passed"

    def test_44_oplock_level_exclusive(self):
        """
        Create file with EXCLUSIVE oplock, logoff the session. With same session, send create open request with EXCLUSIVE oplock.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST44-------------------------------------"
            print "TC 44 - Create file LOGOFF_TEST44 with SMB2_OPLOCK_LEVEL_EXCLUSIVE and send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST44 for testing"
            file_handle1 = chan.create(tree, "LOGOFF_TEST44",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()
            print "File created with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST44 for testing oplock level with EXCLUSIVE after logoff."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "LOGOFF_TEST44",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 44 Passed"

    def test_45_oplock_level_batch(self):
        """
        Create file with BATCH oplock, logoff the session. With same session, send create open request with EXCLUSIVE oplock.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST45-------------------------------------"
            print "TC 45 - Create file LOGOFF_TEST45 with SMB2_OPLOCK_LEVEL_BATCH and send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST45 for testing"
            file_handle1 = chan.create(tree, "LOGOFF_TEST45",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH).result()
            print "File created with SMB2_OPLOCK_LEVEL_BATCH."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST45 for testing oplock level with EXCLUSIVE after logoff."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "LOGOFF_TEST45",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 45 Passed"

    def test_46_rwh_lease(self):
        """
        Create file with RWH lease, logoff the session. With same session, send create open request with RWH lease.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST46-------------------------------------"
            print "TC 46 - Create file LOGOFF_TEST46 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RWH, send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST46 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "LOGOFF_TEST46",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RWH lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST46 for testing oplock level with RWH Lease after logoff."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "LOGOFF_TEST46",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 46 Passed"

    def test_47_rw_lease(self):
        """
        Create file with RW lease, logoff the session. With same session, send create open request with RWH lease.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST47-------------------------------------"
            print "TC 47 - Create file LOGOFF_TEST47 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RW, send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST47 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "LOGOFF_TEST47",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RW lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST47 for testing oplock level with RWH Lease after logoff."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "LOGOFF_TEST47",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 47 Passed"

    def test_48_rh_lease(self):
        """
        Create file with RH lease, logoff the session. With same session, send create open request with RWH lease.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST48-------------------------------------"
            print "TC 48 - Create file LOGOFF_TEST48 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RH, send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST48 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "LOGOFF_TEST48",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RH lease state."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST48 for testing oplock level with RWH Lease after logoff."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "LOGOFF_TEST48",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 48 Passed"

    def test_49_lease_none(self):
        """
        Create file with lease NONE, logoff the session. With same session, send create open request with RWH lease.
        Test case should FAIL.
        """
        try:
            print "\n------------------LOGOFF_TEST49-------------------------------------"
            print "TC 49 - Create file LOGOFF_TEST49 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=NONE, send logoff request."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file LOGOFF_TEST49 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "LOGOFF_TEST49",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and lease state NONE."
            print "Sending Logoff request..."
            conv_obj = utils.Convenience()
            logoff_req = conv_obj.logoff(chan)
            res = conv_obj.transceive(chan, logoff_req)
            print "Session logged off successfully."
            print "Open file LOGOFF_TEST49 for testing oplock level with RWH Lease after logoff."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "LOGOFF_TEST49",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 49 Passed"
    		
    def test_50_multiple_session_logoff(self):
        try:
            print "\n------------------LOGOFF_TEST50-------------------------------------"
            print "TC 50 - Send multiple session setup requests i.e 2^16 sessions and then send logoff request for all the sessions."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Send negotiate request"
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate request is successful"
            conv_obj = utils.Convenience()
            print "Send 2^16 Session setup requests."
            sessions_list = []
            for i in range(0, 65535):
                print "Send session setup request", i
                chan = conn.session_setup(self.creds)
                print "Session setup successful", chan.session.session_id
                sessions_list.append(chan)
            for j in sessions_list:
                print "Disconnecting session id:", j.session.session_id
                logoff_req = conv_obj.logoff(j)
                res = conv_obj.transceive(j, logoff_req)
                print "Logoff successful."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 50 Passed"
