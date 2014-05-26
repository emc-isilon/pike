
#-----------------------------------------------------------------------------
#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:       utils.py
# Purpose:
#
# Abstract:
#
#        This library is extension of model.py with the additions
#        required to execute parametrized test cases.
#
# Author:      Sagar Naik, Calsoft (sagar.naik@calsoftinc.com)
#
#-----------------------------------------------------------------------------

import pike
from pike.smb2 import *
import re
import struct


class Convenience():
    def __init__(self):
       pass
    def read(self,chan_obj,
             file,
             structure_size=49,
             padding=0,
             reserved=0,
             length=0,
             offset=0,
             file_id=0,
             minimum_count=0,
             channel=0,
             remaining_bytes=0,
             readchannelinfooffset=0,
             readchannelinfolength=0,
             buffer=0):
         """
         Performs read operation on the current session
         Includes parameterisation for including all attributes
         """
         smb_req = chan_obj.request(obj=file)
         read_req = pike.smb2.ReadRequest(smb_req)
         read_req.padding = padding
         read_req.reserved = reserved
         read_req.structure_size = structure_size
         read_req.length = length
         if length > 65535:
             smb_req.credit_charge = (length -1)/65536 + 1
         read_req.offset = offset
         read_req.minimum_count = minimum_count
         read_req.buffer = buffer
         read_req.remaining_bytes = remaining_bytes
         read_req.read_channel_info_offset = readchannelinfooffset
         read_req.read_channel_info_length = readchannelinfolength
         if file_id != 0:
             file_id=struct.unpack('<Q',struct.pack('Q',file_id))
             file_id=file_id + file_id
             read_req.file_id =file_id
         else:
             read_req.file_id=file.file_id
         return smb_req.parent

    def write(self,chan_obj,
              file,
              structure_size=49,
              data_offset=112,
              length=None,
              offset=0,
              file_id=' ',
              channel=0,
              remaining_bytes=0,
              write_channel_info_offset=0,
              write_channel_info_length=0,
              flags=0,
              buffer=None):
        """
        Performs write operation on the current session
        Includes parameterisation for including all attributes
        """
        smb_req = chan_obj.request(obj=file)
        write_req = pike.smb2.WriteRequest(smb_req)
        write_req.structure_size = structure_size
        write_req.data_offset = data_offset
        if length == None and buffer != None:
            length = len(buffer)
        write_req.length = length
        if length > 65535:
            smb_req.credit_charge = (length -1)/65536 + 1
        write_req.offset = offset
        if file_id != None:
            file_id=struct.unpack('<Q',struct.pack('Q',file_id))
            file_id=file_id + file_id
            write_req.file_id =file_id
        else:
            write_req.file_id=file.file_id
        write_req.channel = channel
        write_req.remaining_bytes = remaining_bytes
        write_req.write_channel_info_offset = write_channel_info_offset
        write_req.write_channel_info_length = write_channel_info_length
        write_req.buffer = buffer
        write_req.remaining_bytes = remaining_bytes
        write_req.flags = flags
        return smb_req.parent

    def tree_connect(self,chan_obj,server,structure_size=9,reserved=0,path_offset=72,path_length=0,path=None):
        smb_req = chan_obj.request()
        tree_req = pike.smb2.TreeConnectRequest(smb_req)
        tree_req.structure_size = structure_size
        tree_req.reserved = reserved
        tree_req.path_offset = path_offset
        tree_req.path_length = path_length
        match=re.search(r'^\\\\',path)
        if match:
           path_p = path
        else:
           path_p="\\\\" + server + "\\" + path
        tree_req.path = path_p
        return smb_req.parent

    def transceive(self,chan_obj,smb_request):
        smb_response = chan_obj.connection.transceive(smb_request)
        return smb_response

    def create(self,chan_obj,
               tree,
               path,
               structure_size=57,
               security_flags=0,
               oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_NONE,
               impersonation_level=0,
               smb_create_flags=0,
               reserved=0,
               access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE,
               attributes=pike.smb2.FILE_ATTRIBUTE_NORMAL,
               share=0,
               disposition=pike.smb2.FILE_OPEN_IF,
               options=0,
               name_offset=0,
               name_length=0,
               create_contexts_offset=0,
               create_contexts_length=0,
               maximal_access=None,
               allocation_size=0,
               extended_attr={},
               lease_key=None,
               lease_state=None,
               durable=False,
               persistent=False,
               create_guid=None,
               app_instance_id=None,
               security_desc_attr={}):

        prev_open = None

        smb_req = chan_obj.request(obj=tree)
        create_req = pike.smb2.CreateRequest(smb_req)
        create_req.name = path
        create_req.desired_access = access
        create_req.file_attributes = attributes
        create_req.share_access = share
        create_req.create_disposition = disposition
        create_req.create_options = options
        create_req.requested_oplock_level = oplock_level
        create_req.structure_size = structure_size
        create_req.security_flags = security_flags
        create_req.reserved = reserved
        create_req.smb_create_flags = smb_create_flags
        create_req.name_offset = name_offset
        create_req.name_length = name_length

        if maximal_access:
            max_req = pike.smb2.MaximalAccessRequest(create_req)
            if maximal_access is not True:
                max_req.timestamp = maximal_access

        if allocation_size != 0:
            alloc_size =pike.smb2.AllocationSizeRequest(create_req)
            alloc_size.allocation_size =  allocation_size

        if len(extended_attr.keys()) != 0:
            ext_attr_len = len(extended_attr.keys())
            for name,value in extended_attr.iteritems():
                ext_attr = pike.smb2.ExtendedAttributeRequest(create_req)
                if ext_attr_len == 1:
                    next_entry_offset = 0
                else:
                    next_entry_offset = 10 + len(name) + len(value)
                ext_attr.next_entry_offset = next_entry_offset
                ext_attr.ea_name = name
                ext_attr.ea_name_length = len(name)
                ext_attr.ea_value = value
                ext_attr.ea_value_length = len(value)
                ext_attr_len = ext_attr_len - 1

        if len(security_desc_attr.keys()) != 0:
            secd_req = pike.smb2.SecurityDescriptorRequest(create_req)
            secd_req.revision=security_desc_attr['revision']
            secd_req.control = security_desc_attr['control']
            secd_req.sbz1 = security_desc_attr['sbz1']
            secd_req.owner_sid = security_desc_attr['owner_sid'] if security_desc_attr.has_key('owner_sid') else None
            secd_req.group_sid = security_desc_attr['group_sid'] if security_desc_attr.has_key('group_sid') else None
            secd_req.sacl = security_desc_attr['sacl']  if security_desc_attr.has_key('sacl') else None
            secd_req.sacl_aces = security_desc_attr['sacl_aces'] if security_desc_attr.has_key('sacl_aces') else None
            secd_req.dacl = security_desc_attr['dacl'] if security_desc_attr.has_key('dacl') else None
            secd_req.dacl_aces = security_desc_attr['dacl_aces'] if security_desc_attr.has_key('dacl_aces') else None

        if oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_LEASE:
            lease_req = pike.smb2.LeaseRequest(create_req)
            lease_req.lease_key = lease_key
            lease_req.lease_state = lease_state

        if isinstance(durable, pike.model.Open):
            prev_open = durable
            if durable.durable_timeout is None:
                durable_req = pike.smb2.DurableHandleReconnectRequest(create_req)
                durable_req.file_id = durable.file_id
            else:
                durable_req = pike.smb2.DurableHandleReconnectV2Request(create_req)
                durable_req.file_id = durable.file_id
                durable_req.create_guid = durable.create_guid
                durable_req.flags = durable.durable_flags
        elif durable is True:
            durable_req = pike.smb2.DurableHandleRequest(create_req)
        elif durable is not False:
            durable_req = pike.smb2.DurableHandleV2Request(create_req)
            durable_req.timeout = durable
            if persistent:
                durable_req.flags = pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT
            if create_guid is None:
                create_guid = array.array('B',map(random.randint, [0]*16, [255]*16))
            durable_req.create_guid = create_guid

        if app_instance_id:
            app_instance_id_req = pike.smb2.AppInstanceIdRequest(create_req)
            app_instance_id_req.app_instance_id = app_instance_id

        open_future = pike.model.Future(None)

        def finish(f):
            with open_future: open_future(pike.model.Open(tree, f.result(), create_guid=create_guid, prev=prev_open))

        smb_res = chan_obj.connection.submit(smb_req.parent)
        open_future.request_future = smb_res[0]
        open_future.request_future.then(finish)

        return open_future,smb_res

    def echo(self,chan_obj,structure_size=4,reserved=0):
        smb_req = chan_obj.request()
        echo_req = pike.smb2.EchoRequest(smb_req)
        echo_req.structure_size = structure_size
        echo_req.reserved = reserved
        return smb_req.parent

    def flush(self,chan_obj,tree=None,structure_size=24,reserved1=0,reserved2=0,file_id=None):
        smb_req = chan_obj.request(obj=tree)
        flush_req = pike.smb2.FlushRequest(smb_req)
        flush_req.structure_size = structure_size
        flush_req.reserved1 = reserved1
        flush_req.reserved2 = reserved2
        flush_req.file_id = file_id
        return smb_req.parent

    def lock(self,chan_obj,file,structure_size=48,lock_count=0,sequence=0,file_id=' ',locks=[]):
        smb_req = chan_obj.request(obj=file)
        lock_req = pike.smb2.LockRequest(smb_req)
        lock_req.structure_size = structure_size
        lock_req.lock_count = lock_count
        lock_req.lock_sequence = sequence
        if file_id != 0:
            file_id = struct.unpack('<Q',struct.pack('Q',file_id))
            file_id = file_id + file_id
            lock_req.file_id = file_id
        else:
            lock_req.file_id = file.file_id
        lock_req.locks = locks
        return smb_req.parent

    def query_file_info(self,chan_obj,
                        file,
                        file_information_class = pike.smb2.FILE_BASIC_INFORMATION,
                        info_type = pike.smb2.SMB2_0_INFO_FILE,
                        output_buffer_length = 4096):
        smb_req = chan_obj.request(obj=file)
        query_req = pike.smb2.QueryInfoRequest(smb_req)

        query_req.info_type = info_type
        query_req.file_information_class = file_information_class
        query_req.file_id = file.file_id
        query_req.output_buffer_length = output_buffer_length
        return smb_req.parent

    def logoff(self,chan_obj,structure_size=4,reserved=0):
        smb_req = chan_obj.request()
        logoff_req = pike.smb2.LogoffRequest(smb_req)
        logoff_req.structure_size = structure_size
        logoff_req.reserved = reserved
        return smb_req.parent

    def tree_disconnect(self,chan_obj,tree,structure_size=4,reserved=0):
        smb_req = chan_obj.request(obj=tree)
        tree_dis_req = pike.smb2.TreeDisconnectRequest(smb_req)
        tree_dis_req.structure_size = structure_size
        tree_dis_req.reserved = reserved
        return smb_req.parent
