
#-----------------------------------------------------------------------------
#
# Copyright (C) EMC Corporation.  All rights reserved.
#
# Module Name:       xmlparser.py
# Purpose:
#
# Abstract:
#
#        This Script performs xml parsing for the different commands of SMB2
#
# Author:      Sagar Naik, Calsoft (sagar.naik@calsoftinc.com)
#
#-----------------------------------------------------------------------------



class NegotiateRequest():
    """
    XML Parser for the SMB2 Command Negotiate Request
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.DialectCount=tags.find('DialectCount').text
        self.SecurityMode=tags.find('SecurityMode').text
        self.Reserved=tags.find('Reserved').text
        self.Capabilities=tags.find('Capabilities').text
        self.ClientGuid=tags.find('ClientGuid').text
        self.Dialects=tags.find('Dialects').text


    def param(self):
        return (self.StructureSize,self.DialectCount,self.SecurityMode,self.Reserved,self.Capabilities,self.ClientGuid,self.Dialects)



class NegotiateResponse():
    """
    XML Parser for the SMB2 Command Negotiate Response
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.SecurityMode=tags.find('SecurityMode').text
        self.DialectRevision=tags.find('DialectRevision').text
        self.Reserved=tags.find('Reserved').text
        self.ServerGuid=tags.find('ServerGuid').text
        self.Capabilities=tags.find('Capabilities').text
        self.MaxTransactSize=tags.find('MaxTransactSize').text
        self.MaxReadSize=tags.find('MaxReadSize').text
        self.MaxWriteSize=tags.find('MaxWriteSize').text
        self.SystemTime=tags.find('SystemTime').text
        self.ServerStartTime=tags.find('ServerStartTime').text
        self.SecurityBufferOffset=tags.find('SecurityBufferOffset').text
        self.SecurityBufferLength=tags.find('SecurityBufferLength').text
        self.Reserved2=tags.find('Reserved2').text
        self.Buffer=tags.find('Buffer').text

    def param(self):
        return (self.StructureSize,self.SecurityMode, self.DialectRevision,self.Reserved,self.ServerGuid,self.Capabilities,self.MaxTransactSize,self.MaxReadSize,self.MaxWriteSize,self.SystemTime,self.ServerStartTime,self.SecurityBufferOffset,self.SecurityBufferLength,self.Reserved2,self.Buffer)




class SessionSetupRequest():
    """
    XML Parser for the SMB2 Command SessionSetupRequest
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Flags=tags.find('Flags').text
        self.SecurityMode=tags.find('SecurityMode').text
        self.Capabilities=tags.find('Capabilities').text
        self.Channel=tags.find('Channel').text
        self.SecurityBufferOffset=tags.find('SecurityBufferOffset').text
        self.SecurityBufferLength=tags.find('SecurityBufferLength').text
        self.PreviousSessionId=tags.find('PreviousSessionId').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.Flags,self.SecurityMode,self.Capabilities,self.Channel,self.SecurityBufferOffset,self.SecurityBufferLength,self.PreviousSessionId,self.Buffer)


class SessionSetupResponse():
    """
    XML Parser for the SMB2 Command SessionSetupResponse
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.SessionFlags=tags.find('SessionFlags').text
        self.SecurityBufferOffset=tags.find('SecurityBufferOffset').text
        self.SecurityBufferLength=tags.find('SecurityBufferLength').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.SessionFlags,self.SecurityBufferOffset,self.SecurityBufferLength,self.Buffer)


class LOGOFFRequest():
    """
    XML Parser for the SMB2 Command LOGOFFRequest
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text


    def param(self):
        return (self.StructureSize,self.Reserved)


class LOGOFFResponse():
    """
    XML Parser for the SMB2 Command LOGOFFResponse
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text


    def param(self):
        return (self.StructureSize,self.Reserved)


class TreeConnectRequest():
    """
    XML Parser for the SMB2 Command TreeConnectRequest
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text
        self.PathOffset=tags.find('PathOffset').text
        self.PathLength=tags.find('PathLength').text
        self.Buffer=tags.find('Buffer').text



    def param(self):
        return (self.StructureSize,self.Reserved,self.PathOffset,self.PathLength,self.Buffer)


class TreeConnectResponse():
    """
    XML Parser for the SMB2 Command TreeConnect Response
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.ShareType=tags.find('ShareType').text
        self.Reserved=tags.find('Reserved').text
        self.ShareFlags=tags.find('ShareFlags').text
        self.Capabilities=tags.find('Capabilities').text
        self.MaximalAccess=tags.find('MaximalAccess').text


    def param(self):
        return (self.StructureSize,self.ShareType,self.Reserved,self.ShareFlags,self.Capabilities,self.MaximalAccess)


class TreeDisconnectRequest():
    """
    XML Parser for the SMB2 Command TreeDisconnectRequest
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text


    def param(self):
        return (self.StructureSize,self.Reserved)


class TreeDisconnectResponse():
    """
    XML Parser for the SMB2 Command TreeDisconnectResponse
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text


    def param(self):
        return (self.StructureSize,self.Reserved)


class CreateRequest():
    """
    XML Parser for the SMB2 Command Create Request
    """
    def __init__(self, tags):
        self.Buffer=tags.find('Buffer').text
        self.StructureSize=tags.find('StructureSize').text
        self.SecurityFlags=tags.find('SecurityFlags').text
        self.RequestedOplockLevel=tags.find('RequestedOplockLevel').text
        self.ImpersonationLevel=tags.find('ImpersonationLevel').text
        self.SmbCreateFlags=tags.find('SmbCreateFlags').text
        self.Reserved=tags.find('Reserved').text
        self.DesiredAccess=tags.find('DesiredAccess').text
        self.FileAttributes=tags.find('FileAttributes').text
        self.ShareAccess=tags.find('ShareAccess').text
        self.CreateDisposition=tags.find('CreateDisposition').text
        self.CreateOptions=tags.find('CreateOptions').text
        self.NameOffset=tags.find('NameOffset').text
        self.NameLength=tags.find('NameLength').text
        self.CreateContextsOffset=tags.find('CreateContextsOffset').text
        self.CreateContextsLength=tags.find('CreateContextsLength').text


    def param(self):
        return (self.Buffer,self.StructureSize,self.SecurityFlags,self.RequestedOplockLevel,self.ImpersonationLevel,self.SmbCreateFlags,self.Reserved,self.DesiredAccess,self.FileAttributes,self.ShareAccess,self.CreateDisposition,self.CreateOptions,self.NameOffset,self.NameLength,self.CreateContextsOffset,self.CreateContextsLength)

class CreateContextRequest():
    """
    XML Parser for the SMB2 Command Create Request
    """
    def __init__(self, tags):
        self.CreateContextMaximalAccess=tags.find('CreateContextMaximalAccess').text
        self.CreateContextExtendedAttribute=tags.find('CreateContextExtendedAttribute').text
        self.CreateContextSecurityDescriptor=tags.find('CreateContextSecurityDescriptor').text
        self.CreateContextAllocationSize=tags.find('CreateContextAllocationSize').text
        self.CreateContextDurableRequest=tags.find('CreateContextDurableRequest').text
        self.CreateContextDurableReconnect=tags.find('CreateContextDurableReconnect').text

    def param(self):
        return (self.CreateContextMaximalAccess,self.CreateContextExtendedAttribute)
#self.CreateContextSecurityDescriptor,self.CreateContextAllocationSize,self.CreateContextDurableRequest,self.CreateContextDurableReconnect)

class CreateValidation():
    def __init__(self, tags):
        self.ValidationList=tags.find('ValidationList').text
        self.ReadStatus=tags.find('ReadStatus').text
        self.WriteStatus=tags.find('WriteStatus').text
        self.ShareReadStatus=tags.find('ShareReadStatus').text
        self.ShareWriteStatus=tags.find('ShareWriteStatus').text
        self.AllocationSize=tags.find('AllocationSize').text
        self.FileAttributes=tags.find('FileAttributes').text
        self.ShareDeleteStatus=tags.find('ShareDeleteStatus').text
    def param(self):
        return (self.ValidationList,self.ReadStatus,self.WriteStatus,self.ShareReadStatus,self.ShareWriteStatus,self.AllocationSize,self.FileAttributes,self.ShareDeleteStatus)

class CreateResponse():
    """
    XML Parser for the SMB2 Command Create Response
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.OplockLevel=tags.find('OplockLevel').text
        self.Flags=tags.find('Flags').text
        self.CreateAction=tags.find('CreateAction').text
        self.CreationTime=tags.find('CreationTime').text
        self.LastAccessTime=tags.find('LastAccessTime').text
        self.LastWriteTime=tags.find('LastWriteTime').text
        self.ChangeTime=tags.find('ChangeTime').text
        self.AllocationSize=tags.find('AllocationSize').text
        self.EndofFile=tags.find('EndofFile').text
        self.FileAttributes=tags.find('FileAttributes').text
        self.Reserved2=tags.find('Reserved2').text
        self.FileId=tags.find('FileId').text
        self.CreateContextsOffset=tags.find('CreateContextsOffset').text
        self.CreateContextsLength=tags.find('CreateContextsLength').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.OplockLevel,self.Flags,self.CreateAction,self.CreationTime,self.LastAccessTime,self.LastWriteTime,self.ChangeTime,self.AllocationSize,self.EndofFile,self.FileAttributes,self.Reserved2,self.FileId,self.CreateContextsOffset,self.CreateContextsLength,self.Buffer)


class TestBed():
    """
    XML Parser for Test Bed
    """
    def __init__(self, tags):
        self.TestBed=tags.text



    def param(self):
        return (self.TestBed)


class ReadRequest():
    """
    XML Parser for the SMB2 Command Read Request
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Padding=tags.find('Padding').text
        self.Reserved=tags.find('Reserved').text
        self.Length=tags.find('Length').text
        self.Offset=tags.find('Offset').text
        self.FileId=tags.find('FileId').text
        self.MinimumCount=tags.find('MinimumCount').text
        self.Channel=tags.find('Channel').text
        self.RemainingBytes=tags.find('RemainingBytes').text
        self.Buffer=tags.find('Buffer').text
        self.ReadChannelInfoOffset=tags.find('ReadChannelInfoOffset').text
        self.ReadChannelInfoLength=tags.find('ReadChannelInfoLength').text


    def param(self):
        return (self.StructureSize,self.Padding,self.Reserved,self.Length,self.Offset,self.FileId,self.Buffer,self.MinimumCount,self.Channel,self.RemainingBytes,self.ReadChannelInfoOffset,self.ReadChannelInfoOffset)



class ReadResponse():
    """
    XML Parser for the SMB2 Command Read Response
    """
    def __init__(self, tags):
        self.StructureSize=tags.find('StructureSize').text
        self.DataOffset=tags.find('DataOffset').text
        self.Reserved=tags.find('Reserved').text
        self.DataLength=tags.find('DataLength').text
        self.DataRemaining=tags.find('DataRemaining').text
        self.Reserved2=tags.find('Reserved2').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.DataOffset,self.Reserved,self.DataLength,self.DataRemaining,self.Reserved2,self.Buffer)


class Result():
    """
    XML Parser for Result
    """
    def __init__(self, tags):
        self.Cmd = tags.find('Cmd').text
        self.ReturnStatus=tags.find('ReturnStatus').text


    def param(self):
        return (self.Cmd, self.ReturnStatus)


class WriteRequest():
    """
    XML Parser for the SMB2 Command WriteRequest
    """
    def __init__(self,tags):
        self.StructureSize=tags.find('StructureSize').text
        self.DataOffset=tags.find('DataOffset').text
        self.Length=tags.find('Length').text
        self.Offset=tags.find('Offset').text
        self.FileId=tags.find('FileId').text
        self.Channel=tags.find('Channel').text
        self.RemainingBytes=tags.find('RemainingBytes').text
        self.WriteChannelInfoOffset=tags.find('WriteChannelInfoOffset').text
        self.WriteChannelInfoLength=tags.find('WriteChannelInfoLength').text
        self.Flags=tags.find('Flags').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.DataOffset,self.Length,self.Offset,self.FileId,self.Channel,self.RemainingBytes,self.WriteChannelInfoOffset,self.WriteChannelInfoLength,self.Flags,self.Buffer)


class WriteResponse():
    """
    XML Parser for the SMB2 Command WriteResponse
    """
    def __init__(self,tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text
        self.Count=tags.find('Count').text
        self.Remaining=tags.find('Remaining').text
        self.WriteChannelInfoOffset=tags.find('WriteChannelInfoOffset').text
        self.WriteChannelInfoLength=tags.find('WriteChannelInfoLength').text


    def param(self):
        return (self.StructureSize,self.Reserved,self.Count,self.Remaining,self.WriteChannelInfoOffset,self.WriteChannelInfoLength)


class FlushRequest():
    """
    XML Parser for the SMB2 Command FlushRequest
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved1=tags.find('Reserved1').text
        self.Reserved2=tags.find('Reserved2').text
        self.FileId=tags.find('FileId').text

    def param(self):
        return (self.StructureSize,self.Reserved1,self.Reserved2,self.FileId)


class FlushResponse():
    """
    XML Parser for the SMB2 Command FlushResponse
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Reserved)


class LockRequest():
    """
    XML Parser for the SMB2 Command LockRequest
    """
    def __init__(self,tags):
        self.StructureSize=tags.find('StructureSize').text
        self.LockCount=tags.find('LockCount').text
        self.LockSequence=tags.find('LockSequence').text
        self.FileId=tags.find('FileId').text
        self.Locks=tags.find('Locks').text

    def param(self):
        return (self.StructureSize,self.LockCount,self.LockSequence,self.FileId,self.Locks)


class SMB2_LOCK_ELEMENT_Structure():
    """
    XML Parser for the SMB2 Command SMB2_LOCK_ELEMENT_Structure
    """
    def __init__(self):
        self.Offset=tags.find('Offset').text
        self.Length=tags.find('Length').text
        self.Flags=tags.find('Flags').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.Offset,self.Length,self.Flags,self.Reserved)


class LockResponse():
    """
    XML Parser for the SMB2 Command LockResponse
    """
    def __init__(self,tags):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Reserved)


class CancelRequest():
    """
    XML Parser for the SMB2 Command CancelRequest
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Reserved)


class EchoRequest():
    """
    XML Parser for the SMB2 Command EchoRequest
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Reserved)

class EchoResponse():
    """
    XML Parser for the SMB2 Command EchoResponse
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Reserved)


class SMB2_QUERY_DIRECTORY_Request():
    """
    XML Parser for the SMB2 Command SMB2_QUERY_DIRECTORY_Request
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.FileInformationClass=tags.find('FileInformationClass').text
        self.Flags=tags.find('Flags').text
        self.FileIndex=tags.find('FileIndex').text
        self.FileId=tags.find('FileId').text
        self.FileNameOffset=tags.find('FileNameOffset').text
        self.FileNameLength=tags.find('FileNameLength').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.FileInformationClass,self.Flags,self.FileIndex,self.FileId,self.FileNameOffset,self.FileNameLength,self.OutputBufferLength,self.Buffer)


class SMB2_QUERY_DIRECTORY_Response():
    """
    XML Parser for the SMB2 Command SMB2_QUERY_DIRECTORY_Response
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.OutputBufferOffset=tags.find('OutputBufferOffset').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.Buffer=tags.find('Buffer').text

    def param(self):
        return (self.StructureSize,self.OutputBufferOffset,self.OutputBufferLength,self.Buffer)


class SMB2_CHANGE_NOTIFY_Request():
    """
    XML Parser for the SMB2 Command SMB2_CHANGE_NOTIFY_Request
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.Flags=tags.find('Flags').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.FileId=tags.find('FileId').text
        self.CompletionFilter=tags.find('CompletionFilter').text
        self.Reserved=tags.find('Reserved').text

    def param(self):
        return (self.StructureSize,self.Flags,self.OutputBufferLength,self.FileId,self.CompletionFilter,self.Reserved)


class SMB2_CHANGE_NOTIFY_Response():
    """
    XML Parser for the SMB2 Command SMB2_CHANGE_NOTIFY_Response
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.OutputBufferOffset=tags.find('OutputBufferOffset').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.Buffer=tags.find('Buffer').text

    def param(self):
        return (self.StructureSize,self.OutputBufferOffset,self.OutputBufferLength,self.Buffer)


class SMB2_QUERY_INFO_Request():
    """
    XML Parser for the SMB2 Command SMB2_QUERY_INFO_Request
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.InfoType=tags.find('InfoType').text
        self.FileInfoClass=tags.find('FileInfoClass').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.InputBufferOffset=tags.find('InputBufferOffset').text
        self.Reserved=tags.find('Reserved').text
        self.InputBufferLength=tags.find('InputBufferLength').text
        self.AdditionalInformation=tags.find('AdditionalInformation').text
        self.Flags=tags.find('Flags').text
        self.FileId=tags.find('FileId').text
        self.Buffer=tags.find('Buffer').text

    def param(self):
        return (self.StructureSize,self.InfoType,self.FileInfoClass,self.OutputBufferLength,self.InputBufferOffset,self.Reserved,self.InputBufferLength,self.AdditionalInformation,self.Flags,self.FileId,self.Buffer)


class SMB2_QUERY_QUOTA_INFO():
    """
    XML Parser for the SMB2 Command SMB2_QUERY_QUOTA_INFO
    """
    def __init__(self):
        self.ReturnSingle=tags.find('ReturnSingle').text
        self.RestartScan=tags.find('RestartScan').text
        self.Reserved=tags.find('Reserved').text
        self.SidListLength=tags.find('SidListLength').text
        self.StartSidLength=tags.find('StartSidLength').text
        self.StartSidOffset=tags.find('StartSidOffset').text
        self.SidBuffer=tags.find('SidBuffer').text

    def param(self):
        return (self.ReturnSingle,self.RestartScan,self.Reserved,self.SidListLength,self.StartSidLength,self.StartSidOffset,self.SidBuffer)


class SMB2_QUERY_INFO_Response():
    """
    XML Parser for the SMB2 Command SMB2_QUERY_INFO_Response
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.OutputBufferOffset=tags.find('OutputBufferOffset').text
        self.OutputBufferLength=tags.find('OutputBufferLength').text
        self.Buffer=tags.find('Buffer').text


    def param(self):
        return (self.StructureSize,self.OutputBufferOffset,self.OutputBufferLength,self.Buffer)


class SMB2_SET_INFO_Request():
    """
    XML Parser for the SMB2 Command SMB2_SET_INFO_Request
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text
        self.InfoType=tags.find('InfoType').text
        self.FileInfoClass=tags.find('FileInfoClass').text
        self.BufferLength=tags.find('BufferLength').text
        self.BufferOffset=tags.find('BufferOffset').text
        self.Reserved=tags.find('Reserved').text
        self.AdditionalInformation=tags.find('AdditionalInformation').text
        self.FileId=tags.find('FileId').text
        self.Buffer=tags.find('Buffer').text

    def param(self):
        return (self.StructureSize,self.InfoType,self.FileInfoClass,self.BufferLength,self.BufferOffset,self.Reserved,self.AdditionalInformation,self.FileId,self.Buffer)


class SMB2_SET_INFO_Response():
    """
    XML Parser for the SMB2 Command SMB2_SET_INFO_Response
    """
    def __init__(self):
        self.StructureSize=tags.find('StructureSize').text

    def param(self):
        return (self.StructureSize)


