#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:
#
#        echo.py
#
# Abstract:
#
#        Basic echo send/receive testing
#
# Authors: Lingaraj Gowdar (lingaraj.gowdar@calsoftinc.com)
#
import pike.model
import pike.smb2
import pike.test
import random
import array
import utils

# All tests for the echo request/response
class EchoTest(pike.test.PikeTest):

    def test_01_echo_with_valid_struct_size(self):
        try:
            print "\n--------------------ECHO_TC 01 --------------------"
            print "Test case to verify echo request with valid structure size."
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Sending Negotiate request..."
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate successful."
            print "Sending Session setup request..."
            chan = conn.session_setup(self.creds)
            print "Session setup successful."
            print "Sending Echo request..."
            conv_obj = utils.Convenience()
            echo_packet = conv_obj.echo(chan,structure_size=4)
            res = conv_obj.transceive(chan,echo_packet)
            print "Echo request is successfully processed."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 01 failed.")
        print "TC 01 Passed"

    def test_02_echo_with_invalid_struct_size(self):
        try:
            print "\n--------------------ECHO_TC 02 --------------------"
            print "Test case to verify echo request with invalid structure size."
            expected_status = 'STATUS_INVALID_PARAMETER'
            print "Expected status: ",expected_status
            print "Sending Negotiate request..."
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate successful."
            print "Sending Session setup request..."
            chan = conn.session_setup(self.creds)
            print "Session setup successful."
            print "Sending Echo request..."
            conv_obj=utils.Convenience()
            echo_packet = conv_obj.echo(chan,structure_size=5)
            res = conv_obj.transceive(chan,echo_packet)
            print "Echo request is successfully processed."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 02 failed.")
        print "TC 02 Passed"

    def test_03_echo_with_invalid_reserved_value(self):
        try:
            print "\n--------------------ECHO_TC 03 --------------------"
            print "Test case to verify echo request with invalid reserved value."
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Sending Negotiate request..."
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate successful."
            print "Sending Session setup request..."
            chan = conn.session_setup(self.creds)
            print "Session setup successful."
            print "Sending Echo request..."
            conv_obj=utils.Convenience()
            echo_packet = conv_obj.echo(chan,reserved=5)
            res = conv_obj.transceive(chan,echo_packet)
            print "Echo request is successfully processed."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 03 failed.")
        print "TC 03 Passed"

    def test_04_echo_with_valid_reserved_value(self):
        try:
            print "\n--------------------ECHO_TC 04 --------------------"
            print "Test case to verify echo request with valid reserved value."
            expected_status = 'STATUS_SUCCESS'
            print "Expected status: ",expected_status
            print "Sending Negotiate request..."
            conn = pike.model.Client().connect(self.server, self.port).negotiate()
            print "Negotiate successful."
            print "Sending Session setup request..."
            chan = conn.session_setup(self.creds)
            print "Session setup successful."
            print "Sending Echo request..."
            conv_obj=utils.Convenience()
            echo_packet = conv_obj.echo(chan,reserved=0)
            res = conv_obj.transceive(chan,echo_packet)
            print "Echo request is successfully processed."
            actual_status = str(res[0].status)
        except Exception as e:
            actual_status = str(e)
        print "Actual status: ",actual_status
        self.assertIn(expected_status,actual_status,"\nTC 04 failed.")
        print "TC 04 Passed"


