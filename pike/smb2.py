#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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

from __future__ import absolute_import
from builtins import str
from builtins import range

import array
import re

from . import core
from . import nttime
from . import ntstatus


# Dialects constants
class Dialect(core.ValueEnum):
    DIALECT_SMB2_WILDCARD = 0x02FF
    DIALECT_SMB2_002 = 0x0202
    DIALECT_SMB2_1 = 0x0210
    DIALECT_SMB3_0 = 0x0300
    DIALECT_SMB3_0_2 = 0x0302
    DIALECT_SMB3_1_1 = 0x0311


Dialect.import_items(globals())


# Flag constants
class Flags(core.FlagEnum):
    SMB2_FLAGS_NONE = 0x00000000
    SMB2_FLAGS_SERVER_TO_REDIR = 0x00000001
    SMB2_FLAGS_ASYNC_COMMAND = 0x00000002
    SMB2_FLAGS_RELATED_OPERATIONS = 0x00000004
    SMB2_FLAGS_SIGNED = 0x00000008
    SMB2_FLAGS_DFS_OPERATIONS = 0x10000000
    SMB2_FLAGS_REPLAY_OPERATION = 0x20000000


Flags.import_items(globals())


# Command constants
class CommandId(core.ValueEnum):
    SMB2_NEGOTIATE = 0x0000
    SMB2_SESSION_SETUP = 0x0001
    SMB2_LOGOFF = 0x0002
    SMB2_TREE_CONNECT = 0x0003
    SMB2_TREE_DISCONNECT = 0x0004
    SMB2_CREATE = 0x0005
    SMB2_CLOSE = 0x0006
    SMB2_FLUSH = 0x0007
    SMB2_READ = 0x0008
    SMB2_WRITE = 0x0009
    SMB2_LOCK = 0x000A
    SMB2_IOCTL = 0x000B
    SMB2_CANCEL = 0x000C
    SMB2_ECHO = 0x000D
    SMB2_QUERY_DIRECTORY = 0x000E
    SMB2_CHANGE_NOTIFY = 0x000F
    SMB2_QUERY_INFO = 0x0010
    SMB2_SET_INFO = 0x0011
    SMB2_OPLOCK_BREAK = 0x0012


CommandId.import_items(globals())


# Share Capabilities
class ShareCaps(core.FlagEnum):
    SMB2_SHARE_CAP_DFS = 0x00000008
    SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY = 0x00000010
    SMB2_SHARE_CAP_SCALEOUT = 0x00000020
    SMB2_SHARE_CAP_CLUSTER = 0x00000040


ShareCaps.import_items(globals())


# Share flags
class ShareFlags(core.FlagEnum):
    SMB2_SHAREFLAG_MANUAL_CACHING = 0x00000000
    SMB2_SHAREFLAG_AUTO_CACHING = 0x00000010
    SMB2_SHAREFLAG_VDO_CACHING = 0x00000020
    SMB2_SHAREFLAG_NO_CACHING = 0x00000030
    SMB2_SHAREFLAG_DFS = 0x00000001
    SMB2_SHAREFLAG_DFS_ROOT = 0x00000002
    SMB2_SHAREFLAG_RESTRICT_EXCLUSIVE_OPENS = 0x00000100
    SMB2_SHAREFLAG_FORCE_SHARED_DELETE = 0x00000200
    SMB2_SHAREFLAG_ALLOW_NAMESPACE_CACHING = 0x00000400
    SMB2_SHAREFLAG_ACCESS_BASED_DIRECTORY_ENUM = 0x00000800
    SMB2_SHAREFLAG_FORCE_LEVELII_OPLOCK = 0x00001000
    SMB2_SHAREFLAG_ENABLE_HASH_V1 = 0x00002000
    SMB2_SHAREFLAG_ENABLE_HASH_V2 = 0x00004000
    SMB2_SHAREFLAG_ENCRYPT_DATA = 0x00008000


ShareFlags.import_items(globals())

# Misc
RELATED_FID = (2 ** 64 - 1, 2 ** 64 - 1)
UNSOLICITED_MESSAGE_ID = 2 ** 64 - 1


class Smb2(core.Frame):
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True
    _request_table = {}
    _response_table = {}
    _notification_table = {}
    # Decorators to register class as request/response/notification payload
    request = core.Register(_request_table, "command_id", "structure_size")
    response = core.Register(_response_table, "command_id", "structure_size")
    notification = core.Register(_notification_table, "command_id", "structure_size")

    def __init__(self, parent, context=None):
        core.Frame.__init__(self, parent, context)
        self.credit_charge = None
        self.channel_sequence = 0
        self.status = None
        self.command = None
        self.credit_request = None
        self.credit_response = None
        self.flags = SMB2_FLAGS_NONE
        self.next_command = 0
        self.message_id = None
        self.async_id = None
        self.session_id = 0
        self.tree_id = 0
        self._command = None
        if parent is not None:
            parent.append(self)

    def _log_str(self):
        components = []
        if not self.children:
            components.append(type(self).__name__)
        else:
            components.extend(self._log_str_children())
        if self.status:
            components.insert(1, str(self.status))
        return " ".join(components)

    def _children(self):
        return [self._command] if self._command is not None else []

    def _encode(self, cur):
        cur.encode_bytes(b"\xfeSMB")
        cur.encode_uint16le(64)
        cur.encode_uint16le(self.credit_charge)
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            cur.encode_uint32le(self.status)
        else:
            cur.encode_uint16le(self.channel_sequence)
            cur.encode_uint16le(0)

        if self.command is None:
            self.command = self._command.command_id
        cur.encode_uint16le(self.command)

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
            cur.encode_uint32le(0xFEFF)  # default process id
            cur.encode_uint32le(self.tree_id)
        cur.encode_uint64le(self.session_id)
        # Set Signature to 0 for now
        signature_hole = cur.hole.encode_bytes([0] * 16)

        # Encode command body
        self._command.encode(cur)

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
        if not hasattr(self, "signature"):
            if self.flags & SMB2_FLAGS_SIGNED:
                digest = self.context.signing_digest()
                key = self.context.signing_key(self.session_id)
                self.signature = digest(key, self.start[:cur])[:16]
            else:
                self.signature = array.array("B", [0] * 16)

        signature_hole(self.signature)

    def _decode(self, cur):
        if cur.decode_bytes(4).tobytes() != b"\xfeSMB":
            raise core.BadPacket()
        if cur.decode_uint16le() != 64:
            raise core.BadPacket()
        self.credit_charge = cur.decode_uint16le()
        # Look ahead and decode flags first
        self.flags = Flags((cur + 8).decode_uint32le())
        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            self.status = ntstatus.Status(cur.decode_uint32le())
            self.channel_sequence = None
        else:
            self.channel_sequence = cur.decode_uint16le()
            # Ignore reserved
            cur.decode_uint16le()
            self.status = None
        self.command = CommandId(cur.decode_uint16le())
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
        structure_size = (cur + 0).decode_uint16le()

        key = (self.command, structure_size)

        if self.flags & SMB2_FLAGS_SERVER_TO_REDIR:
            # Distinguish unsoliticed response, error response, normal response
            if self.message_id == UNSOLICITED_MESSAGE_ID:
                if key in Smb2._notification_table:
                    cls = Smb2._notification_table[key]
                else:
                    raise core.BadPacket()
            elif key in Smb2._response_table:
                cls = Smb2._response_table[key]
                if (
                    self.status not in cls.allowed_status
                    and structure_size == ErrorResponse.structure_size
                ):
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

        self._command = cls(self)
        with cur.bounded(cur, end):
            self._command.decode(cur)

        # Advance to next frame or end of data
        cur.advanceto(end)

    def verify(self, digest, key):
        if self.flags & SMB2_FLAGS_SIGNED:
            message = self.start[: self.end]
            # Zero out signature in message
            message[12 * 4 : 12 * 4 + 16] = array.array("B", [0] * 16)
            # Calculate signature
            signature = digest(key, message)[:16]
            # Check that signatures match
            if signature != self.signature:
                raise core.BadPacket()


class Command(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        parent._command = self

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
    allowed_status = [ntstatus.STATUS_SUCCESS]


@Smb2.notification
class Notification(Command):
    pass


class ErrorResponse(Command):
    structure_size = 9

    _context_table = {}
    error_context = core.Register(_context_table, "error_id", "parent_status")
    special_statuses = [
        ntstatus.STATUS_STOPPED_ON_SYMLINK,
        ntstatus.STATUS_BUFFER_TOO_SMALL,
    ]

    def __init__(self, parent):
        super(ErrorResponse, self).__init__(parent)
        parent._command = self
        self.byte_count = None
        self.error_context_count = 0
        self.error_data = None
        self._error_contexts = []

    def _log_str(self):
        components = [type(self).__name__]
        if self.parent:
            if self.parent.command:
                components.append(str(self.parent.command))
        return " ".join(components)

    def _children(self):
        return self._error_contexts

    def append(self, e):
        self._error_contexts.append(e)

    def _decode(self, cur):
        self.error_context_count = cur.decode_uint8le()
        # Ignore Reserved
        cur.decode_uint8le()
        self.byte_count = cur.decode_uint32le()
        end = cur + self.byte_count

        # SMB 3.1.1+ Error context handling
        if self.error_context_count > 0:
            for ix in range(self.error_context_count):
                cur.align(self.parent.start, 8)
                data_length = cur.decode_uint32le()
                error_id = cur.decode_uint32le()
                parent_status = self.parent.status
                if parent_status not in self.special_statuses:
                    parent_status = None
                key = (error_id, parent_status)
                ctx = self._context_table[key]
                with cur.bounded(cur, end):
                    ctx(self, data_length).decode(cur)
        elif self.byte_count > 0:
            # compatability shim for older dialects
            error_id = 0
            parent_status = self.parent.status
            if parent_status not in self.special_statuses:
                parent_status = None
            key = (error_id, parent_status)
            ctx = self._context_table[key]
            with cur.bounded(cur, end):
                self.error_data = ctx(self, self.byte_count)
                self.error_data.decode(cur)


class ErrorId(core.ValueEnum):
    SMB2_ERROR_ID_DEFAULT = 0x0


ErrorId.import_items(globals())


@ErrorResponse.error_context
class ErrorResponseContext(core.Frame):
    def __init__(self, parent, data_length):
        core.Frame.__init__(self, parent)
        self.data_length = data_length
        self.error_data = None
        if parent is not None:
            parent.append(self)


class ErrorResponseDefault(ErrorResponseContext):
    error_id = SMB2_ERROR_ID_DEFAULT
    parent_status = None

    def _decode(self, cur):
        self.error_data = cur.decode_bytes(self.data_length)


class ErrorResponseDefaultBufferSize(ErrorResponseContext):
    error_id = SMB2_ERROR_ID_DEFAULT
    parent_status = ntstatus.STATUS_BUFFER_TOO_SMALL

    def _decode(self, cur):
        self.error_data = cur.decode_uint32le()
        self.minimum_buffer_length = self.error_data


class SymbolicLinkErrorResponse(ErrorResponseContext):
    error_id = SMB2_ERROR_ID_DEFAULT
    parent_status = ntstatus.STATUS_STOPPED_ON_SYMLINK

    def _decode(self, cur):
        end = cur + self.data_length
        self.sym_link_length = cur.decode_uint32le()
        self.sym_link_error_tag = cur.decode_uint32le()
        self.reparse_tag = cur.decode_uint32le()
        if self.sym_link_error_tag != 0x4C4D5953:
            raise core.BadPacket()
        reparse_data = GetReparsePointResponse._reparse_tag_map[self.reparse_tag]
        with cur.bounded(cur, end):
            self.error_data = reparse_data(self)
            self.error_data.decode(cur)


class Cancel(Request):
    command_id = SMB2_CANCEL
    structure_size = 4

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(0)


# Negotiate constants
class SecurityMode(core.FlagEnum):
    SMB2_NEGOTIATE_NONE = 0x0000
    SMB2_NEGOTIATE_SIGNING_ENABLED = 0x0001
    SMB2_NEGOTIATE_SIGNING_REQUIRED = 0x0002


SecurityMode.import_items(globals())


class GlobalCaps(core.FlagEnum):
    SMB2_GLOBAL_CAP_DFS = 0x00000001
    SMB2_GLOBAL_CAP_LEASING = 0x00000002
    SMB2_GLOBAL_CAP_LARGE_MTU = 0x00000004
    SMB2_GLOBAL_CAP_MULTI_CHANNEL = 0x00000008
    SMB2_GLOBAL_CAP_PERSISTENT_HANDLES = 0x00000010
    SMB2_GLOBAL_CAP_DIRECTORY_LEASING = 0x00000020
    SMB2_GLOBAL_CAP_ENCRYPTION = 0x00000040


GlobalCaps.import_items(globals())


class NegotiateContextType(core.ValueEnum):
    SMB2_PREAUTH_INTEGRITY_CAPABILITIES = 0x0001
    SMB2_ENCRYPTION_CAPABILITIES = 0x0002


NegotiateContextType.import_items(globals())


class HashAlgorithms(core.ValueEnum):
    SMB2_SHA_512 = 0x0001


HashAlgorithms.import_items(globals())


class NegotiateRequest(Request):
    command_id = SMB2_NEGOTIATE
    structure_size = 36

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.security_mode = 0
        self.capabilities = 0
        self.client_guid = [0] * 16
        self.dialects = []
        self.negotiate_contexts_count = None
        self.negotiate_contexts_offset = None
        self.negotiate_contexts_alignment_skew = 0
        self.negotiate_contexts = []

    def _children(self):
        return self.negotiate_contexts

    def _has_negotiate_contexts(self):
        return (
            self.negotiate_contexts
            or self.negotiate_contexts_offset is not None
            or self.negotiate_contexts_count is not None
        )

    def _encode(self, cur):
        cur.encode_uint16le(len(self.dialects))
        cur.encode_uint16le(self.security_mode)
        cur.encode_uint16le(0)
        cur.encode_uint32le(self.capabilities)
        cur.encode_bytes(self.client_guid)
        if self._has_negotiate_contexts():
            negotiate_contexts_offset_hole = cur.hole.encode_uint32le(0)
            if self.negotiate_contexts_count is None:
                self.negotiate_contexts_count = len(self.negotiate_contexts)
            cur.encode_uint16le(self.negotiate_contexts_count)
            cur.encode_uint16le(0)  # reserved
        else:
            cur.encode_uint64le(0)
        for dialect in self.dialects:
            cur.encode_uint16le(dialect)

        if self._has_negotiate_contexts():
            cur.align(self.parent.start, 8)
            cur.seekto(cur + self.negotiate_contexts_alignment_skew)
            if self.negotiate_contexts_offset is not None:
                negotiate_contexts_offset_hole(self.negotiate_contexts_offset)
            else:
                negotiate_contexts_offset_hole(cur - self.parent.start)

            for ctx in self.negotiate_contexts:
                cur.align(self.parent.start, 8)
                cur.encode_uint16le(ctx.context_type)
                data_length_hole = cur.hole.encode_uint16le(0)
                cur.encode_uint32le(0)  # reserved
                data_start = cur.copy()
                ctx.encode(cur)
                if ctx.data_length is None:
                    ctx.data_length = cur - data_start
                data_length_hole(ctx.data_length)

    def append(self, e):
        self.negotiate_contexts.append(e)


class NegotiateResponse(Response):
    command_id = SMB2_NEGOTIATE
    structure_size = 65

    _context_table = {}
    negotiate_context = core.Register(_context_table, "context_type")

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.security_mode = 0
        self.dialect_revision = 0
        self.server_guid = [0] * 16
        self.capabilities = 0
        self.max_transact_size = 0
        self.max_read_size = 0
        self.max_write_size = 0
        self.system_time = 0
        self.server_start_time = 0
        self.security_buffer = None
        self.negotiate_contexts_count = None
        self.negotiate_contexts_offset = None
        self.negotiate_contexts = []

    def _log_str(self):
        components = [
            super(NegotiateResponse, self)._log_str(),
            str(self.dialect_revision),
        ]
        if self.capabilities:
            components.append("({})".format(self.capabilities))
        return " ".join(components)

    def _children(self):
        return self.negotiate_contexts

    def _decode(self, cur):
        self.security_mode = SecurityMode(cur.decode_uint16le())
        self.dialect_revision = Dialect(cur.decode_uint16le())
        self.negotiate_contexts_count = cur.decode_uint16le()
        self.server_guid = cur.decode_bytes(16)
        self.capabilities = GlobalCaps(cur.decode_uint32le())
        self.max_transact_size = cur.decode_uint32le()
        self.max_read_size = cur.decode_uint32le()
        self.max_write_size = cur.decode_uint32le()
        self.system_time = nttime.NtTime(cur.decode_uint64le())
        self.server_start_time = nttime.NtTime(cur.decode_uint64le())

        offset = cur.decode_uint16le()
        length = cur.decode_uint16le()

        self.negotiate_contexts_offset = cur.decode_uint32le()

        # Advance to security buffer
        cur.advanceto(self.parent.start + offset)
        self.security_buffer = cur.decode_bytes(length)
        if self.negotiate_contexts_count > 0:
            cur.seekto(self.parent.start + self.negotiate_contexts_offset)
            for ix in range(self.negotiate_contexts_count):
                cur.align(self.parent.start, 8)
                context_type = cur.decode_uint16le()
                data_length = cur.decode_uint16le()
                cur.decode_uint32le()  # reserved
                ctx = self._context_table[context_type]
                ctx(self).decode(cur)

    def append(self, e):
        self.negotiate_contexts.append(e)


class NegotiateRequestContext(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.append(self)
        self.data_length = None


@NegotiateResponse.negotiate_context
class NegotiateResponseContext(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.append(self)


class PreauthIntegrityCapabilities(core.Frame):
    context_type = SMB2_PREAUTH_INTEGRITY_CAPABILITIES

    def __init__(self):
        self.hash_algorithms = []
        self.hash_algorithms_count = None
        self.salt = b""
        self.salt_length = None

    def _encode(self, cur):
        if self.hash_algorithms_count is None:
            self.hash_algorithms_count = len(self.hash_algorithms)
        cur.encode_uint16le(self.hash_algorithms_count)
        if self.salt_length is None:
            self.salt_length = len(self.salt)
        cur.encode_uint16le(self.salt_length)
        for h in self.hash_algorithms:
            cur.encode_uint16le(h)
        cur.encode_bytes(self.salt)

    def _decode(self, cur):
        self.hash_algorithm_count = cur.decode_uint16le()
        self.salt_length = cur.decode_uint16le()
        for ix in range(self.hash_algorithm_count):
            self.hash_algorithms.append(HashAlgorithms(cur.decode_uint16le()))
        self.salt = cur.decode_bytes(self.salt_length)


class PreauthIntegrityCapabilitiesRequest(
    NegotiateRequestContext, PreauthIntegrityCapabilities
):
    def __init__(self, parent):
        NegotiateRequestContext.__init__(self, parent)
        PreauthIntegrityCapabilities.__init__(self)


class PreauthIntegrityCapabilitiesResponse(
    NegotiateResponseContext, PreauthIntegrityCapabilities
):
    def __init__(self, parent):
        NegotiateResponseContext.__init__(self, parent)
        PreauthIntegrityCapabilities.__init__(self)


# Session setup constants
class SessionFlags(core.FlagEnum):
    SMB2_SESSION_FLAG_NONE = 0x00
    SMB2_SESSION_FLAG_BINDING = 0x01
    SMB2_SESSION_FLAG_IS_NULL = 0x02
    SMB2_SESSION_FLAG_ENCRYPT_DATA = 0x04


SessionFlags.import_items(globals())


# SMB2_ECHO_REQUEST definition
class EchoRequest(Request):
    command_id = SMB2_ECHO
    structure_size = 4

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.reserved = 0

    def _encode(self, cur):
        # Reserved
        cur.encode_uint16le(self.reserved)


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


# SMB2_FLUSH_REQUEST definition
class FlushRequest(Request):
    command_id = SMB2_FLUSH
    structure_size = 24

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.reserved1 = 0
        self.reserved2 = 0
        self.file_id = None

    def _encode(self, cur):
        # Reserved1
        cur.encode_uint16le(self.reserved1)
        # Reserved2
        cur.encode_uint32le(self.reserved2)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])


# SMB2_FLUSH_RESPONSE definition
class FlushResponse(Response):
    # Expect response whenever SMB2_FLUSH_REQUEST sent
    command_id = SMB2_FLUSH
    structure_size = 4

    def __init__(self, parent):
        Response.__init__(self, parent)

    def _decode(self, cur):
        self.reserved = cur.decode_uint16le()


class SessionSetupRequest(Request):
    command_id = SMB2_SESSION_SETUP
    structure_size = 25

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.security_mode = 0
        self.capabilities = 0
        self.channel = 0  # must not be used
        self.previous_session_id = 0
        self.security_buffer = None
        self.security_buffer_offset = None
        self.security_buffer_length = None

    def _encode(self, cur):
        cur.encode_uint8le(self.flags)
        cur.encode_uint8le(self.security_mode)
        cur.encode_uint32le(self.capabilities)
        cur.encode_uint32le(self.channel)
        # Encode 0 for security buffer offset for now
        sec_buf_ofs = cur.hole.encode_uint16le(0)
        if self.security_buffer_length is None:
            self.security_buffer_length = len(self.security_buffer)
        cur.encode_uint16le(self.security_buffer_length)
        cur.encode_uint64le(self.previous_session_id)
        # Go back and set security buffer offset
        if self.security_buffer_offset is None:
            self.security_buffer_offset = cur - self.parent.start
        sec_buf_ofs(self.security_buffer_offset)
        cur.encode_bytes(self.security_buffer)


class SessionSetupResponse(Response):
    command_id = SMB2_SESSION_SETUP
    allowed_status = [ntstatus.STATUS_SUCCESS, ntstatus.STATUS_MORE_PROCESSING_REQUIRED]
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
        self.flags = 0
        self.path_offset = None
        self.path_length = None
        self.path = None

    def _log_str(self):
        components = [
            super(TreeConnectRequest, self)._log_str(),
            str(self.path),
        ]
        if self.flags:
            components.append("({})".format(self.flags))
        return " ".join(components)

    def _encode(self, cur):
        # Reserved/Flags (SMB 3.1.1)
        cur.encode_uint16le(self.flags)
        # Path Offset
        path_offset_hole = cur.hole.encode_uint16le(0)
        # Path Length
        path_lenght_hole = cur.hole.encode_uint16le(0)

        if self.path_offset is None:
            self.path_offset = cur - self.parent.start
        path_offset_hole(self.path_offset)

        path_start = cur.copy()
        # Path
        cur.encode_utf16le(self.path)

        if self.path_length is None:
            self.path_length = cur - path_start
        path_lenght_hole(self.path_length)


class TreeConnectResponse(Response):
    command_id = SMB2_TREE_CONNECT
    structure_size = 16

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.share_type = 0
        self.share_flags = 0
        self.capabilities = 0
        self.maximal_access = 0

    def _log_str(self):
        components = [
            super(TreeConnectResponse, self)._log_str(),
        ]
        if self.share_flags:
            components.append(str(self.share_flags))
        if self.capabilities:
            components.append(str(self.capabilities))
        return " ".join(components)

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
    SMB2_OPLOCK_LEVEL_NONE = 0x00
    SMB2_OPLOCK_LEVEL_II = 0x01
    SMB2_OPLOCK_LEVEL_EXCLUSIVE = 0x08
    SMB2_OPLOCK_LEVEL_BATCH = 0x09
    SMB2_OPLOCK_LEVEL_LEASE = 0xFF


OplockLevel.import_items(globals())


# Share access
class ShareAccess(core.FlagEnum):
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004


ShareAccess.import_items(globals())

FILE_SHARE_ALL = FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE


# Create dispositions
class CreateDisposition(core.ValueEnum):
    FILE_SUPERSEDE = 0x00000000
    FILE_OPEN = 0x00000001
    FILE_CREATE = 0x00000002
    FILE_OPEN_IF = 0x00000003
    FILE_OVERWRITE = 0x00000004
    FILE_OVERWRITE_IF = 0x00000005


CreateDisposition.import_items(globals())


# Create options
class CreateOptions(core.FlagEnum):
    FILE_DIRECTORY_FILE = 0x00000001
    FILE_WRITE_THROUGH = 0x00000002
    FILE_SEQUENTIAL_ONLY = 0x00000004
    FILE_NO_INTERMEDIATE_BUFFERING = 0x00000008
    FILE_SYNCHRONOUS_IO_ALERT = 0x00000010
    FILE_SYNCRHONOUS_IO_NONALERT = 0x00000020
    FILE_NON_DIRECTORY_FILE = 0x00000040
    FILE_COMPLETE_IF_OPLOCKED = 0x00000100
    FILE_NO_EA_KNOWLEDGE = 0x00000200
    FILE_RANDOM_ACCESS = 0x00000800
    FILE_DELETE_ON_CLOSE = 0x00001000
    FILE_OPEN_BY_FILE_ID = 0x00002000
    FILE_OPEN_FOR_BACKUP_INTENT = 0x00004000
    FILE_NO_COMPRESSION = 0x00008000
    FILE_RESERVE_OPFILTER = 0x00100000
    FILE_OPEN_REPARSE_POINT = 0x00200000
    FILE_OPEN_NO_RECALL = 0x00400000
    FILE_OPEN_FOR_FREE_SPACE_QUERY = 0x00800000


CreateOptions.import_items(globals())


# Access masks
class Access(core.FlagEnum):
    FILE_READ_DATA = 0x00000001
    FILE_WRITE_DATA = 0x00000002
    FILE_APPEND_DATA = 0x00000004
    FILE_READ_EA = 0x00000008
    FILE_WRITE_EA = 0x00000010
    FILE_EXECUTE = 0x00000020
    FILE_READ_ATTRIBUTES = 0x00000080
    FILE_WRITE_ATTRIBUTES = 0x00000100
    DELETE = 0x00010000
    READ_CONTROL = 0x00020000
    WRITE_DAC = 0x00040000
    WRITE_OWNER = 0x00080000
    SYNCHRONIZE = 0x00100000
    ACCESS_SYSTEM_SECURITY = 0x01000000
    MAXIMUM_ALLOWED = 0x02000000
    GENERIC_ALL = 0x10000000
    GENERIC_EXECUTE = 0x20000000
    GENERIC_WRITE = 0x40000000
    GENERIC_READ = 0x80000000
    FILE_LIST_DIRECTORY = 0x00000001
    FILE_ADD_FILE = 0x00000002
    FILE_ADD_SUBDIRECTORY = 0x00000004
    FILE_TRAVERSE = 0x00000020
    FILE_DELETE_CHILD = 0x00000040


Access.import_items(globals())


# File attributes
class FileAttributes(core.FlagEnum):
    FILE_ATTRIBUTE_READONLY = 0x00000001
    FILE_ATTRIBUTE_HIDDEN = 0x00000002
    FILE_ATTRIBUTE_SYSTEM = 0x00000004
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_ARCHIVE = 0x00000020
    FILE_ATTRIBUTE_DEVICE = 0x00000040
    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_ATTRIBUTE_TEMPORARY = 0x00000100
    FILE_ATTRIBUTE_SPARSE_FILE = 0x00000200
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_ATTRIBUTE_COMPRESSED = 0x00000800
    FILE_ATTRIBUTE_OFFLINE = 0x00001000
    FILE_ATTRIBUTE_NOT_CONTENT_INDEXED = 0x00002000
    FILE_ATTRIBUTE_ENCRYPTED = 0x00004000


FileAttributes.import_items(globals())


class CreateRequest(Request):
    command_id = SMB2_CREATE
    structure_size = 57

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.security_flags = 0
        self.requested_oplock_level = SMB2_OPLOCK_LEVEL_NONE
        self.impersonation_level = 0
        self.smb_create_flags = 0
        self.reserved = 0
        self.desired_access = 0
        self.file_attributes = 0
        self.share_access = 0
        self.create_disposition = 0
        self.create_options = 0
        self.name = None
        self.name_offset = None
        self.name_length = None
        self.create_contexts_offset = 0
        self.create_contexts_length = 0
        self._create_contexts = []

    def _log_str(self):
        return " ".join([super(CreateRequest, self)._log_str(), self.name,])

    def _children(self):
        return self._create_contexts

    def _encode(self, cur):
        # SecurityFlags, must be 0
        cur.encode_uint8le(self.security_flags)
        cur.encode_uint8le(self.requested_oplock_level)
        cur.encode_uint32le(self.impersonation_level)
        # SmbCreateFlags, must be 0
        cur.encode_uint64le(self.smb_create_flags)
        # Reserved
        cur.encode_uint64le(self.reserved)
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

        if self.name_offset is None:
            self.name_offset = cur - self.parent.start
        name_offset_hole(self.name_offset)

        name_start = cur.copy()
        cur.encode_utf16le(self.name)

        if self.name_length is None:
            self.name_length = cur - name_start
        name_length_hole(self.name_length)

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
    create_context = core.Register(_context_table, "name")

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
        self.reserved2 = 0
        self.file_id = (0, 0)
        self.create_contexts_offset = 0
        self.create_contexts_length = 0
        self._create_contexts = []

    def _log_str(self):
        return " ".join(
            [
                super(CreateResponse, self)._log_str(),
                "(0x{:x}, 0x{:x})".format(*self.file_id),
            ]
        )

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
        self.reserved2 = cur.decode_uint32le()
        self.file_id = (cur.decode_uint64le(), cur.decode_uint64le())
        self.create_contexts_offset = cur.decode_uint32le()
        self.create_contexts_length = cur.decode_uint32le()

        if self.create_contexts_length > 0:
            create_contexts_start = self.parent.start + self.create_contexts_offset
            create_contexts_end = create_contexts_start + self.create_contexts_length
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

                    name = (con_start + name_offset).decode_bytes(name_length).tobytes()

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
    name = b"MxAc"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.timestamp = None

    def _encode(self, cur):
        if self.timestamp is not None:
            cur.encode_uint64le(self.timestamp)


class MaximalAccessResponse(CreateResponseContext):
    name = b"MxAc"

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.query_status = 0
        self.maximal_access = 0

    def _decode(self, cur):
        self.query_status = ntstatus.Status(cur.decode_uint32le())
        self.maximal_access = Access(cur.decode_uint32le())


class AllocationSizeRequest(CreateRequestContext):
    name = b"AlSi"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.allocation_size = 0

    def _encode(self, cur):
        cur.encode_uint64le(self.allocation_size)


class ExtendedAttributeRequest(CreateRequestContext):
    name = b"ExtA"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.next_entry_offset = 0
        self.flags = 0x00000000
        self.ea_name_length = 0
        self.ea_value_length = 0
        self.ea_name = None
        self.ea_value = None

    def _encode(self, cur):
        cur.encode_uint32le(self.next_entry_offset)
        cur.encode_uint8le(self.flags)
        if self.ea_name is not None:
            self.ea_name = array.array("B", self.ea_name)
            self.ea_name.append(00)
            self.ea_value = array.array("B", self.ea_value)
            cur.encode_uint8le(self.ea_name_length)
            cur.encode_uint16le(self.ea_value_length)
            cur.encode_bytes(self.ea_name)
            cur.encode_bytes(self.ea_value)


class LeaseState(core.FlagEnum):
    SMB2_LEASE_NONE = 0x00
    SMB2_LEASE_READ_CACHING = 0x01
    SMB2_LEASE_HANDLE_CACHING = 0x02
    SMB2_LEASE_WRITE_CACHING = 0x04


LeaseState.import_items(globals())

SMB2_LEASE_R = SMB2_LEASE_READ_CACHING
SMB2_LEASE_RH = SMB2_LEASE_R | SMB2_LEASE_HANDLE_CACHING
SMB2_LEASE_RW = SMB2_LEASE_R | SMB2_LEASE_WRITE_CACHING
SMB2_LEASE_RWH = SMB2_LEASE_RH | SMB2_LEASE_RW


class LeaseFlags(core.FlagEnum):
    SMB2_LEASE_FLAG_NONE = 0x00
    SMB2_LEASE_FLAG_BREAK_IN_PROGRESS = 0x02


LeaseFlags.import_items(globals())


class SecDescControl(core.FlagEnum):
    SR = 0x0001
    RM = 0x0002
    PS = 0x0004
    PD = 0x0008
    SI = 0x0010
    DI = 0x0020
    SC = 0x0040
    DC = 0x0080
    SS = 0x0100
    DT = 0x0200
    SD = 0x0400
    SP = 0x0800
    DD = 0x1000
    DP = 0x2000
    GD = 0x4000
    OD = 0x8000


class AceType(core.ValueEnum):
    ACCESS_ALLOWED_ACE_TYPE = 0x00
    ACCESS_DENIED_ACE_TYPE = 0x01
    SYSTEM_AUDIT_ACE_TYPE = 0x02
    SYSTEM_ALARM_ACE_TYPE = 0x03
    ACCESS_ALLOWED_COMPOUND_ACE_TYPE = 0x04
    ACCESS_ALLOWED_OBJECT_ACE_TYPE = 0x05
    ACCESS_DENIED_OBJECT_ACE_TYPE = 0x06
    SYSTEM_AUDIT_OBJECT_ACE_TYPE = 0x07
    SYSTEM_ALARM_OBJECT_ACE_TYPE = 0x08
    ACCESS_ALLOWED_CALLBACK_ACE_TYPE = 0x09
    ACCESS_DENIED_CALLBACK_ACE_TYPE = 0x0A
    ACCESS_ALLOWED_CALLBACK_OBJECT_ACE_TYPE = 0x0B
    ACCESS_DENIED_CALLBACK_OBJECT_ACE_TYPE = 0x0C
    SYSTEM_AUDIT_CALLBACK_ACE_TYPE = 0x0D
    SYSTEM_ALARM_CALLBACK_ACE_TYPE = 0x0E
    SYSTEM_AUDIT_CALLBACK_OBJECT_ACE_TYPE = 0x0F
    SYSTEM_ALARM_CALLBACK_OBJECT_ACE_TYPE = 0x10
    SYSTEM_MANDATORY_LABEL_ACE_TYPE = 0x11
    SYSTEM_RESOURCE_ATTRIBUTE_ACE_TYPE = 0x12
    SYSTEM_SCOPED_POLICY_ID_ACE_TYPE = 0x13


AceType.import_items(globals())


class AceFlags(core.FlagEnum):
    OBJECT_INHERIT_ACE = 0x01
    CONTAINER_INHERIT_ACE = 0x02
    NO_PROPAGATE_INHERIT_ACE = 0x04
    INHERIT_ONLY_ACE = 0x08
    INHERITED_ACE = 0x10
    SUCCESSFUL_ACCESS_ACE_FLAG = 0x40
    FAILED_ACCESS_ACE_FLAG = 0x80


AceFlags.import_items(globals())


class AclRevision(core.ValueEnum):
    ACL_REVISION = 0x02
    ACL_REVISION_DS = 0x04


AclRevision.import_items(globals())


class SecurityDescriptorRequest(CreateRequestContext):
    name = b"SecD"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.revision = 1
        self.sbz1 = 0
        self.control = None
        self.owner_sid = None
        self.group_sid = None
        self.sacl = None
        self.dacl = None
        self.sacl_aces = None
        self.dacl_aces = None

    def _encode(self, cur):
        (
            self.offset_owner,
            self.offset_group,
            self.offset_sacl,
            self.offset_dacl,
        ) = self._get_offset(
            owner_sid=self.owner_sid,
            group_sid=self.group_sid,
            sacl=self.sacl_aces,
            dacl=self.dacl_aces,
        )
        cur.encode_uint8le(self.revision)
        cur.encode_uint8le(self.sbz1)
        cur.encode_uint16le(self.control)
        cur.encode_uint32le(self.offset_owner)
        cur.encode_uint32le(self.offset_group)
        cur.encode_uint32le(self.offset_sacl)
        cur.encode_uint32le(self.offset_dacl)

        if self.offset_owner != 0:
            id_auth, sub_auth = self._get_sid(self.owner_sid)
            self._encode_sid(cur, id_auth, sub_auth)

        if self.offset_group != 0:
            id_auth, sub_auth = self._get_sid(self.group_sid)
            self._encode_sid(cur, id_auth, sub_auth)

        if self.offset_sacl != 0:
            # Acl Revision
            cur.encode_uint8le(self.sacl)
            # sbz1
            cur.encode_uint8le(0)
            # Acl Size
            sid_size, ace_size, acl_size = self._get_size(acl=self.sacl_aces)
            cur.encode_uint16le(acl_size)
            # Ace Count
            cur.encode_uint16le(len(self.sacl_aces))
            # sbz2
            cur.encode_uint16le(0)
            for ace in self.sacl_aces:
                # Ace Type
                cur.encode_uint8le(ace[0])
                # Ace flags
                cur.encode_uint8le(ace[1])
                # Ace Size
                sid_size, ace_size, acl_size = self._get_size(ace_val=ace)
                cur.encode_uint16le(ace_size)
                # Ace Mask
                cur.encode_uint32le(ace[2])
                id_auth, sub_auth = self._get_sid(ace[3])
                self._encode_sid(cur, id_auth, sub_auth)
        if self.offset_dacl != 0:
            # Acl Revision
            cur.encode_uint8le(self.dacl)
            # sbz1
            cur.encode_uint8le(0)
            # Acl Size
            sid_size, ace_size, acl_size = self._get_size(acl=self.dacl_aces)
            cur.encode_uint16le(acl_size)
            # Ace Count
            cur.encode_uint16le(len(self.dacl_aces))
            # sbz2
            cur.encode_uint16le(0)
            for ace in self.dacl_aces:
                # Ace Type
                cur.encode_uint8le(ace[0])
                # Ace flags
                cur.encode_uint8le(ace[1])
                # Ace Size
                sid_size, ace_size, acl_size = self._get_size(ace_val=ace)
                cur.encode_uint16le(ace_size)
                # Ace Mask
                cur.encode_uint32le(ace[2])
                id_auth, sub_auth = self._get_sid(ace[3])
                self._encode_sid(cur, id_auth, sub_auth)

    def _encode_sid(self, cur, id_auth, sub_auth):
        sub_auth = [int(i) for i in sub_auth]
        # Revision
        cur.encode_uint8le(0x01)
        # Sub Authrty Count
        cur.encode_uint8le(len(sub_auth))
        # Identifier Authority
        tmp_id_auth = array.array("B", [0x00, 0x00, 0x00, 0x00, 0x00])
        tmp_id_auth.append(int(id_auth))
        for tmp in tmp_id_auth:
            cur.encode_uint8le(tmp)
        # Sub Authority
        for tmp_sub_auth in sub_auth:
            cur.encode_uint32le(tmp_sub_auth)

    def _get_sid(self, sid):
        pat = r"S-1-(\d)-(.*)"
        match = re.search(pat, sid)
        id_auth = match.group(1)
        sub_auth = (match.group(2)).split("-")
        return id_auth, sub_auth

    def _get_size(self, sid=None, ace_val=None, acl=None):
        sid_size = 0
        ace_size = 0
        acl_size = 0
        # All Sizes are in Bytes
        sbz1 = 1
        sbz2 = 2
        revision_size = 1
        ace_type_size = 1
        ace_flags_size = 1
        ace_size_param = 2
        ace_mask_size = 4
        acl_revision_size = 1
        acl_size_param = 2
        ace_count_size = 2
        sub_auth_count_size = 1
        identifier_auth_size = 6
        sub_auth_size = 0
        if sid != None:
            id_auth, sub_auth = self._get_sid(sid)
            sub_auth_size += len(sub_auth) * 4
            sid_size = (
                revision_size
                + sub_auth_count_size
                + identifier_auth_size
                + sub_auth_size
            )
        elif ace_val != None:
            sub_auth_size = 0
            id_auth, sub_auth = self._get_sid(ace_val[3])
            sub_auth_size += len(sub_auth) * 4
            sid_size = (
                revision_size
                + sub_auth_count_size
                + identifier_auth_size
                + sub_auth_size
            )
            ace_size = (
                ace_type_size
                + ace_flags_size
                + ace_size_param
                + ace_mask_size
                + sid_size
            )
        elif acl != None:
            tmp_acl_size = 0
            for aces in acl:
                sub_auth_size = 0
                id_auth, sub_auth = self._get_sid(aces[3])
                sub_auth_size += len(sub_auth) * 4
                sid_size = (
                    revision_size
                    + sub_auth_count_size
                    + identifier_auth_size
                    + sub_auth_size
                )
                ace_size = (
                    ace_type_size
                    + ace_flags_size
                    + ace_size_param
                    + ace_mask_size
                    + sid_size
                )
                tmp_acl_size += ace_size
                acl_size = (
                    acl_revision_size
                    + sbz1
                    + acl_size_param
                    + ace_count_size
                    + sbz2
                    + tmp_acl_size
                )
        return sid_size, ace_size, acl_size

    def _get_offset(self, owner_sid=None, group_sid=None, sacl=None, dacl=None):
        default_offset = 20
        owner_sid_size = self._get_size(sid=owner_sid)
        off_owner = 0 if owner_sid_size[0] == 0 else default_offset
        group_sid_size = self._get_size(sid=group_sid)
        off_group = 0 if group_sid_size[0] == 0 else default_offset + owner_sid_size[0]
        sacl_size = self._get_size(acl=sacl)
        off_sacl = (
            0
            if sacl_size[2] == 0
            else default_offset + owner_sid_size[0] + group_sid_size[0]
        )
        dacl_size = self._get_size(acl=dacl)
        off_dacl = (
            0
            if dacl_size[2] == 0
            else default_offset + owner_sid_size[0] + group_sid_size[0] + sacl_size[2]
        )
        return off_owner, off_group, off_sacl, off_dacl


class NT_ACL(core.Frame):
    def __init__(self):
        super(NT_ACL, self).__init__(parent=None)
        self._entries = []
        self.acl_revision = 0
        self.sbz1 = 0
        self.acl_size = -1
        self.ace_count = -1
        self.sbz2 = 0
        self.raw_data = ""

    def _children(self):
        return self._entries

    def append(self, e):
        self._entries.append(e)

    def clone(self):
        """
        return a copy of this NT_ACL with calculated fields reset
        """
        acl = NT_ACL()
        acl.acl_revision = self.acl_revision
        if self.raw_data:
            acl.raw_data = array.array("B", self.raw_data)
        for ace in self:
            ace.clone(new_parent=acl)
        return acl

    def _decode(self, cur):
        """
        decode the ACL
        """
        self.acl_revision = AclRevision(cur.decode_uint8le())
        self.sbz1 = cur.decode_uint8le()
        self.acl_size = cur.decode_uint16le()
        self.ace_count = cur.decode_uint16le()
        self.sbz2 = cur.decode_uint16le()
        for i in range(self.ace_count):
            NT_ACE(self).decode(cur)
        acl_remain = self.start + self.acl_size - cur
        assert acl_remain >= 0
        if acl_remain:
            self.raw_data = cur.decode_bytes(acl_remain)

    def _encode(self, cur):
        """
        encode the acl
        """
        cur.encode_uint8le(self.acl_revision)
        # Reserved
        cur.encode_uint8le(0)
        # hole for acl_size and acl_count
        acl_size_hole = cur.hole.encode_uint16le(0)
        acl_count_hole = cur.hole.encode_uint16le(0)
        # Reserved
        cur.encode_uint16le(0)
        for entry in self._entries:
            entry.encode(cur)
        if len(self.raw_data):
            cur.encode_bytes(self.raw_data)
        if self.acl_size == -1:
            self.acl_size = cur - self.start
        acl_size_hole(self.acl_size)
        if self.ace_count == -1:
            self.ace_count = len(self._entries)
        acl_count_hole(self.ace_count)


class NT_ACE(core.Frame):
    def __init__(self, parent=None, end=None):
        super(NT_ACE, self).__init__(parent)
        if parent is not None:
            parent.append(self)
        self.ace_type = 0
        self.ace_flags = 0
        self.ace_size = -1
        self.access_mask = 0
        self.sid = None
        self.raw_data = ""
        self._entries = []

    def clone(self, new_parent=None):
        """
        return a copy of this NT_ACE with calculated fields reset
        """
        ace = NT_ACE(new_parent)
        ace.ace_type = self.ace_type
        ace.ace_flags = self.ace_flags
        ace.access_mask = self.access_mask
        ace.sid = self.sid.clone()
        if self.raw_data:
            ace.raw_data = array.array("B", self.raw_data)
        return ace

    def _decode(self, cur):
        """
        decode the ACE
        """
        self.ace_type = AceType(cur.decode_uint8le())
        self.ace_flags = AceFlags(cur.decode_uint8le())
        self.ace_size = cur.decode_uint16le()
        self.access_mask = Access(cur.decode_uint32le())
        self.sid = NT_SID()
        self.sid.decode(cur)
        # check if we reach the end
        ace_remain = self.start + self.ace_size - cur
        assert ace_remain >= 0
        if ace_remain:
            self.raw_data = cur.decode_bytes(ace_remain)

    def _encode(self, cur):
        """
        encode the ace
        """
        cur.encode_uint8le(self.ace_type)
        cur.encode_uint8le(self.ace_flags)
        # hole for ace size
        ace_size_hole = cur.hole.encode_uint16le(0)
        cur.encode_uint32le(self.access_mask)
        self.sid.encode(cur)
        if len(self.raw_data):
            cur.encode_bytes(self.raw_data)
        if self.ace_size == -1:
            self.ace_size = cur - self.start
        ace_size_hole(self.ace_size)


class NT_SID(core.Frame):
    def __init__(self):
        super(NT_SID, self).__init__(self, None)
        self.raw_data = ""
        self.revision = 0
        self.sub_authority_count = -1
        self.identifier_authority = 0
        self.sub_authority = []

    def clone(self):
        """
        return a copy of this NT_SID with calculated fields reset
        """
        sid = NT_SID()
        sid.revision = self.revision
        sid.identifier_authority = self.identifier_authority
        sid.sub_authority = self.sub_authority[:]
        if self.raw_data:
            sid.raw_data = array.array("B", self.raw_data)
        return sid

    def _str(self, indent):
        return self.string

    @property
    def string(self):
        sid_str = (
            "S-"
            + (str(self.revision) + "-" + str(self.identifier_authority))
            + "-"
            + "-".join(str(x) for x in self.sub_authority)
        )
        return sid_str

    def _decode(self, cur):
        """
        decode the raw data to the specified end of buffer
        """
        self.revision = cur.decode_uint8le()
        self.sub_authority_count = cur.decode_uint8le()
        id_auth_high = cur.decode_uint16be()
        id_auth_low = cur.decode_uint32be()
        self.identifier_authority = (id_auth_high << 32) + id_auth_low
        for i in range(self.sub_authority_count):
            self.sub_authority.append(cur.decode_uint32le())

    def _encode(self, cur):
        """
        encode the sid
        """
        cur.encode_uint8le(self.revision)
        subauth_count_hole = cur.hole.encode_uint8le(0)
        auth_bytes = "{:06x}".format(self.identifier_authority)
        cur.encode_uint16be((self.identifier_authority >> 32) & 0xFFFFFFFF)
        cur.encode_uint32be(self.identifier_authority & 0xFFFFFFFF)
        for i in range(len(self.sub_authority)):
            cur.encode_uint32le(self.sub_authority[i])
        if self.sub_authority_count == -1:
            self.sub_authority_count = len(self.sub_authority)
        subauth_count_hole(self.sub_authority_count)


class LeaseRequest(CreateRequestContext):
    name = b"RqLs"

    # This class handles V2 requests as well.  Set
    # the lease_flags field to a non-None value
    # to enable the extended fields
    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.lease_key = array.array("B", [0] * 16)
        self.lease_state = 0
        # V2 fields
        self.lease_flags = None
        self.parent_lease_key = None
        self.epoch = None

    def _encode(self, cur):
        cur.encode_bytes(self.lease_key)
        cur.encode_uint32le(self.lease_state)
        if self.lease_flags is not None:
            # V2 variant
            cur.encode_uint32le(self.lease_flags)
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
    name = b"RqLs"
    v1_size = 32
    v2_size = 52
    # This class handles V2 responses as well.
    # The extended fields will be set to None
    # if the response was not V2

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.lease_key = array.array("B", [0] * 16)
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
    name = b"DHnQ"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)

    def _encode(self, cur):
        # Reserved
        cur.encode_uint64le(0)
        cur.encode_uint64le(0)


class DurableHandleResponse(CreateResponseContext):
    name = b"DHnQ"

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)

    def _decode(self, cur):
        # Ignore reserved
        cur.decode_uint64le()


class DurableHandleReconnectRequest(CreateRequestContext):
    name = b"DHnC"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.file_id = None

    def _encode(self, cur):
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])


class DurableHandleV2Request(CreateRequestContext):
    name = b"DH2Q"

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
    name = b"DH2Q"

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.timeout = 0
        self.flags = 0

    def _decode(self, cur):
        self.timeout = cur.decode_uint32le()
        self.flags = DurableFlags(cur.decode_uint32le())


class DurableHandleReconnectV2Request(CreateRequestContext):
    name = b"DH2C"

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
    name = b"\x45\xBC\xA6\x6A\xEF\xA7\xF7\x4A\x90\x08\xFA\x46\x2E\x14\x4D\x74"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)
        self.structure_size = 20
        self.app_instance_id = array.array("B", [0] * 16)

    def _encode(self, cur):
        cur.encode_uint16le(self.structure_size)
        # Reserved
        cur.encode_uint16le(0)
        cur.encode_bytes(self.app_instance_id)


class QueryOnDiskIDRequest(CreateRequestContext):
    name = b"QFid"

    def __init__(self, parent):
        CreateRequestContext.__init__(self, parent)

    def _encode(self, cur):
        pass  # client sends no data to server


class QueryOnDiskIDResponse(CreateResponseContext):
    name = b"QFid"

    def __init__(self, parent):
        CreateResponseContext.__init__(self, parent)
        self.file_id = array.array("B", [0] * 32)

    def _decode(self, cur):
        self.file_id = cur.decode_bytes(32)


class TimewarpTokenRequest(CreateRequestContext):
    name = b"TWrp"

    def __init__(self, parent):
        super(TimewarpTokenRequest, self).__init__(parent)
        self.timestamp = 0

    def _encode(self, cur):
        cur.encode_uint64le(self.timestamp)


class CloseRequest(Request):
    command_id = SMB2_CLOSE
    structure_size = 24

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.file_id = None

    def _log_str(self):
        components = [
            super(CloseRequest, self)._log_str(),
            "(0x{:x}, 0x{:x})".format(*self.file_id),
        ]
        if self.flags:
            components.append("({})".format(self.flags))
        return " ".join(components)

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
        self.reserved = cur.decode_uint32le()
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.allocation_size = cur.decode_uint64le()
        self.end_of_file = cur.decode_uint64le()
        self.file_attributes = FileAttributes(cur.decode_uint32le())


class FileInformationClass(core.ValueEnum):
    FILE_SECURITY_INFORMATION = 0
    FILE_DIRECTORY_INFORMATION = 1
    FILE_FULL_DIRECTORY_INFORMATION = 2
    FILE_BASIC_INFORMATION = 4
    FILE_STANDARD_INFORMATION = 5
    FILE_INTERNAL_INFORMATION = 6
    FILE_EA_INFORMATION = 7
    FILE_ACCESS_INFORMATION = 8
    FILE_NAME_INFORMATION = 9
    FILE_RENAME_INFORMATION = 10
    FILE_NAMES_INFORMATION = 12
    FILE_DISPOSITION_INFORMATION = 13
    FILE_POSITION_INFORMATION = 14
    FILE_MODE_INFORMATION = 16
    FILE_ALIGNMENT_INFORMATION = 17
    FILE_ALL_INFORMATION = 18
    FILE_ALLOCATION_INFORMATION = 19
    FILE_END_OF_FILE_INFORMATION = 20
    FILE_STREAM_INFORMATION = 22
    FILE_COMPRESSION_INFORMATION = 28
    FILE_NETWORK_OPEN_INFORMATION = 34
    FILE_ATTRIBUTE_TAG_INFORMATION = 35
    FILE_ID_BOTH_DIR_INFORMATION = 37
    FILE_ID_FULL_DIR_INFORMATION = 38
    FILE_VALID_DATA_LENGTH_INFORMATION = 39


FileInformationClass.import_items(globals())


class FileSystemInformationClass(core.ValueEnum):
    FILE_FS_VOLUME_INFORMATION = 1
    FILE_FS_SIZE_INFORMATION = 3
    FILE_FS_DEVICE_INFORMATION = 4
    FILE_FS_ATTRIBUTE_INFORMATION = 5
    FILE_FS_CONTROL_INFORMATION = 6
    FILE_FS_FULL_SIZE_INFORMATION = 7
    FILE_FS_OBJECTID_INFORMATION = 8
    FILE_FS_SECTOR_SIZE_INFORMATION = 11


FileSystemInformationClass.import_items(globals())


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

    def _log_str(self):
        components = [
            super(QueryDirectoryRequest, self)._log_str(),
        ]
        if self.file_information_class:
            components.append(str(self.file_information_class))
        if self.flags:
            components.append("({})".format(self.flags))
        return " ".join(components)

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
    file_information = core.Register(_file_info_map, "file_information_class")

    def __init__(self, parent):
        Response.__init__(self, parent)
        self._file_information_class = None

        # Try to figure out file information class by looking up
        # associated request in context
        request = None
        context = self.context

        if context:
            request = context.get_request(parent.message_id)

        if request and request.children:
            self._file_information_class = request[0].file_information_class

        self._entries = []

    def _log_str(self):
        components = [
            super(QueryDirectoryResponse, self)._log_str(),
        ]
        if self._file_information_class:
            components.append(str(self._file_information_class))
        return " ".join(components)

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
            Information(self, end).decode(cur)


class InfoType(core.ValueEnum):
    SMB2_0_INFO_FILE = 0x01
    SMB2_0_INFO_FILESYSTEM = 0x02
    SMB2_0_INFO_SECURITY = 0x03
    SMB2_0_INFO_QUOTA = 0x04


InfoType.import_items(globals())


class SecurityInformation(core.FlagEnum):
    OWNER_SECURITY_INFORMATION = 0x00000001
    GROUP_SECURITY_INFORMATION = 0x00000002
    DACL_SECURITY_INFORMATION = 0x00000004
    SACL_SECURITY_INFORMATION = 0x00000008
    ATTRIBUTE_SECURITY_INFORMATION = 0x00000020


SecurityInformation.import_items(globals())


class ScanFlags(core.FlagEnum):
    SL_RESTART_SCAN = 0x00000001
    SL_RETURN_SINGLE_ENTRY = 0x00000002
    SL_INDEX_SPECIFIED = 0x00000004


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

    def _log_str(self):
        components = [
            super(QueryInfoRequest, self)._log_str(),
        ]
        if self.info_type == SMB2_0_INFO_FILE:
            if self.file_information_class:
                components.append(str(self.file_information_class))
        else:
            components.append(str(self.info_type))
        if self.flags:
            components.append("({})".format(self.flags))
        return " ".join(components)

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
    allowed_status = [ntstatus.STATUS_SUCCESS, ntstatus.STATUS_BUFFER_OVERFLOW]
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True

    _info_map = {}
    information = core.Register(_info_map, "info_type", "file_information_class")

    def __init__(self, parent):
        Response.__init__(self, parent)
        self._info_type = None
        self._file_information_class = None

        context = self.context
        if context:
            request = context.get_request(parent.message_id)

        if request and request.children:
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

        key = (self._info_type, self._file_information_class)
        info_cls = self._info_map.get(key)
        if info_cls is not None:
            if info_cls == FileSecurityInformation:
                info_cls(self, end).decode(cur)
            else:
                with cur.bounded(cur, end):
                    while cur < end:
                        info_cls(self).decode(cur)
        else:
            Information(self, end).decode(cur)


class SetInfoRequest(Request):
    command_id = SMB2_SET_INFO
    structure_size = 33
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.info_type = 0
        self.file_information_class = 0
        self.input_buffer_length = 0
        self.input_buffer_offset = 0
        self.additional_information = 0
        self.file_id = None

        self._entries = []

    def _children(self):
        return self._entries

    def append(self, e):
        self._entries.append(e)

    def _encode(self, cur):
        if not self.info_type:
            self.info_type = self[0].info_type

        if not self.file_information_class:
            # Determine it from child object
            self.file_information_class = self[0].file_information_class

        cur.encode_uint8le(self.info_type)
        cur.encode_uint8le(self.file_information_class)

        buffer_length_hole = cur.hole.encode_uint32le(0)
        buffer_offset_hole = cur.hole.encode_uint16le(0)
        cur.encode_uint16le(0)  # Reserved

        cur.encode_uint32le(self.additional_information)
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
        # The response is only the structure size
        pass


class Information(core.Frame):
    """
    Base class for all info frames. Holds the raw data if no specific decoder
    has been registered for the given info type
    """

    info_type = 0
    file_information_class = 0

    def __init__(self, parent=None, end=None):
        super(Information, self).__init__(parent)
        if parent is not None:
            parent.append(self)
        self.end = end
        self.raw_data = ""

    def _decode(self, cur):
        """
        decode the raw data to the specified end of buffer
        """
        if self.end is not None:
            self.raw_data = cur.decode_bytes(self.end - cur)

    def _encode(self, cur):
        """
        encode the raw data
        """
        cur.encode_bytes(self.raw_data)


@QueryDirectoryResponse.file_information
@QueryInfoResponse.information
class FileInformation(Information):
    info_type = SMB2_0_INFO_FILE


@QueryInfoResponse.information
class FileSystemInformation(Information):
    info_type = SMB2_0_INFO_FILESYSTEM


class FileSecurityInformation(FileInformation):
    file_information_class = FILE_SECURITY_INFORMATION
    info_type = SMB2_0_INFO_SECURITY

    def __init__(self, parent=None, end=None):
        FileInformation.__init__(self, parent)
        self.revision = 0
        self.sbz1 = 0
        self.control = 0
        self.offset_owner = -1
        self.offset_group = -1
        self.offset_sacl = -1
        self.offset_dacl = -1
        self.other = ""
        self.end = end
        self.owner_sid = None
        self.group_sid = None
        self.sacl = None
        self.dacl = None

    def _static_clone(o1, o2, copy_fields=None):
        """
        static method implementing both clone and clone_from methods

        o1 is updated based on the values in o2

        copy_fields is a list of field names that will be cloned.
        if copy_fields is None (default), all fields are copied

        header fields 'revision' and 'control' are always cloned
        """
        o1.revision = o2.revision
        o1.control = o2.control
        if copy_fields is None or "other" in copy_fields:
            if o2.other:
                o1.other = array.array("B", o2.other)
        if copy_fields is None or "owner_sid" in copy_fields:
            o1.owner_sid = o2.owner_sid.clone()
        if copy_fields is None or "group_sid" in copy_fields:
            o1.group_sid = o2.group_sid.clone()
        if copy_fields is None or "sacl" in copy_fields:
            o1.sacl = o2.sacl
        if copy_fields is None or "dacl" in copy_fields:
            o1.dacl = o2.dacl.clone()

    def clone_from(self, sec_info, copy_fields=None):
        """
        update the fields in this FileSecurityInformation based on the values
        of sec_info

        copy_fields is a list of field names that will be cloned.
        if copy_fields is None (default), all fields are copied

        header fields 'revision' and 'control' are always cloned

        all calculated fields will be reset and this FileSecurityInformation
        may be subsequently modified and used to set FileSecurityInformation
        """
        FileSecurityInformation._static_clone(self, sec_info, copy_fields)

    def clone(self, new_parent=None, copy_fields=None):
        """
        return a copy of this FileSecurityInfo with calculated fields reset

        copy_fields is a list of field names that will be cloned.
        if copy_fields is None (default), all fields are copied

        header fields 'revision' and 'control' are always cloned
        """
        sec_info = FileSecurityInformation(new_parent)
        FileSecurityInformation._static_clone(sec_info, self, copy_fields)
        return sec_info

    def _decode(self, cur):
        self.revision = cur.decode_uint8le()
        self.sbz1 = cur.decode_uint8le()
        self.control = SecDescControl(cur.decode_uint16le())
        self.offset_owner = cur.decode_uint32le()
        self.offset_group = cur.decode_uint32le()
        self.offset_sacl = cur.decode_uint32le()
        self.offset_dacl = cur.decode_uint32le()
        if self.offset_owner != 0:
            # find next non-zero offset in list
            self.owner_sid = NT_SID()
            self.owner_sid.decode(cur)
        if self.offset_group != 0:
            self.group_sid = NT_SID()
            self.group_sid.decode(cur)
        if self.offset_sacl != 0:
            sacl_len = (
                (self.offset_dacl - self.offset_sacl)
                if self.offset_dacl > 0
                else (self.end - self.start - self.offset_sacl)
            )
            self.sacl = cur.decode_bytes(sacl_len)
        if self.offset_dacl != 0:
            self.dacl = NT_ACL()
            self.dacl.decode(cur)
        if self.end is not None:
            self.other = cur.decode_bytes(self.end - cur)

    def _encode(self, cur):
        cur.encode_uint8le(self.revision)
        cur.encode_uint8le(0)
        cur.encode_uint16le(self.control)
        # Encode 0 for all the offsets for now
        owner_ofs = cur.hole.encode_uint32le(0)
        group_ofs = cur.hole.encode_uint32le(0)
        sacl_ofs = cur.hole.encode_uint32le(0)
        dacl_ofs = cur.hole.encode_uint32le(0)
        if self.owner_sid is not None:
            if self.offset_owner == -1:
                self.offset_owner = cur - self.start
            owner_ofs(self.offset_owner)
            self.owner_sid.encode(cur)
        if self.group_sid is not None:
            if self.offset_group == -1:
                self.offset_group = cur - self.start
            group_ofs(self.offset_group)
            self.group_sid.encode(cur)
        if self.sacl is not None:
            if self.offset_sacl == -1:
                self.offset_sacl = cur - self.start
            sacl_ofs(self.offset_sacl)
            cur.encode_bytes(self.sacl)
        if self.dacl is not None:
            if self.offset_dacl == -1:
                self.offset_dacl = cur - self.start
            dacl_ofs(self.offset_dacl)
            self.dacl.encode(cur)


class FileAccessInformation(FileInformation):
    file_information_class = FILE_ACCESS_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.access_flags = 0

    def _decode(self, cur):
        self.access_flags = Access(cur.decode_uint32le())


# Alignment Requirement flags
class Alignment(core.ValueEnum):
    FILE_BYTE_ALIGNMENT = 0x00000000
    FILE_WORD_ALIGNMENT = 0x00000001
    FILE_LONG_ALIGNMENT = 0x00000003
    FILE_QUAD_ALIGNMENT = 0x00000007
    FILE_OCTA_ALIGNMENT = 0x0000000F
    FILE_32_BYTE_ALIGNMENT = 0x0000001F
    FILE_64_BYTE_ALIGNMENT = 0x0000003F
    FILE_128_BYTE_ALIGNMENT = 0x0000007F
    FILE_256_BYTE_ALIGNMENT = 0x000000FF
    FILE_512_BYTE_ALIGNMENT = 0x000001FF


Alignment.import_items(globals())


class FileAlignmentInformation(FileInformation):
    file_information_class = FILE_ALIGNMENT_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.alignment_requirement = 0

    def _decode(self, cur):
        self.alignment_requirement = Alignment(cur.decode_uint32le())


class FileAllInformation(FileInformation):
    file_information_class = FILE_ALL_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)

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
            frame = getattr(self, field)
            if isinstance(frame, core.Frame):
                frame.decode(cur)


class FileDirectoryInformation(FileInformation):
    file_information_class = FILE_DIRECTORY_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.end_of_file = 0
        self.allocation_size = 0
        self.file_attributes = 0
        self.ea_size = 0
        self.file_name = None

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


class FileFullDirectoryInformation(FileInformation):
    file_information_class = FILE_FULL_DIRECTORY_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.end_of_file = 0
        self.allocation_size = 0
        self.file_attributes = 0
        self.ea_size = 0
        self.file_name = None

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
        self.ea_size = cur.decode_uint32le()

        self.file_name = cur.decode_utf16le(file_name_length)
        if next_offset:
            cur.advanceto(self.start + next_offset)
        else:
            cur.advanceto(cur.upperbound)


class FileIdFullDirectoryInformation(FileInformation):
    file_information_class = FILE_ID_FULL_DIR_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.end_of_file = 0
        self.allocation_size = 0
        self.file_attributes = 0
        self.ea_size = 0
        self.reserved = 0
        self.file_id = 0
        self.file_name = None

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
        self.ea_size = cur.decode_uint32le()
        self.reserved = cur.decode_uint32le()
        self.file_id = cur.decode_uint64le()

        self.file_name = cur.decode_utf16le(file_name_length)
        if next_offset:
            cur.advanceto(self.start + next_offset)
        else:
            cur.advanceto(cur.upperbound)


class FileIdBothDirectoryInformation(FileInformation):
    file_information_class = FILE_ID_BOTH_DIR_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.end_of_file = 0
        self.allocation_size = 0
        self.file_attributes = 0
        self.ea_size = 0
        self.file_id = 0
        self.short_name = None
        self.file_name = None

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

        self.file_name_length = cur.decode_uint32le()
        self.ea_size = cur.decode_uint32le()
        self.short_name_length = cur.decode_uint8le()
        reserved = cur.decode_uint8le()
        self.short_name = cur.decode_bytes(24)
        reserved = cur.decode_uint16le()
        self.file_id = cur.decode_uint64le()
        self.file_name = cur.decode_utf16le(self.file_name_length)

        if next_offset:
            cur.advanceto(self.start + next_offset)
        else:
            cur.advanceto(cur.upperbound)


class FileBasicInformation(FileInformation):
    file_information_class = FILE_BASIC_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.file_attributes = 0

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


class FileNetworkOpenInformation(FileInformation):
    file_information_class = FILE_NETWORK_OPEN_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.creation_time = 0
        self.last_access_time = 0
        self.last_write_time = 0
        self.change_time = 0
        self.allocation_size = 0
        self.end_of_file = 0
        self.file_attributes = 0

    def _decode(self, cur):
        self.creation_time = nttime.NtTime(cur.decode_uint64le())
        self.last_access_time = nttime.NtTime(cur.decode_uint64le())
        self.last_write_time = nttime.NtTime(cur.decode_uint64le())
        self.change_time = nttime.NtTime(cur.decode_uint64le())
        self.allocation_size = cur.decode_int64le()
        self.end_of_file = cur.decode_int64le()
        self.file_attributes = FileAttributes(cur.decode_uint32le())
        # Ignore the 4-byte reserved field
        cur.decode_uint32le()


class FileAttributeTagInformation(FileInformation):
    file_information_class = FILE_ATTRIBUTE_TAG_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_attributes = 0
        self.reparse_tag = 0

    def _decode(self, cur):
        self.file_attributes = FileAttributes(cur.decode_uint32le())
        self.reparse_tag = cur.decode_uint32le()


class FileStreamInformation(FileInformation):
    file_information_class = FILE_STREAM_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.next_entry_offset = 0
        self.stream_name_length = 0
        self.stream_size = 0
        self.stream_allocation_size = 0
        self.stream_name = None

    def _decode(self, cur):
        self.next_entry_offset = cur.decode_uint32le()
        self.stream_name_length = cur.decode_uint32le()
        self.stream_size = cur.decode_int64le()
        self.stream_allocation_size = cur.decode_int64le()
        self.stream_name = cur.decode_utf16le(self.stream_name_length)
        if self.next_entry_offset:
            cur.advanceto(self.start + self.next_entry_offset)


# Compression Format
class CompressionFormat(core.ValueEnum):
    COMPRESSION_FORMAT_NONE = 0x0000
    COMPRESSION_FORMAT_LZNT1 = 0x0002


CompressionFormat.import_items(globals())


class FileCompressionInformation(FileInformation):
    file_information_class = FILE_COMPRESSION_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.compressed_file_size = 0
        self.compression_format = 0
        self.compression_unit_shift = 0
        self.chunk_shift = 0
        self.cluster_shift = None
        self.reserved = 0

    def _decode(self, cur):
        self.compressed_file_size = cur.decode_int64le()
        self.compression_format = CompressionFormat(cur.decode_uint16le())
        self.compression_unit_shift = cur.decode_uint8le()
        self.chunk_shift = cur.decode_uint8le()
        self.cluster_shift = cur.decode_uint8le()

        # This is a single reserved field of 3 bytes.
        self.reserved = (
            cur.decode_uint8le()
            | (cur.decode_uint8le() << 8)
            | (cur.decode_uint8le() << 16)
        )


class FileInternalInformation(FileInformation):
    file_information_class = FILE_INTERNAL_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.index_number = 0

    def _decode(self, cur):
        self.index_number = cur.decode_uint64le()


class FileModeInformation(FileInformation):
    file_information_class = FILE_MODE_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        # See Create options (e.g. FILE_DELETE_ON_CLOSE) for available flags
        self.mode = 0

    def _decode(self, cur):
        self.mode = CreateOptions(cur.decode_uint32le())

    def _encode(self, cur):
        cur.encode_uint32le(self.mode)


class FileNameInformation(FileInformation):
    file_information_class = FILE_NAME_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_name = None

    def _decode(self, cur):
        file_name_length = cur.decode_uint32le()
        self.file_name = cur.decode_utf16le(file_name_length)


class FileRenameInformation(FileInformation):
    file_information_class = FILE_RENAME_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.replace_if_exists = 0
        self.root_directory = (0, 0)
        self.file_name = None

    def _encode(self, cur):
        cur.encode_uint8le(self.replace_if_exists)
        cur.encode_uint8le(0)  # reserved
        cur.encode_uint16le(0)  # reserved
        cur.encode_uint32le(0)  # reserved
        cur.encode_uint32le(self.root_directory[0])
        cur.encode_uint32le(self.root_directory[1])
        file_name_length_hole = cur.hole.encode_uint32le(0)
        file_name_start = cur.copy()
        cur.encode_utf16le(self.file_name)
        file_name_length_hole(cur - file_name_start)


class FileAllocationInformation(FileInformation):
    file_information_class = FILE_ALLOCATION_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.allocation_size = 0

    def _encode(self, cur):
        cur.encode_int64le(self.allocation_size)


class FileDispositionInformation(FileInformation):
    file_information_class = FILE_DISPOSITION_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.delete_pending = 0

    def _encode(self, cur):
        cur.encode_uint8le(self.delete_pending)


class FileEndOfFileInformation(FileInformation):
    file_information_class = FILE_END_OF_FILE_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.endoffile = 0

    def _encode(self, cur):
        cur.encode_int64le(self.endoffile)


class FileValidDataLengthInformation(FileInformation):
    file_information_class = FILE_VALID_DATA_LENGTH_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.valid_data_length = 0

    def _encode(self, cur):
        cur.encode_int64le(self.valid_data_length)


class FileNamesInformation(FileInformation):
    file_information_class = FILE_NAMES_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.file_index = 0
        self.file_name = None

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

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.current_byte_offset = 0

    def _decode(self, cur):
        self.current_byte_offset = cur.decode_uint64le()

    def _encode(self, cur):
        cur.encode_uint64le(self.current_byte_offset)


class FileStandardInformation(FileInformation):
    file_information_class = FILE_STANDARD_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.allocation_size = 0
        self.end_of_file = 0
        self.number_of_links = 0
        self.delete_pending = 0
        self.directory = 0

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
        cur.encode_uint16le(0)


class FileEaInformation(FileInformation):
    file_information_class = FILE_EA_INFORMATION

    def __init__(self, parent=None):
        FileInformation.__init__(self, parent)
        self.ea_size = 0

    def _decode(self, cur):
        self.ea_size = cur.decode_uint32le()


class FileFsSizeInformation(FileSystemInformation):
    file_information_class = FILE_FS_SIZE_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.total_allocation_units = 0
        self.available_allocation_units = 0
        self.sectors_per_allocation_unit = 0
        self.bytes_per_sector = 0

    def _decode(self, cur):
        self.total_allocation_units = cur.decode_int64le()
        self.available_allocation_units = cur.decode_int64le()
        self.sectors_per_allocation_unit = cur.decode_uint32le()
        self.bytes_per_sector = cur.decode_uint32le()


class FileFsFullSizeInformation(FileSystemInformation):
    file_information_class = FILE_FS_FULL_SIZE_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.total_allocation_units = 0
        self.caller_available_allocation_units = 0
        self.actual_available_allocation_units = 0
        self.sectors_per_allocation_unit = 0
        self.bytes_per_sector = 0

    def _decode(self, cur):
        self.total_allocation_units = cur.decode_uint64le()
        self.caller_available_allocation_units = cur.decode_uint64le()
        self.actual_available_allocation_units = cur.decode_uint64le()
        self.sectors_per_allocation_unit = cur.decode_uint32le()
        self.bytes_per_sector = cur.decode_uint32le()


# DeviceType
class DeviceType(core.ValueEnum):
    FILE_DEVICE_CD_ROM = 0x00000002
    FILE_DEVICE_DISK = 0x00000007


DeviceType.import_items(globals())


# Volume Characteristics
class Characteristics(core.FlagEnum):
    FILE_REMOVABLE_MEDIA = 0x00000001
    FILE_READ_ONLY_DEVICE = 0x00000002
    FILE_FLOPPY_DISKETTE = 0x00000004
    FILE_WRITE_ONCE_MEDIA = 0x00000008
    FILE_REMOTE_DEVICE = 0x00000010
    FILE_DEVICE_IS_MOUNTED = 0x00000020
    FILE_VIRTUAL_VOLUME = 0x00000040
    FILE_DEVICE_SECURE_OPEN = 0x00000100
    FILE_CHARACTERISTIC_TS_DEVICE = 0x00001000
    FILE_CHARACTERISTIC_WEBDAV_DEVICE = 0x00002000
    FILE_DEVICE_ALLOW_APPCONTAINER_TRAVERSAL = 0x00020000


Characteristics.import_items(globals())


class FileFsDeviceInformation(FileSystemInformation):
    file_information_class = FILE_FS_DEVICE_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.device_type = 0
        self.characteristics = 0

    def _decode(self, cur):
        self.device_type = DeviceType(cur.decode_uint32le())
        self.characteristics = Characteristics(cur.decode_uint32le())


# File System Attributes
class FileSystemAtrribute(core.FlagEnum):
    FILE_CASE_SENSITIVE_SEARCH = 0x00000001
    FILE_CASE_PRESERVED_NAMES = 0x00000002
    FILE_UNICODE_ON_DISK = 0x00000004
    FILE_PERSISTENT_ACLS = 0x00000008
    FILE_FILE_COMPRESSION = 0x00000010
    FILE_VOLUME_QUOTAS = 0x00000020
    FILE_SUPPORTS_SPARSE_FILES = 0x00000040
    FILE_SUPPORTS_REPARSE_POINTS = 0x00000080
    FILE_SUPPORTS_REMOTE_STORAGE = 0x00000100
    FILE_VOLUME_IS_COMPRESSED = 0x00008000
    FILE_SUPPORTS_OBJECT_IDS = 0x00010000
    FILE_SUPPORTS_ENCRYPTION = 0x00020000
    FILE_NAMED_STREAMS = 0x00040000
    FILE_READ_ONLY_VOLUME = 0x00080000
    FILE_SEQUENTIAL_WRITE_ONCE = 0x00100000
    FILE_SUPPORTS_TRANSACTIONS = 0x00200000
    FILE_SUPPORTS_HARD_LINKS = 0x00400000
    FILE_SUPPORTS_EXTENDED_ATTRIBUTES = 0x00800000
    FILE_SUPPORTS_OPEN_BY_FILE_ID = 0x01000000
    FILE_SUPPORTS_USN_JOURNAL = 0x02000000
    FILE_SUPPORT_INTEGRITY_STREAMS = 0x04000000


FileSystemAtrribute.import_items(globals())


class FileFsAttributeInformation(FileSystemInformation):
    file_information_class = FILE_FS_ATTRIBUTE_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.file_system_attibutes = 0
        self.maximum_component_name_length = 0
        self.file_system_name_length = 0
        self.file_system_name = 0

    def _decode(self, cur):
        self.file_system_attibutes = cur.decode_uint32le()
        self.maximum_component_name_length = cur.decode_int32le()
        self.file_system_name_length = cur.decode_uint32le()
        self.file_system_name = cur.decode_utf16le(self.file_system_name_length)


class FileFsVolumeInformation(FileSystemInformation):
    file_information_class = FILE_FS_VOLUME_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.volume_creation_time = 0
        self.volume_serial_number = 0
        self.volume_label_length = 0
        self.supports_objects = 0
        self.reserved = 0
        self.volume_label = None

    def _decode(self, cur):
        self.volume_creation_time = nttime.NtTime(cur.decode_uint64le())
        self.volume_serial_number = cur.decode_uint32le()
        self.volume_label_length = cur.decode_uint32le()
        self.supports_objects = cur.decode_uint8le()
        cur.decode_uint8le()
        self.volume_label = cur.decode_utf16le(self.volume_label_length)


# File System Control Flags
class FileSystemControlFlags(core.FlagEnum):
    FILE_VC_QUOTA_TRACK = 0x00000001
    FILE_VC_QUOTA_ENFORCE = 0x00000002
    FILE_VC_CONTENT_INDEX_DISABLED = 0x00000008
    FILE_VC_LOG_QUOTA_THRESHOLD = 0x00000010
    FILE_VC_LOG_QUOTA_LIMIT = 0x00000020
    FILE_VC_LOG_VOLUME_THRESHOLD = 0x00000040
    FILE_VC_LOG_VOLUME_LIMIT = 0x00000080
    FILE_VC_QUOTAS_INCOMPLETE = 0x00000100
    FILE_VC_QUOTAS_REBUILDING = 0x00000200


FileSystemControlFlags.import_items(globals())


class FileFsControlInformation(FileSystemInformation):
    file_information_class = FILE_FS_CONTROL_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.free_space_start_filtering = 0
        self.free_space_threshold = 0
        self.free_space_stop_filtering = 0
        self.default_quota_threshold = 0
        self.default_quota_limit = 0
        self.file_system_control_flags = None
        self.padding = 0

    def _encode(self, cur):
        cur.encode_int64le(self.free_space_start_filtering)
        cur.encode_int64le(self.free_space_threshold)
        cur.encode_int64le(self.free_space_stop_filtering)
        cur.encode_uint64le(self.default_quota_threshold)
        cur.encode_uint64le(self.default_quota_limit)
        cur.encode_uint32le(self.file_system_control_flags)
        cur.encode_uint32le(self.padding)

    def _decode(self, cur):
        self.free_space_start_filtering = cur.decode_int64le()
        self.free_space_threshold = cur.decode_int64le()
        self.free_space_stop_filtering = cur.decode_int64le()
        self.default_quota_threshold = cur.decode_uint64le()
        self.default_quota_limit = cur.decode_uint64le()
        self.file_system_control_flags = FileSystemControlFlags(cur.decode_uint32le())
        self.padding = cur.decode_uint32le()


class FileFsObjectIdInformation(FileSystemInformation):
    file_information_class = FILE_FS_OBJECTID_INFORMATION

    def __init__(self, parent=None):
        FileSystemInformation.__init__(self, parent)
        self.objectid = ""
        self.extended_info = ""

    def _decode(self, cur):
        for count in range(2):
            self.objectid += str(cur.decode_uint64le())
        for count in range(6):
            self.extended_info += str(cur.decode_uint64le())


class CompletionFilter(core.FlagEnum):
    SMB2_NOTIFY_CHANGE_FILE_NAME = 0x001
    SMB2_NOTIFY_CHANGE_DIR_NAME = 0x002
    SMB2_NOTIFY_CHANGE_ATTRIBUTES = 0x004
    SMB2_NOTIFY_CHANGE_SIZE = 0x008
    SMB2_NOTIFY_CHANGE_LAST_WRITE = 0x010
    SMB2_NOTIFY_CHANGE_LAST_ACCESS = 0x020
    SMB2_NOTIFY_CHANGE_CREATION = 0x040
    SMB2_NOTIFY_CHANGE_EA = 0x080
    SMB2_NOTIFY_CHANGE_SECURITY = 0x100
    SMB2_NOTIFY_CHANGE_STREAM_NAME = 0x200
    SMB2_NOTIFY_CHANGE_STREAM_SIZE = 0x400
    SMB2_NOTIFY_CHANGE_STREAM_WRITE = 0x800


CompletionFilter.import_items(globals())


class ChangeNotifyFlags(core.FlagEnum):
    SMB2_WATCH_TREE = 0x01


ChangeNotifyFlags.import_items(globals())


class FileNotifyInfoAction(core.ValueEnum):
    SMB2_ACTION_ADDED = 0x001
    SMB2_ACTION_REMOVED = 0x002
    SMB2_ACTION_MODIFIED = 0x003
    SMB2_ACTION_RENAMED_OLD_NAME = 0x004
    SMB2_ACTION_RENAMED_NEW_NAME = 0x005
    SMB2_ACTION_ADDED_STREAM = 0x006
    SMB2_ACTION_REMOVED_STREAM = 0x007
    SMB2_ACTION_MODIFIED_STREAM = 0x008
    SMB2_ACTION_REMOVED_BY_DELETE = 0x009


FileNotifyInfoAction.import_items(globals())


class FileNotifyInformation(core.Frame):
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        self.action = 0
        self.filename = None
        if parent is not None:
            parent.append(self)

    def _decode(self, cur):
        startoffset = cur.offset
        neo = cur.decode_uint32le()
        self.action = FileNotifyInfoAction(cur.decode_uint32le())
        filenamelength = cur.decode_uint32le()
        self.filename = cur.decode_utf16le(filenamelength)
        cur.offset = startoffset + neo
        return neo

    def __repr__(self):
        return "<{0} {1} '{2}'>".format(
            self.__class__.__name__, self.action, self.filename
        )


class ChangeNotifyResponse(Response):
    command_id = SMB2_CHANGE_NOTIFY
    allowed_status = [ntstatus.STATUS_SUCCESS, ntstatus.STATUS_NOTIFY_CLEANUP]
    structure_size = 9

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.notifications = []

    @property
    def children(self):
        return self.notifications

    def append(self, child):
        self.notifications.append(child)

    def _decode(self, cur):
        self.offset = cur.decode_uint16le()
        self.buffer_length = cur.decode_uint32le()
        if self.buffer_length > 0:
            while True:
                neo = FileNotifyInformation(self)._decode(cur)
                if neo == 0:
                    break


class ChangeNotifyRequest(Request):
    command_id = SMB2_CHANGE_NOTIFY
    structure_size = 32

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.flags = 0
        self.file_id = None
        self.buffer_length = 4096
        self.completion_filter = 0

    def _encode(self, cur):
        cur.encode_uint16le(self.flags)
        cur.encode_uint32le(self.buffer_length)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        cur.encode_uint32le(self.completion_filter)
        # Reserved
        cur.encode_uint32le(0)


class BreakLeaseFlags(core.FlagEnum):
    SMB2_NOTIFY_BREAK_LEASE_FLAG_NONE = 0x00
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
        self.reserved1 = cur.decode_uint8le()
        self.reserved2 = cur.decode_uint32le()
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
        self.break_reason = cur.decode_uint32le()
        self.access_mask_hint = cur.decode_uint32le()
        self.share_mask_hint = cur.decode_uint32le()


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
        self.reserved1 = cur.decode_uint8le()
        self.reserved2 = cur.decode_uint32le()
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
        self.reserved = cur.decode_uint16le()
        self.flags = BreakLeaseFlags(cur.decode_uint32le())
        self.lease_key = cur.decode_bytes(16)
        self.lease_state = LeaseState(cur.decode_uint32le())
        self.lease_duration = cur.decode_uint64le()


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

        self.padding = 0
        self.reserved = 0
        self.channel = 0
        self.read_channel_info_offset = None
        self.read_channel_info_length = None
        self.buffer = 0

    def _log_str(self):
        return " ".join(
            [
                super(ReadRequest, self)._log_str(),
                "({}@{})".format(self.length, self.offset),
            ]
        )

    def _encode(self, cur):
        # Padding
        cur.encode_uint8le(self.padding)
        # Reserved
        cur.encode_uint8le(self.reserved)
        cur.encode_uint32le(self.length)
        cur.encode_uint64le(self.offset)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        cur.encode_uint32le(self.minimum_count)
        # Channel
        cur.encode_uint32le(self.channel)

        cur.encode_uint32le(self.remaining_bytes)

        # ReadChannelInfoLength
        if self.read_channel_info_offset is None:
            self.read_channel_info_offset = 0
        cur.encode_uint16le(self.read_channel_info_offset)

        # ReadChannelInfoLength
        if self.read_channel_info_length is None:
            self.read_channel_info_length = 0
        cur.encode_uint16le(self.read_channel_info_length)

        # Buffer
        cur.encode_uint8le(self.buffer)


class ReadResponse(Response):
    command_id = SMB2_READ
    structure_size = 17

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.offset = 0
        self.length = 0
        self.data = None
        self.reserved = 0
        self.data_remaining = 0
        self.reserved2 = 0

    def _log_str(self):
        return " ".join(
            [super(ReadResponse, self)._log_str(), "({})".format(self.length),]
        )

    def _decode(self, cur):
        self.offset = cur.decode_uint8le()
        self.reserved = cur.decode_uint8le()
        self.length = cur.decode_uint32le()
        self.data_remaining = cur.decode_uint32le()
        self.reserved2 = cur.decode_uint32le()

        # Advance to data
        cur.advanceto(self.parent.start + self.offset)

        self.data = cur.decode_bytes(self.length)


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
        self.data_offset = None
        self.length = None
        self.channel = 0
        self.write_channel_info_offset = 0
        self.write_channel_info_length = 0

    def _log_str(self):
        components = [super(WriteRequest, self)._log_str()]
        if self.flags:
            components.append("({})".format(self.flags))
        if self.buffer:
            components.append("({}@{})".format(len(self.buffer), self.offset))
        return " ".join(components)

    def _encode(self, cur):
        # Encode 0 for buffer offset for now
        buf_ofs = cur.hole.encode_uint16le(0)
        if self.length == None and self.buffer != None:
            cur.encode_uint32le(len(self.buffer))
        elif self.buffer == None:
            cur.encode_uint32le(0)
        else:
            cur.encode_uint32le(self.length)
        cur.encode_uint64le(self.offset)
        cur.encode_uint64le(self.file_id[0])
        cur.encode_uint64le(self.file_id[1])
        # Channel
        cur.encode_uint32le(self.channel)
        # RemainingBytes
        cur.encode_uint32le(self.remaining_bytes)
        # WriteChannelInfoOffset
        cur.encode_uint16le(self.write_channel_info_offset)
        # WriteChannelInfoLength:
        cur.encode_uint16le(self.write_channel_info_length)
        # Flags
        cur.encode_uint32le(self.flags)
        # Go back and set buffer offset

        if self.data_offset is None:
            self.data_offset = cur - self.parent.start
        buf_ofs(self.data_offset)

        if self.buffer:
            cur.encode_bytes(self.buffer)


class WriteResponse(Response):
    command_id = SMB2_WRITE
    structure_size = 17

    def __init__(self, parent):
        Response.__init__(self, parent)
        self.count = 0
        self.reserved = 0
        self.remaining = 0
        self.write_channel_info_offset = 0
        self.write_channel_info_length = 0

    def _log_str(self):
        components = [
            super(WriteResponse, self)._log_str(),
            "({})".format(self.count),
        ]
        if self.remaining:
            components.append("(remaining {})".format(self.remaining))
        return " ".join(components)

    def _decode(self, cur):
        self.reserved = cur.decode_uint16le()
        self.count = cur.decode_uint32le()
        self.remaining = cur.decode_uint32le()
        self.write_channel_info_offset = cur.decode_uint16le()
        self.write_channel_info_length = cur.decode_uint16le()


class LockFlags(core.FlagEnum):
    SMB2_LOCKFLAG_SHARED_LOCK = 0x00000001
    SMB2_LOCKFLAG_EXCLUSIVE_LOCK = 0x00000002
    SMB2_LOCKFLAG_UN_LOCK = 0x00000004
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
        self.lock_count = None

    def _encode(self, cur):
        if self.lock_count == None:
            self.lock_count = len(self.locks)
        cur.encode_uint16le(self.lock_count)
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
        self.reserved = cur.decode_uint16le()


class IoctlCode(core.ValueEnum):
    FSCTL_DFS_GET_REFERRALS = 0x00060194
    FSCTL_PIPE_PEEK = 0x0011400C
    FSCTL_PIPE_WAIT = 0x00110018
    FSCTL_PIPE_TRANSCEIVE = 0x0011C017
    FSCTL_SRV_COPYCHUNK = 0x001440F2
    FSCTL_SRV_ENUMERATE_SNAPSHOTS = 0x00144064
    FSCTL_SRV_REQUEST_RESUME_KEY = 0x00140078
    FSCTL_SRV_READ_HASH = 0x001441BB
    FSCTL_SRV_COPYCHUNK_WRITE = 0x001480F2
    FSCTL_LMR_REQUEST_RESILIENCY = 0x001401D4
    FSCTL_QUERY_NETWORK_INTERFACE_INFO = 0x001401FC
    FSCTL_SET_REPARSE_POINT = 0x000900A4
    FSCTL_GET_REPARSE_POINT = 0x000900A8
    FSCTL_DFS_GET_REFERRALS_EX = 0x000601B0
    FSCTL_FILE_LEVEL_TRIM = 0x00098208
    FSCTL_VALIDATE_NEGOTIATE_INFO = 0x00140204
    FSCTL_SET_ZERO_DATA = 0x000980C8
    FSCTL_SET_SPARSE = 0x000900C4


IoctlCode.import_items(globals())


class IoctlFlags(core.FlagEnum):
    SMB2_0_IOCTL_IS_FSCTL = 0x00000001


IoctlFlags.import_items(globals())


class IoctlRequest(Request):
    command_id = SMB2_IOCTL
    structure_size = 57
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True

    field_blacklist = ["ioctl_input"]

    def __init__(self, parent):
        Request.__init__(self, parent)
        self.ctl_code = None
        # MS-SMB2 says that the file ID should be set to 0xffffffffffffffff for
        # certain IOCTLs.  Assuming that means both persistent and volatile.
        self.file_id = (0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF)
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
        # For requests, output offset and count should be 0
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
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True

    field_blacklist = ["ioctl_output"]

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

    def _encode(self, cur):
        cur.encode_uint32le(self.capabilities)
        cur.encode_bytes(self.client_guid)
        cur.encode_uint16le(self.security_mode)

        # If dialects_count was not set manually, calculate it here.
        if self.dialects_count is None:
            self.dialects_count = len(self.dialects)
        cur.encode_uint16le(self.dialects_count)

        for dialect in self.dialects:
            cur.encode_uint16le(dialect)


class QueryNetworkInterfaceInfoRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_QUERY_NETWORK_INTERFACE_INFO

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)

    def _encode(self, cur):
        pass


class RequestResumeKeyRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_SRV_REQUEST_RESUME_KEY

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        parent.ioctl_input = self

    def _encode(self, cur):
        pass


class NetworkResiliencyRequestRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_LMR_REQUEST_RESILIENCY

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        self.timeout = 0
        self.reserved = 0

    def _encode(self, cur):
        cur.encode_uint32le(self.timeout)
        cur.encode_uint32le(self.reserved)


class CopyChunkCopyRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_SRV_COPYCHUNK

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        self.source_key = 0
        self.chunk_count = 0
        self._children = []

    def append(self, child):
        self._children.append(child)

    def _encode(self, cur):
        cur.encode_bytes(self.source_key)
        cur.encode_uint32le(self.chunk_count)
        cur.encode_uint32le(0)  # reserved
        # encode the chunks
        for chunk in self._children:
            chunk.encode(cur)


class CopyChunkCopyWriteRequest(CopyChunkCopyRequest):
    ioctl_ctl_code = FSCTL_SRV_COPYCHUNK_WRITE


class CopyChunk(core.Frame):
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        parent.append(self)
        self.source_offset = 0
        self.target_offset = 0
        self.length = 0

    def _encode(self, cur):
        cur.encode_uint64le(self.source_offset)
        cur.encode_uint64le(self.target_offset)
        cur.encode_uint32le(self.length)
        cur.encode_uint32le(0)


class SetReparsePointRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_SET_REPARSE_POINT

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        self.reparse_data = None

    def _encode(self, cur):
        if self.reparse_data is not None:
            self.reparse_data.encode(cur)


class GetReparsePointRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_GET_REPARSE_POINT

    def _encode(self, *args, **kwds):
        pass


class EnumerateSnapshotsRequest(IoctlInput):
    ioctl_ctl_code = FSCTL_SRV_ENUMERATE_SNAPSHOTS

    def _encode(self, *args, **kwds):
        pass


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


class QueryNetworkInterfaceInfoResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_QUERY_NETWORK_INTERFACE_INFO

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)

    def _decode(self, cur):
        pass


class RequestResumeKeyResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_SRV_REQUEST_RESUME_KEY

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        self.resume_key = array.array("B", [0] * 24)
        self.context_length = 0

    def _decode(self, cur):
        self.resume_key = cur.decode_bytes(24)
        self.context_length = cur.decode_uint32le()


class NetworkResiliencyRequestResponse(IoctlOutput):

    ioctl_ctl_code = FSCTL_LMR_REQUEST_RESILIENCY

    def _decode(self, cur):
        pass


class CopyChunkCopyResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_SRV_COPYCHUNK

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        self.chunks_written = 0
        self.chunk_bytes_written = 0
        self.total_bytes_written = 0

    def _decode(self, cur):
        self.chunks_written = cur.decode_uint32le()
        self.chunk_bytes_written = cur.decode_uint32le()
        self.total_bytes_written = cur.decode_uint32le()


class CopyChunkCopyWriteResponse(CopyChunkCopyResponse):
    ioctl_ctl_code = FSCTL_SRV_COPYCHUNK_WRITE


class SetReparsePointResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_SET_REPARSE_POINT

    def _decode(self, *args, **kwds):
        pass


class GetReparsePointResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_GET_REPARSE_POINT

    field_blacklist = ["reparse_data"]
    _reparse_tag_map = {}
    reparse_tag = core.Register(_reparse_tag_map, "reparse_tag")

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        self.tag = 0

    def _children(self):
        return [self.reparse_data] if self.reparse_data is not None else []

    def _decode(self, cur):
        self.tag = cur.decode_uint32le()
        reparse_data = self._reparse_tag_map[self.tag]
        reparse_data(self).decode(cur)


@GetReparsePointResponse.reparse_tag
class ReparseDataBuffer(core.Frame):
    def __init__(self, parent):
        super(ReparseDataBuffer, self).__init__(parent)
        if parent is not None:
            parent.reparse_data = self


class SymbolicLinkFlags(core.FlagEnum):
    SYMLINK_FLAG_ABSOLUTE = 0x0
    SYMLINK_FLAG_RELATIVE = 0x1


SymbolicLinkFlags.import_items(globals())


class SymbolicLinkReparseBuffer(ReparseDataBuffer):
    reparse_tag = 0xA000000C

    def __init__(self, parent):
        super(SymbolicLinkReparseBuffer, self).__init__(parent)
        self.unparsed_path_length = 0  # for ErrorResponse only
        self.substitute_name = None
        self.substitute_name_length = None
        self.substitute_name_offset = 0
        self.print_name = None
        self.print_name_length = None
        self.print_name_offset = None
        self.flags = 0

    def _encode(self, cur):
        cur.encode_uint32le(self.reparse_tag)
        reparse_data_length_hole = cur.hole.encode_uint16le(0)
        cur.encode_uint16le(0)  # reserved
        reparse_data_len_start = cur.copy()
        cur.encode_uint16le(self.substitute_name_offset)
        sname_len_hole = cur.hole.encode_uint16le(0)
        pname_offset_hole = cur.hole.encode_uint16le(0)
        pname_len_hole = cur.hole.encode_uint16le(0)
        cur.encode_uint32le(self.flags)

        sname_start = cur.copy()
        cur.encode_utf16le(self.substitute_name)
        if self.substitute_name_length is None:
            self.substitute_name_length = cur - sname_start
        sname_len_hole(self.substitute_name_length)

        if self.print_name is None:
            self.print_name = self.substitute_name
        pname_start = cur.copy()
        if self.print_name_offset is None:
            self.print_name_offset = self.substitute_name_length
        pname_offset_hole(self.print_name_offset)
        cur.encode_utf16le(self.print_name)
        if self.print_name_length is None:
            self.print_name_length = cur - pname_start
        pname_len_hole(self.print_name_length)

        reparse_data_length_hole(cur - reparse_data_len_start)

    def _decode(self, cur):
        reparse_data_length = cur.decode_uint16le()
        self.unparsed_path_length = cur.decode_uint16le()
        self.substitute_name_offset = cur.decode_uint16le()
        self.substitute_name_length = cur.decode_uint16le()
        self.print_name_offset = cur.decode_uint16le()
        self.print_name_length = cur.decode_uint16le()
        self.flags = cur.decode_uint32le()

        buf_start = cur.copy()
        self.substitute_name = cur.decode_utf16le(self.substitute_name_length)
        cur.seekto(buf_start + self.print_name_offset)
        self.print_name = cur.decode_utf16le(self.print_name_length)


class EnumerateSnapshotsResponse(IoctlOutput):
    ioctl_ctl_code = FSCTL_SRV_ENUMERATE_SNAPSHOTS

    def __init__(self, parent):
        super(EnumerateSnapshotsResponse, self).__init__(parent)
        self.number_of_snapshots = 0
        self.number_of_snapshots_returns = 0
        self.snapshot_array_size = 0
        self.snapshots = []

    def _decode(self, cur):
        self.number_of_snapshots = cur.decode_uint32le()
        self.number_of_snapshots_returned = cur.decode_uint32le()
        self.snapshot_array_size = cur.decode_uint32le()
        snapshot_buffer = cur.decode_utf16le(self.snapshot_array_size)
        # TODO: handle the case where the buffer is too small
        self.snapshots = snapshot_buffer.strip("\0").split("\0")


class SetZeroDataRequest(IoctlInput):
    ioctl_ctl_code = IoctlCode.FSCTL_SET_ZERO_DATA

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        self.file_offset = 0
        self.beyond_final_zero = 0
        parent.ioctl_input = self

    def _encode(self, cur):
        cur.encode_uint64le(self.file_offset)
        cur.encode_uint64le(self.beyond_final_zero)


class SetZeroDataResponse(IoctlOutput):
    ioctl_ctl_code = IoctlCode.FSCTL_SET_ZERO_DATA

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        parent.ioctl_output = self

    def _decode(self, cur):
        pass


class SetSparseRequest(IoctlInput):
    ioctl_ctl_code = IoctlCode.FSCTL_SET_SPARSE

    def __init__(self, parent):
        IoctlInput.__init__(self, parent)
        parent.ioctl_input = self

    def _encode(self, cur):
        pass


class SetSparseResponse(IoctlOutput):
    ioctl_ctl_code = IoctlCode.FSCTL_SET_SPARSE

    def __init__(self, parent):
        IoctlOutput.__init__(self, parent)
        parent.ioctl_output = self

    def _decode(self, cur):
        pass
