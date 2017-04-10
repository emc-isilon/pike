#Copyright (C) Calsoft.  All rights reserved.
#
# Module Name:
#
#        create_additional_dir.py
#
# Abstract:
#
#        Additional test cases of Create directory
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

class Create_Dir(pike.test.PikeTest):
    def test_add_sub(self):
        try:
            print "---------------------------------------------"
            print "TC 001 -  Try to Create a directory with same name of  existing dir(FILE_ADD_SUBDIRECTORY). "
            expected_status = "STATUS_OBJECT_NAME_COLLISION"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir001', access=pike.smb2.FILE_ADD_SUBDIRECTORY, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Directory created successfully"
            print "Close the first handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Creating a second directory"
            file_handle1 = chan.create(tree,'CreateDir001', access=pike.smb2.FILE_READ_EA,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Create second directory successful"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 001 has passed."

    def test_add_file_sub(self):
        try:
            print "-----------------------------------------------"
            print "TC 002 - Try to create a directory with same name of existing file."
            expected_status = "STATUS_OBJECT_NAME_COLLISION"
            print "Expected status:",expected_status
            print "Creating session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a file."
            file_handle = chan.create(tree,'CreateDir002', access=pike.smb2.FILE_READ_DATA, options=pike.smb2.FILE_NON_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "File created successfully."
            print "Close the first handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Creating a directory"
            file_handle1 = chan.create(tree,'CreateDir002', access=pike.smb2.FILE_READ_EA,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Create directory successful"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 002 has passed."

    def test_write_attr(self):
        try:
            print "------------------------------------------------"
            print "TC 003 - Create a dir with File write attr flag set. Change the attributes of the file."
            expected_status ="FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_READONLY"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory."
            file_handle = chan.create(tree,'CreateDir003', access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Directory created  successfully."
            print "Querying the directory to check its file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_attribute = info.basic_information.file_attributes
            print "When the directory is created file-attribute is :",file_attribute
            print "Trying to change the attribute"
            with chan.set_file_info(file_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Changing the attribute......"
            info1 = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_attribute1 = info1.basic_information.file_attributes
            print "After changing the file-attribute is :",file_attribute1
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(file_attribute1)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 003 has passed."

    def test_createdir_writeattr(self):
        try:
            print "--------------------------------------------------"
            print "TC 004 -Set this flag(FILE_WRITE_ATTRIBUTES) only and read attributes of the directory"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            conv_obj = utils.Convenience()
            print "Session and tree connect successful."
            print "Creating a directory."
            file_handle = chan.create(tree,'CreateDir004', access=pike.smb2.FILE_WRITE_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Directory created successfully."
            print "Querying the directory to read the attributes"
            query_packet = conv_obj.query_file_info(chan, file_handle, pike.smb2.FILE_ALL_INFORMATION)
            res = conv_obj.transceive(chan, query_packet)
            info = res[0]
            print "Query is successful"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(info.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 004 has passed."

    def test_createdir_hiddenattr(self):
        try:
            print "--------------------------------------------------"
            print "TC 005 -Create a hidden folder and verify that the hidden flag is set."
            expected_status = "FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_HIDDEN"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir005', access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_HIDDEN).result()
            print "Directory created  successfully."
            print "Querying the directory to read the attributes"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_attribute = info.basic_information.file_attributes
            print "The file attribute of the directory is :",file_attribute
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(file_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 005 has passed."

    def test_createsubdir_hiddenattr(self):
        try:
            print "---------------------------------------------------"
            print "TC 006 - Create a hidden folder and inside that folder create regular files and folders. Verify the windows behaviour if the subfolders inherit parent hidden attribute"
            expected_status = "FILE_ATTRIBUTE_DIRECTORY"
            print "Expected status:",expected_status
            print "Creating a first session and tree connect."
            chan, tree = self.tree_connect()
            print "First session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir006', access=pike.smb2.FILE_ADD_SUBDIRECTORY,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_HIDDEN).result()
            print "Directory created successfully."
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            print "Creating a subdirectory inside parent directory"
            file_handle1 = chan.create(tree,'CreateDir006\CreateSubDir006', access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Subdirectory created successfully."
            print "Querying the Subdirectory to read the attributes"
            info = chan.query_file_info(file_handle1,pike.smb2.FILE_ALL_INFORMATION)
            print "Checking for the subdirectory attribute."
            file_attribute = info.basic_information.file_attributes
            print "The file-attribute of subdirectory is :",file_attribute
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second handle closed successfully"
            actual_status = str(file_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 006 has passed."

    def test_createdir_attrnormal(self):
        try:
            print "----------------------------------------------------"
            print "TC 007 - Create a simple directory with this flag set(FILE_ATTRIBUTE_NORMAL), and directory should be visible, non-compressed and unencrypted."
            expected_status = "FILE_ATTRIBUTE_DIRECTORY"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan,tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory."
            file_handle = chan.create(tree,'CreateDir007',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL).result()
            print "Directory created successfully."
            print "Querying the directory"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Checking for the directory attribute."
            file_attribute = info.basic_information.file_attributes
            print "The file-attribute of directory is :",file_attribute
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(file_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 007 has passed."

    def test_createdir_normal(self):
        try:
            print "---------------------------------------------------"
            print "TC 008 -  Create  dir with other flags ( Archive, compressed,encrypted,hidden ... ) set  and verify that this flag(FILE_ATTRIBUTE_NORMAL) is ignored when other flags are set."
            expected_status = "FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_HIDDEN"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir008',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL|pike.smb2.FILE_ATTRIBUTE_HIDDEN).result()
            print "Directory created successfully"
            print "Querying the directory"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_attribute = info.basic_information.file_attributes
            print "File Attribute ",file_attribute
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(file_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 008 has passed."

    def test_createdir_readonly(self):
        try:
            print "----------------------------------------------------"
            print "TC 009 - Create a dir with this attribute(FILE_ATTRIBUTE_READONLY) and try to create new files/directories in the dir.Verify the result"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir009',access=pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_ADD_SUBDIRECTORY,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "Directory created successfully."
            print "Creating a subdirectory."
            file_handle1 = chan.create(tree,'CreateDir009\CreateSubDir009',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "Sub directory created  successfully."
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
            print "Verify the second hanlde has been created or not "
            if isinstance(file_handle1,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 009 has passed."

    def test_createdir_readonly_delete(self):
        try:
            print "-------------------------------------------------------"
            print "TC 010 - Create a dir with this attribute(FILE_ATTRIBUTE_READONLY) and try to delete the dir.Verify the result"
            expected_status = "STATUS_CANNOT_DELETE"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir010',access=pike.smb2.DELETE,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "Directory created successfully."
            print "Open the file with acess = DELETE and options = FILE_DELETE_ON_CLOSE"
            file_handle1 = chan.create(tree,'CreateDir010',access=pike.smb2.DELETE,options=pike.smb2.FILE_DELETE_ON_CLOSE,disposition=pike.smb2.FILE_OPEN,attributes=pike.smb2.FILE_ATTRIBUTE_READONLY).result()
            print "Directory deleted successfully"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
            print "Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 010 has passed."

    def test_createdir_sparse(self):
        try:
            print "-------------------------------------------------------"
            print "TC 011 - Set this flag(FILE_ATTRIBUTE_SPARSE_FILE) and try to create a directory. Should be ignored / error should be returned that the directory cannot be sparse."
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir011',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_SPARSE_FILE).result()
            print "Directory created successfully."
            print "Verify the handle has been created or not "
            if isinstance(file_handle,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 011 has passed."

    def test_createdir_system(self):
        try:
            print "-------------------------------------------------------"
            print "TC 012 - Create a directory with this flag(FILE_ATTRIBUTE_SYSTEM) and verify that this flag is set on the attributes"
            expected_status = "FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_SYSTEM"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory."
            file_handle = chan.create(tree,'CreateDir012',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_SYSTEM).result()
            print "Directory created successfully."
            print "Querying the directory for file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            file_attribute = info.basic_information.file_attributes
            print "The file-attribute of directory is :",file_attribute
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
            actual_status = str(file_attribute)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 012 has passed."

    def test_creatdir_temporary(self):
        try:
            print "--------------------------------------------------------"
            print "TC 013 - Create a temporary directory with flag (FILE_ATTRIBUTE_TEMPORARY) & create a normal file  in that directory."
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir013',access=pike.smb2.FILE_READ_ATTRIBUTES|pike.smb2.FILE_ADD_FILE,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_TEMPORARY).result()
            print "Directory created successfully."
            print "Querying the directory for file attribute"
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            dirname = info.name_information.file_name.split('\\')[2].strip()
            print "The directory name is :",dirname
            print "Creating a sub directory."
            file_handle1 = chan.create(tree,'CreateDir013\CreateSubDir013',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE,attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL).result()
            print "Sub directory created  successfully."
            print "Verifying the file is present or not "
            names = map(lambda res: res.file_name,chan.query_directory(file_handle))
            self.assertIn("CreateSubDir013",names)
            if isinstance(file_handle1,pike.model.Open):
                actual_status = "STATUS_SUCCESS"
            print "Close the second file handle"
            chan.close(file_handle1)
            print "Second file handle closed successfully"
            print"Close the first file handle"
            chan.close(file_handle)
            print "First file handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 013 has passed."

    def test_creatdir_directory(self):
        try:
            print "------------------------------------------------------"
            print "TC 014 - Create nonexisting dir with this flag(FILE_DIRECTORY_FILE) set. Create disposition - file open - should fail."
            expected_status = "STATUS_OBJECT_NAME_NOT_FOUND"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating a directory"
            file_handle = chan.create(tree,'CreateDir014',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_OPEN).result()
            print "Directory created successfully"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 014 has passed."

    def test_createdir_compressed(self):
        try:
            print "-----------------------------------------------------"
            print "TC 015 - Set flag(FILE_NO_COMPRESSION) for directory create. Create should be successful."
            expected_status = "STATUS_SUCCESS"
            print "Expected status:",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "Creating  a directory "
            file_handle = chan.create(tree,'CreateDir015',access=pike.smb2.FILE_READ_ATTRIBUTES,options=pike.smb2.FILE_NO_COMPRESSION|pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Directory created successfully."
            if isinstance(file_handle,pike.model.Open):
               actual_status = "STATUS_SUCCESS"
            print "Close the file handle"
            chan.close(file_handle)
            print "File handle closed successfully"
        except Exception as e:
             actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 015 has passed."

    def test_createdir_EAbuffer(self):
        try:
            print "--------------------------------------"
            print "TC 016: Create a dir with EA buffer. Verify that the EA's were applied to the dir"
            expected_status = 'STATUS_SUCCESS'
            print "Expected status : ",expected_status
            print "Creating a session and tree connect."
            conv_obj=utils.Convenience()
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            print "trying to create a directory"
            create_tmp,create_resp = conv_obj.create(chan,tree,'CreateDir10',
                    access=pike.smb2.FILE_READ_EA | pike.smb2.FILE_READ_ATTRIBUTES,
                    name_offset = None,
                    name_length = None,
                    options=pike.smb2.FILE_DIRECTORY_FILE,
                    extended_attr={"Author":"Prayas"})
            file = create_tmp.result()
            print "Directory create successful with EA buffer set"
            print "Querying the file and checking EA size value"
            info = chan.query_file_info(file,pike.smb2.FILE_ALL_INFORMATION)
            ea_size = info.ea_information.ea_size
            print "The ea size of file is :",ea_size
            if isinstance(file,pike.model.Open):
                actual_status = "STATUS_SUCCESS"
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)
        print "TC 016 has passed."

    def test_createdir_allocation(self):
        try:
            print "-----------------------------------------------------------"
            print "TC 017: Create a dir with allocaiton size.Try to set allocation size on directory"
            expected_status = "STATUS_INVALID_PARAMETER"
            print "Expected status : ",expected_status
            print "Creating a session and tree connect."
            chan, tree = self.tree_connect()
            print "Session and tree connect successful."
            alloc_size = 8192
            print "Trying to create directory"
            file_handle = chan.create(tree,'CreateDir017',access=pike.smb2.FILE_WRITE_ATTRIBUTES|pike.smb2.FILE_WRITE_DATA | pike.smb2.FILE_READ_ATTRIBUTES, options=pike.smb2.FILE_DIRECTORY_FILE,disposition=pike.smb2.FILE_CREATE).result()
            print "Directory created."
            print "Trying to set the alloc size..."
            with chan.set_file_info(file_handle, pike.smb2.FileAllocationInformation) as file_info:
                file_info.allocation_size = alloc_size
            info = chan.query_file_info(file_handle,pike.smb2.FILE_ALL_INFORMATION)
            Alloc_size = info.standard_information.allocation_size
            print "Alloc size set successfully",Alloc_size
            print "Matching the Allcation size value"
            if Alloc_size == alloc_size:
                actual_status = "STATUS_SUCCESS"
            chan.close(file_handle)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:",actual_status
        print "Matching the actual_status and expected_status"
        self.assertRegexpMatches(actual_status,expected_status)



