#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        create_dir_open_additional.py
#
# Abstract:
#
#        Directory open tests: Directories which are created on the share have to be deleted before test execution otherwise
#        it will result in STATUS_OBJECT_NAME_COLLISION.
#
# Authors: Prayas Gupta (prayas.gupta@calsoftinc.com)
#

from pike.smb2 import *
import pike.test
import utils
import unittest
import pike.model

class directory_open(pike.test.PikeTest):

    def test_01_open_directory_with_file_list_directory(self):
        try:
            print "\n--------------------Open_Directory_TC 01 --------------------"
            print "Test case to list the contents of the directory with FILE_LIST_DIRECTORY permission.\n"
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Open a directory named Directory_open1 with FILE_LIST_DIRECTORY permission:"
            directory_handle =chan.create(tree,"Directory_open1",access = pike.smb2.FILE_LIST_DIRECTORY|pike.smb2.FILE_ADD_FILE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create a normal file inside Directory_open1 with the name Child_file:"
            file_handle = chan.create(tree,"Directory_open1\Child_file",access = pike.smb2.FILE_READ_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Directory_open1 directory."
            print "Close the file handle:"
            chan.close(file_handle)
            print "Child_file handle closed."
            print "Verify whether Child_file is present inside the Directory_open1 directory:"
            names = map(lambda res: res.file_name,chan.query_directory(directory_handle))
            self.assertIn("Child_file", names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open1 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 01 Passed"

    def test_02_open_directory_without_file_list_directory(self):
        try:
            print "\n--------------------Open_Directory_TC 02 --------------------"
            print "Test case to list the contents of the directory without FILE_LIST_DIRECTORY permission.\n"
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Open a directory named Directory_open2 without FILE_LIST_DIRECTORY permission:"
            directory_handle =chan.create(tree,"Directory_open2",access = pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create a normal file inside Directory_open2 with the name Child_file:"
            file_handle = chan.create(tree,"Directory_open2\Child_file",access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Directory_open2 directory."
            print "Close the file handle:"
            chan.close(file_handle)
            print "Child_file handle closed."
            print "Verify whether Child_file is present inside the Directory_open2 directory:"
            names = map(lambda res: res.file_name,chan.query_directory(directory_handle))
            self.assertIn("Child_file", names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open2 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 02 Passed"

    def test_03_open_Child_directory_without_file_list_directory(self):
        try:
            print "\n--------------------Open_Directory_TC 03 --------------------"
            print "Test case to list the contents of the child directory without FILE_LIST_DIRECTORY permission\n."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a directory named Directory_open3 with FILE_LIST_DIRECTORY permission:"
            directory_handle = chan.create(tree,"Directory_open3",access = pike.smb2.FILE_LIST_DIRECTORY,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create child directory inside Directory_open3, named Child_directory without FILE_LIST_DIRECTORY permission:"
            child_handle = chan.create(tree,"Directory_open3\Child_directory",access = pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Child_Directory created inside Directory_open3 directory."
            print "Create a normal file inside Directory_open3\Child_directory named Child_file:"
            file_handle = chan.create(tree,"Directory_open3\Child_directory\Child_file",access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Child_directory."
            print "Close the file handle of Child_file:"
            chan.close(file_handle)
            print "Child_file handle closed."
            print "Verify whether listing the contents of Child_directory:"
            names = map(lambda res: res.file_name,chan.query_directory(child_handle))
            self.assertIn("Child_directory", names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the child directory handle:"
            chan.close(child_handle)
            print "Child_directory handle closed."
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open3 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 03 Passed"

    def test_04_open_directory_with_file_add_file(self):
        try:
            print "\n--------------------Open_Directory_TC 04 --------------------"
            print "Test case to open a directory with FILE_ADD_FILE in desired access, create a file and list the contents of directory\n."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Open a directory named Directory_open4 with FILE_ADD_FILE  permission:"
            directory_handle =chan.create(tree,"Directory_open4",access = pike.smb2.FILE_LIST_DIRECTORY|pike.smb2.FILE_ADD_FILE,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create a normal file inside Directory_open4 named Child_file:"
            file_handle = chan.create(tree,"Directory_open4\Child_file",access = pike.smb2.FILE_READ_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Directory_open4 directory."
            print "Close the file handle:"
            chan.close(file_handle)
            print "Child_file handle closed."
            print "Verify whether Child_file is present inside the Directory_open4 directory:"
            names = map(lambda res: res.file_name,chan.query_directory(directory_handle))
            self.assertIn("Child_file", names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open4 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 04 Passed"

    def test_05_open_directory_without_file_add_file(self):
        try:
            print "\n--------------------Open_Directory_TC 05 --------------------"
            print "Test case to open a directory without FILE_ADD_FILE in desired access, create a file and list the contents of directory\n."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Open a directory named Directory_open5 without FILE_ADD_FILE permission:"
            directory_handle =chan.create(tree,"Directory_open5",access = pike.smb2.FILE_LIST_DIRECTORY|pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create a normal file inside Directory_open5 named Child_file:"
            file_handle = chan.create(tree,"Directory_open5\Child_file",access = pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Directory_open6 directory."
            print "Close the file handle:"
            chan.close(file_handle)
            print "Child_file handle closed."
            print "Verify whether Child_file is present inside the Directory_open5 directory:"
            names = map(lambda res: res.file_name,chan.query_directory(directory_handle))
            self.assertIn("Child_file", names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open5 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 05 Passed"

    def test_06_open_directory_without_read_attributes(self):
        try:
            print "\n--------------------Open_Directory_TC 06 --------------------"
            print "Test case to open a directory to read the attributes without FILE_READ_ATTRIBUTES permission."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status for this test: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a directory named Directory_open6 with FILE_WRITE_ATTRIBUTES permission:"
            directory_handle =chan.create(tree,"Directory_open6",access = pike.smb2.FILE_WRITE_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Reading attributes on the directory:"
            info = chan.query_file_info(directory_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Reading attributes of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open6 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 06 Passed"

    def test_07_open_directory_without_write_attributes(self):
        try:
            print "\n--------------------Open_Directory_TC 07 --------------------"
            print "Test case to open a directory to write the attributes that does not have FILE_WRITE_ATTRIBUTES permission set."
            expected_status = "STATUS_ACCESS_DENIED"
            print "Expected status for this test: ",expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a directory named Directory_open7 without FILE_WRITE_ATTRIBUTES permission:"
            directory_handle =chan.create(tree,"Directory_open7",access = pike.smb2.FILE_READ_ATTRIBUTES,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Reading attributes on the directory before changing them:"
            info = chan.query_file_info(directory_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Reading attributes of the directory completed"
            attribute_before = info.basic_information.file_attributes
            print "Directory FILE_ATTRIBUTE before changing : ",attribute_before
            print "Change the attributes of the directory:"
            with chan.set_file_info(directory_handle, pike.smb2.FileBasicInformation) as directory_info:
                directory_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Changing attributes of the directory completed."
            print "Query attributes on the directory after changing them:"
            info1 = chan.query_file_info(directory_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Querying attributes of the directory completed"
            attribute_after = info1.basic_information.file_attributes
            print "Directory FILE_ATTRIBUTE after changing : ",attribute_after
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open7 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 07 Passed"

    def test_08_open_directory_with_GENERIC_ALL(self):
        try:
            print "\n--------------------Open_Directory_TC 08 --------------------"
            print "Test case to open a directory with GENERIC_ALL permission and try related operations."
            expected_status = "STATUS_SUCCESS"
            print "Expected status: ", expected_status
            print "Creating session and tree connect..."
            chan, tree = self.tree_connect()
            print "Session setup and Tree connect is successful."
            print "Create a directory named Directory_open8 with GENERIC_ALL permission:"
            directory_handle =chan.create(tree,"Directory_open8",access = pike.smb2.GENERIC_ALL,disposition = pike.smb2.FILE_OPEN_IF,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created."
            print "Create a file inside Directory_open10 directory:"
            file_handle = chan.create(tree,"Directory_open8\Child_file1",access = pike.smb2.FILE_WRITE_DATA,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE,share=pike.smb2.FILE_SHARE_DELETE ).result()
            print "File created inside Directory_open8 directory."
            print "Close the file handle:"
            chan.close(file_handle)
            print "Child_file1 file handle closed."
            print "Verifying FILE_ADD_FILE on Directory_open8 directory:"
            file_add_file =chan.create(tree,"Directory_open8\Child_file2",access = pike.smb2.GENERIC_READ,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_NON_DIRECTORY_FILE ).result()
            print "File created inside Directory_open8 directory."
            print "Close the Child_file2 file handle:"
            chan.close(file_add_file)
            print "Child_file2 file handle closed."
            print "Verifying FILE_ADD_SUBDIRECTORY on Directory_open8 directory:"
            file_add_subdirectory = chan.create(tree,"Directory_open8\Child_directory",access = pike.smb2.GENERIC_READ,disposition = pike.smb2.FILE_CREATE,options=pike.smb2.FILE_DIRECTORY_FILE ).result()
            print "Directory created inside Directory_open8 directory."
            print "Close the Child_directory handle:"
            chan.close(file_add_subdirectory)
            print "Child_Directory handle closed."
            print "Query attributes on the directory before changing them:"
            info = chan.query_file_info(directory_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Querying attributes of the directory completed"
            attribute_before = info.basic_information.file_attributes
            print "Directory FILE_ATTRIBUTE before changing : ",attribute_before
            print "Change the attributes of the directory:"
            with chan.set_file_info(directory_handle, pike.smb2.FileBasicInformation) as file_info:
                file_info.file_attributes = pike.smb2.FILE_ATTRIBUTE_READONLY
            print "Changing attributes of the directory completed."
            print "Query attributes on the directory after changing them:"
            info1 = chan.query_file_info(directory_handle,pike.smb2.FILE_ALL_INFORMATION)
            print "Querying attributes of the directory completed."
            attribute_after = info1.basic_information.file_attributes
            print "Directory FILE_ATTRIBUTE after changing : ",attribute_after
            print 'List the contents of the directory Directory_open8: '
            names = map(lambda res: res.file_name,chan.query_directory(directory_handle))
            self.assertIn('Child_file1', names)
            print "Listing the contents of the directory completed"
            actual_status = "STATUS_SUCCESS"
            print "Close the directory handle:"
            chan.close(directory_handle)
            print "Directory_open8 handle closed."
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 08 Passed"

