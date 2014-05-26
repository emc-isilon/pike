#-----------------------------------------------------------------------------
#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:       runner.py
# Purpose:
#
# Abstract:
#
#        This Script performs xml parsing for the different commands
#        of SMB2 and run the pike tests for the respective tests.
#
# Author:      Sagar Naik, Calsoft (sagar.naik@calsoftinc.com)
#
#-----------------------------------------------------------------------------

import hashlib
import pike.model
from pike.smb2 import *
import pike.test
import xml.etree.ElementTree as ET
from xmlparser import *
import ConfigParser
import os
import re
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import utils
import array
import platform

class ParametrizedTestCase(pike.test.PikeTest):
    """
    TestCase classes that want to be parametrized should
    inherit from this class.
    """
    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(tc_class, param=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(tc_class)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(tc_class(name, param=param))
        return suite


class Execute(ParametrizedTestCase):

    """
    This is the main Execute class used for execution of all tests cases,
    after parsing the XML files

    - Parse the XML files specified in tc.config file and run test cases,:
      based on the inputs specified in XML files
    - Handles the negative test cases by catching the error response and
      comparing it with expected error response specified in the XML files.

    """
    def statuscheck(self, expected_result=None, exception_val=None, cmdname=None, tcname=None):
        """
        Error Handling

        If the server responds with an expected exception,
        it is a valid negative test case,
        Else The Test case fails.
        """
        print "Expected Status - ",expected_result.ReturnStatus
        print "Actual Status - ",exception_val
        self.assertIn(str(expected_result.ReturnStatus), exception_val, "%s has Failed."%tcname)

    def test_execute(self):
        """
        Parse the XML files specified in tc.config file,
        and run test cases based on the inputs specified in XML files
        """

        #Get testcases from xml file
        fail =0
        Execute.file = ''
        Execute.file1 = ''
        print "---------------------"
        conv_obj=utils.Convenience()
        tc=self.param
        share_all = pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_READ
        mainfiledata = ''
        maintestdata = ''
        r = tc.find('Result')
        cmd = r.find('Cmd')
        cmdcheck = cmd.text
        return_status = r.find('ReturnStatus')
        validation_mechanism = r.find('ValidationMechanism')
        expected_result = Result(r)
        desc = tc.find('Desc')
        print desc.text

        for tags in (tc):
            for cmd in (tags):
                if cmd.tag == "NegotiateRequest":
                    negoutput = NegotiateRequest(cmd).param()
                    negoutput = filter(lambda x: x != None, list(negoutput))
                    negoutput = filter(lambda x: x != ' ', list(negoutput))
                    StructureSize = int(NegotiateRequest(cmd).StructureSize)
                    Capabilities = str(NegotiateRequest(cmd).Capabilities)
                    ClientGuid = NegotiateRequest(cmd).ClientGuid
                    Dialects = NegotiateRequest(cmd).Dialects
                    conn = pike.model.Client().connect(self.server, self.port).negotiate()
                    negotiateresp = conn.negotiate_response

                elif cmd.tag == "NegotiateResponse":
                    neg_res_output = NegotiateResponse(cmd).param()
                    smbnegotiate_resp = conn.negotiate_response

                elif cmd.tag == "SessionSetupRequest":
                    sessoutput = SessionSetupRequest(cmd).param()
                    Execute.chan = conn.session_setup(self.creds)
                elif cmd.tag == "SessionSetupResponse":
                    ses_resp_output = SessionSetupResponse(cmd).param()

                elif cmd.tag == "LOGOFFRequest":
                    logoffreq_output = LOGOFFRequest(cmd).param()

                elif cmd.tag == "LOGOFFResponse":
                    logoffresp_output = LOGOFFResponse(cmd).param()

                elif cmd.tag == "TreeConnectRequest":
                    tree_conn=''
                    smb_res=''
                    if cmdcheck == "Tree_Connect" or cmdcheck == "Create" or cmdcheck == "Lock":
                        tree_connect_request=TreeConnectRequest(cmd).param()
                        tree_connect_request=filter(lambda x:x!=None, list(tree_connect_request))
                        tree_connect_request=filter(lambda x:x!=' ', list(tree_connect_request))
                        structure_size = TreeConnectRequest(cmd).StructureSize
                        reserved = TreeConnectRequest(cmd).Reserved
                        pathoffset = TreeConnectRequest(cmd).PathOffset
                        pathlength = TreeConnectRequest(cmd).PathLength
                        path = TreeConnectRequest(cmd).Buffer
                        Tree_connect_list = []
                        if structure_size == ' ':
                            structure_size = 9
                            Tree_connect_list.append(structure_size)
                        else:
                            Tree_connect_list.append(structure_size)
                        if reserved == ' ':
                            reserved = 0
                            Tree_connect_list.append(reserved)
                        else:
                            Tree_connect_list.append(reserved)
                        if pathoffset == ' ':
                            pathoffset = 72
                            Tree_connect_list.append(pathoffset)
                        else:
                            Tree_connect_list.append(pathoffset)
                        if pathlength == ' ':
                            pathlength = 0
                            Tree_connect_list.append(pathlength)
                        else:
                            Tree_connect_list.append(pathlength)
                        Tree_connect_list = map(int, Tree_connect_list)
                        if path != ' ':
                            if  isinstance (path, unicode) :
                                Tree_connect_list.append(path)
                            else:
                                Tree_connect_list.append(path)
                        else:
                            path = self.share
                            Tree_connect_list.append(path)
                        try:
                            treeconnectpacket = conv_obj.tree_connect(Execute.chan,self.server,*Tree_connect_list)
                            smb_res = conv_obj.transceive(Execute.chan,treeconnectpacket)[0]
                            tree_conn=pike.model.Tree(Execute.chan.session, path, smb_res)
                        except Exception as e:
                            self.statuscheck(expected_result,str(e),"Tree Connect",tc.find('Desc').text.split(' ')[0])
                        if cmdcheck == "Tree_Connect":
                            if tree_conn != '':
                                self.statuscheck(expected_result,str(smb_res.status),"Tree Connect",tc.find('Desc').text.split(' ')[0])
                    else:
                        tree_conn = Execute.chan.tree_connect(self.share)
                        path = tree_conn.path

                elif cmd.tag == "TreeConnectResponse":
                    tree_connresp_output = TreeConnectResponse(cmd).param()

                elif cmd.tag == "TreeDisconnectRequest":
                    tree_disconnect_request = TreeDisconnectRequest(cmd).param()
                    tree_disconnect_request = filter(lambda x: x is not None, list(tree_disconnect_request))
                    tree_disconnect_request = filter(lambda x: x != ' ', list(tree_disconnect_request))
                    structure_size = TreeDisconnectRequest(cmd).StructureSize
                    reserved = TreeDisconnectRequest(cmd).Reserved
                    tree_disconnect_list = [structure_size, reserved]
                    tree_disconnect_list = [item if item != ' 'else 0 for item in tree_disconnect_list]
                    tree_disconnect_list = map(int, tree_disconnect_list)

                elif cmd.tag == "TreeDisconnectResponse":
                    tree_disconnect_resp_output = TreeDisconnectResponse(cmd).param()

                elif cmd.tag == "TestBed":
                    testbed = cmd.text
                    test_bed_file = str(testbed)

                elif cmd.tag == "CreateContextRequest":
                    cc_max_access = None if CreateContextRequest(cmd).CreateContextMaximalAccess is None else eval(CreateContextRequest(cmd).CreateContextMaximalAccess)
                    cc_ext_attr = {} if CreateContextRequest(cmd).CreateContextExtendedAttribute is None else eval(CreateContextRequest(cmd).CreateContextExtendedAttribute)
                    cc_sd_attr = {} if CreateContextRequest(cmd).CreateContextSecurityDescriptor is None else eval(CreateContextRequest(cmd).CreateContextSecurityDescriptor)
                    cc_alloc_size =  0 if CreateContextRequest(cmd).CreateContextAllocationSize is None else eval(CreateContextRequest(cmd).CreateContextAllocationSize)
                    cc_durable = False if CreateContextRequest(cmd).CreateContextDurableRequest is None else eval(CreateContextRequest(cmd).CreateContextDurableRequest)

                elif cmd.tag == "CreateRequest":
                    if cmdcheck == "Create" or cmdcheck == "Lock":
                        create_val=tc.find('CreateValidation')
                        val_list=create_val.find('ValidationList').text
                        val_list = [] if val_list is None else val_list.split(',')
                        if isinstance(Execute.file,pike.model.Open):
                            try:
                                stat = True
                                print "Second Create..."
                                if Execute.file.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_BATCH or Execute.file.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE:
                                    Execute.file.on_oplock_break(lambda level: level)
                                Execute.file1,create_response1 = self.CreatePacket(conv_obj,Execute.chan,tree_conn,path,smb_res,expected_result,cmd,cmdcheck,return_status,share_all,create_contexts_maximal_access=cc_max_access,ext_attr=cc_ext_attr,alloc_size=cc_alloc_size,durable=cc_durable,Tree_connect_list=Tree_connect_list,security_desc_attr = cc_sd_attr)
                                print "Second create has passed."
                                if not isinstance(cc_durable, pike.model.Open):
                                    stat=self.create_validation(conv_obj,Execute.chan,tree_conn,tc,Execute.file,Execute.file1,create_val,val_list,create_response)
                                if stat:
                                    print "Create validation has Passed."
                                else:
                                    print "Create validation has Failed."
                            except Exception as e:
                                self.statuscheck(expected_result,str(e),"Create second handle",tc.find('Desc').text.split('-')[0])
                                fail = 1
                        else:
                            try:
                                print "First Create for Testing..."
                                Execute.file,create_response = self.CreatePacket(conv_obj,Execute.chan,tree_conn,path,smb_res,expected_result,cmd,cmdcheck,return_status,share_all,create_contexts_maximal_access=cc_max_access,ext_attr=cc_ext_attr,alloc_size=cc_alloc_size,durable=cc_durable,Tree_connect_list=Tree_connect_list,security_desc_attr = cc_sd_attr)
                                print "First create has passed."
                            except Exception as e:
                                self.statuscheck(expected_result,str(e),"Create first handle",tc.find('Desc').text.split('-')[0])
                                fail = 1
                    else:
                        Execute.file = self.CreatePacket(conv_obj,Execute.chan,tree_conn,path,smb_res,expected_result,cmd,cmdcheck,return_status,share_all)
                    create_buffer = CreateRequest(cmd).Buffer

                elif cmd.tag == "CreateResponse":
                    create_resp = CreateResponse(cmd).param()

                elif cmd.tag == "ReadRequest":
                    if isinstance(Execute.file1,pike.model.Open):
                        self.ReadPacket(cmd, tc, conv_obj, return_status, Execute.chan,
                                    create_buffer,Execute.file1, expected_result,
                                    mainfiledata, maintestdata)
                    else:
                        self.ReadPacket(cmd, tc, conv_obj, return_status, Execute.chan,
                                    create_buffer,Execute.file, expected_result,
                                    mainfiledata, maintestdata)

                elif cmd.tag == "ReadResponse":
                    Read_Response = ReadResponse(cmd).param()

                elif cmd.tag == "WriteRequest":
                    if fail == 0:
                        if isinstance(Execute.file1,pike.model.Open):
                            self.WritePacket(cmd, tc, conv_obj, return_status,
                                         Execute.chan, Execute.file1,
                                         expected_result)
                        else:
                            self.WritePacket(cmd, tc, conv_obj, return_status,
                                         Execute.chan, Execute.file,
                                         expected_result)

                elif cmd.tag == "WriteResponse":
                    write_response = WriteResponse(cmd).param()

                elif cmd.tag == "LockRequest":
                    stat=True
                    if isinstance(Execute.file1,pike.model.Open):
                        try:
                            print "Second Lock for testing..."
                            lock_status=self.LockPacket(cmd, conv_obj, return_status, Execute.chan, Execute.file1, expected_result)
                            self.statuscheck(expected_result,lock_status,"Second Lock",tc.find('Desc').text.split(' ')[0])
                        except Exception as e:
                            print "Lock2 validation Failed due to : ",str(e)
                            self.statuscheck(expected_result,e,"Second Lock",tc.find('Desc').text.split(' ')[0])
                            fail = 1
                    elif fail == 0:
                        try:
                            print "First Lock for testing..."
                            lock_status=self.LockPacket(cmd, conv_obj, return_status, Execute.chan, Execute.file, expected_result)
                            stat=self.lock_validation(tc,cmd, conv_obj, lock_status, Execute.chan,Execute.file, expected_result)
                            if stat==False:
                                self.statuscheck(expected_result,lock_status,"First Lock",tc.find('Desc').text.split(' ')[0])
                                fail=1
                            else:
                                print "First Lock has Passed."
                        except Exception as e:
                            self.statuscheck(expected_result,str(e),"First Lock",tc.find('Desc').text.split(' ')[0])
                            fail = 1

                elif cmd.tag == "LockResponse":
                    lock_response = LockResponse(cmd).param()

                if fail !=0:
                    break

        if return_status.text == "STATUS_SUCCESS":
            if cmdcheck == 'Read':
                #MD5 from local file data
                checksum1 = self.verifychecksum(mainfiledata)
                #MD5 from server data
                checksum2 = self.verifychecksum(maintestdata)
                self.assertEqual(checksum1, checksum2)
                print "Verified the md5 sum for this positive test case"
            elif cmdcheck == 'Create' and Execute.file1 == '' and fail == 0:
                print "Verifying create status"
                self.statuscheck(expected_result,str(create_response[0].result().status),"Create",tc.find('Desc').text.split(' ')[0])

    def tearDown(self):
        try:
            if isinstance(Execute.file,pike.model.Open):
                print "closing file handle 1"
                Execute.chan.close(Execute.file)
            if isinstance(Execute.file1,pike.model.Open):
                print "closing file handle 2"
                Execute.chan.close(Execute.file1)
        except Exception as e:
            pass

    def CreatePacket(self,conv_obj,chan,tree_conn,path,smb_res,expected_result,cmd,cmdcheck,return_status,share_all,create_contexts_maximal_access='',ext_attr={},alloc_size=0,durable=False,Tree_connect_list=[],security_desc_attr = {}):
        create_req = CreateRequest(cmd).param()
        create_buffer = CreateRequest(cmd).Buffer
        if cmdcheck == "Create" or cmdcheck == "Lock":
            #code for default parameters
            structure_size = 57 if CreateRequest(cmd).StructureSize is None else int(CreateRequest(cmd).StructureSize)
            security_flags = 0 if CreateRequest(cmd).SecurityFlags is None else int(CreateRequest(cmd).SecurityFlags)
            requested_oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_NONE if CreateRequest(cmd).RequestedOplockLevel is None else eval(CreateRequest(cmd).RequestedOplockLevel)
            impersonation_level = 0 if CreateRequest(cmd).ImpersonationLevel is None else int(CreateRequest(cmd).ImpersonationLevel)
            smb_create_flags =  0 if CreateRequest(cmd).SmbCreateFlags is None else int(CreateRequest(cmd).SmbCreateFlags)
            reserved = 0 if CreateRequest(cmd).Reserved is None else int(CreateRequest(cmd).Reserved)
            desired_access = pike.smb2.FILE_READ_DATA if CreateRequest(cmd).DesiredAccess is None else eval(CreateRequest(cmd).DesiredAccess)
            file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL if CreateRequest(cmd).FileAttributes is None else eval(CreateRequest(cmd).FileAttributes)
            share_access = pike.smb2.FILE_SHARE_READ if CreateRequest(cmd).ShareAccess is None else eval(CreateRequest(cmd).ShareAccess)
            create_disposition = pike.smb2.FILE_OPEN_IF if CreateRequest(cmd).CreateDisposition is None else eval(CreateRequest(cmd).CreateDisposition)
            create_options = 0 if CreateRequest(cmd).CreateOptions is None else eval(CreateRequest(cmd).CreateOptions)
            name_offset = None if CreateRequest(cmd).NameOffset is None else int(CreateRequest(cmd).NameOffset)
            name_length = None if CreateRequest(cmd).NameLength is None else int(CreateRequest(cmd).NameLength)
            create_contexts_offset = None if CreateRequest(cmd).CreateContextsOffset is None else int(CreateRequest(cmd).CreateContextsOffset)
            create_contexts_length = None if CreateRequest(cmd).CreateContextsLength is None else int(CreateRequest(cmd).CreateContextsLength)

            if str(requested_oplock_level) == "SMB2_OPLOCK_LEVEL_LEASE":
                lease_key = array.array('B',[34, 140, 250, 173, 46, 104, 194, 41, 176, 104, 239, 55, 0, 233, 103, 41])
                lease_state = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_WRITE_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING
            else:
                lease_key = None
                lease_state = None

            if isinstance(durable,pike.model.Open):
                chan.connection.close()
                conn = pike.model.Client().connect(self.server, self.port).negotiate()
                chan2 = conn.session_setup(self.creds)
                treeconnectpacket = conv_obj.tree_connect(chan2,self.server,*Tree_connect_list)
                smb_res = conv_obj.transceive(chan2,treeconnectpacket)[0]
                tree_conn=pike.model.Tree(chan2.session, path, smb_res)
                chan = chan2
            create_tmp = ''
            create_resp = ''
            create_tmp,create_resp = conv_obj.create(chan,tree_conn,
                    create_buffer,
                    structure_size=structure_size,
                    security_flags=security_flags,
                    oplock_level=requested_oplock_level,
                    impersonation_level = impersonation_level,
                    smb_create_flags = smb_create_flags,
                    reserved = reserved,
                    access=desired_access,
                    attributes=file_attributes,
                    share=share_access,
                    disposition=create_disposition,
                    options=create_options,
                    name_offset=name_offset,
                    name_length=name_length,
                    create_contexts_offset=create_contexts_offset,
                    create_contexts_length=create_contexts_length,
                    maximal_access = create_contexts_maximal_access,
                    extended_attr=ext_attr,
                    allocation_size=alloc_size,
                    durable=durable,
                    security_desc_attr = security_desc_attr,
                    lease_key=lease_key,
                    lease_state=lease_state)

            file = create_tmp.result()
            if file == '':
                return
            else:
                return file,create_resp

        else:
            file = chan.create(tree_conn,
                   create_buffer,
                   access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE, share=share_all,
                   disposition=pike.smb2.FILE_OPEN_IF,
                   options=0).result()
            return file

    def create_validation(self,conv_obj=None,chan=None,tree_id=None,tc=None,handle1=None,handle2=None,tagval=None,val_list=[],response=None):
        """
        Function for Create Validation.
        """
        status = True
        try:
            info=chan.query_file_info(handle1,pike.smb2.FILE_ALL_INFORMATION)
        except Exception as e:
            self.assertIn(str(info.status),'STATUS_SUCCESS','Querying general attributes of file...FAILED.')

        for item in val_list:
            val= getattr(self,item)
            status=val(chan,tree_id,tc,handle1,handle2,tagval,info,response)
            if status is True:
                pass
            else:
                status=False
                break
        return status

    def Dir_List(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to verify is particular file is listed in the directory listing.
        """
        print "Verifying Directory listing."
        desired_access = info.access_information.access_flags
        info.name_information.file_name
        dirname = info.name_information.file_name.split('\\')[-1].strip()

        if 'FILE_ADD_SUBDIRECTORY' in str(desired_access):
            filename = dirname+'\\subdir'
            create_options = pike.smb2.FILE_DIRECTORY_FILE
        else:
            create_options = pike.smb2.FILE_COMPLETE_IF_OPLOCKED
            filename = dirname+'\\child_file'
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        #have a create to create a subdirectory or a file
        tmp_file = chan.create(tree_id,
                          filename,
                          access=pike.smb2.GENERIC_ALL,
                          share= share_all,
                          disposition=pike.smb2.FILE_CREATE,
                          options=create_options
                          ).result()
        if 'FILE_ATTRIBUTE_DIRECTORY' in str(response[0].response.children[0].file_attributes):
            names = map(lambda res: res.file_name,chan.query_directory(handle1))
            #split the filename from full filename path and verify if it appears in directory listing.
            self.assertIn(filename.split('\\')[1], names, "Directory listing validation failed.")
            print "Directory listing validation passed."
            return True

    def Delete_Child(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Delete Child.
        """
        print 'Validating delete child from directory...'
        dirname = info.name_information.file_name.split('\\')[-1].strip()
        print "dirname is :",dirname
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        filename = dirname+'\\childdir'
        print "filename is : ",filename
        tmp_file = chan.create(tree_id,
                          filename,
                          access=pike.smb2.DELETE,
                          share= share_all,
                          disposition=pike.smb2.FILE_CREATE,
                          options=pike.smb2.FILE_DELETE_ON_CLOSE|pike.smb2.FILE_DIRECTORY_FILE
                          ).result()
        chan.close(tmp_file)
        if 'FILE_ATTRIBUTE_DIRECTORY' in str(response[0].response.children[0].file_attributes):
            names = map(lambda res: res.file_name,chan.query_directory(handle1))
            self.assertNotIn(filename.split('\\')[1], names,"Delete child validation failed.")
            print "Delete child validation passed"
            return True

    def General(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function for General Validation. Includes file creation time, file attributes, access flags, filename and return status validation.
        """
        creation_time = info.basic_information.creation_time
        file_attributes = info.basic_information.file_attributes
        access_flags = info.access_information.access_flags
        filename = info.name_information.file_name
        status = response[0].result().status
        print "Status : ",status
        print "Filename : ",filename
        print "Creation Time :  ",creation_time
        print "File Attributes : ",file_attributes
        print "Access Flags : ",access_flags
        return True

    def Oplock_Validation(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function for Oplock validation. Oplock level with Exclusive/Batch in first create
        will have to be broken and downgraded to level2 oplock, in other cases requested
        oplock should be granted.
        """
        print "Verifying oplock on first and second handle."
        handle1_requested_oplock = tc.findall('SMB2Create')[0].find('CreateRequest').find('RequestedOplockLevel').text
        handle1_obtained_oplock = str(response[0].response[0].oplock_level)
        handle2_requested_oplock = tc.findall('SMB2Create')[1].find('CreateRequest').find('RequestedOplockLevel').text
        handle2_expected_oplock = 'SMB2_OPLOCK_LEVEL_NONE' if handle2_requested_oplock == 'SMB2_OPLOCK_LEVEL_NONE' else 'SMB2_OPLOCK_LEVEL_II'
        handle2_obtained_oplock = str(handle2.oplock_level)
        print "Oplock level requested on handle1: ",handle1_requested_oplock
        print "Oplock level obtained on handle1: ",handle1_obtained_oplock
        print "Oplock level requested on handle2: ",handle2_requested_oplock
        print "Oplock level expected on handle2: ",handle2_expected_oplock
        print "Oplock Level obtained on handle2: ",handle2_obtained_oplock
        self.assertEqual(handle1_requested_oplock, handle1_obtained_oplock,"handle 1 requested and obtained oplocks are not same")
        self.assertEqual(handle2_expected_oplock, handle2_obtained_oplock,"handle 2 requested and obtained oplocks are not same")
        if handle1_requested_oplock == 'SMB2_OPLOCK_LEVEL_EXCLUSIVE' or handle1_requested_oplock == 'SMB2_OPLOCK_LEVEL_BATCH':
            oplock_on_break_expected = "SMB2_OPLOCK_LEVEL_II"
            print "Oplock Level expected after break on handle1: ",oplock_on_break_expected
            oplock_on_break_obtained = str(handle1.oplock_level)
            print "Oplock Level after break on handle1: ",oplock_on_break_obtained
            self.assertEqual(oplock_on_break_expected,oplock_on_break_obtained,"Oplock validation has failed.")
            print "Oplock validation has passed."
        return True

    def Ea(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Extended Attributes.
        """
        print "Verifying EA on file."
        easize = info.ea_information.ea_size
        self.assertNotEqual(easize,0,"EA size validation has failed.")
        print "EA size validation has passed."
        return True

    def Alloc_Size(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Allocation Size.
        """
        print "Verifying allocation size set on the file."
        expected_alloc_size = int(tagval.find('AllocationSize').text)
        print "response",response[0].result().children[0]
        try:
            actual_alloc_size = int(response[0].result().children[0].allocation_size)
            self.assertEqual(expected_alloc_size,actual_alloc_size,"Allocation size has not been set correctly. Allocation size validation has failed.")
            print "Allocation size validation has passed."
        except:
            print "Allocation Size not supported"
        return True

    def Maximal_Access(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Maximal Access.
        """
        print "Verifying Maximal access set on the file."
        expected_maximal_status = 'STATUS_SUCCESS'
        try:
            actual_maximal_status = str(response[0].result().children[0][0].query_status)
            self.assertEqual(expected_maximal_status,actual_maximal_status,"Maximal Access validation has failed.")
            print "Maximal Access validation has passed."
        except:
            print "Maximal Access not supported"
        return True

    def Durable_Handle(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Durable handle.
        """
        print "Verifying durable handle."
        assert "DurableHandleResponse" in str(response[0].result()), "Durable handle response not found in Create response."
        print "Durable handle validation has passed."
        return True

    def Read(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Read for Create command.
        """
        print 'Validating read for first handle.'
        expected_status=tagval.find('ReadStatus').text
        buffer="testing123"
        try:
            read_output = chan.read(handle1,len(buffer),0)
            actual_status='STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print 'Expected - ',expected_status
        print 'Actual - ',actual_status
        self.assertIn(expected_status,actual_status,"Read validation has failed.")
        print "Read validation has passed."
        return True

    def Write(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Write for Create command.
        """
        print 'Validating write for first handle.'
        expected_status=tagval.find('WriteStatus').text
        buffer="testing123"
        try:
            bytes_written = chan.write(handle1,0,buffer)
            if bytes_written == len(buffer):
                actual_status='STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print 'Expected  - ',expected_status
        print 'Actual - ',actual_status
        self.assertIn(expected_status,actual_status,"Write validation has failed.")
        print "Write validation has passed."
        return True

    def ShareRead(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Share Read.
        """
        print 'Validating share read.'
        expected_status=tagval.find('ShareReadStatus').text
        buffer="testing123"
        try:
            read_output = chan.read(handle2,len(buffer),0)
            actual_status='STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print 'Expected - ',expected_status
        print 'Actual - ',actual_status
        self.assertIn(expected_status,actual_status,"Share Read validation has failed.")
        print "Shared Read validation has passed."
        return True

    def ShareWrite(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Share Write.
        """
        print 'Validating share write.'
        expected_status=tagval.find('ShareWriteStatus').text
        buffer="testing123"
        try:
            bytes_written = chan.write(handle2,11,buffer)
            if bytes_written == len(buffer):
                actual_status='STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print 'Expected - ',expected_status
        print 'Actual - ',actual_status
        self.assertIn(expected_status,actual_status,"Share Write validation has failed.")
        print "Shared Write validation has passed."
        return True

    def ShareDelete(self,chan,tree_id,tc,handle1,handle2,tagval,info,response):
        """
        Function to validate Share Delete.
        """
        print 'Validating share delete.'
        expected_status=tagval.find('ShareDeleteStatus').text
        filename = info.name_information.file_name
        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
        buffer="testing123"
        try:
            chan.close(handle1)
            chan.close(handle2)
            tmp_file = chan.create(tree_id,
                              filename,
                              access=pike.smb2.GENERIC_ALL,
                              share= share_all,
                              disposition=pike.smb2.FILE_OPEN,
                              options=pike.smb2.FILE_COMPLETE_IF_OPLOCKED
                              ).result()
            if isinstance(tmp_file,pike.model.Open):
                actual_status = 'STATUS_SUCCESS'
        except Exception as e:
            actual_status = str(e)
        print 'Expected - ',expected_status
        print 'Actual - ',actual_status
        self.assertIn(expected_status,actual_status,"Share Delete valiadtion has failed.")
        print "Share Delete validation has passed."
        return True

    def ReadPacket(self, cmd, tc, conv_obj, return_status, chan, Createbuffer,
                    file, expected_result, mainfiledata, maintestdata):
        readresponse = ''
        read_request = ReadRequest(cmd).param()
        structure_size = 49 if ReadRequest(cmd).StructureSize is None else int(ReadRequest(cmd).StructureSize)
        padding = 0 if ReadRequest(cmd).Padding is None else int(ReadRequest(cmd).Padding)
        reserved = 0 if ReadRequest(cmd).Reserved is None else int(ReadRequest(cmd).Reserved)
        length = 1 if ReadRequest(cmd).Length is None else int(ReadRequest(cmd).Length)
        offset = 0 if ReadRequest(cmd).Offset is None else int(ReadRequest(cmd).Offset)
        file_id = 0 if ReadRequest(cmd).FileId is None else int(ReadRequest(cmd).FileId,16)
        minimum_count = 0 if ReadRequest(cmd).MinimumCount is None else int(ReadRequest(cmd).MinimumCount)
        channel = 0 if ReadRequest(cmd).Channel is None else int(ReadRequest(cmd).Channel)
        remaining_bytes = 0 if ReadRequest(cmd).RemainingBytes is None else int(ReadRequest(cmd).RemainingBytes)
        read_channel_info_offset = 0 if ReadRequest(cmd).ReadChannelInfoOffset is None else int(ReadRequest(cmd).ReadChannelInfoOffset)
        read_channel_info_length = 0 if ReadRequest(cmd).ReadChannelInfoLength is None else int(ReadRequest(cmd).ReadChannelInfoLength)
        buffer1 = 0 if ReadRequest(cmd).Buffer is None else int(ReadRequest(cmd).Buffer)
        read_list = [structure_size, padding, reserved, length, offset, file_id, minimum_count, channel, remaining_bytes, read_channel_info_offset, read_channel_info_length, buffer1]
        try:
            readpacket = conv_obj.read(chan, file, *read_list)
            readresponse = conv_obj.transceive(chan,readpacket)
            if return_status.text == "STATUS_SUCCESS":
                testdata = readresponse[0][0].data
                testdata = testdata.tostring()
                maintestdata = maintestdata + testdata
            fh= open(Createbuffer, 'r')
            filedata = fh.read()
            offset = int(ReadRequest(cmd).Offset)
            length = int(ReadRequest(cmd).Length)
            filedata = filedata[offset:offset + length]
            mainfiledata = mainfiledata + filedata
            fh.close()
            read_status = str(readresponse[0].status)
        except Exception as e:
            read_status = str(e)
        self.statuscheck(expected_result, read_status,"Read",tc.find('Desc').text.split(' ')[0])

    def WritePacket(self, cmd, tc, conv_obj, cmdcheck, chan,
                    file, expected_result):
        write_output=''
        structure_size = 49 if WriteRequest(cmd).StructureSize is None else int(WriteRequest(cmd).StructureSize)
        data_offset = 112 if WriteRequest(cmd).DataOffset is None else int(WriteRequest(cmd).DataOffset)
        write_length = 1 if WriteRequest(cmd).Length is None else int(WriteRequest(cmd).Length)
        write_offset = 0 if WriteRequest(cmd).Offset is None else int(WriteRequest(cmd).Offset)
        file_id = None if WriteRequest(cmd).FileId is None else int(WriteRequest(cmd).FileId,16)
        channel = 0 if WriteRequest(cmd).Channel is None else int(WriteRequest(cmd).Channel)
        remaining_bytes = 0 if WriteRequest(cmd).RemainingBytes is None else int(WriteRequest(cmd).RemainingBytes)
        write_channel_info_offset = 0 if WriteRequest(cmd).WriteChannelInfoOffset is None else int(WriteRequest(cmd).WriteChannelInfoOffset)
        write_channel_info_length = 0 if WriteRequest(cmd).WriteChannelInfoLength is None else int(WriteRequest(cmd).WriteChannelInfoLength)
        flags = 0 if WriteRequest(cmd).Flags is None else int(WriteRequest(cmd).Flags)
        input_file = None if WriteRequest(cmd).Buffer is None else str(WriteRequest(cmd).Buffer)

        fh = open(input_file, 'r')
        write_buffer = fh.read()
        fh.close()
        write_list = [structure_size, data_offset, write_length,
                      write_offset, file_id, channel, remaining_bytes,
                      write_channel_info_offset, write_channel_info_length,
                      flags, write_buffer]
        try:
            write_packet = conv_obj.write(chan, Execute.file, *write_list)
            write_output = conv_obj.transceive(chan,write_packet)
            write_status = str(write_output[0].status)
            if write_status == "STATUS_SUCCESS":
                print "Write is successful."
            if cmdcheck != "Lock":
                source_data = write_buffer[0: write_length]
                checksum1 = self.verifychecksum(source_data)
                readpacket = conv_obj.read(chan, Execute.file, length=write_length,
                                    offset=write_offset)
                readresponse = conv_obj.transceive(chan,readpacket)
                read_data = readresponse[0][0].data
                checksum2 = self.verifychecksum(read_data.tostring())
                self.assertEqual(checksum1, checksum2)
                print "Verified the md5 sum for this positive test case"
                self.assertEqual(write_length, write_output[0][0].count)
                print "Verified count  for this positive test case"
        except Exception as e:
            write_status = str(e)
        self.statuscheck(expected_result, write_status, "Write", tc.find('Desc').text.split(' ')[0])

    def LockPacket(self, cmd, conv_obj, return_status, chan,
                    file, expected_result):
        try:
            lock_output = ''
            structure_size = 48 if LockRequest(cmd).StructureSize is None else int(LockRequest(cmd).StructureSize)
            lock_count = 0 if LockRequest(cmd).LockCount is None else int(LockRequest(cmd).LockCount)
            lock_sequence = 0 if LockRequest(cmd).LockSequence is None else int(LockRequest(cmd).LockSequence)
            file_id = 0 if LockRequest(cmd).FileId is None else int(LockRequest(cmd).FileId,16)
            locks = [] if LockRequest(cmd).Locks is None else eval(LockRequest(cmd).Locks)
            lock_list = [structure_size, lock_count, lock_sequence, file_id, locks]
            lock_packet = conv_obj.lock(chan, Execute.file, *lock_list)
            lock_output = conv_obj.transceive(chan,lock_packet)
            lock_status = str(lock_output[0].status)
            return lock_status
        except Exception as e:
            return str(e)

    def lock_validation(self, tc, cmd, conv_obj, lock_status, chan,
                    file, expected_result):
        """
        Validation for first lock.
        """
        if lock_status == "STATUS_SUCCESS":
            return True
        else:
            return False

    def verifychecksum(self, input):
        """
        Function for finding the md5checksum values
        """
        md5data = hashlib.md5()
        md5data.update(input)
        checksum = md5data.hexdigest()
        return checksum

def get_tc_list():
    """
    Read TCs from config file
    """
    config_file = '../test/tc.config'
    if os.path.exists(config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        for section in config.sections():
            for option in config.options(section):
                tmp = config.get(section, option)
                tc_list = str(tmp).split(',')
    else:
        raise Exception("Config file %s does not exist" % config_file)
        exit
    return tc_list

#Get testcases from xml file
ts_list=get_tc_list()
suite = unittest.TestSuite()
for test_case_xml in ts_list:
    test_xml = '../test/' + test_case_xml
    print "---------------------"
    print "Executing testcases from : ", test_case_xml
    print "---------------------"
    tree = ET.parse(test_xml)
    for tc in tree.getiterator('TC'):
        suite.addTest(ParametrizedTestCase.parametrize(Execute, param=tc))
    if __name__ == '__main__':
        unittest.TextTestRunner().run(suite)

