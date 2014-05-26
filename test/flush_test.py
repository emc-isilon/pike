#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        flush_test.py
#
# Abstract:
#
#        SMB2_FLUSH command tests
#
# Authors: Lingaraj Gowdar (lingaraj.gowdar@calsoftinc.com)
#
import pike.model
import pike.smb2
import pike.test
import random
import array
import utils

class FlushTest(pike.test.PikeTest):
    
    def test_01_flush_with_valid_input(self):
        try:
            print "\n--------------------Flush_TC 01 --------------------"
            print "Verify SMB2_FLUSH with valid parameters."
            buffer = "testing123"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush1.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush1.txt", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."  
            print "Sending Write request..."
            bytes_written = chan.write(file_handle,
                                          0,
                                       buffer)
            self.assertEqual(bytes_written, len(buffer))
            print "Write request completed."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24) 
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."  
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."    
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 01 failed.")
        print "TC 01 Passed"

    def test_02_flush_for_STATUS_FILE_CLOSED(self):
        try:
            print "\n--------------------Flush_TC 02 --------------------"
            print "Close create file handle and verify SMB2_FLUSH response."
            expected_status = 'STATUS_FILE_CLOSED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush2.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush2.txt", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            chan.close(file_handle)
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 02 failed.")
        print "TC 02 Passed"

    def test_03_flush_with_invalid_structure_size(self):
        try:
            print "\n--------------------Flush_TC 03 --------------------"
            print "Verify SMB2_FLUSH with invalid structure size."
            expected_status = 'STATUS_INVALID_PARAMETER'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush3.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush3.txt", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,structure_size=20,file_id = file_handle.file_id)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 03 failed.")
        print "TC 03 Passed"

    def test_04_flush_with_invalid_file_id(self):
        try:
            print "\n--------------------Flush_TC 04 --------------------"
            print "Verify SMB2_FLUSH with invalid file_id."
            expected_status = 'STATUS_FILE_CLOSED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush4.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush4.txt", disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = (12345555L,11222223333L),structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 04 failed.")
        print "TC 04 Passed"

    def test_05_flush_STATUS_ACCESS_DENIED(self):
        try:
            print "\n--------------------Flush_TC 05 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_READ_DATA."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush5.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush5.txt", access = pike.smb2.FILE_READ_DATA ,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 05 failed.")
        print "TC 05 Passed"
    
    def test_06_flush_for_STATUS_NETWORK_NAME_DELETED(self):
        try:
            print "\n--------------------Flush_TC 06 --------------------"
            print "Verify SMB2_FLUSH response without sending tree_id in SMB2_FLUSH request."
            expected_status = 'STATUS_NETWORK_NAME_DELETED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush6.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush6.txt", access = pike.smb2.FILE_READ_DATA ,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 06 failed.")
        print "TC 06 Passed"
     
    def test_07_flush_for_STATUS_ACCESS_DENIED_for_delete_permission(self):
        try:
            print "\n--------------------Flush_TC 07 --------------------"
            print "Verify SMB2_FLUSH when create desired access is DELETE."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush7.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush7.txt", access = pike.smb2.DELETE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 07 failed.")
        print "TC 07 Passed"
    
    def test_08_flush_for_STATUS_ACCESS_DENIED_For_READ_ATTRIBUTES(self):
        try:
            print "\n--------------------Flush_TC 08 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_READ_ATTRIBUTES."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush8.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush8.txt", access = pike.smb2.FILE_READ_ATTRIBUTES, disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 08 failed.")
        print "TC 08 Passed"
    
    def test_09_flush_for_FILE_APPEND_DATA(self):
        try:
            print "\n--------------------Flush_TC 09 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_APPEND_DATA."
            buffer = "testing123"
            expected_status = "STATUS_SUCCESS"
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush9.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush9.txt", access = pike.smb2.FILE_APPEND_DATA,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Write request..."
            bytes_written = chan.write(file_handle,
                                          0,
                                       buffer)
            self.assertEqual(bytes_written, len(buffer))
            print "Write request completed."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 09 failed.")
        print "TC 09 Passed"

    def test_10_flush_for_MAXIMUM_ALLOWED(self):
        try:
            print "\n--------------------Flush_TC 10 --------------------"
            print "Verify SMB2_FLUSH when create desired access is MAXIMUM_ALLOWED."
            buffer = "testing123"
            expected_status = "STATUS_SUCCESS"
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush10.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush10.txt", access = pike.smb2.MAXIMUM_ALLOWED,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Write request..."
            bytes_written = chan.write(file_handle,
                                          0,
                                       buffer)
            self.assertEqual(bytes_written, len(buffer))
            print "Write request completed."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 10 failed.")
        print "TC 10 Passed"

    def test_11_flush_STATUS_ACCESS_DENIED_for_GENERIC_READ(self):
        try:
            print "\n--------------------Flush_TC 11 --------------------"
            print "Verify SMB2_FLUSH when create desired access is GENERIC_READ."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush11.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush11.txt", access = pike.smb2.GENERIC_READ,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 11 failed.")
        print "TC 11 Passed"

    def test_12_flush_for_WRITE_DATA(self):
        try:
            print "\n--------------------Flush_TC 12 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_WRITE_DATA."
            buffer = "testing123"
            expected_status = "STATUS_SUCCESS"
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush12.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush12.txt", access = pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Write request..."        
            bytes_written = chan.write(file_handle,
                                          0,
                                       buffer)
            self.assertEqual(bytes_written, len(buffer))
            print "Write request completed."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)    
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 12 failed.")
        print "TC 12 Passed"

    def test_13_flush_STATUS_ACCESS_DENIED_for_FILE_WRITE_ATTRIBUTES(self):
        try:
            print "\n--------------------Flush_TC 13 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_WRITE_ATTRIBUTES."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush13.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush13.txt", access = pike.smb2.FILE_WRITE_ATTRIBUTES,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 13 failed.")
        print "TC 13 Passed"

    def test_14_flush_STATUS_ACCESS_DENIED_for_FILE_WRITE_EA(self):
        try:
            print "\n--------------------Flush_TC 14 --------------------"
            print "Verify SMB2_FLUSH when create desired access is FILE_WRITE_EA."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush14.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush14.txt", access = pike.smb2.FILE_WRITE_EA,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 14 failed.")
        print "TC 14 Passed"
    
    def test_15_flush_STATUS_FILE_CLOSED_for_session_logoff(self):
        try:
            print "\n--------------------Flush_TC 15 --------------------"
            print "Log off the session and verify SMB2_FLUSH response."
            expected_status = 'STATUS_FILE_CLOSED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush15.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush15.txt",disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Sending Logoff request..."
            chan.logoff()
            print "Successfully logged out from the Session."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 15 failed.")
        print "TC 15 Passed"

    def test_16_flush_STATUS_FILE_CLOSED_for_tree_disconnect(self):
        try:
            print "\n--------------------Flush_TC 16 --------------------"
            print "Disconnect the tree and verify SMB2_FLUSH response."
            expected_status = 'STATUS_FILE_CLOSED'
            print "Expected Status: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a file Flush16.txt for testing flush request:"
            file_handle  = chan.create(tree, "Flush16.txt",disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created."
            print "Disconnecting tree..."
            chan.tree_disconnect(tree)
            print "Tree disconnected."
            print "Sending Flush request..."
            conv_obj=utils.Convenience()
            flush_packet = conv_obj.flush(chan,tree,file_id = file_handle.file_id,structure_size=24)
            res = conv_obj.transceive(chan,flush_packet)
            print "Flush request is successful."
            print "Close the file handle:"
            chan.close(file_handle)
            print "File handle closed."  
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 16 failed.")
        print "TC 16 Passed"
    
