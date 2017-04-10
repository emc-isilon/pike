#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        query_info.py
#
# Abstract:
#
#        SMB2_QUERY_INFO command tests. These tests aim to test Query 
#         info functionality incorporated in Pike framework and
#         standard results are as observed on Windows2k8r2 server. 
#         If OneFS behavior matches with the Windows server behavior, the 
#         test is marked as Passed, else failed.
#        Along with testing query_info_file with SMB2_0_INFO_FILE info-type,
#        it also checks for SMB2_0_INFO_FILESYSTEM in one test case.
#        
#        If query_file operation is done without having READ_ATTRIBUTES 
#        permission, the request shall Fail.
#
#        open_file method serves as a re-usable method to open a file with 
#         access set to FILE_READ_ATTRIBUTES on a NON_DIRECTORY_FILE.
#        Access parameter is over-written as per requirement of the test case.
# 
# Authors: Abhilasha Bhardwaj(abhilasha.bhardwaj@calsoftinc.com)

import pike.model
import pike.smb2
import pike.test
import unittest
import datetime
import utils

class QueryTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(QueryTest, self).__init__(*args, **kwargs)
        self.chan = None
        self.tree = None
        self.conv_obj = utils.Convenience()

    def gather_info(self, chan, file, file_information_class = pike.smb2.FILE_ALL_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILE):
        """
        """
        query_packet = self.conv_obj.query_file_info(chan, file, file_information_class, info_type)
        res = self.conv_obj.transceive(chan, query_packet)
        return res[0]
        #print "exception in gather info  " + str(err)
        #return err

    def test_01_query_file_network_open_info_for_FILE_READ_ATTRIBUTES(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 01-------------------"
            print "Query FILE_NETWORK_OPEN_INFORMATION when file is opened with FILE_READ_ATTIBUTES"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test01.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test01.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file network info for file test01.txt"

            info = self.gather_info(self.chan, file, pike.smb2.FILE_ALL_INFORMATION)
            print info.children[0][0].basic_information.creation_time
            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_NETWORK_OPEN_INFORMATION)
            print info1.children[0][0].creation_time
            print "Query file network info request for file test01.txt successful."
            print "Validate file creation time."
            self.assertEqual(str(info.children[0][0].basic_information.creation_time), str(info1.children[0][0].creation_time))
            print "Validated file creation time successfully."
            print "Validate file last access time:"
            self.assertEqual(str(info.children[0][0].basic_information.last_access_time), str(info1.children[0][0].last_access_time))
            print "Validated file last access time successfully."
            print "Validate File attributes."
            self.assertEqual(str(info.children[0][0].basic_information.file_attributes), str(info1.children[0][0].file_attributes)) 
            print "Validated File attributes successfully."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 01 has Passed"
			
    def test_02_query_file_network_open_info_for_FILE_READ_DATA(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 02-------------------"
            print "Query FILE_NETWORK_OPEN_INFORMATION when file is opened with access FILE_READ_DATA"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test02.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test02.txt",
                            access=pike.smb2.FILE_READ_DATA,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file info for test02.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_NETWORK_OPEN_INFORMATION)
            print "Query info request for test02.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 02 has Passed"
		
    def test_03_query_file_network_open_info_for_READ_CONTROL(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 03-------------------"
            print "Query FILE_NETWORK_OPEN_INFORMATION when file is opened with access READ_CONTROL"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test03.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test03.txt",
                            access=pike.smb2.READ_CONTROL,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file network info for test03.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_NETWORK_OPEN_INFORMATION)
            print "Query info request for test03.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 03 Passed"

    def test_04_query_file_network_open_info_for_GENERIC_WRITE(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 04-------------------"
            print "Query file FILE_NETWORK_OPEN_INFORMATION when file is opened with access GENERIC_WRITE"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test04.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test04.txt",
                            access=pike.smb2.GENERIC_WRITE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file network info for test04.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_NETWORK_OPEN_INFORMATION)
            print "Query info request for test04.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 04 has Passed"

    def test_05_query_file_attribute_tag_info_for_FILE_READ_ATTRIBUTES(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 05-------------------"
            print "Query FILE_ATTRIBUTE_TAG_INFORMATION when file is opened with access FILE_READ_ATTIBUTES"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test05.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test05.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_OPEN_REPARSE_POINT).result()
            print "File created."
            reparse_tag = 0
            print "Query file attribute tag information for test05.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_ATTRIBUTE_TAG_INFORMATION, pike.smb2.SMB2_0_INFO_FILE)
            print "Query file attribute tag information request for test05.txt successful."
            print "Validating FileAttributeTagInformation:"
            print "The Reparse tag is:", info1.children[0][0].reparse_tag
            self.assertEqual(str(reparse_tag), str(info1.children[0][0].reparse_tag))
            self.assertIn("reparse_tag", str(info1))
            self.assertIn("file_attributes", str(info1))
            print "Validation successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status, "\nTC 05 has failed.")
        print "TC 05 has Passed"		

    def test_06_query_file_attribute_tag_info_for_FILE_READ_DATA(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 06-------------------"
            print "Query FILE_ATTRIBUTE_TAG_INFORMATION when file is opened with access FILE_READ_DATA"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test06.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test06.txt",
                            access=pike.smb2.FILE_READ_DATA,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file attribute tag information for test06.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_ATTRIBUTE_TAG_INFORMATION)
            print "Query info request for test06.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 06 has Passed"

    def test_07_query_file_attribute_tag_info_for_READ_CONTROL(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 07-------------------"
            print "Query FILE_ATTRIBUTE_TAG_INFORMATION when file is opened with access READ_CONTROL"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test07.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test07.txt",
                            access=pike.smb2.READ_CONTROL,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file attribute tag information for test07.txt"

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_ATTRIBUTE_TAG_INFORMATION)
            print "Query request for test07.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 07 has Passed"

    def test_08_query_file_attribute_tag_info_for_GENERIC_WRITE(self):
        """
        """
        try:
            print "\n-------------------Query_file_TC 08-------------------"
            print "Query FILE_ATTRIBUTE_TAG_INFORMATION when file is opened with access GENERIC_WRITE"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test08.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test08.txt",
                            access=pike.smb2.GENERIC_WRITE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file attribute tag info request for test08.txt successful."

            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_ATTRIBUTE_TAG_INFORMATION)
            print "Query request for test08.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status,actual_status)
        print "TC 08 has Passed"

    def test_09_query_file_stream_info(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 09--------------------"
            print "Query FILE_STREAM_INFORMATION when file is opened with access FILE_READ_ATTIBUTES"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test09.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test09.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileStreamInformation for test09.txt"
            
            stream_name = "::$DATA"
            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_STREAM_INFORMATION)
            print "Query request for test09.txt successful."
            print "The stream name : ", info1.children[0][0].stream_name
            self.assertEqual(str(stream_name), str(info1.children[0][0].stream_name))
            print "Validating parameters for FileStreamInformation:"
            self.assertIn("next_entry_offset", str(info1))
            self.assertIn("stream_name_length", str(info1))
            self.assertIn("stream_size", str(info1))
            self.assertIn("stream_allocation_size", str(info1))
            self.assertIn("stream_name", str(info1))
            print "The stream name is:", info1.children[0][0].stream_name
            print "Validation successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
            print "status as returned by server", str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status,actual_status)
        print "TC 09 has Passed"

    def test_10_query_file_compression_info(self):
        """
        """
        try:
            print "\n-------------------Query_file_TC 10--------------------"
            print "Query file FILE_COMPRESSION_INFORMATION when file is opened with access FILE_READ_ATTIBUTES"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test10.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test10.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query file compression information for test10.txt"
            
            info1 = self.gather_info(self.chan, file, pike.smb2.FILE_COMPRESSION_INFORMATION)
            print "Query request for test10.txt successful"
            compressed_file_size = 0
            print "Validate parameters for FileCompressionInformation"
            self.assertEqual( str(compressed_file_size), str(info1.children[0][0].compressed_file_size))
            self.assertIn("compression_format", str(info1))
            self.assertIn("compression_unit_shift", str(info1))
            self.assertIn("chunk_shift", str(info1))
            self.assertIn("cluster_shift", str(info1))
            print "Validation successful"
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status,actual_status)
        print "TC 10 has Passed"

    def test_11_query_file_fs_size_info(self):
        """
        """
        try:
            print "\n-------------------Query_file_TC 11--------------------"
            print "Query file FILE_FS_SIZE_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test11.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test11.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsSizeInformation for test11.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_SIZE_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test11.txt successful."
            print "Validate parameters in FileFsSizeInformation"
            self.assertIn("total_allocation_units", str(info1))
            self.assertIn("available_allocation_unit", str(info1))
            self.assertIn("sectors_per_allocation_unit", str(info1))
            self.assertIn("bytes_per_sector", str(info1))
            print "Validation successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 11 has Passed"

    def test_12_query_file_fs_volume_info(self):
        """
        """
        try:
            print "\n-------------------Query_file_TC 12 --------------------"
            print "Query file FILE_FS_VOLUME_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test12.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test12.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsVolumeInformation for test12.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_VOLUME_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test12.txt successful."
            print "Validate parameters in FileFsVolumeInformation."
            self.assertIn("volume_creation_time", str(info1))
            self.assertIn("volume_serial_number", str(info1))
            self.assertIn("volume_label_length", str(info1))
            self.assertIn("supports_objects", str(info1))
            self.assertIn("volume_label", str(info1))
            print "Validation of parameters successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 12 has Passed"

    def test_13_query_file_fs_device_info(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 13--------------------"
            print "Query file FILE_FS_DEVICE_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test13.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test13.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FILE_FS_DEVICE_INFORMATION for test13.txt."

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_DEVICE_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test13.txt successful."
            print "Validate parameters in FILE_FS_DEVICE_INFORMATION"
            device_type = "FILE_DEVICE_DISK"
            print "Device type on which file system is mounted: ", info1.children[0][0].device_type
            self.assertEqual(str(device_type), str(info1.children[0][0].device_type))
            self.assertIn("characteristics", str(info1))
            print "Validation of parameters successful"
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 13 has Passed"
		
    def test_14_query_file_fs_full_size_info(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 14-------------------"
            print "Query file FILE_FS_FULL_SIZE_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test14.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test14.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Query FILE_FS_FULL_SIZE_INFO for test14.txt."

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_FULL_SIZE_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test14.txt successful."
            print "Validate parameters in FILE_FS_FULL_SIZE_INFORMATION."
            self.assertIn("total_allocation_units", str(info1))
            self.assertIn("sectors_per_allocation_unit", str(info1))
            print "Validation of parameters in FILE_FS_FULL_SIZE_INFORMATION successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 14 has Passed"

    def test_15_query_file_fs_attribute_info(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 15--------------------"
            print "Query file FILE_FS_ATTRIBUTE_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test15.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test15.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "Query file FileFsAttributeInformation for test15.txt."

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_ATTRIBUTE_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for file15.txt successful."
            print "Validate parameters in FILE_FS_ATTRIBUTE_INFO."
            file_system_name = "NTFS"
            self.assertEqual(str(file_system_name), str(info1.children[0][0].file_system_name))
            self.assertIn("file_system_attibutes", str(info1))
            self.assertIn("maximum_component_name_length", str(info1))
            self.assertIn("file_system_name", str(info1))
            print "Name of file system:", info1.children[0][0].file_system_name
            print "Validation of parameters successful."
            self.chan.close(file)
            print "File Closed."	
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 15 Passed"

    def test_16_query_file_fs_ctrl_info_for_FILE_READ_DATA(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 16------------------"
            print "Query file FILE_FS_CONTROL_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test16.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test16.txt",
                            access=pike.smb2.FILE_READ_DATA,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsControlInformation for test16.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_CONTROL_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test16.txt successful"
            print "Validate parameters in FS CTRL info."
            self.assertIn("free_space_start_filtering", str(info1))
            self.assertIn("free_space_threshold", str(info1))
            self.assertIn("free_space_stop_filtering", str(info1))
            self.assertIn("default_quota_threshold", str(info1))
            self.assertIn("default_quota_limit", str(info1))
            self.assertIn("file_system_control_flags", str(info1))
            print "Validation successful"
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 16 has Passed"

    def test_17_query_file_fs_ctrl_info_for_FILE_READ_ATTRIBUTES(self):
        """
        """
        try:
            print "\n------------------Query_file_TC 17--------------------"
            print "Query file FILE_FS_CONTROL_INFORMATION when file is opened with access FILE_READ_ATTRIBUTES"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test17.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test17.txt",
                            access=pike.smb2.FILE_READ_ATTRIBUTES,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsControlInformation for test17.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_CONTROL_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test17.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 17 has Passed"


    def test_18_query_file_fs_ctrl_info_for_READ_CONTROL(self):
        """
        """
        try:
            print "\n------------------Query_file_TC 18--------------------"
            print "Query file FILE_FS_CONTROL_INFORMATION when a file is opened with access READ_CONTROL"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test18.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test18.txt",
                            access=pike.smb2.READ_CONTROL,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsControlInformation for test18.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_CONTROL_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test18.txt successful, test case failed."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 18 has Passed"

    def test_19_query_file_fs_ctrl_info_for_GENERIC_WRITE(self):
        """
        """
        try:
            print "\n--------------------Query_file_TC 19--------------------"
            print "Query file FILE_FS_CONTROL_INFORMATION when a file is opened with access GENERIC_WRITE"
            expected_status = 'STATUS_ACCESS_DENIED'
            print "Expected status:", expected_status
            print "\nCreate and open a file test19.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test19.txt",
                            access=pike.smb2.GENERIC_WRITE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsControlInformation for test19.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_CONTROL_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            print "Query request for test19.txt successful."
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertIn(expected_status, actual_status)
        print "TC 19 has Passed"		

    def test_20_query_file_fs_objectid_info_for_GENERIC_WRITE(self):
        """
        """
        try:
            print "\n------------------Query_file_TC 20--------------------"
            print "Query FILE_FS_OBJECTID_INFORMATION"
            expected_status = "STATUS_SUCCESS"
            print "Expected status:", expected_status
            print "\nCreate and open a file test20.txt."

            self.chan, self.tree = self.tree_connect()
            file = self.chan.create(self.tree, "test20.txt",
                            access=pike.smb2.GENERIC_WRITE,
                            disposition=pike.smb2.FILE_SUPERSEDE,
                            options=pike.smb2.FILE_NON_DIRECTORY_FILE).result()
            print "File created."
            print "Query FileFsObjectIdInformation for test20.txt"

            info1 = self.gather_info(self.chan, file, file_information_class = pike.smb2.FILE_FS_OBJECTID_INFORMATION, info_type = pike.smb2.SMB2_0_INFO_FILESYSTEM)
            self.assertIn("objectid", str(info1))
            self.assertIn("extended_info", str(info1))
            print "Query request for test20.txt successful"
            self.chan.close(file)
            print "File Closed."
            actual_status = str(info1.status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status:", actual_status
        self.assertEqual(expected_status, actual_status)
        print "TC 20 has Passed"
