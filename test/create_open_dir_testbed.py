#-----------------------------------------------------------------------------
#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:       create_open_dir_testbed.py
#
# Purpose: Test Bed Script for create open directory test cases
#
#
# Author:      Sagar Naik, Calsoft (sagar.naik@calsoftinc.com)
#
#-----------------------------------------------------------------------------


import xml.etree.ElementTree as ET
from pike.smb2 import *
from xmlparser import *
import pike.model
import pike.test
import re
import utils

class create_open_dir(pike.test.PikeTest):
    def test_opendir(self):
        file = ''
        conv_obj=utils.Convenience()
        conn = pike.model.Client().connect(self.server, self.port).negotiate()
        chan = conn.session_setup(self.creds)
        tree = ET.parse("../test/Create_Open_Directory_Testbed.xml")
        for tc in tree.getiterator('TC'):
            for tags in (tc):
                for cmd in (tags):
                    if cmd.tag == "TreeConnectRequest":
                        tree_conn=''
                        smb_res=''
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
                            treeconnectpacket = conv_obj.tree_connect(chan,self.server,*Tree_connect_list)
                            smb_res = conv_obj.transceive(chan,treeconnectpacket)[0]
                            tree_conn=pike.model.Tree(chan.session, path, smb_res)
                        except Exception as e:
                            pass

                    elif cmd.tag == "CreateContextRequest":
                        cc_max_access = None if CreateContextRequest(cmd).CreateContextMaximalAccess is None else eval(CreateContextRequest(cmd).CreateContextMaximalAccess)
                        cc_ext_attr = {} if CreateContextRequest(cmd).CreateContextExtendedAttribute is None else eval(CreateContextRequest(cmd).CreateContextExtendedAttribute)
                        cc_sd_attr = {} if CreateContextRequest(cmd).CreateContextSecurityDescriptor is None else eval(CreateContextRequest(cmd).CreateContextSecurityDescriptor)
                        cc_alloc_size =  0 if CreateContextRequest(cmd).CreateContextAllocationSize is None else eval(CreateContextRequest(cmd).CreateContextAllocationSize)
                        cc_durable = False if CreateContextRequest(cmd).CreateContextDurableRequest is None else eval(CreateContextRequest(cmd).CreateContextDurableRequest)

                    elif cmd.tag == "CreateRequest":
                            #code for default parameters
                        structure_size = 57 if CreateRequest(cmd).StructureSize is None else int(CreateRequest(cmd).StructureSize)
                        security_flags = 0 if CreateRequest(cmd).SecurityFlags is None else int(CreateRequest(cmd).SecurityFlags)
                        requested_oplock_level = pike.smb2.SMB2_OPLOCK_LEVEL_NONE if CreateRequest(cmd).RequestedOplockLevel is None else eval(CreateRequest(cmd).RequestedOplockLevel)
                        impersonation_level = 0 if CreateRequest(cmd).ImpersonationLevel is None else int(CreateRequest(cmd).ImpersonationLevel)
                        smb_create_flags =  0 if CreateRequest(cmd).SmbCreateFlags is None else int(CreateRequest(cmd).SmbCreateFlags)
                        reserved = 0 if CreateRequest(cmd).Reserved is None else int(CreateRequest(cmd).Reserved)
                        desired_access = eval(CreateRequest(cmd).DesiredAccess)
                        file_attributes = pike.smb2.FILE_ATTRIBUTE_NORMAL if CreateRequest(cmd).FileAttributes is None else eval(CreateRequest(cmd).FileAttributes)
                        share_access = pike.smb2.FILE_SHARE_READ if CreateRequest(cmd).ShareAccess is None else eval(CreateRequest(cmd).ShareAccess)
                        create_disposition = pike.smb2.FILE_CREATE
                        create_options = 0 if CreateRequest(cmd).CreateOptions is None else eval(CreateRequest(cmd).CreateOptions)
                        name_offset = None if CreateRequest(cmd).NameOffset is None else int(CreateRequest(cmd).NameOffset)
                        name_length = None if CreateRequest(cmd).NameLength is None else int(CreateRequest(cmd).NameLength)
                        create_contexts_offset = None if CreateRequest(cmd).CreateContextsOffset is None else int(CreateRequest(cmd).CreateContextsOffset)
                        create_contexts_length = None if CreateRequest(cmd).CreateContextsLength is None else int(CreateRequest(cmd).CreateContextsLength)
                        create_buffer = CreateRequest(cmd).Buffer

                        file_handle,create_resp = conv_obj.create(chan,tree_conn,
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
                                maximal_access=cc_max_access,
                                extended_attr=cc_ext_attr,
                                allocation_size=cc_alloc_size,
                                durable=cc_durable,
                                security_desc_attr=cc_sd_attr)
                        file = file_handle.result()
                        if isinstance(file,pike.model.Open):
                            chan.close(file)

