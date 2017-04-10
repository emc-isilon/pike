# Copyright (C) Calsoft.  All rights reserved.
#
# Module Name:
#
#        create_additional.py
#
# Abstract:
#
#        Additional test cases of Create file
#
# Authors: Prayas Gupta (prayas.gupta@calsoftinc.com)
#
import pike.smb2
import pike.model
import pike.test
import re
import random
import array

class create_manual(pike.test.PikeTest):
    def test_file_with_readea_set(self):
        file_handle=''
        dir_handle=''
        stat = True
        try:
            print "----------------------------------"
            print "TC001 : Create a file with read attributes set within a directory where read EA permission is not granted on the parent directory"
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
            file_access = pike.smb2.FILE_READ_EA | pike.smb2.FILE_READ_ATTRIBUTES 
	    print "Creating a directory."
            dir_handle = chan.create(tree,'Createman02', access=pike.smb2.FILE_LIST_DIRECTORY, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
	    print "Directory created successfully."
	    print "Creating and opening a file."
            file_handle = chan.create(tree,'Createman02\create02.txt', access=file_access, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
	    print "File created and opened successfully."
            print "Trying to read file information as parent directory doesn't have Read permission"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "The file attribute is :",info.command.children[0].access_information.access_flags

	    print "Closing the file handle."
            chan.close(file_handle)
            print "File handle closed successfully"
	    print "Closing the directory handle."
            chan.close(dir_handle)
            print "Directory handle closed successfully"
        except Exception as e:
            stat = False
        if stat:
            print "Test case 001 has Passed"    
        else:
            print "Failed due to ",str(e)
        self.assertEqual(stat,True)

    def test_file_share(self):

        try:
            print "-----------------------------------"
            print "TC002: Have a file on the share and try to create a new directory with the same filename with CreateOption=FILE_DIRECTORY_FILE and CreateDisposition=FILE_CREATE"
            expected_status = 'STATUS_OBJECT_NAME_COLLISION'
            print "Expected status: ",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating and opening a file."
            file_handle = chan.create(tree,'Createman21',access=pike.smb2.FILE_READ_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN_IF).result()
	    print "File created and opened successfully."
	    print "Creating a directory."
            dir_handle = chan.create(tree,'Createman21', access=pike.smb2.FILE_LIST_DIRECTORY, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
	    print "Directory createdsuccessfully."
            print "Closing the file handle."
	    chan.close(file_handle)
            print "File handle closed successfully"
	    print "Closing the directory handle."			
	    chan.close(dir_handle)
            print "Directory handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching Actual status and Expected status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 002 has passed."
    def test_fileread_attribute(self):
        buffer = "testing 123"
        try:
            print "-----------------------------------"
            print "TC003: Create a file with this(FILE_ATTRIBUTE_READONLY) attribute and try to write to the file"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status :",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
            print "Creating a file."
            file_handle = chan.create(tree,'Createman17.txt', access=pike.smb2.FILE_READ_DATA,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "File created and opened successfully."
	    print "Trying to write to a file."
            bytes_written = chan.write(file_handle,0,buffer)
            print "Buffer write successful"
            print "Closing the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
             actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
	self.assertRegexpMatches(actual_status,expected_status)
	print "TC 003 has passed."
            
    def test_file_sequential_and_random(self):
        try:
            print "-------------------------------------"
            print "TC004: Create a file and in CreateOptions, set both the flags FILE_SEQUENTIAL_ONLY and FILE_RANDOM_ACCESS in the same request."
            expected_status = 'FILE_RANDOM_ACCESS'
            print "Expected File mode: ",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating a file."
            file_handle = chan.create(tree,'Createman022.txt', access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_SEQUENTIAL_ONLY|pike.smb2.FILE_RANDOM_ACCESS).result()
            print "File created successfully."
            print "Querying the file for Mode Information"
            info = chan.query_file_info(file_handle, pike.smb2.FILE_ALL_INFORMATION)
            
            file_mode_info = info.command.children[0].mode_information.mode
            print "File mode info is :",file_mode_info
            actual_status = str(file_mode_info)       
            print "Closing the file handle."
            chan.close(file_handle)
            print "File handle closed successfully" 
        except Exception as e:
            actual_status = str(e)        		
        print "Actual status :",actual_status
        print "Matching the actual_status and expected_status"
        self.assertEqual(actual_status,expected_status)
        print "TC 004 has passed."
	
    def test_file_sequential_only(self):
        try:
            print "-------------------------------------"
            print "TC005: Set flag - FILE_SEQUENTIAL_ONLY only and verify server behaviour"
            expected_status = 'STATUS_SUCCESS'
            print "Expected status :",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating a file."
            file_handle =  chan.create(tree,'Createman023.txt', access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_SEQUENTIAL_ONLY).result()
            print "Querying the file for Mode Information"
            info = chan.query_file_info(file_handle, pike.smb2.FILE_ALL_INFORMATION)
            file_mode = info.command.children[0].mode_information.mode
            print "The file mode is :",file_mode
            actual_status = str(info.status)
            print "Closing the file handle."
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            print "Failed due to :",str(e)
	print "Actual status : ",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 005 has passed."
    
    def test_directory(self):
        try:
            print "-------------------------------------"
            print "TC006: Create a directory on the server and in Create Request, try to create a file with same directory name"
            expected_status = 'STATUS_FILE_IS_A_DIRECTORY'
            print "Expected status :",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating a directory."
            dir_handle = chan.create(tree,'Createman026', access=pike.smb2.FILE_LIST_DIRECTORY, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
	    print "Directory created successfully."
	    print "Creating a file."
            file_handle = chan.create(tree,'Createman026', access=pike.smb2.FILE_READ_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
	    print "File created  successfully."
            if isinstance(file_handle,pike.model.Open):
               actual_status = "STATUS_SUCCESS"    
            print "Closing the directory handle."
            chan.close(dir_handle)
            print "Directory handle closed successfully"			
	    print "Closing the file handle."			
            chan.close(file_handle)
            print "File handle closed successfully"            
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 006 has passed."

    def test_filedirectory_nonfiledirectory(self):
        try:
            print "------------------------------------"
            print "TC007: USE FILE_NON_DIRECTORY_FILE and FILE_DIRECTORY_FILE together"
            expected_status = 'STATUS_INVALID_PARAMETER'
            print "Expected status : ",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating a file."
            file_handle = chan.create(tree,'Createman027.txt', access=pike.smb2.FILE_READ_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE|pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
	    print "File created successfully."
            if isinstance(file_handle,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
            print "Closing the file handle."
            chan.close(file_handle)
            print "File handle closed successfully"			
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 007 has passed."
    
    def test_file_no_eaknowlwdge_and_create_ea_buffer(self):
        try:
            print "--------------------------------------"
            print "TC008: Create a file with this flag(FILE_NO_EA_KNOWLEDGE) set and SMB2_CREATE_EA_BUFFER create context"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status : ",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
            nb_req = chan.frame()
            smb_req1 = chan.request(nb_req, obj=tree)
	    print "Creating a file."
            create_req = pike.smb2.CreateRequest(smb_req1)
            create_req.name = 'createman8.txt'
            create_req.desired_access = pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE
            create_req.file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL
            create_req.create_disposition = pike.smb2.FILE_CREATE
            create_req.create_options = pike.smb2.FILE_NO_EA_KNOWLEDGE
            ea_req = pike.smb2.ExtendedAttributeRequest(create_req)
            name = 'Author'
            value = 'Prayas'
            ea_req.ea_name_length = len(name)
            ea_req.ea_value_length = len(value)
            ea_req.ea_name = name
            ea_req.ea_value =  value
            actual_status = 'STATUS_SUCCESS'
            chan.connection.transceive(nb_req)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 008 has passed."
		
    def test_file_write_attr(self):
        try:
            print "--------------------------------------"
            print "TC009: Create a file with File write attr flag set. Change the attributes of the file."
            expected_status = "FILE_ATTRIBUTE_READONLY"
            print "Expected status : ",expected_status
            chan, tree = self.tree_connect()
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a file."			
            file_handle = chan.create(tree,'Createman09.txt',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_READ_ATTRIBUTES,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "File created successfully."
            print "Querying the file and check file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute = info.command.children[0].basic_information.file_attributes
            print "When file created file attribute is :",file_create_attribute
            print "Trying to change the file attribute"
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            info1 = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_create_attribute_after = info1.command.children[0].basic_information.file_attributes 
            print "After Set operation file attribute of file is :",file_create_attribute_after
            actual_status =str(file_create_attribute_after)
	    print "Closing the file handle."
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual File Attribute :",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status) 
	print "TC 009 has passed."
		
    def test_create_temporary_file_with_data(self):
        buffer = "testing 123"
        try:
            print "--------------------------------------"
            print "TC010: Create a temporary file and write some data into it."
            expected_status = "STATUS_SUCCESS"
            print "Expected status : ",expected_status
            print "Creating a session and tree connect."			
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating a file."
            file_handle1 = chan.create(tree,'Createman10.txt',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "File created successfully."
            print "Changing the file attribute FILE_ATTRIBUTE_TEMPORARY"
            with chan.set_file_info(file_handle1, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_TEMPORARY
            print "Trying to write buffer"
            bytes_written = chan.write(file_handle1,0,buffer)
            print "Buffer write successful"
	    print "Closing the first handle."
            chan.close(file_handle1)
            print "File handle closed successfully"
	    print "Opening the file for read."
            file_handle2 = chan.create(tree,'Createman10.txt',access=pike.smb2.FILE_READ_DATA,disposition=pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "File opened successfully."
            print "trying to read the buffer"
            bytes_read = chan.read(file_handle2,len(buffer),0)
            print "Buffer read successful"
	    print "Closing the second handle."
            chan.close(file_handle2)
            print "Second File handle closed successfully"
            print "Matching the bytes read with length of buffer"
            if len(bytes_read) == len(buffer):
                actual_status = "STATUS_SUCCESS"
        except Exception as e:
            actual_status = str(e)
        print "The temporary file remains in server after close"
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 010 has passed."

    def test_create_temporary_file_without_data(self):
        try:
            print "--------------------------------------"
            print "TC011: Create a temporary file and close without writing any data ."
            expected_status = "STATUS_SUCCESS"
            print "Expected status : ",expected_status
	    print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
	    print "Session and tree connect successful."
	    print "Creating  a file."
            file_handle1 = chan.create(tree,'Createman11.txt',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA,disposition=pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "File created successfully."
            print "Changing the file attribute FILE_ATTRIBUTE_TEMPORARY"
            with chan.set_file_info(file_handle1, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_TEMPORARY
	    print "Closing the first handle."
            chan.close(file_handle1)
            print "File handle closed successfully"
	    print "Opening the file."
            file_handle2 = chan.create(tree,'Createman11.txt',access=pike.smb2.FILE_READ_DATA,disposition=pike.smb2.FILE_OPEN,options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
	    print "Fileopened successfully."
            if isinstance(file_handle2,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
            print "Closing the second handle."
            chan.close(file_handle2)
            print "Second File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "The temporary file remains in server after close"
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
	print "TC 011 has passed."
