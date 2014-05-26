#Copyright (C) Calsoft.  All rights reserved.
#
# Module Name:
#
#        create_open_additional.py
#
# Abstract:
#
#        Additional test cases of Create open file
#
# Authors: Prayas Gupta (prayas.gupta@calsoftinc.com)
#
import pike.smb2
import pike.model
import pike.test
import re
import random
import array
import utils


class CreateOpen(pike.test.PikeTest):

    def __init__(self, *args, **kwargs):
        super(CreateOpen, self).__init__(*args, **kwargs)
        self.buffer = "testing123456"

    def test_open_file_append(self):
        try:
            print "----------------------------------"
            print "TC001 - Open a file for append and try to read it.Should have read persmissions"
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'create001.txt', access=pike.smb2.FILE_READ_DATA|pike.smb2.FILE_WRITE_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File creation successful"
            print "Writing data into file"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Data write successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle,len(self.buffer),0)
            print "Read data successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Matching Bytes_read and Buffer length"
            if len(bytes_read) == len(self.buffer):
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC001 has passed"

    def test_open_file_without_read(self):

        try:
            print "----------------------------------"
            print "TC002 - Open a file for append without read permissions. Try to read from the file."
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'create002.txt', access=pike.smb2.FILE_WRITE_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
            print "File creation successful"
            print "Writing data into file"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Data write successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle,len(self.buffer),0)
            print "Read data successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC002 has passed"

    def test_open_file_execute(self):
        try:
            print "------------------------------------"
            print "TC003 -  open a file with execute and read it."
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create003.txt',access=pike.smb2.FILE_WRITE_DATA ,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Writing data into file"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Data write successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Opening file with FILE_EXECUTE"
            file_handle1 = chan.create(tree,'Create003.txt',access=pike.smb2.FILE_EXECUTE,disposition=pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Opening file successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            print "Read data successful"
            print "Close the handle"
            chan.close(file_handle1)
            print "File handle closed successfully"
            print "Matching Bytesread and buffer length"
            if len(bytes_read) == len(self.buffer):
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC003 has passed"

    def test_open_file_readattr(self):
        try:
            print "-------------------------------------"
            print "TC004 - Open a file for read attr and try to read from the file"
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create004.txt',access=pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_READ_DATA,disposition=pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Querying the file"

            conv_obj = utils.Convenience()
            query_packet = conv_obj.query_file_info(chan, file_handle, pike.smb2.FILE_ALL_INFORMATION)
            res = conv_obj.transceive(chan,query_packet)
            info = res[0]

            #info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Querying file is successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(info.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC004 has passed"

    def test_open_file_read_sync(self):

        try:
            print "--------------------------------------"
            print "TC 005 - Open with read and sync set . Server should ignore sync  and allow read."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create005.txt',access = pike.smb2.FILE_READ_DATA|pike.smb2.SYNCHRONIZE|pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Writing data into file"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Data write successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle,len(self.buffer),0)
            print "Read data successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Matching Bytesread and buffer length"
            if len(bytes_read) == len(self.buffer):
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC005 has passed"

    def test_open_file_all_cases(self):
        try:
            print "----------------------------------------"
            print "TC006 - Open for all cases with desired access set to 0.See the server response."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create006.txt',access = 0,disposition=pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "If file handle exists"
            if isinstance(file_handle,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC006 has passed"


    def test_open_file_maxallowed_ro(self):

        try:
            print "-----------------------------------------"
            print "TC007 - Open with Max_allowed flag on a RO file.Try writing data on the file"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create007.txt',access =pike.smb2.MAXIMUM_ALLOWED,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File creation successful"
            print "Querying the file"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Querying is successful"
            file_attr = info.basic_information.file_attributes
            print "File attribute is :",file_attr
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Opening the file"
            file_handle2 = chan.create(tree,'Create007.txt',access =pike.smb2.MAXIMUM_ALLOWED,disposition=pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Opening file is successful"
            print "Trying to write data"
            bytes_written = chan.write(file_handle2,0,self.buffer)
            print "Write data successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle2,len(self.buffer),0)
            print "Read data successful"
            print "Matching Byteswritten and Bytesread with buffer length"
            if bytes_written == len(self.buffer) and len(bytes_read) == len(self.buffer):
                actual_status = "STATUS_SUCCESS"
            print "Close the second handle"
            chan.close(file_handle2)
            print "Second handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC007 has passed"


    def test_open_file_maxallowed_wo(self):

        try:
            print "------------------------------------------"
            print "TC008 - Open a RO file with write permissions and try writing data "
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create008.txt',access =pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File creation successful"
            print "Close the handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Opening the file"
            file_handle2 = chan.create(tree,'Create008.txt',access =pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Opening file is successful"
            print "Trying to write data"
            bytes_written = chan.write(file_handle2,0,self.buffer)
            print "Write data successful"
            print "Close the second handle"
            chan.close(file_handle2)
            print "Second handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC008 has passed"

    def test_open_file_appenddata(self):
        buffer2 = "@calsoft"
        try:
            print "----------------------------------------------"
            print "TC009 - Open a file for append and append data"
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create009.txt',access = pike.smb2.FILE_APPEND_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Trying to write data"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Write data successful"
            print "Close first handle"
            chan.close(file_handle)
            print "First handle closed successfully"
            print "Opening the file"
            file_handle2 = chan.create(tree,'Create009.txt',access = pike.smb2.FILE_APPEND_DATA,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()

            print "File opening successful"
            print "Trying to append data"
            bytes_written2 = chan.write(file_handle2,len(self.buffer),buffer2)
            print "Append data successful"
            final_buffer = len(self.buffer) + len(buffer2)
            print "The final buffer length is :",final_buffer
            final_bytes_written = int(bytes_written + bytes_written2)
            print "The final buffer written length is :",final_bytes_written
            print "Checking final buffer length and final buffer written length is equal or not"
            if final_buffer == final_bytes_written:
                actual_status = 'STATUS_SUCCESS'
            print "Close the second handle"
            chan.close(file_handle2)
            print "Second handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC009 has passed"

    def test_open_file_write_ea(self):
        try:
            print "--------------------------------------"
            print "TC 010 - Open a file that does not have permission to write-ea for write-ea "
            easize = 0
            expected_status = str(easize)
            print "Expected status: ",expected_status
            conv_obj=utils.Convenience()
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            create_tmp,create_resp = conv_obj.create(chan,tree,'Create10.txt',
                    access=pike.smb2.FILE_READ_EA | pike.smb2.FILE_READ_ATTRIBUTES,
             attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL,
             disposition=pike.smb2.FILE_OPEN_IF,
             options=pike.smb2.FILE_NON_DIRECTORY_FILE,
             extended_attr={"Author":"Prayas"})
            file = create_tmp.result()
            print "File opening successful"
            print "Querying the file and checking EA size value"
            info = chan.query_file_info(file,pike.smb2.FILE_ALL_INFORMATION)
            ea_size = info.ea_information.ea_size
            print "The ea size of file is :",ea_size
            actual_status = str(ea_size)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC010 has passed"

    def test_open_file_readattributes(self):
        try:
            print "-----------------------------------------"
            print "TC 011 - Open a file to read attributes that has the proper permissions i.e FILE_READ_ATTRIBUTES."
            expected_status = "FILE_ATTRIBUTE_ARCHIVE"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create011.txt',access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File opening successful"
            print "Reading file-attribute"
            conv_obj = utils.Convenience()
            query_packet = conv_obj.query_file_info(chan, file_handle, pike.smb2.FILE_ALL_INFORMATION)
            res = conv_obj.transceive(chan,query_packet)
            info = res[0]
            file_attribute = info.children[0][0].basic_information.file_attributes
            print "The file attributes is :",file_attribute
            actual_status = str(file_attribute)
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC011 has passed"

    def test_open_file_without_readattributes(self):
        try:
            print "-----------------------------------------"
            print "TC 012 - Open a file which does NOT have read attribute permission, and try to read attributes."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            conv_obj = utils.Convenience()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create012.txt',access = pike.smb2.FILE_WRITE_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File opening successful"
            print "Trying to read attributes"
            query_packet = conv_obj.query_file_info(chan, file_handle, pike.smb2.FILE_ALL_INFORMATION)
            res = conv_obj.transceive(chan, query_packet)
            info = res[0]
            file_attribute = info.children[0][0].basic_information.file_attributes
            print "The file attributes is :",file_attribute
            actual_status = str(info.status)
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC012 has passed"

    def test_open_file_writeattributes(self):
        try:
            print "-------------------------------------------"
            print "TC 013 - Open a file with perms(FILE_WRITE_ATTRIBUTES) to change attributes. Change some attribute of the file and save"
            expected_status = "FILE_ATTRIBUTE_READONLY"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create013.txt',access = pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File opening successful"
            print "Trying to read the file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute_old = info.basic_information.file_attributes
            print "When file created file-attribute is :",file_create_attribute_old
            print "Changing file-attribute to FILE_ATTRIBUTE_READONLY"
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Checking file for changed attribute"
            info1 = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute_new = info1.basic_information.file_attributes
            print "The changed attribute is : ",file_create_attribute_new
            actual_status =str(file_create_attribute_new)
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC013 has passed"

    def test_open_file_without_writeattributes(self):
        try:
            print "-------------------------------------------"
            print "TC 014 - Open a file which doesn't have  perms(FILE_WRITE_ATTRIBUTES) to change attributes"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create014.txt',access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File opening successful"
            print "Reading the file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute = info.basic_information.file_attributes
            print "When file created file attribute is :",file_create_attribute
            print "Trying to change file attribute"
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC014 has passed"

    def test_open_file_synchronize(self):
        try:
            print "-------------------------------------------"
            print "TC 015 - Open a file with SYNCHRONIZE flag and verify server ignores this flag"
            expected_status = "SYNCHRONIZE | FILE_READ_ATTRIBUTES"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create015.txt',access = pike.smb2.SYNCHRONIZE | pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File opening successful"
            print "Reading desired access of file"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_desired_access = info.access_information.access_flags
            print "The file got created and opened ignoring Desired access(SYNCHRONIZE) flag",file_desired_access
            actual_status = str(file_desired_access)
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC015 has passed"

    def test_open_file_read_max_allowed(self):
        buffer1 = "Calsoft"
        try:
            print "------------------------------------------"
            print "TC 016 - Open a file that has file attribute = READONLY and desired access with maximum allowed and verify that only read is allowed and write fails"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create016.txt',access = pike.smb2.MAXIMUM_ALLOWED,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File creation successful"
            print "Writing data into file"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Buffer writing successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
            print "Opening file"
            file_handle1 = chan.create(tree,'Create016.txt',access = pike.smb2.MAXIMUM_ALLOWED,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File opening successful"
            print "Trying to read data"
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            if len(bytes_read) == len(self.buffer):
                print "Read data successful"
            print "Trying to write data into file when file is open with attribute = FILE_ATTRIBUTE_READONLY"
            bytes_written1 = chan.write(file_handle1,0,buffer1)
            if bytes_written1 == len(buffer1):
                print "Bytes write is successful"
                actual_status = "STATUS_SUCCESS"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC016 has passed"

    def test_open_file_append_write(self):
        buffer2 = "@calsoft"
        try:
            print "-------------------------------------------"
            print "TC 017 - Open a file with append and write permission with MAXIMUM ALLOWED flag."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create017.txt',access = pike.smb2.MAXIMUM_ALLOWED|pike.smb2.FILE_APPEND_DATA|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Trying to write buffer"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Buffer write successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create017.txt',access = pike.smb2.MAXIMUM_ALLOWED|pike.smb2.FILE_APPEND_DATA|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File Open successful"
            print "Trying to append buffer"
            bytes_written2 = chan.write(file_handle1,14,buffer2)
            print "Append data successful"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
            final_buffer = len(self.buffer) + len(buffer2)
            print "The final buffer length is :",final_buffer
            final_bytes_written = int(bytes_written + bytes_written2)
            print "The final buffer written length is :",final_bytes_written
            print "Matching final buffer and final_bytes_written"
            if final_buffer == final_bytes_written:
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC017 has passed"

    def test_open_file_genericall_readonly(self):

        try:
            print "-------------------------------------------"
            print "TC 018 - Open with generic all  with read only permissions. Try to write the file."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create018.txt',access = pike.smb2.GENERIC_ALL,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File creation successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create018.txt',access = pike.smb2.GENERIC_ALL,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "File Open successful"
            print "Trying to write data"
            bytes_written = chan.write(file_handle1,0,self.buffer)
            print "Buffer write successful"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"

        except Exception as e :
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC018 has passed"

    def test_open_file_genericall_readwrite(self):

        try:
            print "----------------------------------------------"
            print "TC019 - Open with generic all with read-write  permissions. try to write and then read the written data"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening file"
            file_handle = chan.create(tree,'Create019.txt',access = pike.smb2.GENERIC_ALL|pike.smb2.FILE_READ_DATA|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creat and open successful"
            print "Try to write data"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Write buffer successful"
            print "Try to read data"
            bytes_read = chan.read(file_handle,len(self.buffer),0)
            print "Buffer read successful"
            print "The length of bytes written:",bytes_written
            print "The length of bytes read :",len(bytes_read)
            print "Matching bytes_written and length of bytes_read"
            if bytes_written == len(bytes_read):
                actual_status = "STATUS_SUCCESS"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successful"
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC019 has passed"

    def test_open_file_genericaall_writeonly(self):

        try:
            print "---------------------------------------------"
            print "TC020 - Open file with generic all and  write only permissions and try to read"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create020.txt',access = pike.smb2.GENERIC_ALL|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Trying to write data"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Write bufffer successful"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create020.txt',access = pike.smb2.GENERIC_ALL|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File open successfull"
            print "Trying to read data"
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            print "Read data successfull"
            print "The length of bytes written:",bytes_written
            print "The length of bytes read :",len(bytes_read)
            print "Matching bytes_written and length of bytes_read"
            if bytes_written == len(bytes_read):
                actual_status = "STATUS_SUCCESS"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC020 has passed"

    def test_open_genericwrite(self):

        try:
            print "---------------------------------------------"
            print "TC 021 -  open a file with generic write and try to write."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan, tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create021.txt',access = pike.smb2.GENERIC_WRITE,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create021.txt',access = pike.smb2.GENERIC_WRITE,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File open successfull"
            print "Try to write data"
            bytes_written = chan.write(file_handle1,0,self.buffer)
            print "Write data successfull"
            print "The length of bytes written:",bytes_written
            print "The length of buffer is :",len(self.buffer)
            print "Matching the length of buffer and bytes_written"
            if len(self.buffer) == bytes_written:
                actual_status = "STATUS_SUCCESS"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual Status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC021 has passed"

    def test_open_genericwrite_writeattr(self):
        try:
            print "-------------------------------------------"
            print "TC 022 - open a file with generic write and write Attributes and try to change attributes"
            expected_status = "FILE_ATTRIBUTE_READONLY"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create022.txt',access = pike.smb2.GENERIC_WRITE|pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Trying to read the attribute of file"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute = info.basic_information.file_attributes
            print "When file created file attribute is :",file_create_attribute
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create022.txt',access = pike.smb2.GENERIC_WRITE|pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File open successfull"
            print "Trying to change the attribute of file"
            with chan.set_file_info(file_handle1, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Querying the file and checking the new file attribute"
            info1 = chan.query_file_info(file_handle1,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute_new = info1.basic_information.file_attributes
            print "The new file attribute after change is :",file_create_attribute_new
            actual_status =str(file_create_attribute_new)
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual File Attribute :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC022 has passed"

    def test_open_genericread(self):
        try:
            print "---------------------------------------------"
            print "TC 023 -open a file with generic read and try to read data."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create023.txt',access = pike.smb2.GENERIC_READ|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Trying to write buffer"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Buffer write successful"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create023.txt',access = pike.smb2.GENERIC_READ,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File open successfull"
            print "Trying to read the buffer"
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            print "Buffer read successful"
            print "The length of bytes written is :",bytes_written
            print "The length of bytes read is :",len(bytes_read)
            print "Matching the bytes_written and length of bytes_read"
            if bytes_written == len(bytes_read):
                actual_status = "STATUS_SUCCESS"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
             actual_status = str(e)
        print "Actual Status is :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC023 has passed"

    def test_open_genericread_attr(self):
        try:
            print "---------------------------------------------"
            print "TC 024 - open a file with generic read and read Attributes."
            expected_status = "FILE_ATTRIBUTE_ARCHIVE"
            print "Expected status: ",expected_status
            print "Creating session and treeconnect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating file"
            file_handle = chan.create(tree,'Create024.txt',access = pike.smb2.GENERIC_READ,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File creation successful"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Opening the file"
            file_handle1 = chan.create(tree,'Create024.txt',access = pike.smb2.GENERIC_READ,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File open successfull"
            print "Querying the file to read the attribute"
            info = chan.query_file_info(file_handle1,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute = info.basic_information.file_attributes
            print "When file created file attribute is :",file_create_attribute
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
            actual_status = str(file_create_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC024 has passed"

    def test_open_shareread(self):

        try:
            print "---------------------------------------------"
            print "TC 025 - Open a file with file share read. Over a different session open the same with file for write"
            expected_status = "STATUS_SHARING_VIOLATION"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file with FILE_SHARE_READ with GENERIC_READ"
            file_handle = chan.create(tree,'Create025.txt',access = pike.smb2.GENERIC_READ,share= pike.smb2.FILE_SHARE_READ,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file with GENERIC_WRITE and FILE_SHARE_READ"
            file_handle1 = chan1.create(tree1,'Create025.txt',access = pike.smb2.GENERIC_WRITE,share = pike.smb2.FILE_SHARE_READ,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Trying to write data into file"
            bytes_written = chan.write(file_handle1,0,self.buffer)
            print "Write buffer successful"
            print "Closing first handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Closing second handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC025 has passed"

    def test_open_shareread_delete(self):
        try:
            print "-----------------------------------------------"
            print "TC 026 - Open a file with file share read. Over a different session, open a file with  deleteflag set."
            expected_status = "STATUS_SHARING_VIOLATION"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file with FILE_SHARE_READ and GENERIC_READ"
            file_handle = chan.create(tree,'Create026.txt',access = pike.smb2.GENERIC_READ,share= pike.smb2.FILE_SHARE_READ,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file with DELETE and FILE_SHARE_READ"
            file_handle1 = chan1.create(tree1,'Create026.txt',access = pike.smb2.DELETE,share = pike.smb2.FILE_SHARE_READ,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Closing first handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Closing second handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC026 has passed"

    def test_open_sharewrite(self):
        buffer1 = "@Calsoft"
        try:
            print "------------------------------------------------"
            print "TC 027 - Open a file with file share write and from different session, open for write. Try writing to different areas of files"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file with FILE_SHARE_WRITE and FILE_WRITE_DATA"
            file_handle = chan.create(tree,'Create027.txt',access = pike.smb2.FILE_WRITE_DATA,share= pike.smb2.FILE_SHARE_WRITE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file with FILE_WRITE_DATA and FILE_SHARE_WRITE"
            file_handle1 = chan1.create(tree1,'Create027.txt',access = pike.smb2.FILE_WRITE_DATA,share = pike.smb2.FILE_SHARE_WRITE,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Writing data into it"
            bytes_written = chan1.write(file_handle1,0,self.buffer)
            if bytes_written == len(self.buffer):
                print "Write buffer successful"
            print "Appending data"
            bytes_written1 = chan1.write(file_handle1,20,buffer1)
            if bytes_written1 == len(buffer1):
                print "Append data successful"
                actual_status = "STATUS_SUCCESS"
            print "Closing first handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Closing second handle"
            chan1.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC027 has passed"

    def test_open_sharewrite_read(self):

        try:
            print "------------------------------------------------"
            print "TC 028 -  Open a file with file share write and then open from different session with file share read."
            expected_status = "STATUS_SHARING_VIOLATION"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file with FILE_SHARE_WRITE and FILE_WRITE_DATA"
            file_handle = chan.create(tree,'Create028.txt',access = pike.smb2.FILE_WRITE_DATA,share= pike.smb2.FILE_SHARE_WRITE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Writing data into it ..."
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Write buffer successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file with FILE_WRITE_DATA and FILE_SHARE_READ"
            file_handle1 = chan1.create(tree1,'Create028.txt',access = pike.smb2.FILE_WRITE_DATA,share = pike.smb2.FILE_SHARE_READ,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Trying to read data ..."
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            print "Read data successful"
            print "Close the first handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Close the second handle"
            chan1.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status :",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC028 has passed"

    def test_open_sharedelete_delete(self):
        try:
            print "------------------------------------------------"
            print "TC 029 - Open a file with file share delete and from a different session open for deletion."
            expected_status = "STATUS_SHARING_VIOLATION"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file with FILE_READ_DATA and FILE_SHARE_DELETE"
            file_handle = chan.create(tree,'Create029.txt',access = pike.smb2.FILE_READ_DATA,share= pike.smb2.FILE_SHARE_DELETE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file with DELETE and FILE_SHARE_DELETE"
            file_handle1 = chan1.create(tree1,'Create029.txt',access = pike.smb2.DELETE,share = pike.smb2.FILE_SHARE_DELETE,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Close the first handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Close the second handle"
            chan1.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC029 has passed"

    def test_open_sharedelete_session(self):
        try:
            print "------------------------------------------------"
            print "TC 030 - OPen a file for delete from other session. delete that file i.e close the second open before the first one"
            expected_status = "STATUS_SHARING_VIOLATION"
            print "Expected status: ",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file"
            file_handle = chan.create(tree,'Create030.txt',access = pike.smb2.DELETE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()

            print "Create and open successful"
            print "Creating a second session and tree connect"
            chan1,tree1 = self.tree_connect()
            print "Second Session and treeconnect successful"
            print "Opening the same file"
            file_handle1 = chan1.create(tree1,'Create030.txt',access = pike.smb2.DELETE,share = pike.smb2.FILE_SHARE_DELETE,disposition = pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Open file successful"
            print "Close the second handle"
            chan1.close(file_handle1)
            print "Second file handle closed successfully"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC030 has passed"

    def test_open_supersede(self):
        try:
            print "-----------------------------------------------"
            print "TC 031 -  Open existing flag with File Supersede. Verify that the file is truncated to zero and the create time has not changed."
            expected_status = "STATUS_END_OF_FILE"
            print "Expected status:",expected_status
            print "Creating a first session and tree connect"
            chan,tree = self.tree_connect()
            print "Session and treeconnect successful"
            print "Creating and opening a file"
            file_handle = chan.create(tree,'Create031.txt',access = pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create and open successful"
            print "Querying the file and checking creation time"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            creation_time = info.basic_information.creation_time
            print "When the file created the creation time of  file:",creation_time
            print "Try to write buffer"
            bytes_written = chan.write(file_handle,0,self.buffer)
            print "Buffer write successful"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Creating file with FILE_SUPERSEDE"
            file_handle1 = chan.create(tree,'Create031.txt',access = pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_READ_DATA,disposition = pike.smb2.FILE_SUPERSEDE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Creation file successful"
            print "Query the file and check creation time"
            info1 = chan.query_file_info(file_handle1,pike.smb2.FILE_ALL_INFORMATION)
            creation_time1 = info1.basic_information.creation_time
            print "When the file got supersede creation time:",creation_time1
            print "Try to read data "
            bytes_read = chan.read(file_handle1,len(self.buffer),0)
            print "Read data successful"
            print "Bytes read is :",bytes_read
            print "Close the first file handle"
            chan.close(file_handle1)
            print "First file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "Matching the creation times"
        self.assertRegexpMatches(str(creation_time),str(creation_time1))

    def test_open_file_overwrite(self):
        try:
            print "-----------------------------------------------"
            print "TC 032 - Open a nonexistant file."
            expected_status = "STATUS_OBJECT_NAME_NOT_FOUND"
            print "Expected status: ",expected_status
            print "Creating a  session and tree connect"
            chan,tree = self.tree_connect()
            print "Try overwriting a file"
            file_handle = chan.create(tree,'Create032.txt',access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OVERWRITE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Create file successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)

