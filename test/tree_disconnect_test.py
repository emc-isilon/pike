# Copyright (C) Calsoft.  All rights reserved.
#
# Module Name:
#
#        tree_disconnect_test.py
#
# Abstract:
#
#         Test cases for Tree Disconnect Command.
#
# Authors: Prayas Gupta (prayas.gupta@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.test
import utils
import array
import random
import itertools


class TreeDisconnectTest(pike.test.PikeTest):
    def test_01_valid_input(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST01-------------------------------------"
            print "TC 01 - Testing SMB2_TREE_DISCONNECT with valid inputs"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Sending tree disconnect request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree,structure_size=4,reserved=0)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull." 
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 01 Passed"

    def test_02_less_strucsize(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST02-------------------------------------"
            print "TC 02 - Testing SMB2_TREE_DISCONNECT for structureSize less than valid structureSize"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Sending Tree disconnect request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree,structure_size=2,reserved=0)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 02 Passed"

    def test_03_greater_strucsize(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST03-------------------------------------"
            print "TC 03 - Testing SMB2_TREE_DISCONNECT for structureSize greater than valid structureSize"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Sending Tree disconnect request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree,structure_size=8,reserved=0)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 03 Passed"

    def test_04_greater_reserved(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST04-------------------------------------"
            print "TC 04 - Testing SMB2_TREE_DISCONNECT for reserved value greater than zero."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Sending Tree disconnect request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree,structure_size=4,reserved=8)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 04 Passed"

    def test_05_tree_disc_consecutive(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST05-------------------------------------"
            print "TC 05 - Testing SMB2_TREE_DISCONNECT for consecutive tree disconnect requests."
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Sending first TREE_DISCONNECT request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect first request successfull."
            print "Sending second TREE_DISCONNECT request..."
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res2 = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect second request successfull."
            actual_status = str(res2[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 05 Passed"

    def test_06_tree_disc_close_fh(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST06-------------------------------------"
            print "TC 06 - Testing SMB2_TREE_DISCONNECT followed by closing file handle."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Create a file TREE_DISCONNECT_TEST06 for testing"
            file_handle  = chan.create(tree, "TREE_DISCONNECT_TEST06").result()
            print "File creation is successfull."
            print "Sending TREE_DISCONNECT request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect request successfull."
            print "Closing file handle"
            chan.close(file_handle)
            actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File handle closed successfully."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 06 Passed"

    def test_07_tree_disconnect_open_file(self):
        try:
            print "\n------------------SMB2_TREE_DISCONNECT_TEST07-------------------------------------"
            print "TC 07 - Create file TREE_DISCONNECT_TEST07 and do the Treedisconnect. Send create open request for TREE_DISCONNECT_TEST07 file."
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Create a file TREE_DISCONNECT_TEST07 for testing"
            file_handle  = chan.create(tree, "TREE_DISCONNECT_TEST07").result()
            print "File creation is successfull."
            print "Sending TREE_DISCONNECT request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfully."
            print "Sending create Open request on the file TREE_DISCONNECT_TEST07"
            file_handle2  = chan.create(tree, "TREE_DISCONNECT_TEST07", disposition=pike.smb2.FILE_OPEN).result()
            actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File TREE_DISCONNECT_TEST07 opened"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 07 Passed"

    def test_08_tree_disconnect_read(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST08-------------------------------------"
            print "TC 08 - Create file TREE_DISCONNECT_TEST08 and do the treedisconnect. Send read request on the TREE_DISCONNECT_TEST08 file."
            buffer = "testing 123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successfull."
            print "Create a file TREE_DISCONNECT_TEST08 for testing"
            file_handle  = chan.create(tree, "TREE_DISCONNECT_TEST08").result()
            print "File creation is successfull."
            print "Sending write request"
            bytes_written = chan.write(file_handle,0,buffer)
            print "Written data onto the file"
            print "Sending TREE_DISCONNECT request..."
            conv_obj=utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending read request"
            read_packet = conv_obj.read(chan, file_handle)
            read_res = conv_obj.transceive(chan, read_packet)
            actual_status = str(read_res[0].status)
            print "Unexpected success : Successfully read data from the file"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 08 Passed"

    def test_09_tree_disconnect_write(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST09-------------------------------------"
            print "TC 09 - Create file TREE_DISCONNECT_TEST09 and do the treedisconnect. Send write request on the TREE_DISCONNECT_TEST09 file."
            buffer = "testing 123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST09 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST09").result()
            print "File created."
            print "Sending TREE_DISCONNECT request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending write request..."
            bytes_written = chan.write(file_handle, 0, buffer)
            actual_status = "STATUS_SUCCESS"
            print "Unexpected success. Written data onto the file"
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 09 Passed"

    def test_10_tree_disconnect_invalid_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST10-------------------------------------"
            print "TC 10 - Testing TREE_DISCONNECT with inavlid treeid"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            correct_tree_id = tree.tree_id
            print "Tree ID for first tree connect is :",correct_tree_id
            print "Sending TREE_DISCONNECT request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            tree_disconnect_req[0].tree_id = correct_tree_id + 6
            print "Tree disconnect after setting tree id ",tree_disconnect_req
            res = conv_obj.transceive(chan, tree_disconnect_req)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 10 Passed"

    def test_11_tree_disconnect_set(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST11-------------------------------------"
            print "TC 11 - Testing TREE_DISCONNECT request followed by set info request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST11 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST11").result()
            print "File created."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending set_info request on TREE_DISCONNECT_TEST11."
            requested_file_attr = pike.smb2.FILE_ATTRIBUTE_READONLY
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = requested_file_attr
            if requested_file_attr == file_info.file_attributes:
                actual_status = "UNEXPECTED_SUCCESS"
            print "Unexpected success. File attribute information set on TREE_DISCONNECT_TEST11."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 11 Passed"


    def test_12_tree_disconnect_query_file(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST12-------------------------------------"
            print "TC 12 - Testing TREE_DISCONNECT followed by query file info request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST12 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST12").result()
            print "File created."
            print "Sending TREE_DISCONNECT request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Querying file info on TREE_DISCONNECT_TEST12 file"
            info = chan.query_file_info(file_handle, pike.smb2.FILE_ALL_INFORMATION)
            actual_status = str(info.status)
            print "Unexpected success. Query file info on TREE_DISCONNECT_TEST12 done."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 12 Passed"

    def test_13_tree_disconnect_durable_open(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST13-------------------------------------"
            print "TC 13 - Create file TREE_DISCONNECT_TEST13 with durable set and do the tree disconnect.Send create open request on TREE_DISCONNECT_TEST13 file with same session and treeid ."
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST13 for testing"
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan, tree,"TREE_DISCONNECT_TEST13",
                                                        access=pike.smb2.GENERIC_READ,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
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
            print "Sending TREE_DISCONNECT request..."
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "TREE_DISCONNECT successfull."
            print "Sending create Open request on the file TREE_DISCONNECT_TEST13..."
            create_tmp2, create_resp2 = conv_obj.create(chan, tree,
                                                        'TREE_DISCONNECT_TEST13',
                                                        access=pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        name_offset=120,
                                                        name_length=26,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE)
            file_handle2 = create_tmp2.result()
            print "File TREE_DISCONNECT_TEST13 opened."
            create_result2 = create_resp2[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result2[0].children), "Durable handle response not found in Create response."
            print "Durable reconnect validation has passed."
            actual_status = str(create_result2.status) 
            print "Unexpected success. File open successfull."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 13 Passed"

    def test_14_tree_disconnect_invalid_session_id(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST14-------------------------------------"
            print "TC 14 - Testing SMB2_TREE_DISCONNECT with invalid session id."
            expected_status = "STATUS_USER_SESSION_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Sending TREE_DISCONNECT request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree,structure_size=4,reserved=0)
            tree_disconnect_req[0].session_id = 1234561234567
            res = conv_obj.transceive(chan, tree_disconnect_req)
            actual_status = str(res[0].status)
            print "Unexpected success. Tree Disconnect successfull."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 14 Passed"

    def test_15_tree_disconnect_shared_lock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST15-------------------------------------"
            print "TC 15 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK and do the tree disconnect. With old session and new tree_id try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST15 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST15").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK flag..."
            chan.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending  tree disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST15 for testing"
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST15", disposition=pike.smb2.FILE_OPEN).result()
            print "File TREE_DISCONNECT_TEST15 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 15 Passed"

    def test_16_tree_disconnect_exclusive_lock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST16-------------------------------------"
            print "TC 16 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and do the tree disconnect.With old session and new tree_id try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST16 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST16").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            chan.lock(file_handle1, lock1).result()
            print "File locked with exclusive lock on requested byte ranges."
            print "Sending tree_disconnect  request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST16 for testing"
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST16", disposition=pike.smb2.FILE_OPEN).result()
            print "File TREE_DISCONNECT_TEST16 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 16 Passed"

    def test_17_tree_disconnect_shared_lock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST17-------------------------------------"
            print "TC 17 - Lock file with SMB2_LOCKFLAG_SHARED_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and do the tree disconnect.With old session and new tree_id try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST18 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST18").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY flag..."
            chan.lock(file_handle1, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second Tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST18 for testing"
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST18", disposition=pike.smb2.FILE_OPEN).result()
            print "File TREE_DISCONNECT_TEST18 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 17 Passed"

    def test_18_tree_disconnect_exclusive_lock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST18-------------------------------------"
            print "TC 18 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY and do the tree disconnect. With old session and new tree_id try SMB2_LOCKFLAG_EXCLUSIVE_LOCK on same byte ranges."
            expected_status = "STATUS_SUCCESS"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK | pike.smb2.SMB2_LOCKFLAG_FAIL_IMMEDIATELY)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST18 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST18").result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK|SMB2_LOCKFLAG_FAIL_IMMEDIATELY flag..."
            chan.lock(file_handle1, lock1).result()
            print "File locked with exclusive lock on requested byte ranges."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second Tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST18 for testing"
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST18", disposition=pike.smb2.FILE_OPEN).result()
            print "File TREE_DISCONNECT_TEST18 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_EXCLUSIVE_LOCK flag..."
            lock_res2 = chan.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "File locked with shared lock on requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 18 Passed"

    def test_19_tree_disconnect_unlock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST19-------------------------------------"
            print "TC 19 - Lock file with SMB2_LOCKFLAG_EXCLUSIVE_LOCK and do the tree disconnect.With old session and new treeid try to unlock same byte ranges."
            expected_status = "STATUS_RANGE_NOT_LOCKED"
            lock1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)]
            lock2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT _TEST19 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST19", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK..."
            lock_res1 = chan.lock(file_handle, lock1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull." 
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST19 for testing"
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST19", disposition=pike.smb2.FILE_OPEN).result()
            print "File TREE_DISCONNECT_TEST19 opened."
            print "Sending Lock request with SMB2_LOCKFLAG_UN_LOCK flag..."
            lock_res2 = chan.lock(file_handle2, lock2).result()
            actual_status = str(lock_res2.status)
            print "Unexpected success. Unlocked requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 19 Passed"

    def test_20_tree_disconnect_shared_unlock(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST20-------------------------------------"
            print "TC 20 - Lock file TREE_DISCONNECT_TEST20 with SMB2_LOCKFLAG_SHARED_LOCK and do the tree disconnect.Send unlock request on same byte ranges."
            expected_status = "STATUS_FILE_CLOSED"
            locks1 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_SHARED_LOCK)]
            locks2 = [(8, 8, pike.smb2.SMB2_LOCKFLAG_UN_LOCK)]
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST20 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST20", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Lock request with SMB2_LOCKFLAG_SHARED_LOCK..."
            lock_res1 = chan.lock(file_handle, locks1).result()
            print "File locked with shared lock on requested byte ranges."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending Lock request with SMB2_LOCKFLAG_UN_LOCK flag..."
            lock_res2 = chan.lock(file_handle, locks2).result()
            actual_status = str(lock_res2.status)
            print "Unexpected success. Unlocked requested byte ranges."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 20 Passed"

    def test_21_tree_disconnect_oplock_none(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST21-------------------------------------"
            print "TC 21 - Create file TREE_DISCONNECT_TEST21 with SMB2_OPLOCK_LEVEL_NONE and send tree disconnect request.With old session and new treeid try to send create open request with EXCLUSIVE oplock"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST21 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST21",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_NONE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST21 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST21",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 21 Passed"

    def test_22_tree_disconnect_oplock_2(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST22-------------------------------------"
            print "TC 22 - Create file TREE_DISCONNECT_TEST22 with SMB2_OPLOCK_LEVEL_II and send tree disconnect request. With old session_id and new tree_id try to send create open request with EXCLUSIVE oplock"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST22 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST22",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
            print "File created with SMB2_OPLOCK_LEVEL_II."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST22 for testing oplock level with EXCLUSIVE"
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST22",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 22 Passed"

    def test_23_tree_disconnect_oplock_exclusive(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST23-------------------------------------"
            print "TC 23 - Create file TREE_DISCONNECT_TEST23 with SMB2_OPLOCK_LEVEL_EXCLUSIVE and send tree disconnect request. With old session_id and new tree_id try to send create open request with EXCLUSIVE oplock."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST23 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST23",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()
            print "File created with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST23 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST23",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 23 Passed"

    def test_24_tree_disconnect_oplock_batch(self):
        try:
            print "\n-----------------TREE_DISCONNECT_TEST24-------------------------------------"
            print "TC 24 - Create file TREE_DISCONNECT_TEST24 with SMB2_OPLOCK_LEVEL_BATCH and send tree disconnect request. With old session_id and new tree_id try to send create open request with EXCLUSIVE oplock."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST24 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST24",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH).result()
            print "File created with SMB2_OPLOCK_LEVEL_BATCH."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull." 
            print "Open file TREE_DISCONNECT_TEST24 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST24",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 24 Passed"

    def test_25_tree_disconnect_rwh_lease(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST25-------------------------------------"
            print "TC 25 - Create file TREE_DISCONNECT_TEST25 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RWH, send tree disconnect request.With old session_id and new tree_id try to send create open request"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST25 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST25",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RWH lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST25 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST25",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 25 Passed"

    def test_26_tree_disconnect_rw_lease(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST26-------------------------------------"
            print "TC 26 - Create file TREE_DISCONNECT_TEST26 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RW, send tree disconnect request.With old session_id and new tree_id try to send create open request"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST26 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST26",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RW lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST26 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST26",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 26 Passed"


    def test_27_tree_disconnect_rh_lease(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST27-------------------------------------"
            print "TC 27 - Create file TREE_DISCONNECT_TEST27 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RH, send tree disconnect request.With old session_id and new tree_id try to send create open request"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST27 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST27",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RH lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST27 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST27",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 27 Passed"

    def test_28_tree_disconnect_lease_none(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST28-------------------------------------"
            print "TC 28 - Create file TREE_DISCONNECT_TEST28 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=NONE, send tree disconnect request.With old session_id and new tree_id try to send create open request"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST28 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST28",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and lease state NONE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successful."
            print "Open file TREE_DISCONNECT_TEST28 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree2, "TREE_DISCONNECT_TEST28",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 28 Passed"


    def test_29_lease_none_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST29-------------------------------------"
            print "TC 29 - Create file TREE_DISCONNECT_TEST29 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=NONE, send tree disconnect request. With old session_id and old tree_id try to send create open request"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST29 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST29",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and lease state NONE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST29 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST29",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 29 Passed"

    def test_30_tree_disconnect_flush(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST30-------------------------------------"
            print "TC 30 - Create file TREE_DISCONNECT_TEST30 and do the tree disconnect. Send flush request on the TREE_DISCONNECT_TEST30 file with same session_id."
            buffer = "testing 123"
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST30 for testing"
            file_handle = chan.create(tree, "TREE_DISCONNECT_TEST30", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending flush request..."
            flush_packet = conv_obj.flush(chan, tree, file_id=file_handle.file_id)
            res1 = conv_obj.transceive(chan, flush_packet)
            actual_status = str(res1[0].status)
            print "Unexpected success. Flush request successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 30 Passed"

    def test_31_tree_disconnect_echo(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST31-------------------------------------"
            print "TC 31 - Create file TREE_DISCONNECT_TEST31 and do the tree disconnect. Send echo request."
            buffer = "testing 123"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Sending echo request..."
            echo_packet = conv_obj.echo(chan)
            res2 = conv_obj.transceive(chan,echo_packet)
            actual_status = str(res2[0].status)
            print "Echo request successfully processed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 31 Passed"

    def test_32_tree_disconnect_query(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST32-------------------------------------"
            print "TC 32 - Testing Tree disconnect followed by query directory request."
            expected_status = "STATUS_FILE_CLOSED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Tree connection successful."
            print "Create a file TREE_DISCONNECT_TEST32 for testing"
            dir_handle = chan.create(tree, "TREE_DISCONNECT_TEST32", disposition=pike.smb2.FILE_OPEN_IF, options=pike.smb2.FILE_DIRECTORY_FILE).result()
            print "File created."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Querying directory information on TREE_DISCONNECT_TEST32."
            names = map(lambda info: info.file_name, chan.query_directory(dir_handle))
            if self.assertIn('TREE_DISCONNECT_TEST32', names):
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. Querying directory information on TREE_DISCONNECT_TEST32 done."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 32 Passed"

    def test_33_difftree_durable_open(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST33-------------------------------------"
            print "TC 33 - Create file TREE_DISCONNECT_TEST33 with durable set and do the tree disconnect.Send create open request on TREE_DISCONNECT_TEST33 file with same session and different treeid ."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST33 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            conv_obj = utils.Convenience()
            create_tmp1, create_resp1 = conv_obj.create(chan, tree, 'TREE_DISCONNECT_TEST33',
                                                        access=pike.smb2.GENERIC_READ,
                                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                                        disposition=pike.smb2.FILE_OPEN_IF,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE,
                                                        name_offset=120,
                                                        name_length=26,
                                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH,
                                                        durable=True)
            file_handle1 = create_tmp1.result()
            print "File created."
            create_result1 = create_resp1[0].result()
            print "Verifying durable handle..."
            assert "DurableHandleResponse" in str(create_result1[0].children), "Durable handle response not found in Create response."
            print "Durable handle validation has passed."
            print "Sending TREE_DISCONNECT request..."
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "TREE_DISCONNECT successfull."
            print "Sending create Open request on the file TREE_DISCONNECT_TEST33..."
            print "Creating new treeid"
            tree2 = chan.tree_connect(self.share)
            print "New tree connect successfull"
            print "Sending create Open request with different treeid on the file TREE_DISCONNECT_TEST33..."
            create_tmp2, create_resp2 = conv_obj.create(chan, tree2,
                                                        'TREE_DISCONNECT_TEST33',
                                                        access=pike.smb2.FILE_WRITE_DATA,
                                                        attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY,
                                                        share=pike.smb2.FILE_SHARE_WRITE,
                                                        disposition=pike.smb2.FILE_OPEN,
                                                        name_offset=120,
                                                        name_length=26,
                                                        options=pike.smb2.FILE_NO_EA_KNOWLEDGE)
            file_handle2 = create_tmp2.result()
            print "File TREE_DISCONNECT_TEST33 opened."
            create_result2 = create_resp2[0].result()
            actual_status = str(create_result2.status)
            print "File open successful."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 33 Passed"

    def test_34_oplock_none_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST34-------------------------------------"
            print "TC 34 - Create file TREE_DISCONNECT_TEST34 with SMB2_OPLOCK_LEVEL_NONE and send tree disconnect request.With old session and old treeid try to send create open request with EXCLUSIVE oplock"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST34 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST34",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE).result()
            print "File created with SMB2_OPLOCK_LEVEL_NONE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST34 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST34",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 34 Passed"

    def test_35_oplock_2_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST35-------------------------------------"
            print "TC 35 - Create file TREE_DISCONNECT_TEST35 with SMB2_OPLOCK_LEVEL_II and send tree disconnect request. With old session_id and old tree_id try to send create open request with EXCLUSIVE oplock"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST35 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST35",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
            print "File created with SMB2_OPLOCK_LEVEL_II."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST35 for testing oplock level with EXCLUSIVE"
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST35",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 35 Passed"

    def test_36_oplock_exclusive_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST36-------------------------------------"
            print "TC 36 - Create file TREE_DISCONNECT_TEST36 with SMB2_OPLOCK_LEVEL_EXCLUSIVE and send tree disconnect request. With old session_id and old tree_id try to send create open request with EXCLUSIVE oplock."
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST36 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST36",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()
            print "File created with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST36 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST36",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success.File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 36 Passed"

    def test_37_oplock_batch_same_treeid(self):
        try:
            print "\n-----------------TREE_DISCONNECT_TEST37-------------------------------------"
            print "TC 37 - Create file TREE_DISCONNECT_TEST37 with SMB2_OPLOCK_LEVEL_BATCH and send tree disconnect request. With old session_id and old tree_id try to send create open request with EXCLUSIVE oplock."
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST37 for testing"
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST37",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_BATCH).result()
            print "File created with SMB2_OPLOCK_LEVEL_BATCH."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Creating second tree connect..."
            tree2 = chan.tree_connect(self.share)
            print "Second tree connect successfull."
            print "Open file TREE_DISCONNECT_TEST37 for testing oplock level with EXCLUSIVE."
            requested_oplock = pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST37",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=requested_oplock).result()
            if requested_oplock == file_handle2.oplock_level:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with SMB2_OPLOCK_LEVEL_EXCLUSIVE."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 37 Passed"

    def test_38_rwh_lease_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST38-------------------------------------"
            print "TC 38 - Create file TREE_DISCONNECT_TEST38 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RWH, send tree disconnect request.With old session_id and old tree_id try to send create open request"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST25 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST38",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RWH lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST38 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST38",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 38 Passed"

    def test_39_rw_lease_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST39-------------------------------------"
            print "TC 39 - Create file TREE_DISCONNECT_TEST39 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RW, send tree disconnect request.With old session_id and old tree_id try to send create open request"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successful."
            print "Create a file TREE_DISCONNECT_TEST39 for testing"
            self.lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST39",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RW lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST39 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST39",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=self.lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 39 Passed"

    def test_40_rh_lease_same_treeid(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST40-------------------------------------"
            print "TC 40 - Create file TREE_DISCONNECT_TEST40 with SMB2_OPLOCK_LEVEL_LEASE and lease_state=RH, send tree disconnect request. With old session_id and old tree_id try to send create open request"
            expected_status = "STATUS_NETWORK_NAME_DELETED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect successfull."
            print "Create a file TREE_DISCONNECT_TEST40 for testing"
            lease1 = array.array('B', map(random.randint, [0] * 16, [255] * 16))
            file_handle1 = chan.create(tree, "TREE_DISCONNECT_TEST40",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN_IF,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            print "File created with SMB2_OPLOCK_LEVEL_LEASE and RH lease state."
            print "Sending tree_disconnect request..."
            conv_obj = utils.Convenience()
            tree_disconnect_req = conv_obj.tree_disconnect(chan,tree)
            res = conv_obj.transceive(chan, tree_disconnect_req)
            print "Tree Disconnect successfull."
            print "Open file TREE_DISCONNECT_TEST40 for testing oplock level with EXCLUSIVE."
            requested_lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            file_handle2 = chan.create(tree, "TREE_DISCONNECT_TEST40",
                                        access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA,
                                        share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                                        disposition=pike.smb2.FILE_OPEN,
                                        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                                        lease_key=lease1,
                                        lease_state=pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING).result()
            if requested_lease_state == file_handle2.lease.lease_state:
                actual_status = "STATUS_SUCCESS"
            print "Unexpected success. File opened with RWH lease."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 40 Passed"
    
    def test_41_multiple_tree_connect(self):
        try:
            print "\n------------------TREE_DISCONNECT_TEST41-------------------------------------"
            print "TC 41 - Send multiple tree connect requests to connect to share i.e 2^16 tree connects and then send tree disconnect request for all the tree connects."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Send negotiate request"
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate request is successfull"
            print "Send session setup request"
            chan = conn.session_setup(self.creds)
            print "Session setup successfull"
            conv_obj = utils.Convenience()
            print "Send 2^16 tree connect requests to access to a particular share on the server"
            tree_connect_id = []
            for i in range(0,65535):
                print "Tree Connect number :", i
                tree = chan.tree_connect(self.share)
                print "The tree id is :",tree.tree_id
                tree_connect_id.append(tree)
            for t in tree_connect_id:
                print "Disconnecting tree id:",t.tree_id
                tree_disconnect_req = conv_obj.tree_disconnect(chan,t)
                res = conv_obj.transceive(chan, tree_disconnect_req)
                print "Tree Disconnect successfull."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 41 Passed"
 
