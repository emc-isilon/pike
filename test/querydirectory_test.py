#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        querydirectory_test.py
#
# Abstract:
#
#        Query directory tests
#
# Authors: Dhanashree Patil (dhanashree.patil@calsoftinc.com)
#

import pike.model
import pike.smb2
import pike.test


class QueryDirectoryTest(pike.test.PikeTest):

    def test_file_directory_info(self):
        try:
            print "------------------------------------------------------"
            print "TC 01 - Testing the SMB2_QUERY_DIRECTORY for FILE_DIRECTORY_INFORMATION class"
            print "Creating a session and tree connect"
            chan, tree = self.tree_connect()
            print "Session and tree connect successful"
            print "Creating a directory"
            root = chan.create(tree, 'QueryDirectory', access=pike.smb2.GENERIC_ALL, options=pike.smb2.FILE_DIRECTORY_FILE).result()
            print "Directory created successfully"
            print "Querying the directory"
            names = map(lambda info: info.file_name, chan.query_directory(root))
            self.assertIn('.', names)
            self.assertIn('..', names)
            print "Query directory successful"
            print "Close the file handle"
            chan.close(root)
            print "File handle closed successfully"
            print "Test case has Passed"
        except Execption as e:
            print "Test case failed due to ", str(e)

    def test_file_full_directory_info(self):
	try:
	    print "------------------------------------------------------"
	    print "TC 02 - Testing the SMB2_QUERY_DIRECTORY for FILE_FULL_DIRECTORY_INFORMATION class"
            print "Creating a session and tree connect"
  	    chan, tree = self.tree_connect()
            print "Session and tree connect successful"
            print "Creating a directory"
            root = chan.create(tree, 'QueryDirectory', access=pike.smb2.GENERIC_ALL, options=pike.smb2.FILE_DIRECTORY_FILE).result()
            print "Querying the directory"
            names = map(lambda info: info.file_name, chan.query_directory(root, file_information_class=pike.smb2.FILE_FULL_DIRECTORY_INFORMATION))
            self.assertIn('.', names)
            self.assertIn('..', names)
            print "Query directory successful"
            print "Close the file handle"
            chan.close(root)
            print "File handle closed successfully"
	    print "Test case has Passed"
	except Exception as e:
	    print "Test case has failed due to ", str(e)

    def test_file_id_full_dir_info(self):
	try:
	    print "------------------------------------------------------"
	    print "TC 03 - Testing the SMB2_QUERY_DIRECTORY for FILE_ID_FULL_DIRECTORY_INFORMATION class"
            print "Creating a session and tree connect"
            chan, tree = self.tree_connect()
            print "Session and tree connect successful"
            print "Creating a directory"
            root = chan.create(tree, 'QueryDirectory', access=pike.smb2.GENERIC_ALL, options=pike.smb2.FILE_DIRECTORY_FILE).result()
            names = map(lambda info: info.file_name, chan.query_directory(root, file_information_class=pike.smb2.FILE_ID_FULL_DIR_INFORMATION))
            print "Querying the directory"
            self.assertIn('.', names)
            self.assertIn('..', names)
            print "Query directory successful"
            print "Close the file handle"
            chan.close(root)
            print "File handle closed successfully"
	    print "Test case has Passed"
	except Exception as e:
	    print "Test case has failed due to ", str(e)

    def test_file_names_info(self):
        try:
	    print "------------------------------------------------------"
	    print "TC 04 - Testing the SMB2_QUERY_DIRECTORY for FILE_NAMES_INFORMATION class"
            print "Creating a session and tree connect"
	    chan, tree = self.tree_connect()
            print "Session and tree connect successful"
            print "Creating a directory"
            root = chan.create(tree, 'QueryDirectory', access=pike.smb2.GENERIC_ALL, options=pike.smb2.FILE_DIRECTORY_FILE).result()
            print "Querying the directory"
            names = map(lambda info: info.file_name, chan.query_directory(root, file_information_class=pike.smb2.FILE_NAMES_INFORMATION))
            self.assertIn('.', names)
            self.assertIn('..', names)
            print "Query directory successful"
            print "Close the file handle"
            chan.close(root)
            print "File handle closed successfully"
	    print "Test case has Passed"
	except Exception as e:
            print "Test case has failed due to ", str(e)



