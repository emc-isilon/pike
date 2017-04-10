#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        set_info_test.py
#
# Abstract:
#
#        Automated Test cases for SET_INFO SMB2 Command.
#
# Authors: Prayas Gupta (prayas.gupta@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.nttime
import pike.test
import datetime
import unittest
import re

class SetInfo(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(SetInfo, self).__init__(*args, **kwargs)
        self.chan = None
        self.tree = None

    def create_file(self, filename):
        self.chan, self.tree = self.tree_connect()
        response = self.chan.create(self.tree, filename,access=pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_READ_ATTRIBUTES, disposition=pike.smb2.FILE_SUPERSEDE, options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
        return response

    def test_set_alloc_size(self):
        try:
            print "-----------------------------------------------------"
            print "TC 01 - Set Allocation Size (FILE_ALLOCATION_INFORMATION class)  and verify the status"
            alloc_size = 8192
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Trying to create a file"
            response = self.create_file("set_test1.txt")
            print "File creation successful"
            print "Querying the file for allocation size"
            info = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            old_alloc_size = info.standard_information.allocation_size
            print "The alloc size of the file before set operation :",old_alloc_size
            print "Trying to change the allocation size of file using Set operation"
            with self.chan.set_file_info(response, pike.smb2.FileAllocationInformation) as file_info:
                file_info.allocation_size = alloc_size
            print "Set operation successful"
            print "Querying the file for new allocation size value"
            info1 = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            new_alloc_size = info1.standard_information.allocation_size
            print "The alloc size of the file after set operation :",new_alloc_size
            print "Matching the allocation size to be set  and new allocation size value"
            self.assertRegexpMatches(str(alloc_size),str(new_alloc_size))
            actual_status = 'STATUS_SUCCESS'
            print "Close the handle"
            self.chan.close(response)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 01 has passed"

    def test_set_disposition_info_delete(self):
        try:
            print "-------------------------------------------------------"
            print "TC 02 - Set the Delete pending flag (FILE_DISPOSITION_INFORMATION class) with delete access and verify the status"
            expected_status = "STATUS_OBJECT_NAME_NOT_FOUND"
            print "Expected status:",expected_status
            print "Create session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and tree connect is successful"
            print "Trying to create file"
            file_handle = chan.create(tree,'set_test2.txt',access=pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.DELETE, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File creation successful"
            print "Querying the file for delete_pending value"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            delete_pending = info.standard_information.delete_pending
            print "The value of delete pending flag before doing set operation : ",delete_pending
            print "Trying to change the delete pending flag value using Set operation"
            with chan.set_file_info(file_handle, pike.smb2.FileDispositionInformation) as file_info:
                 file_info.delete_pending = 1
            print "Set operation successful"
            print "Querying the file for new delete_pending value"
            info1 = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            delete_pending1 = info1.standard_information.delete_pending
            print "The value of delete pending flag after doing set operation : ",delete_pending1
            print "Verifying that if delete_pending flag set to 1"
            self.assertEqual(1,delete_pending1)
            print "After closing file handle, the file should get deleted from server"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Try to open file with FILE_OPEN flag. It should fail"
            file_handle2 = chan.create(tree,'set_test2.txt',access=pike.smb2.FILE_READ_ATTRIBUTES, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN).result()

            if isinstance(file_handle2,pike.model.Open):
                actual_status = "STATUS_SUCCESS"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 02 has passed"

    def test_set_endoffile(self):
        try:
            print "---------------------------------------------------------"
            print "TC 03 - Set the End of File flag (FILE_END_OF_FILE_INFORMATION class) and verify the status"
            buffer = "testing123"
            buffer2 = "@calsoft"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Trying to create a file"
            response = self.create_file("set_test3.txt")
            print "File creation successful"
            print "Trying to write the buffer"
            bytes_written = self.chan.write(response,0,buffer)
            print "Data write successful"
            print "Querying the file for end of file flag value"
            info = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            endoffile = info.standard_information.end_of_file
            print "The value of end of file flag before doing set operation : ",endoffile
            print "Trying to set the end of file flag value to 23 using set operation"
            with self.chan.set_file_info(response, pike.smb2.FileEndOfFileInformation) as file_info:
                file_info.endoffile = 23
            print "Set operation successful"
            print "Querying the file for new end of file flag value"
            info1 = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            new_endoffile = info1.standard_information.end_of_file
            print "The value of end of file flag after doing set operation : ",new_endoffile
            print "Writing data into file"
            bytes_written1 = self.chan.write(response,23,buffer2)
            print "Buffer write successful"
            print "Querying the file for new endoffile"
            info2 = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            new_endoffile1 = info2.standard_information.end_of_file
            print "After writing data the value of end of file flag :",new_endoffile1
            total_endoffile = new_endoffile + len(buffer2)
            print "The total endoffile flag value is:",total_endoffile
            print "Verifying total endoffile length and length of endoffile after buffer write"
            self.assertEqual(total_endoffile,new_endoffile1)
            actual_status = "STATUS_SUCCESS"
            print "Close the handle"
            self.chan.close(response)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 03 has passed"

    def test_set_valid_data(self):
        try:
            print "---------------------------------------------------------"
            print "TC 04 - Set the correct Valid data length flag (FileValidDataLengthInformation class) and verify the status"
            buffer = "testing123"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Trying to create a file"
            response = self.create_file("set_test4.txt")
            print "File created successfully"
            print "Trying to write buffer"
            bytes_written = self.chan.write(response,0,buffer)
            print "Buffer write successful"
            print "The length of buffer in file is",len(buffer)
            print "Setting the correct value of buffer with Set operation"
            with self.chan.set_file_info(response, pike.smb2.FileValidDataLengthInformation) as file_info:
                file_info.valid_data_length = len(buffer)
            print "Set operation successful"
            info = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
            print "Close the handle"
            self.chan.close(response)
            print "File handle closed successfully"
            actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 04 has passed"

    def test_set_invalid_data_len(self):
        try:
           print "---------------------------------------------------------"
           print "TC 05 - Set the incorrect Valid data length flag (FileValidDataLengthInformation class) and verify the status"
           buffer = "testing123"
           expected_status = "STATUS_INVALID_PARAMETER"
           print "Expected status:",expected_status
           print "Trying to create a file"
           response = self.create_file("set_test5.txt")
           print "File created successfully"
           print "Trying to write data"
           bytes_written = self.chan.write(response,0,buffer)
           print "Buffer write successful"
           print "The length of buffer in file is",len(buffer)
           print "Setting the incorrect value of length of buffer using Set operation"
           with self.chan.set_file_info(response, pike.smb2.FileValidDataLengthInformation) as file_info:
               file_info.valid_data_length = len(buffer) + 5
           print "Set operation successful"
           print "Close the handle"
           self.chan.close(response)
           print "File handle closed successfully"
           actual_status = None
        except Exception as e:
           actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 05 has passed"

    def test_set_valid_data_write_protected(self):
        try:
            print "--------------------------------------------------------"
            print "TC 06 - Try to write the data when file doesn't have  write permission (FileValidDataLengthInformation class) and verify the status"
            buffer = "testing123"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status:",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Trying to create file"
            file_handle = chan.create(tree,'set_test6.txt',access=pike.smb2.FILE_READ_ATTRIBUTES, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created successfully"
            print "Trying to set the valid data length flag with length of buffer"
            with chan.set_file_info(file_handle, pike.smb2.FileValidDataLengthInformation) as file_info:
               file_info.valid_data_length = len(buffer)
            print "Set operation successful"
            print "Trying to write the file"
            bytes_written = self.chan.write(file_handle,0,buffer)
            print "Buffer write successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            if bytes_written == len(buffer) :
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 06 has passed"

    def test_set_zero_data_len(self):
        try:
           print "---------------------------------------------------------"
           print "TC 07 - Set the Valid data length flag = 0(FileValidDataLengthInformation class) and verify the status"
           buffer = "testing123"
           expected_status = "STATUS_INVALID_PARAMETER"
           print "Expected status:",expected_status
           print "Trying to create file"
           response = self.create_file("set_test7.txt")
           print "File created successfully"
           print "Trying to write data"
           bytes_written = self.chan.write(response,0,buffer)
           print "The length of buffer in file is",len(buffer)
           print "Setting the incorrect value of buffer using Set Command"
           with self.chan.set_file_info(response, pike.smb2.FileValidDataLengthInformation) as file_info:
               file_info.valid_data_length = 0
           print "Set operation successful"
           print "Close the file handle"
           self.chan.close(response)
           print "File handle closed successfully"
           actual_status = None
        except Exception as e:
           actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 07 has passed"

    def test_set_allocsize_without_writeperm(self):
        try:
            print "--------------------------------------------------------"
            print "TC 08 - Try to set the allocation size(FILE_ALLOCATION_INFORMATION class) for a file which doesn't have write permission the data or attribute  and verify the status"
            alloc_size = 8192
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status:",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Trying to create file"
            file_handle = chan.create(tree,'set_test8.txt',access=pike.smb2.FILE_READ_ATTRIBUTES, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File created successfully"
            print "Trying to change allocation size using Set operation"
            with chan.set_file_info(file_handle, pike.smb2.FileAllocationInformation) as file_info:
                file_info.allocation_size = alloc_size

            print "Set operation successful"
            print "Querying the file for new allocation size value"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            new_alloc_size = info.standard_information.allocation_size
            print "Verifying the allocation size value to be set and allocation szie after set operation"
            self.assertEqual(alloc_size,new_alloc_size)
            actual_status = "STATUS_SUCCESS"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 08 has passed"

    def test_set_allocsize_directory(self):
        try:
            print "--------------------------------------------------------"
            print "TC 09 - Try to set the allocation size(FILE_ALLOCATION_INFORMATION class) for a directory and verify the status"
            alloc_size = 8192
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status:",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Trying to create Directory"
            file_handle = chan.create(tree,'set_test9',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "Directory created successfully"
            print "Trying to change allocation size value using Set Command"
            with chan.set_file_info(file_handle, pike.smb2.FileAllocationInformation) as file_info:
                file_info.allocation_size = alloc_size
            print "Set operation successfully"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = None
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 09 has passed"

    def test_set_disposition_info_without_delete(self):
        try:
           print "---------------------------------------------------------"
           print "TC 10 - Set the Delete pending flag (FILE_DISPOSITION_INFORMATION class) without delete access  and verify the status"
           expected_status = "STATUS_ACCESS_DENIED"
           print "Expected status:",expected_status
           print "Trying to create file"
           response = self.create_file("set_test10.txt")
           print "File created successfully"
           print "Trying to change deletepending flag value using Set operation"
           with self.chan.set_file_info(response, pike.smb2.FileDispositionInformation) as file_info:
                file_info.deletepending = 1
           print "Querying the file for deletepending flag"
           info = self.chan.query_file_info(response,pike.smb2.FILE_ALL_INFORMATION)
           delete_pending = info.standard_information.delete_pending
           print "The value of deletepending flag after set operation:",delete_pending
           print "Verifying Deletepending flag value with 1"
           self.assertEqual(1,delete_pending)
           actual_status = "STATUS_SUCCESS"
           print "Close the file handle"
           self.chan.close(response)
           print "File handle closed successfully"
        except Exception as e:
           actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 10 has passed"

    def test_set_endoffile_directory(self):
        try:
            print "---------------------------------------------------------"
            print "TC 11 - Set the End of File flag (FILE_END_OF_FILE_INFORMATION class)for the directory and verify the status"
            buffer = "testing123"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status:",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and Treeconnect successful"
            print "Trying to create directory"
            file_handle = chan.create(tree,'set_test11',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "Directory created successful"
            print "Trying to set endoffile equal to 0 using Set operation"
            with chan.set_file_info(file_handle, pike.smb2.FileEndOfFileInformation) as file_info:
                file_info.endoffile = 0
            print "Trying to write data"
            bytes_written1 = chan.write(file_handle,0,buffer)
            print "Data write successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = None
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 11 has passed"
