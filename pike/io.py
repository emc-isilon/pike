"""
file-like wrapper for an open file
"""
from __future__ import absolute_import

import functools
import io

import attr

from .exceptions import ResponseError
from . import ntstatus
from . import smb2


@attr.s
class _Open(object):
    """private

    Base class for ``Open``.

    Handle the SMB2-specific protocol interaction for leases, oplocks, and
    durable handles.

    Wrap :py:class:`~pike.model.Channel` operations which accept an ``Open`` as an
    argument.

    This class shouldn't be instantiated directly. See :py:class:`~pike.io.Open`
    """

    tree = attr.ib()
    create_request = attr.ib()
    create_response = attr.ib()
    create_guid = attr.ib()
    _previous_open = attr.ib()
    oplock_level = attr.ib(init=False)
    lease = attr.ib(init=False)
    _is_resilient = attr.ib(init=False)
    _is_durable = attr.ib(init=False)

    @oplock_level.default
    def _init_oplock_level(self):
        oplock_level = self.create_response.oplock_level
        if oplock_level not in (
            smb2.SMB2_OPLOCK_LEVEL_NONE,
            smb2.SMB2_OPLOCK_LEVEL_LEASE,
        ):
            self.arm_oplock_future()
        return oplock_level

    @lease.default
    def _init_lease(self):
        if self.oplock_level == smb2.SMB2_OPLOCK_LEVEL_LEASE:
            for ctx in self.create_response:
                if isinstance(ctx, smb2.LeaseResponse):
                    return self.tree.session.client.lease(self.tree, ctx)

    @_is_durable.default
    def _init_is_durable(self):
        if self._previous_open is not None:
            return self._previous_open.is_durable
        return (
            self.durable_handle_ctx is not None
            or self.durable_handle_v2_ctx is not None
        )

    @_is_resilient.default
    def _init_is_resilient(self):
        if self._previous_open is not None:
            return self._previous_open.is_resilient
        return False

    @property
    def channel(self):
        """
        :rtype: pike.model.Channel
        :return: The first Channel associated with this handle.

        (The session may have multiple bound channels).
        """
        if not self.closed:
            return self.tree.session.first_channel()
        raise ValueError("I/O operation on closed file")

    @property
    def file_id(self):
        """
        :rtype: 2-tuple of (int, int)
        :return: the server-opaque file handle returned in the CREATE response
        """
        return self.create_response.file_id

    @property
    def durable_handle_ctx(self):
        """
        :rtype: smb2.DurableHandleResponse or None
        """

        for ctx in self.create_response:
            if isinstance(ctx, smb2.DurableHandleResponse):
                return ctx

    @property
    def durable_handle_v2_ctx(self):
        """
        :rtype: smb2.DurableHandleV2Response or None
        """
        for ctx in self.create_response:
            if isinstance(ctx, smb2.DurableHandleV2Response):
                return ctx

    @property
    def durable_timeout(self):
        """
        :rtype: int or None
        :return: the durable handle timeout in seconds (or None if not durable)
        """
        ctx = self.durable_handle_v2_ctx
        if ctx:
            return ctx.durable_timeout
        elif self._previous_open is not None:
            return self._previous_open.durable_timeout

    @property
    def durable_flags(self):
        """
        :rtype: int or None
        :return: the durable handle flags (or None if not durable)
        """
        ctx = self.durable_handle_v2_ctx
        if ctx:
            return ctx.durable_flags
        elif self._previous_open is not None:
            return self._previous_open.durable_flags
        return 0

    @property
    def is_durable(self):
        """
        :return: True if the handle is durable
        """
        return self._is_durable

    @property
    def is_resilient(self):
        """
        :return: True if the handle is resilient
        """
        return self._is_resilient

    @property
    def is_persistent(self):
        """
        :return: True if the handle is persistent
        """
        return self.durable_flags & smb2.SMB2_DHANDLE_FLAG_PERSISTENT != 0

    @property
    def closed(self):
        """
        :return: True if the handle is closed
        """
        return self.tree is None

    def arm_oplock_future(self):
        """
        (Re)arm the oplock future for this open. This function should be called
        when an oplock changes level to anything except SMB2_OPLOCK_LEVEL_NONE
        """
        self.oplock_future = self.tree.session.client.oplock_break_future(self.file_id)

    def on_oplock_break(self, cb):
        """
        Simple oplock break callback handler.

        :type cb: Callable[[pike.smb2.OplockLevel], pike.smb2.OplockLevel])
        :param cb: callback function is passed the
            ``pike.smb2.OplockBreakNotification.oplock_level`` and must return
            the desired :py:class:`pike.smb2.OplockLevel` to break to.
        """

        def simple_handle_break(op, smb_res, cb_ctx):
            """
            note that op is not used in this callback,
            since it already closes over self
            """
            notify = smb_res[0]
            if self.oplock_level != smb2.SMB2_OPLOCK_LEVEL_II:
                ack = self.channel.oplock_break_acknowledgement(self, smb_res)
                ack.oplock_level = cb(notify.oplock_level)
                ack_res = self.channel.connection.transceive(ack.parent.parent)[0][0]
                if ack.oplock_level != smb2.SMB2_OPLOCK_LEVEL_NONE:
                    self.arm_oplock_future()
                    self.on_oplock_break(cb)
                self.oplock_level = ack_res.oplock_level
            else:
                self.oplock_level = notify.oplock_level

        self.on_oplock_break_request(simple_handle_break)

    def on_oplock_break_request(self, cb, cb_ctx=None):
        """
        Complex oplock break callback handler.

        :type cb: Callable[[Open, pike.smb2.Smb2, Optional[Any]], Any])
        :param cb: callback function is passed the file handle, the Smb2
            :py:func:`~pike.smb2.OplockBreakNotification`, and an arbitrary
            context and should handle breaking the oplock in some way. The
            callback is also responsible for calling
            :py:func:`arm_oplock_future` and and updating the ``.oplock_level``
            (if changed)
        :type cb_ctx: Optional[Any]
        :param cb_ctx: arbitrary context passed to the callback
        """

        def handle_break(f):
            smb_res = f.result()
            cb(self, smb_res, cb_ctx)

        self.oplock_future.then(handle_break)

    def dispose(self):
        """
        Clear resources held by this object.

        Called implicitly when the object is closed.
        """
        self.tree = None
        if self.lease is not None:
            self.lease.dispose()
            self.lease = None

    def close(self):
        """
        Close the handle on the server.

        If the channel or connection is unavailable, this is a no-op.
        """
        if self.closed:
            return
        try:
            self.channel.close(self)
            self.dispose()
        except StopIteration:
            # If the underlying connection for the channel is closed explicitly
            # open will not able to find an appropriate channel, to send close.
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # Helper operations call through to self.channel
    @property
    def query_directory_request(self):
        return functools.partial(self.channel.query_directory_request, self)

    @property
    def query_directory(self):
        return functools.partial(self.channel.query_directory, self)

    @property
    def enum_directory(self):
        return functools.partial(self.channel.enum_directory, self)

    @property
    def query_file_info_request(self):
        return functools.partial(self.channel.query_file_info_request, self)

    @property
    def query_file_info(self):
        return functools.partial(self.channel.query_file_info, self)

    @property
    def set_file_info_request(self):
        return functools.partial(self.channel.set_file_info_request, self)

    @property
    def set_file_info(self):
        return functools.partial(self.channel.set_file_info, self)

    @property
    def change_notify_request(self):
        return functools.partial(self.channel.change_notify_request, self)

    @property
    def change_notify(self):
        return functools.partial(self.channel.change_notify, self)

    @property
    def flush_request(self):
        return functools.partial(self.channel.flush_request, self)

    @property
    def flush(self):
        return functools.partial(self.channel.flush, self)

    @property
    def lock_request(self):
        return functools.partial(self.channel.lock_request, self)

    @property
    def lock(self):
        return functools.partial(self.channel.lock, self)

    @property
    def set_symlink_request(self):
        return functools.partial(self.channel.set_symlink_request, self)

    @property
    def set_symlink(self):
        return functools.partial(self.channel.set_symlink, self)

    @property
    def get_symlink_request(self):
        return functools.partial(self.channel.get_symlink_request, self)

    @property
    def get_symlink(self):
        return functools.partial(self.channel.get_symlink, self)

    @property
    def request(self):
        return functools.partial(self.channel.request, obj=self)


class CompatOpen(_Open):
    """
    pike.model.Open compatible __init__ signature.

    Please refactor code to use the new _Open constructor
    """

    def __init__(self, tree, smb_res, create_guid=None, prev=None):
        super(CompatOpen, self).__init__(
            tree=tree,
            create_response=smb_res[0],
            create_guid=create_guid,
            previous_open=prev,
        )


@attr.s
class Open(_Open, io.RawIOBase):
    """
    Represents an open file handle on a remote SMB2 server.

    Can be used as a contextmanager, which will automatically close
    the file when the context block exits.

    This class should not be instantiated directly. Use one of the following
    methods to get an instance:

        * :py:func:`pike.model.Channel.create`
        * :py:func:`pike.path.PikePath.open`

    This class provides a file-like interface with support for ``read``,
    ``write``, ``seek``, ``flush``, and derivatives provided by ``RawIOBase``.

    :vartype tree: pike.model.Tree
    :ivar tree: the :py:class:`~pike.model.Tree` associated with this handle
    :vartype create_request: pike.smb2.CreateRequest
    :ivar create_request: the raw request sent to open this handle
    :vartype create_response: pike.smb2.CreateResponse
    :ivar create_response: the raw response returned by the server
    :vartype create_guid: str
    :ivar create_guid: the create_guid associated with the durable handle
    :vartype oplock_level: pike.smb2.OplockLevel
    :ivar oplock_level: the current Oplock level of the handle
    :vartype lease: pike.model.Lease
    :ivar lease: the current Lease state of the handle
    """

    _offset = attr.ib(default=0, init=False)
    _end_of_file = attr.ib(init=False)

    @_end_of_file.default
    def _init_end_of_file(self):
        return self.create_response.end_of_file

    @property
    def end_of_file(self):
        """
        :return: Byte offset of the end of file as reported by the CREATE response

        Note: this value is only updated by ``write`` and ``read``!
              if other operations are performed directly or via other sessions
              this value may get out of sync.
        """
        return self._end_of_file

    def seek(self, offset, whence=io.SEEK_SET):
        """
        Change the stream position to the given byte offset.

        offset is interpreted relative to the position indicated by whence.

        The default value for whence is SEEK_SET. Values for whence are:

            * ``io.SEEK_SET`` or ``0`` - start of the stream (the default);
              offset should be zero or positive
            * ``io.SEEK_CUR`` or ``1`` - current stream position; offset may be negative
            * ``io.SEEK_END`` or ``2`` - end of the stream; offset is usually negative

        :type offset: int
        :type whence: int (see above)
        :rtype: int
        :return: the new absolute position
        """
        if whence == io.SEEK_SET:
            self._offset = offset
        elif whence == io.SEEK_CUR:
            self._offset += offset
        elif whence == io.SEEK_END:
            self._offset = self.end_of_file + offset
        return self._offset

    def seekable(self):
        """
        :return: True if the stream supports random access.

        All ``Open`` instances support random access.
        """
        return True

    def tell(self):
        """
        :rtype: int
        :return: the absolute byte position within the file
        """
        return self._offset

    def truncate(self, size=None):
        """
        Resize the stream to the given size. NOT SUPPORTED.
        """
        raise NotImplementedError("truncate() not supported")

    def _has_access(self, access):
        if self.create_request is not None:
            return self.create_request.desired_access & access
        return None

    def readable(self):
        """
        :return: True if the stream can be read from
        """
        return any(
            self._has_access(a)
            for a in (smb2.FILE_READ_DATA, smb2.GENERIC_READ, smb2.GENERIC_ALL)
        )

    def _read_range(self, start=0, end=None):
        """
        Read a range of bytes from the file.

        Multiple requests will be made if necessary.

        :type start: int
        :param start: the beginning offset to read from
        :type end: int or None
        :param end: the end offset to read from. If None, read until
            STATUS_END_OF_FILE is returned.
        :rtype: bytes
        :return: bytes read from the file
        """
        max_read_size = self.channel.connection.negotiate_response.max_read_size
        offset = start
        response_buffers = []
        while end is None or offset < end:
            if end is not None:
                max_read_size = min(end - offset, max_read_size)
            available = min(
                self.channel.connection.credits * smb2.BYTES_PER_CREDIT,
                max_read_size,
            )
            try:
                read_resp = self.channel.read(self, available, offset)
                response_buffers.append(read_resp)
                offset += len(read_resp)
            except ResponseError as re:
                if re.response.status == ntstatus.STATUS_END_OF_FILE:
                    break
                raise
        read_buffer = b"".join(rb.tobytes() for rb in response_buffers)
        if read_buffer:
            self._offset = start + len(read_buffer)
            # update the EOF marker if we read past it
            self._end_of_file = max(self.end_of_file, self._offset)
        return read_buffer

    def readall(self):
        """
        Read all bytes from the current offset to EOF.
        """
        return self._read_range(self._offset)

    def readinto(self, b):
        """
        Read bytes into the preallocated buffer, b.

        Note: this function performs extra copying and is inefficient.
        """
        read_resp = self._read_range(self._offset, self._offset + len(b))
        bytes_read = len(read_resp)
        b[:bytes_read] = read_resp
        return bytes_read

    def _write_at(self, data, offset):
        """
        Write bytes to the file at the given offset.

        Multiple requests will be made if necessary.

        :type offset: int
        :param offset: the beginning offset to read from
        :rtype: int
        :return: count of bytes written
        """
        n_data = len(data)
        bytes_written = 0
        while bytes_written < n_data:
            available = min(
                n_data - bytes_written,
                self.channel.connection.credits * smb2.BYTES_PER_CREDIT,
                self.channel.connection.negotiate_response.max_write_size,
            )
            chunk = data[bytes_written : bytes_written + available]
            count = self.channel.write(self, offset + bytes_written, chunk)
            bytes_written += count
        if bytes_written:
            self._offset += bytes_written
            # update the EOF marker if we write past it
            self._end_of_file = max(self.end_of_file, self._offset)
        return bytes_written

    def writable(self):
        """
        :return: True if the stream can be written to
        """
        return any(
            self._has_access(a)
            for a in (
                smb2.FILE_WRITE_DATA,
                smb2.FILE_APPEND_DATA,
                smb2.GENERIC_WRITE,
                smb2.GENERIC_ALL,
            )
        )

    def write(self, b):
        """
        Write bytes from the buffer, b.

        Note: this function may perform extra copying and could be inefficient.
        """
        return self._write_at(b, self._offset)

    def flush(self):
        """
        Issue an SMB2 FLUSH request to the server.

        This instructs the server to flush any intermediate buffers to disk.

        The server may return a response before the data has been flushed.

        For non-writable streams, this call is a no-op.
        """
        if not self.writable():
            # don't flush non-writable streams
            return
        return super(Open, self).flush()
