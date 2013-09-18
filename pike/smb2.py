#
# Copyright (c) 2013, EMC Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Module Name:
#
#        smb2.py
#
# Abstract:
#
#        SMB2 support
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

"""
SMB2 packet definitions

This module contains definitions of SMB2 packet frames and
associated constants and data types.

Packet field names are derived by taking the name from MS-SMB2 and
making it PEP-8 compliant. For example, FooBarBaz becomes foo_bar_baz.
This makes it simple to correlate the code with the spec while
maintaining a clear visual distinction between values and types.
"""

import array
import core
import nttime

# Dialects constants
class Dialect(core.ValueEnum):
    DIALECT_SMB2_WILDCARD = 0x02FF
    DIALECT_SMB2_002      = 0x0202
    DIALECT_SMB2_1        = 0x0210
    DIALECT_SMB3_0        = 0x0300

Dialect.import_items(globals())

class Status(core.ValueEnum):
    # We don't have all codes yet, so be permissive
    permissive = True

    STATUS_SUCCESS                  = 0x00000000
    STATUS_PENDING                  = 0x00000103
    STATUS_MORE_PROCESSING_REQUIRED = 0xC0000016
    STATUS_CANCELLED                = 0xC0000120
    STATUS_FILE_NOT_AVAILABLE       = 0xC0000467
    STATUS_ACCESS_DENIED            = 0xC0000022
    STATUS_BUFFER_TOO_SMALL         = 0xC0000023
    STATUS_NO_MORE_FILES            = 0x80000006
    STATUS_OBJECT_NAME_NOT_FOUND    = 0xC0000034

Status.import_items(globals())

# Flag constants
class Flags(core.FlagEnum):
    SMB2_FLAGS_NONE               = 0x00000000
    SMB2_FLAGS_SERVER_TO_REDIR    = 0x00000001
    SMB2_FLAGS_ASYNC_COMMAND      = 0x00000002
    SMB2_FLAGS_RELATED_OPERATIONS = 0x00000004
    SMB2_FLAGS_SIGNED             = 0x00000008
    SMB2_FLAGS_DFS_OPERATIONS     = 0x10000000
    SMB2_FLAGS_REPLAY_OPERATION   = 0x20000000

Flags.import_items(globals())

# Command constants
class Command(core.ValueEnum):
    SMB2_NEGOTIATE       = 0x0000
    SMB2_SESSION_SETUP   = 0x0001
    SMB2_LOGOFF          = 0x0002
    SMB2_TREE_CONNECT    = 0x0003
    SMB2_TREE_DISCONNECT = 0x0004
    SMB2_CREATE          = 0x0005
    SMB2_CLOSE           = 0x0006
    SMB2_READ            = 0x0008
    SMB2_WRITE           = 0x0009
    SMB2_LOCK            = 0x000a
    SMB2_IOCTL           = 0x000b
    SMB2_CANCEL          = 0x000c
    SMB2_ECHO            = 0x000d
    SMB2_QUERY_DIRECTORY = 0x000e
    SMB2_QUERY_INFO      = 0x0010
    SMB2_SET_INFO        = 0x0011
    SMB2_OPLOCK_BREAK    = 0x0012

Command.import_items(globals())

# Share Capabilities
class ShareCaps(core.FlagEnum):
    SMB2_SHARE_CAP_DFS                     = 0x00000008
    SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY = 0x00000010
    SMB2_SHARE_CAP_SCALEOUT                = 0x00000020
    SMB2_SHARE_CAP_CLUSTER                 = 0x00000040

ShareCaps.import_items(globals())

# Misc
RELATED_FID = (2**64-1,2**64-1)
UNSOLICITED_MESSAGE_ID = (2**64-1)

class Smb2(core.Frame):
    _request_table = {}
    _response_table = {}
    _notification_table = {}
    # Decorators to register class as request/response/notification payload
    request = core.Register(_request_table, 'command_id', 'structure_size')
    response = core.Register(_response_table, 'command_id', 'structure_size')
    notification = core.Register(_notification_table, 'command_id', 'structure_size')
    field_blacklist = ['command']

    def __init__(self, parent, context=None):
        core.Frame.__init__(self, parent, context)
        self.credit_charge = 0
        self.channel_sequence = 0
        self.status = None
        self.flags = SMB2_FLAGS_NONE
        self.credit_request = 0
        self.credit_response = None
        self.next_command = 0
        self.message_id = None
        self.async_id = None
        self.session_id = 0
        self.tree_id = 0
        self.command = None
        if parent is not None:
            parent.append(self)

    def _children(self):
        return [self.command] if self.command is not None else []

    def _encode(self, cur):
        cur.encode_bytes('\xfeSMB')
        cur.encode_uint16le(64)
        cur.encode_uint16le(self.credit_charge)
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            cur.encode_uint32le(self.status)
        else:
            cur.encode_uint16le(self.channel_sequence)
            cur.encode_uint16le(0)
        cur.encode_uint16le(self.command.command_id)
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            cur.encode_uint16le(self.credit_response)
        else:
            cur.encode_uint16le(self.credit_request)
        cur.encode_uint32le(self.flags)
        # Set NextCommand to 0 for now
        next_command_hole = cur.hole.encode_uint32le(0)
        cur.encode_uint64le(self.message_id)
        if self.flags & SMB2_FLAGS_ASYNC_COMMAND:
            cur.encode_uint64le(self.async_id)
        else:
            cur.encode_uint32le(0)
            cur.encode_uint32le(self.tree_id)
        cur.encode_uint64le(self.session_id)
        # Set Signature to 0 for now
        signature_hole = cur.hole.encode_bytes([0]*16)

        # Encode command
        self.command.encode(cur)

        # If we are not last command in chain
        if not self.is_last_child():
            # Add padding
            cur.align(self.start, 8)
            cur.trunc()

            # Calculate next_command
            self.next_command = cur - self.start
        else:
            self.next_command = 0

        next_command_hole(self.next_command)
        
        # Calculate and backpatch signature
        if self.flags & SMB2_FLAGS_SIGNED:
            digest = self.context.signing_digest()
            key = self.context.signing_key(self.session_id)
            self.signature = digest(key, self.start[:cur])[:16]
        else:
            self.signature = array.array('B',[0]*16)
            
        signature_hole(self.signature)

    def _decode(self, cur):
        if (cur.decode_bytes(4).tostring() != '\xfeSMB'):
            raise core.BadPacket()
        if (cur.decode_uint16le() != 64):
            raise core.BadPacket()
        self.credit_charge = cur.decode_uint16le()
        # Look ahead and decode flags first
        self.flags = Flags((cur + 8).decode_uint32le())
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            self.status = Status(cur.decode_uint32le())
            self.channel_sequence = None
        else:
            self.channel_sequence = cur.decode_uint16le()
            # Ignore reserved
            cur.decode_uint16le()
            self.status = None
        command_id = cur.decode_uint16le()
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            self.credit_response = cur.decode_uint16le()
            self.credit_request = None
        else:
            self.credit_request = cur.decode_uint16le()
            self.credit_response = None
        # Skip over flags
        cur += 4
        self.next_command = cur.decode_uint32le()
        self.message_id = cur.decode_uint64le()
        if self.flags & SMB2_FLAGS_ASYNC_COMMAND:
            self.async_id = cur.decode_uint64le()
            self.tree_id = None
        else:
            # Ignore reserved
            cur.decode_uint32le()
            self.tree_id = cur.decode_uint32le()
            self.async_id = None
        self.session_id = cur.decode_uint64le()
        self.signature = cur.decode_bytes(16)

        # Peek ahead at structure_size
        structure_size = (cur+0).decode_uint16le()

        key = (command_id, structure_size)

        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            # Distinguish unsoliticed response, error response, normal response
            if self.message_id == UNSOLICITED_MESSAGE_ID:
                if key in Smb2._notification_table:
                    cls = Smb2._notification_table[key]
                else:
                    raise core.BadPacket()
            elif key in Smb2._response_table:
                cls = Smb2._response_table[key]
                if self.status not in cls.allowed_status:
                    cls = ErrorResponse
            else:
                cls = ErrorResponse
        else:
            cls = Smb2._request_table[key]

        # Figure out limit of command data
        if self.next_command:
            end = self.start + self.next_command
        else:
            end = cur.upperbound

        self.command = cls(self)
        with cur.bounded(cur, end):
            self.command.decode(cur)

        # Advance to next frame or end of data
        cur.advanceto(end)

    def verify(self, digest, key):
        if self.flags & SMB2_FLAGS_SIGNED:
            message = self.start[:self.end]
            # Zero out signature in message
            message[12*4:12*4+16] = array.array('B',[0]*16)
            # Calculate signature
            signature = digest(key, message)[:16]
            # Check that signatures match
            if signature != self.signature:
                raise core.BadPacket()

class Command(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        parent.command = self

    def _encode_pre(self, cur):
        core.Frame._encode_pre(self, cur)
        cur.encode_uint16le(self.structure_size)

    def _decode_pre(self, cur):
        core.Frame._decode_pre(self, cur)
        if cur.decode_uint16le() != self.structure_size:
            raise core.BadPacket()

@Smb2.request
class Request(Command):
    pass

@Smb2.response
class Response(Command):
    allowed_status = [STATUS_SUCCESS]

@Smb2.notification
class Notification(Command):
    pass

class ErrorResponse(Command):
    structure_size = 9

    def __init__(self, parent):
        Command.__init__(self, parent)
        parent.command = self
        self.byte_count = None
        self.error_data = None

    def _decode(self, cur):
        # Ignore Reserved
        cur.decode_uint16le()
        self.byte_count = cur.decode_uint32le()

        if self.parent.status == STATUS_BUFFER_TOO_SMALL and self.byte_count == 4:
            # Parse required buffer size
            self.error_data = cur.decode_uint32le()
        else:
           # Ignore ErrorData (FIXME: symlinks)
           cur += self.byte_count if self.byte_count else 1

class Cancel(Request):
    command_id = SMB2_CANCEL
    structure_size = 4

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)

# Negotiate constants
class SecurityMode(core.FlagEnum):
    SMB2_NEGOTIATE_NONE             = 0x0000
    SMB2_NEGOTIATE_SIGNING_ENABLED  = 0x0001
    SMB2_NEGOTIATE_SIGNING_REQUIRED = 0x0002

SecurityMode.import_items(globals())

class GlobalCaps(core.FlagEnum):
    SMB2_GLOBAL_CAP_DFS                = 0x00000001
    SMB2_GLOBAL_CAP_LEASING            = 0x00000002 
    SMB2_GLOBAL_CAP_LARGE_MTU          = 0x00000004
    SMB2_GLOBAL_CAP_MULTI_CHANNEL      = 0x00000008
    SMB2_GLOBAL_CAP_PERSISTENT_HANDLES = 0x00000010
    SMB2_GLOBAL_CAP_DIRECTORY_LEASING  = 0x00000020
    SMB2_GLOBAL_CAP_ENCRYPTION         = 0x00000040 

GlobalCaps.import_items(globals())

class NegotiateRequest(Request):
    command_id = SMB2_NEGOTIATE
    structure_size = 36

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.security_mode = 0
        self.capabilities = 0
        self.client_guid = [0]*16
        self.dialects = []

    def _encode(self, cur):
        cur.encode_uint16le(len(self.dialects))
        cur.encode_uint16le(self.security_mode)
        cur.encode_uint16le(0)
        cur.encode_uint32le(self.capabilities)
        cur.encode_bytes(self.client_guid)
        cur.encode_uint64le(0)
        for dialect in self.dialects:
            cur.encode_uint16le(dialect)

class NegotiateResponse(Response):
    command_id = SMB2_NEGOTIATE
    structure_size = 65

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.security_mode = 0
        self.dialect_revision = 0
        self.server_guid = [0]*16
        self.capabilities = 0
        self.max_transact_size = 0
        self.max_read_size = 0
        self.max_write_size = 0
        self.system_time = 0
        self.server_start_time = 0
        self.security_buffer = None

    def _decode(self, cur):
        self.security_mode = SecurityMode(cur.decode_uint16le())
        self.dialect_revision = Dialect(cur.decode_uint16le())
        # Reserved (ignore)
        cur.decode_uint16le()
        self.server_guid = cur.decode_bytes(16)
        self.capabilities = GlobalCaps(cur.decode_uint32le())
        self.max_transact_size = cur.decode_uint32le()
        self.max_read_size = cur.decode_uint32le()
        self.max_write_size = cur.decode_uint32le()
        self.system_time = nttime.NtTime(cur.decode_uint64le())
        self.server_start_time = nttime.NtTime(cur.decode_uint64le())

        offset = cur.decode_uint16le()
        length = cur.decode_uint16le()

        # Reserved2 (ignore)
        cur.decode_uint32le()

        # Advance to security buffer
        cur.advanceto(self.parent.start + offset)

        self.security_buffer = cur.decode_bytes(length)

# Session setup constants
class SessionFlags(core.FlagEnum):
    SMB2_SESSION_FLAG_NONE    = 0x00
    SMB2_SESSION_FLAG_BINDING = 0x01

SessionFlags.import_items(globals())

# SMB2_ECHO_REQUEST definition
class EchoRequest(Request):
    command_id = SMB2_ECHO
    structure_size = 4

    def __init__(self, parent):
        Request.__init__(self, parent)

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)

# SMB2_ECHO_RESPONSE definition
class EchoResponse(Response):
    # Expect response whenever SMB2_ECHO_REQUEST sent
    command_id = SMB2_ECHO
    structure_size = 4

    def __init__(self, parent):
        Response.__init__(self, parent)

    def _decode(self, cur):
        # Reserved
        cur.decode_uint16le()

class SessionSetupRequest(Request):
    command_id = SMB2_SESSION_SETUP
    structure_size = 25

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.security_mode = 0
        self.capabilities = 0
        self.previous_session_id = 0
        self.security_buffer = None

    def _encode(self, cur):
        cur.encode_uint8le(self.flags)
        cur.encode_uint8le(self.security_mode)
        cur.encode_uint32le(self.capabilities)
        # Channel, must not be used
        cur.encode_uint32le(0)
        # Encode 0 for security buffer offset for now
        sec_buf_ofs = cur.hole.encode_uint16le(0)
        cur.encode_uint16le(len(self.security_buffer))
        cur.encode_uint64le(self.previous_session_id)
        # Go back and set security buffer offset
        sec_buf_ofs(cur - self.parent.start)
        cur.encode_bytes(self.security_buffer)

class SessionSetupResponse(Response):
    command_id = SMB2_SESSION_SETUP
    allowed_status = [STATUS_SUCCESS, STATUS_MORE_PROCESSING_REQUIRED]
    structure_size = 9

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.session_flags = 0
        self.security_buffer = None

    def _decode(self, cur):
        self.session_flags = SessionFlags(cur.decode_uint16le())
        offset = cur.decode_uint16le()
        length = cur.decode_uint16le()

        # Advance to sec buffer
        cur.advanceto(self.parent.start + offset)
        self.security_buffer = cur.decode_bytes(length)

class TreeConnectRequest(Request):
    command_id = SMB2_TREE_CONNECT
    structure_size = 9

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.path = None

    def _encode(self, cur):
        cur.encode_uint16le(0)
        # Set path offset and length to 0 for now
        path_offset = cur.hole.encode_uint16le(0)
        path_len = cur.hole.encode_uint16le(0)
        # Now set correct path offset
        path_offset(cur - self.parent.start)
        path_start = cur.copy()
        cur.encode_utf16le(self.path)
        # Now set correct path length
        path_len(cur - path_start)

class TreeConnectResponse(Response):
    command_id = SMB2_TREE_CONNECT
    structure_size = 16

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.share_type = 0
        self.share_flags = 0
        self.capabilities = 0
        self.maximal_access = 0

    def _decode(self, cur):
        self.share_type = cur.decode_uint8le()
        # Ignore reserved
        cur.decode_uint8le()
        self.share_flags = cur.decode_uint32le()
        self.capabilities = cur.decode_uint32le()
        self.maximal_access = Access(cur.decode_uint32le())

class TreeDisconnectRequest(Request):
    command_id = SMB2_TREE_DISCONNECT
    structure_size = 4

    def __init__(self, parent):
        Request.__init__(self, parent)

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)

class TreeDisconnectResponse(Response):
    command_id = SMB2_TREE_DISCONNECT
    structure_size = 4

    def __init__(self, parent):
        Response.__init__(self, parent)

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint16le()

class LogoffRequest(Request):
    command_id = SMB2_LOGOFF
    structure_size = 4

    def __init__(self, parent):
        Request.__init__(self, parent)

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)

class LogoffResponse(Response):
    command_id = SMB2_LOGOFF
    structure_size = 4

    def __init__(self, parent):
        Response.__init__(self, parent)

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint16le()

# Oplock levels
class OplockLevel(core.ValueEnum):
    SMB2_OPLOCK_LEVEL_NONE      = 0x00
    SMB2_OPLOCK_LEVEL_II        = 0x01
    SMB2_OPLOCK_LEVEL_EXCLUSIVE = 0x08
    SMB2_OPLOCK_LEVEL_BATCH     = 0x09
    SMB2_OPLOCK_LEVEL_LEASE     = 0xFF

OplockLevel.import_items(globals())

# Share access
class ShareAccess(core.FlagEnum):
    FILE_SHARE_READ   = 0x00000001
    FILE_SHARE_WRITE  = 0x00000002
    FILE_SHARE_DELETE = 0x00000004

ShareAccess.import_items(globals())

# Create dispositions
class CreateDisposition(core.ValueEnum):
    FILE_SUPERSEDE    = 0x00000000
    FILE_OPEN         = 0x00000001
    FILE_CREATE       = 0x00000002
    FILE_OPEN_IF      = 0x00000003
    FILE_OVERWRITE    = 0x00000004
    FILE_OVERWRITE_IF = 0x00000005

CreateDisposition.import_items(globals())

# Create options
class CreateOptions(core.FlagEnum):
    FILE_DIRECTORY_FILE            = 0x00000001
    FILE_WRITE_THROUGH             = 0x00000002
    FILE_SEQUENTIAL_ONLY           = 0x00000004
    FILE_NO_INTERMEDIATE_BUFFERING = 0x00000008
    FILE_SYNCHRONOUS_IO_ALERT      = 0x00000010
    FILE_SYNCRHONOUS_IO_NONALERT   = 0x00000020
    FILE_NON_DIRECTORY_FILE        = 0x00000040
    FILE_COMPLETE_IF_OPLOCKED      = 0x00000100
    FILE_NO_EA_KNOWLEDGE           = 0x00000200
    FILE_RANDOM_ACCESS             = 0x00000800
    FILE_DELETE_ON_CLOSE           = 0x00001000
    FILE_OPEN_BY_FILE_ID           = 0x00002000
    FILE_OPEN_FOR_BACKUP_INTENT    = 0x00004000
    FILE_NO_COMPRESSION            = 0x00008000
    FILE_RESERVE_OPFILTER          = 0x00100000
    FILE_OPEN_REPARSE_POINT        = 0x00200000
    FILE_OPEN_NO_RECALL            = 0x00400000
    FILE_OPEN_FOR_FREE_SPACE_QUERY = 0x00800000

CreateOptions.import_items(globals())

# Access masks
class Access(core.FlagEnum):
    FILE_READ_DATA          = 0x00000001
    FILE_WRITE_DATA         = 0x00000002
    FILE_APPEND_DATA        = 0x00000004
    FILE_READ_EA            = 0x00000008
    FILE_WRITE_EA           = 0x00000010
    FILE_EXECUTE            = 0x00000020
    FILE_READ_ATTRIBUTES    = 0x00000080
    FILE_WRITE_ATTRIBUTES   = 0x00000100
    DELETE                  = 0x00010000
    READ_CONTROL            = 0x00020000
    WRITE_DAC               = 0x00040000
    WRITE_OWNER             = 0x00080000
    SYNCHRONIZE             = 0x00100000
    ACCESS_SYSTEM_SECURITY  = 0x01000000
    MAXIMUM_ALLOWED         = 0x02000000
    GENERIC_ALL             = 0x10000000
    GENERIC_EXECUTE         = 0x20000000
    GENERIC_WRITE           = 0x40000000
    GENERIC_READ            = 0x80000000
    FILE_LIST_DIRECTORY     = 0x00000001
    FILE_ADD_FILE           = 0x00000002
    FILE_ADD_SUBDIRECTORY   = 0x00000004
    FILE_TRAVERSE           = 0x00000020
    FILE_DELETE_CHILD       = 0x00000040

Access.import_items(globals())

# File attributes
class FileAttributes(core.FlagEnum):
    FILE_ATTRIBUTE_READONLY              = 0x00000001
    FILE_ATTRIBUTE_HIDDEN                = 0x00000002
    FILE_ATTRIBUTE_SYSTEM                = 0x00000004
    FILE_ATTRIBUTE_DIRECTORY             = 0x00000010
    FILE_ATTRIBUTE_ARCHIVE               = 0x00000020
    FILE_ATTRIBUTE_DEVICE                = 0x00000040
    FILE_ATTRIBUTE_NORMAL                = 0x00000080
    FILE_ATTRIBUTE_TEMPORARY             = 0x00000100
    FILE_ATTRIBUTE_SPARSE_FILE           = 0x00000200
    FILE_ATTRIBUTE_REPARSE_POINT         = 0x00000400
    FILE_ATTRIBUTE_COMPRESSED            = 0x00000800
    FILE_ATTRIBUTE_OFFLINE               = 0x00001000
    FILE_ATTRIBUTE_NOT_CONTENT_INDEXED   = 0x00002000
    FILE_ATTRIBUTE_ENCRYPTED             = 0x00004000

FileAttributes.import_items(globals())

class CreateRequest(Request):
    command_id = SMB2_CREATE
    structure_size = 57
    
    def __init__(self, parent):
        Request.__init__(self, parent)
        self.requested_oplock_level = SMB2_OPLOCK_LEVEL_NONE
        self.impersonation_level = 0
        self.desired_access = 0
        self.file_attributes = 0
        self.share_access = 0
        self.create_disposition = 0
        self.create_options = 0
        self.name = None
        self._create_contexts = []

    def _children(self):
        return self._create_contexts

    def _encode(self, cur):
        # SecurityFlags, must be 0
        cur.encode_uint8le(0)
        cur.encode_uint8le(self.requested_oplock_level)
        cur.encode_uint32le(self.impersonation_level)
        # SmbCreateFlags, must be 0
        cur.encode_uint64le(0)
        # Reserved
        cur.encode_uint64le(0)
        cur.encode_uint32le(self.desired_access)
        cur.encode_uint32le(self.file_attributes)
        cur.encode_uint32le(self.share_access)
        cur.encode_uint32le(self.create_disposition)
        cur.encode_uint32le(self.create_options)
        
        name_offset_hole = cur.hole.encode_uint16le(0)
        name_length_hole = cur.hole.encode_uint16le(0)

        create_contexts_offset_hole = cur.hole.encode_uint32le(0)
        create_contexts_length_hole = cur.hole.encode_uint32le(0)
        
        cur.align(self.parent.start, 2)
        
        buffer_start = cur.copy()

        name_offset_hole(cur - self.parent.start)
        name_start = cur.copy()
        cur.encode_utf16le(self.name)
        name_length_hole(cur - name_start)

        if len(self._create_contexts) != 0:
            # Next field of previous context to fill in
            next_hole = None
            # Pointer to start of previous context
            con_start = None
            cur.align(self.parent.start, 8)
            create_contexts_start = cur.copy()
            create_contexts_offset_hole(cur - self.parent.start)

            for con in self._create_contexts:
                cur.align(self.parent.start, 8)
                if next_hole:
                    next_hole(cur - con_start)
                con_start = cur.copy()
                next_hole = cur.hole.encode_uint32le(0)

                name_offset_hole = cur.hole.encode_uint16le(0)
                cur.encode_uint16le(len(con.name))
                # Reserved
                cur.encode_uint16le(0)
                data_offset_hole = cur.hole.encode_uint16le(0)
                data_length_hole = cur.hole.encode_uint32le(0)

                # Name
                cur.align(self.parent.start, 8)
                name_offset_hole(cur - con_start)
                cur.encode_bytes(con.name)
                name_end = cur.copy()

                # Data
                cur.align(self.parent.start, 8)
                data_start = cur.copy()
                con.encode(cur)
                data_length = cur - data_start
                if data_length:
                    data_offset_hole(data_start - con_start)
                    data_length_hole(cur - data_start)
                else:
                    # Undo align
                    cur.reverseto(name_end)

            create_contexts_length_hole(cur - create_contexts_start)

        if cur == buffer_start:
            # Buffer must be at least 1 byte
            cur.encode_uint8le(0)

    def append(self, e):
        self._create_contexts.append(e)

class CreateResponse(Response):
    command_id = SMB2_CREATE
    structure_size = 89

    _context_table = {}
    create_context = core.Register(_context_table, 'name')

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.oplock_level = 0
        self.flags = 0
        self.create_action = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.allocation_size = 0
        self.end_of_file = 0
        self.file_attributes = 0
        self.file_id = (0,0)
        self._create_contexts = []

    def _children(self):
        return self._create_contexts

    def _decode(self, cur):
        self.oplock_level = OplockLevel(cur.decode_uint8le())
        self.flags = cur.decode_uint8le()
        self.create_action = cur.decode_uint32le()
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.allocation_size = cur.decode_uint64le()
        self.end_of_file = cur.decode_uint64le()
        self.file_attributes = FileAttributes(cur.decode_uint32le())
        # Ignore Reserved2
        cur.decode_uint32le()
        self.file_id = (cur.decode_uint64le(),cur.decode_uint64le())
        create_contexts_offset = cur.decode_uint32le()
        create_contexts_length = cur.decode_uint32le()

        if create_contexts_length:
            create_contexts_start = self.parent.start + create_contexts_offset
            create_contexts_end = create_contexts_start + create_contexts_length
            next_cur = create_contexts_start

            with cur.bounded(create_contexts_start, create_contexts_end):
                while next_cur:
                    cur.seekto(next_cur)
                    con_start = cur.copy()
                    next_offset = cur.decode_uint32le()
                    name_offset = cur.decode_uint16le()
                    name_length = cur.decode_uint16le()
                    # Ignore Reserved
                    cur.decode_uint16le()
                    data_offset = cur.decode_uint16le()
                    data_length = cur.decode_uint32le()
                    
                    name = (con_start + name_offset).decode_bytes(name_length).tostring()
                    
                    cur.seekto(con_start + data_offset)
                    with cur.bounded(cur, cur + data_length):
                        self._context_table[name](self).decode(cur)
                    
                    next_cur = con_start + next_offset if next_offset != 0 else None

            # Make sure we end up at the end regardless of how much we jumped around
            cur.advanceto(create_contexts_end)

    def append(self, e):
        self._create_contexts.append(e)

class CreateRequestContext(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.append(self)

@CreateResponse.create_context
class CreateResponseContext(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.append(self)

class MaximalAccessRequest(CreateRequestContext):
    name = 'MxAc'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.timestamp = None

    def _encode(self, cur):
        if self.timestamp is not None:
            cur.encode_uint64le(self.timestamp)

class MaximalAccessResponse(CreateResponseContext):
    name = 'MxAc'

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.query_status = 0
        self.maximal_access = 0

    def _decode(self, cur):
        self.query_status = Status(cur.decode_uint32le())
        self.maximal_access = Access(cur.decode_uint32le())

class LeaseState(core.FlagEnum):
    SMB2_LEASE_NONE           = 0x00
    SMB2_LEASE_READ_CACHING   = 0x01
    SMB2_LEASE_HANDLE_CACHING = 0x02
    SMB2_LEASE_WRITE_CACHING  = 0x04

LeaseState.import_items(globals())

class LeaseFlags(core.FlagEnum):
    SMB2_LEASE_FLAG_NONE              = 0x00
    SMB2_LEASE_FLAG_BREAK_IN_PROGRESS = 0x02

LeaseFlags.import_items(globals())

class LeaseRequest(CreateRequestContext):
    name = 'RqLs'
    # This class handles V2 requests as well.  Set
    # the lease_flags field to a non-None value
    # to enable the extended fields
    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.lease_key = array.array('B', [0]*16)
        self.lease_state = 0
        # V2 fields
        self.lease_flags = None
        self.parent_lease_key = None
        self.epoch = None

    def _encode(self, cur):
        cur.encode_bytes(self.lease_key)
        cur.encode_uint32le(self.lease_state)
        if (self.lease_flags is not None):
            # V2 variant
            cur.encode_uint32le(self.flags)
            # LeaseDuration is reserved
            cur.encode_uint64le(0)
            cur.encode_bytes(self.parent_lease_key)
            cur.encode_uint16le(self.epoch)
            # Reserved
            cur.encode_uint16le(0)
        else:
            # Regular variant
            # LeaseFlags is reserved
            cur.encode_uint32le(0)
            # LeaseDuration is reserved
            cur.encode_uint64le(0)

class LeaseResponse(CreateResponseContext):
    name = 'RqLs'
    v1_size = 32
    v2_size = 52
    # This class handles V2 responses as well.
    # The extended fields will be set to None
    # if the response was not V2

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.lease_key = array.array('B', [0]*16)
        self.lease_state = 0
        self.lease_flags = 0
        self.parent_lease_key = None
        self.epoch = None

    def _decode(self, cur):
        size = cur.upperbound - cur
        if size != self.v1_size and size != self.v2_size:
            raise core.BadPacket()
        self.lease_key = cur.decode_bytes(16)
        self.lease_state = LeaseState(cur.decode_uint32le())
        self.lease_flags = LeaseFlags(cur.decode_uint32le())
        # LeaseDuration is reserved
        cur.decode_uint64le()

        if size == self.v2_size:
            self.parent_lease_key = cur.decode_bytes(16)
            self.epoch = cur.decode_uint16le()
            # Ignore Reserved
            cur.decode_uint16le()
        else:
            self.parent_lease_key = None
            self.epoch = None

class DurableFlags(core.FlagEnum):
    SMB2_DHANDLE_FLAG_PERSISTENT = 0x02

DurableFlags.import_items(globals())

class DurableHandleRequest(CreateRequestContext):
    name = 'DHnQ'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)

    def _encode(self, cur):
        # Reserved
        cur.encode_uint64le(0)
        cur.encode_uint64le(0)

class DurableHandleResponse(CreateResponseContext):
    name = 'DHnQ'

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint64le()

class DurableHandleReconnectRequest(CreateRequestContext):
    name = 'DHnC'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.file_id = None

    def _encode(self, cur):
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])

class DurableHandleV2Request(CreateRequestContext):
    name = 'DH2Q'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.timeout = 0
        self.flags = 0
        self.create_guid = None

    def _encode(self, cur):
        cur.encode_uint32le(self.timeout)
        cur.encode_uint32le(self.flags)
        # Reserved
        cur.encode_uint64le(0)
        cur.encode_bytes(self.create_guid)

class DurableHandleV2Response(CreateResponseContext):
    name = 'DH2Q'

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.timeout = 0
        self.flags = 0

    def _decode(self, cur):
        self.timeout = cur.decode_uint32le()
        self.flags = DurableFlags(cur.decode_uint32le())

class DurableHandleReconnectV2Request(CreateRequestContext):
    name = 'DH2C'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.fileid = None
        self.create_guid = None
        self.flags = 0

    def _encode(self, cur):
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        cur.encode_bytes(self.create_guid)
        cur.encode_uint32le(self.flags)

class AppInstanceIdRequest(CreateRequestContext):
    name = '\x45\xBC\xA6\x6A\xEF\xA7\xF7\x4A\x90\x08\xFA\x46\x2E\x14\x4D\x74'

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.structure_size = 20
        self.app_instance_id = array.array('B', [0]*16)

    def _encode(self, cur):
        cur.encode_uint16le(self.structure_size)
        # Reserved
        cur.encode_uint16le(0)
        cur.encode_bytes(self.app_instance_id)

class CloseRequest(Request):
    command_id = SMB2_CLOSE
    structure_size = 24

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.file_id = None

    def _encode(self, cur):
        cur.encode_uint16le(self.flags)
        # Reserved
        cur.encode_uint32le(0)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])

class CloseFlags(core.FlagEnum):
    SMB2_CLOSE_FLAG_POSTQUERY_ATTRIB = 0x0001

CloseFlags.import_items(globals())

class CloseResponse(Response):
    command_id = SMB2_CLOSE
    structure_size = 60
    
    def __init__(self, parent):
        Response.__init__(self, parent)
        self.flags = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.allocation_size = 0
        self.end_of_file = 0
        self.file_attributes = 0

    def _decode(self, cur):
        self.flags = CloseFlags(cur.decode_uint16le())
        # Ignore Reserved
        cur.decode_uint32le()
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.allocation_size = cur.decode_uint64le()
        self.end_of_file = cur.decode_uint64le()
        self.file_attributes = FileAttributes(cur.decode_uint32le())

class FileInformationClass(core.ValueEnum):
    FILE_DIRECTORY_INFORMATION = 1
    FILE_BASIC_INFORMATION = 4
    FILE_STANDARD_INFORMATION = 5
    FILE_INTERNAL_INFORMATION = 6
    FILE_EA_INFORMATION = 7
    FILE_ACCESS_INFORMATION = 8
    FILE_NAME_INFORMATION = 9
    FILE_NAMES_INFORMATION = 12
    FILE_POSITION_INFORMATION = 14
    FILE_MODE_INFORMATION = 16
    FILE_ALIGNMENT_INFORMATION = 17
    FILE_ALL_INFORMATION = 18

FileInformationClass.import_items(globals())

class QueryDirectoryRequest(Request):
    command_id = SMB2_QUERY_DIRECTORY
    structure_size = 33

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.file_information_class = 0
        self.flags = 0
        self.file_index = 0
        self.file_id = None
        self.file_name = None
        self.output_buffer_length = 0

    def _encode(self, cur):
        cur.encode_uint8le(self.file_information_class)
        cur.encode_uint8le(self.flags)
        cur.encode_uint32le(self.file_index)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        
        file_name_offset_hole = cur.hole.encode_uint16le(0)
        file_name_length_hole = cur.hole.encode_uint16le(0)
        
        cur.encode_uint32le(self.output_buffer_length)
        
        file_name_start = cur.copy()
        file_name_offset_hole(file_name_start - self.parent.start)
        cur.encode_utf16le(self.file_name)
        file_name_length_hole(cur - file_name_start)

class QueryDirectoryResponse(Response):
    command_id = SMB2_QUERY_DIRECTORY
    structure_size = 9

    _file_info_map = {}
    file_information = core.Register(_file_info_map, 'file_information_class')

    def __init__(self, parent):
        Response.__init__(self, parent)
        
        # Try to figure out file information class by looking up
        # associated request in context
        context = self.context

        if context:
            request = context.get_request(parent.message_id)
        
        if request:
            self._file_information_class = request[0].file_information_class
        else:
            self._file_information_class = None

        self._entries = []

    def _children(self):
        return self._entries

    def append(self, e):
        self._entries.append(e)

    def _decode(self, cur):
        output_buffer_offset = cur.decode_uint16le()
        output_buffer_length = cur.decode_uint32le()
        
        cur.advanceto(self.parent.start + output_buffer_offset)

        end = cur + output_buffer_length

        if self._file_information_class is not None:
            cls = self._file_info_map[self._file_information_class]

            with cur.bounded(cur, end):
                while cur < end:
                    cls(self).decode(cur)
        else:
            cur.advanceto(end)

class InfoType(core.ValueEnum):
    SMB2_0_INFO_FILE       = 0x01
    SMB2_0_INFO_FILESYSTEM = 0x02
    SMB2_0_INFO_SECURITY   = 0x03
    SMB2_0_INFO_QUOTA      = 0x04

InfoType.import_items(globals())

class SecurityInformation(core.FlagEnum):
    OWNER_SECURITY_INFORMATION = 0x00000001
    GROUP_SECURITY_INFORMATION = 0x00000002
    DACL_SECURITY_INFORMATION = 0x00000004
    SACL_SECURITY_INFORMATION = 0x00000008

SecurityInformation.import_items(globals())

class ScanFlags(core.FlagEnum):
    SL_RESTART_SCAN        = 0x00000001
    SL_RETURN_SINGLE_ENTRY = 0x00000002
    SL_INDEX_SPECIFIED     = 0x00000004

ScanFlags.import_items(globals())

class QueryInfoRequest(Request):
    command_id = SMB2_QUERY_INFO
    structure_size = 41
    
    def __init__(self, parent):
        Request.__init__(self, parent)
        self.info_type = None
        self.file_information_class = 0
        self.additional_information = 0
        self.flags = 0
        self.file_id = None
        self.output_buffer_length = 4096
        
    def _encode(self, cur):
        cur.encode_uint8le(self.info_type)
        cur.encode_uint8le(self.file_information_class)
        cur.encode_uint32le(self.output_buffer_length)
        
        # We're not implementing the input buffer support right now
        cur.encode_uint16le(0)
        cur.encode_uint16le(0)  # Reserved
        
        # We're not implementing the input buffer support right now
        cur.encode_uint32le(0)

        cur.encode_uint32le(self.additional_information)
        cur.encode_uint32le(self.flags)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])


class QueryInfoResponse(Response):
    command_id = SMB2_QUERY_INFO
    structure_size = 9
    
    _file_info_map = {}
    file_information = core.Register(_file_info_map, "file_information_class")
    
    def __init__(self, parent):
        Response.__init__(self, parent)
        self._info_type = 0
        self._file_information_class = 0
        
        context = self.context
        if context:
            request = context.get_request(parent.message_id)
        
        if request:
            self._info_type = request[0].info_type
            self._file_information_class = request[0].file_information_class
        
        self._entries = []
        
    def _children(self):
        return self._entries
    
    def append(self, e):
        self._entries.append(e)
        
    def _decode(self, cur):
        output_buffer_offset = cur.decode_uint16le()
        output_buffer_length = cur.decode_uint32le()
        
        cur.advanceto(self.parent.start + output_buffer_offset)
        end = cur + output_buffer_length
        
        if self._file_information_class is not None:
            cls = self._file_info_map[self._file_information_class]
            with cur.bounded(cur, end):
                cls(self).decode(cur)
        else:
            cur.advanceto(end)
        

class SetInfoRequest(Request):
    command_id = SMB2_SET_INFO
    structure_size = 33

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.info_type = 0
        self.file_information_class = 0
        self.input_buffer_length = 0
        self.input_buffer_offset = 0
        self.security_info = 0                # SMB2_QUERY_INFO.AdditionalInformation
        self.file_id = None
        
        self._entries = []
        
    def _children(self):
        return self._entries
    
    def append(self, e):
        self._entries.append(e)
        
    def _encode(self, cur):
        if not self.info_type:
            # Only one supported at the moment.
            # When we support more, look at child object
            # to decide what kind of set we are doing
            self.info_type = SMB2_0_INFO_FILE

        if not self.file_information_class:
            # Determine it from child object
            self.file_information_class = self[0].file_information_class

        cur.encode_uint8le(self.info_type)
        cur.encode_uint8le(self.file_information_class)
        
        buffer_length_hole = cur.hole.encode_uint32le(0)
        buffer_offset_hole = cur.hole.encode_uint16le(0)
        cur.encode_uint16le(0)  # Reserved
        
        cur.encode_uint32le(self.security_info)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])

        buffer_start = cur.copy()
        buffer_offset_hole(buffer_start - self.parent.start)

        for info in self._entries:
            info.encode(cur)

        buffer_length_hole(cur - buffer_start)


class SetInfoResponse(Response):
    command_id = SMB2_SET_INFO
    structure_size = 2

    def __init__(self, parent):
        Response.__init__(self, parent)
        
    def _decode(self, cur):
        #The response is only the structure size
        pass


@QueryDirectoryResponse.file_information
@QueryInfoResponse.file_information
class FileInformation(core.Frame):
    pass

class FileAccessInformation(FileInformation):
    file_information_class = FILE_ACCESS_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.access_flags = 0
        if parent is not None:
            parent.append(self)
        
    def _decode(self, cur):
        self.access_flags = Access(cur.decode_uint32le())
        
# Alignment Requirement flags
class Alignment(core.ValueEnum):
    FILE_BYTE_ALIGNMENT = 0x00000000
    FILE_WORD_ALIGNMENT = 0x00000001
    FILE_LONG_ALIGNMENT = 0x00000003
    FILE_QUAD_ALIGNMENT = 0x00000007
    FILE_OCTA_ALIGNMENT = 0x0000000f
    FILE_32_BYTE_ALIGNMENT = 0x0000001f
    FILE_64_BYTE_ALIGNMENT = 0x0000003f
    FILE_128_BYTE_ALIGNMENT = 0x0000007f
    FILE_256_BYTE_ALIGNMENT = 0x000000ff
    FILE_512_BYTE_ALIGNMENT = 0x000001ff

Alignment.import_items(globals())

class FileAlignmentInformation(FileInformation):
    file_information_class = FILE_ALIGNMENT_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.alignment_requirement = 0
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        self.alignment_requirement = Alignment(cur.decode_uint32le())

class FileAllInformation(FileInformation):
    file_information_class = FILE_ALL_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        if parent is not None:
            parent.append(self)
        
        self.basic_information = FileBasicInformation()
        self.standard_information = FileStandardInformation()
        self.internal_information = FileInternalInformation()
        self.ea_information = FileEaInformation()
        self.access_information = FileAccessInformation()
        self.position_information = FilePositionInformation()
        self.mode_information = FileModeInformation()
        self.alignment_information = FileAlignmentInformation()
        self.name_information = FileNameInformation()
            
    def _decode(self, cur):
        for field in self.fields:
            getattr(self, field).decode(cur)
            
class FileDirectoryInformation(FileInformation):
    file_information_class = FILE_DIRECTORY_INFORMATION

    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.end_of_file = 0
        self.allocation_size = 0
        self.file_attributes = 0
        self.file_name = None
        if parent is not None:
            parent.append(self)

    def _decode(self, cur):
        next_offset = cur.decode_uint32le()
        self.file_index = cur.decode_uint32le()
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.end_of_file = cur.decode_uint64le()
        self.allocation_size = cur.decode_uint64le()
        self.file_attributes = FileAttributes(cur.decode_uint32le())

        file_name_length = cur.decode_uint32le()
        self.file_name = cur.decode_utf16le(file_name_length)

        if next_offset:
            cur.advanceto(self.start + next_offset)
        else:
            cur.advanceto(cur.upperbound)
            

class FileBasicInformation(FileInformation):
    file_information_class = FILE_BASIC_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.file_attributes = 0
        if parent is not None:
            parent.append(self)
        
    def _decode(self, cur):
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.file_attributes = FileAttributes(cur.decode_uint32le())
        # Ignore the 4-byte reserved field
        cur.decode_uint32le()

    def _encode(self, cur):
        cur.encode_uint64le(self.creation_time)
        cur.encode_uint64le(self.last_access_time)
        cur.encode_uint64le(self.last_write_time)
        cur.encode_uint64le(self.change_time)
        cur.encode_uint32le(self.file_attributes)
        # Ignore the 4-byte reserved field
        cur.encode_uint32le(0)

class FileInternalInformation(FileInformation):
    file_information_class = FILE_INTERNAL_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.index_number = 0
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        self.index_number = cur.decode_uint64le()

class FileModeInformation(FileInformation):
    file_information_class = FILE_MODE_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        # See Create options (e.g. FILE_DELETE_ON_CLOSE) for available flags
        self.mode = 0
        if parent is not None:
            parent.append(self)
        
    def _decode(self, cur):
        self.mode = CreateOptions(cur.decode_uint32le())
        
    def _encode(self, cur):
        cur.encode_uint32le(self.mode)

class FileNameInformation(FileInformation):
    file_information_class = FILE_NAME_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.file_name = None
        
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        file_name_length = cur.decode_uint32le()
        self.file_name = cur.decode_utf16le(file_name_length)
                
class FileNamesInformation(FileInformation):
    file_information_class = FILE_NAMES_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.file_name = None
        
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        next_entry_offset = cur.decode_uint32le()
        self.file_index = cur.decode_uint32le()
        
        file_name_length = cur.decode_uint32le()
        self.file_name = cur.decode_utf16le(file_name_length)
        
        if next_entry_offset:
            cur.advanceto(self.start + next_entry_offset)
        else:
            cur.advanceto(cur.upperbound)
        
class FilePositionInformation(FileInformation):
    file_information_class = FILE_POSITION_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.current_byte_offset = 0
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        self.current_byte_offset = cur.decode_uint64le()
    
    def _encode(self, cur):
        cur.encode_uint64le(self.current_byte_offset)

class FileStandardInformation(FileInformation):
    file_information_class = FILE_STANDARD_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.allocation_size = 0
        self.end_of_file = 0
        self.number_of_links = 0
        self.delete_pending = 0
        self.directory = 0
        if parent is not None:
            parent.append(self)
            
    def _decode(self, cur):
        self.allocation_size = cur.decode_uint64le()
        self.end_of_file = cur.decode_uint64le()
        self.number_of_links = cur.decode_uint32le()
        self.delete_pending = cur.decode_uint8le()
        self.directory = cur.decode_uint8le()
        # Ignore 2-bytes Reserved field
        cur.decode_uint16le()

    def _encode(self, cur):
        cur.encode_uint64le(self.allocation_size)
        cur.encode_uint64le(self.end_of_file)
        cur.encode_uint32le(self.number_of_links)
        cur.encode_uint8le(self.delete_pending)
        cur.encode_uint8le(self.directory)
        # Ignore 2-bytes Reserved field
        cur.encode_uint16le()
        
class FileEaInformation(FileInformation):
    file_information_class = FILE_EA_INFORMATION
    
    def __init__(self, parent = None):
        FileInformation.__init__(self, parent)
        self.ea_size = 0
        if parent is not None:
            parent.append(self)
    
    def _decode(self, cur):
        self.ea_size = cur.decode_uint32le()

class BreakLeaseFlags(core.FlagEnum):
    SMB2_NOTIFY_BREAK_LEASE_FLAG_NONE         = 0x00
    SMB2_NOTIFY_BREAK_LEASE_FLAG_ACK_REQUIRED = 0x01

BreakLeaseFlags.import_items(globals())

class OplockBreakNotification(Notification):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 24

    def __init__(self, parent):
        Notification.__init__(self, parent)
        self.oplock_level = 0
        self.file_id = None

    def _decode(self, cur):
        self.oplock_level = OplockLevel(cur.decode_uint8le())
        # Ignore Reserved1
        cur.decode_uint8le()
        # Ignore Reserved2
        cur.decode_uint32le()
        self.file_id = (cur.decode_uint64le(), cur.decode_uint64le())

class LeaseBreakNotification(Notification):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 44

    def __init__(self, parent):
        Notification.__init__(self, parent)
        self.new_epoch = 0
        self.flags = 0
        self.lease_key = 0
        self.current_lease_state = 0
        self.new_lease_state = 0

    def _decode(self, cur):
        self.new_epoch = cur.decode_uint16le()
        self.flags = BreakLeaseFlags(cur.decode_uint32le())
        self.lease_key = cur.decode_bytes(16)
        self.current_lease_state = LeaseState(cur.decode_uint32le())
        self.new_lease_state = LeaseState(cur.decode_uint32le())
        # Ignore BreakReason
        cur.decode_uint32le()
        # Ignore AcccessMaskHint
        cur.decode_uint32le()
        # Ignore ShareMaskHint
        cur.decode_uint32le()

class OplockBreakAcknowledgement(Request):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 24

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.oplock_level = 0
        self.file_id = None

    def _encode(self, cur):
        cur.encode_uint8le(self.oplock_level)
        # Reserved
        cur.encode_uint8le(0)
        # Reserved2
        cur.encode_uint32le(0)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])

class LeaseBreakAcknowledgement(Request):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 36

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.lease_key = 0
        self.lease_state = 0

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)
        cur.encode_uint32le(self.flags)
        cur.encode_bytes(self.lease_key)
        cur.encode_uint32le(self.lease_state)
        # LeaseDuration is reserved
        cur.encode_uint64le(0)

class OplockBreakResponse(Response):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 24
    
    def __init__(self, parent):
        Response.__init__(self, parent)
        self.oplock_level = 0
        self.file_id = 0

    def _decode(self, cur):
        self.oplock_level = OplockLevel(cur.decode_uint8le())
        # Ignore Reserved1
        cur.decode_uint8le()
        # Ignore Reserved2
        cur.decode_uint32le()
        self.file_id = (cur.decode_uint64le(), cur.decode_uint64le())

class LeaseBreakResponse(Response):
    command_id = SMB2_OPLOCK_BREAK
    structure_size = 36
    
    def __init__(self, parent):
        Response.__init__(self, parent)
        self.flags = 0
        self.lease_key = 0
        self.lease_state = 0

    def _decode(self, cur):
        # Ignore Reserved
        cur.decode_uint16le()
        self.flags = BreakLeaseFlags(cur.decode_uint32le())
        self.lease_key = cur.decode_bytes(16)
        self.lease_state = LeaseState(cur.decode_uint32le())
        # Ignore LeaseDuration
        cur.decode_uint64le()

class ReadRequest(Request):
    command_id = SMB2_READ
    structure_size = 49

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.length = 0
        self.offset = 0
        self.minimum_count = 0
        self.remaining_bytes = 0
        self.file_id = None

    def _encode(self, cur):
        # Padding
        cur.encode_uint8le(16)
        # Reserved
        cur.encode_uint8le(0)
        cur.encode_uint32le(self.length)
        cur.encode_uint64le(self.offset)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        cur.encode_uint32le(self.minimum_count)
        # Channel
        cur.encode_uint32le(0)
        cur.encode_uint32le(self.remaining_bytes)
        # ReadChannelInfoOffset
        cur.encode_uint16le(0)
        # ReadChannelInfoLength
        cur.encode_uint16le(0)
        # Buffer
        cur.encode_uint8le(0)

class ReadResponse(Response):
    command_id = SMB2_READ
    structure_size = 17

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.data = None

    def _decode(self, cur):
        offset = cur.decode_uint8le()
        # Ignore reserved
        cur.decode_uint8le()
        length = cur.decode_uint32le()
        # Ignore DataRemaining
        cur.decode_uint32le()
        # Ignore reserved
        cur.decode_uint32le()

        # Advance to data
        cur.advanceto(self.parent.start + offset)

        self.data = cur.decode_bytes(length)

# Flag constants
class WriteFlags(core.FlagEnum):
    SMB2_WRITEFLAG_WRITE_THROUGH = 0x00000001

WriteFlags.import_items(globals())

class WriteRequest(Request):
    command_id = SMB2_WRITE
    structure_size = 49

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.offset = 0
        self.file_id = None
        self.remaining_bytes = 0
        self.flags = 0
        self.buffer = None

    def _encode(self, cur):
        # Encode 0 for buffer offset for now
        buf_ofs = cur.hole.encode_uint16le(0)
        if self.buffer:
            cur.encode_uint32le(len(self.buffer))
        else:
            cur.encode_uint32le(0)
        cur.encode_uint64le(self.offset)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        # Channel
        cur.encode_uint32le(0)
        cur.encode_uint32le(self.remaining_bytes)
        # WriteChannelInfoOffset
        cur.encode_uint16le(0)
        # WriteChannelInfoLength
        cur.encode_uint16le(0)
        cur.encode_uint32le(self.flags)
        # Go back and set buffer offset
        buf_ofs(cur - self.parent.start)
        if self.buffer:
            cur.encode_bytes(self.buffer)

class WriteResponse(Response):
    command_id = SMB2_WRITE
    structure_size = 17

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.count = 0

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint16le()
        self.count = cur.decode_uint32le()
        # Ignore Remaining
        cur.decode_uint32le()
        # Ignore WriteChannelInfoOffset
        cur.decode_uint16le()
        # Ignore WriteChannelInfoLength
        cur.decode_uint16le()

class LockFlags(core.FlagEnum):
    SMB2_LOCKFLAG_SHARED_LOCK      = 0x00000001
    SMB2_LOCKFLAG_EXCLUSIVE_LOCK   = 0x00000002
    SMB2_LOCKFLAG_UN_LOCK          = 0x00000004
    SMB2_LOCKFLAG_FAIL_IMMEDIATELY = 0x00000010

LockFlags.import_items(globals())

class LockRequest(Request):
    """
    @ivar locks: A list of lock tuples, each of which consists of (offset, length, flags).
    """
    command_id = SMB2_LOCK
    structure_size = 48
    
    def __init__(self, parent):
        Request.__init__(self, parent)
        self.file_id = None
        self.lock_sequence = 0
        self.locks = []

    def _encode(self, cur):
        cur.encode_uint16le(len(self.locks))
        cur.encode_uint32le(self.lock_sequence)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])

        for lock in self.locks:
            # Offset
            cur.encode_uint64le(lock[0])
            # Length
            cur.encode_uint64le(lock[1])
            # Flags
            cur.encode_uint32le(lock[2])
            # Reserved
            cur.encode_uint32le(0)

class LockResponse(Response):
    command_id = SMB2_LOCK
    structure_size = 4

    def __init__(self, parent):
        Response.__init__(self, parent)

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint16le()

class IoctlCode(core.ValueEnum):
    FSCTL_DFS_GET_REFERRALS            = 0x00060194
    FSCTL_PIPE_PEEK                    = 0x0011400C
    FSCTL_PIPE_WAIT                    = 0x00110018
    FSCTL_PIPE_TRANSCEIVE              = 0x0011C017
    FSCTL_SRV_COPYCHUNK                = 0x001440F2
    FSCTL_SRV_ENUMERATE_SNAPSHOTS      = 0x00144064
    FSCTL_SRV_REQUEST_RESUME_KEY       = 0x00140078
    FSCTL_SRV_READ_HASH                = 0x001441bb
    FSCTL_SRV_COPYCHUNK_WRITE          = 0x001480F2
    FSCTL_LMR_REQUEST_RESILIENCY       = 0x001401D4
    FSCTL_QUERY_NETWORK_INTERFACE_INFO = 0x001401FC
    FSCTL_SET_REPARSE_POINT            = 0x000900A4
    FSCTL_DFS_GET_REFERRALS_EX         = 0x000601B0
    FSCTL_FILE_LEVEL_TRIM              = 0x00098208
    FSCTL_VALIDATE_NEGOTIATE_INFO      = 0x00140204

IoctlCode.import_items(globals())

class IoctlFlags(core.FlagEnum):
    SMB2_0_IOCTL_IS_FSCTL = 0x00000001

IoctlFlags.import_items(globals())
    
class IoctlRequest(Request):
    command_id = SMB2_IOCTL
    structure_size = 57

    field_blacklist = ['ioctl_input']

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.ctl_code = None
        # MS-SMB2 says that the file ID should be set to 0xffffffffffffffff for
        # certain IOCTLs.  Assuming that means both persistent and volatile.
        self.file_id = (0xffffffffffffffff, 0xffffffffffffffff)
        self.input_offset = None
        self.input_count = None
        self.max_input_response = 0
        self.output_offset = 0
        self.output_count = 0
        self.max_output_response = 256
        self.flags = 0
        self.buffer = None
        self.ioctl_input = None

    def _children(self):
        return [self.ioctl_input] if self.ioctl_input is not None else []

    def _encode(self, cur):
        if not self.ctl_code:
            self.ctl_code = self[0].ioctl_ctl_code

        # Reserved should be set to 0
        cur.encode_uint16le(0)
        cur.encode_uint32le(self.ctl_code)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        # Create holes where we will fill in offset and count later
        input_offset_hole = cur.hole.encode_uint32le(0)
        input_count_hole = cur.hole.encode_uint32le(0)
        cur.encode_uint32le(self.max_input_response)
        #For requests, output offset and count should be 0
        cur.encode_uint32le(self.output_offset)
        cur.encode_uint32le(self.output_count)
        cur.encode_uint32le(self.max_output_response)
        cur.encode_uint32le(self.flags)
        # Reserved2 should be set to 0
        cur.encode_uint32le(0)

        buffer_start = cur.copy()
        input_offset_hole(buffer_start - self.parent.start)
        
        # Encode the ioctl
        self.ioctl_input.encode(cur)
        # Set the ioctl count, which is the length in bytes
        input_count_hole(cur - buffer_start)

class IoctlResponse(Response):
    command_id = SMB2_IOCTL
    structure_size = 49

    field_blacklist = ['ioctl_output']

    # Set up a map so that the correct IoctlOutput frame decoder will be called,
    # based on the ioctl_ctl_code defined in the IoctlOutput
    _ioctl_ctl_code_map = {}
    ioctl_ctl_code = core.Register(_ioctl_ctl_code_map, "ioctl_ctl_code")

    def __init__(self, parent):
        Response.__init__(self, parent)
        self._ioctl_output = None

    def _children(self):
        return [self.ioctl_output] if self.ioctl_output is not None else []

    def _decode(self, cur):
        self.reserved = cur.decode_uint16le()
        self.ctl_code = IoctlCode(cur.decode_uint32le())
        self.file_id = (cur.decode_uint64le(), cur.decode_uint64le())
        self.input_offset = cur.decode_uint32le()
        self.input_count = cur.decode_uint32le()
        self.output_offset = cur.decode_uint32le()
        self.output_count = cur.decode_uint32le()
        self.flags = cur.decode_uint32le()
        self.reserved2 = cur.decode_uint32le()

        cur.advanceto(self.parent.start + self.output_offset)
        end = cur + self.output_count
        
        ioctl = self._ioctl_ctl_code_map[self.ctl_code]
        with cur.bounded(cur, end):
            ioctl(self).decode(cur)

class IoctlInput(core.Frame):
    def __init__(self, parent):
        super(IoctlInput, self).__init__(parent)
        if parent is not None:
            parent.ioctl_input = self

class ValidateNegotiateInfoRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_VALIDATE_NEGOTIATE_INFO

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        self.capabilities = None
        self.client_guid = None
        self.security_mode = None
        self.dialects_count = None
        self.dialects = None

    def  _encode(self, cur):
        cur.encode_uint32le(self.capabilities)
        cur.encode_bytes(self.client_guid)
        cur.encode_uint16le(self.security_mode)

        # If dialects_count was not set manually, calculate it here.
        if self.dialects_count is None:
            self.dialects_count = len(self.dialects)
        cur.encode_uint16le(self.dialects_count)

        for dialect in self.dialects:
            cur.encode_uint16le(dialect)

@IoctlResponse.ioctl_ctl_code
class IoctlOutput(core.Frame):
    def __init__(self, parent):
        super(IoctlOutput, self).__init__(parent)
        if parent is not None:
            parent.ioctl_output = self
    
class ValidateNegotiateInfoResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_VALIDATE_NEGOTIATE_INFO

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        self.capabilities = None
        self.guid = None
        self.security_mode = None
        self.dialect = None

    def _decode(self, cur):
        self.capabilities = GlobalCaps(cur.decode_uint32le())
        self.client_guid = cur.decode_bytes(16)
        self.security_mode = SecurityMode(cur.decode_uint16le())
        self.dialect = Dialect(cur.decode_uint16le())
