"""
pike.io: file-like wrapper for an open file
"""
import io

import attr

from . import smb2


@attr.s
class _Open(object):
    tree = attr.ib()
    create_request = attr.ib()
    create_response = attr.ib()
    create_guid = attr.ib()
    _previous_open = attr.ib()
    oplock_level = attr.ib(init=False)
    lease = attr.ib(init=False)
    is_resilient = attr.ib(init=False)
    is_durable = attr.ib(init=False)

    @oplock_level.default
    def _init_oplock_level(self):
        return self.create_response.oplock_level

    @lease.default
    def _init_lease(self):
        if self.oplock_level != smb2.SMB2_OPLOCK_LEVEL_NONE:
            if self.oplock_level == smb2.SMB2_OPLOCK_LEVEL_LEASE:
                for ctx in self.create_response:
                    if isinstance(ctx, smb2.LeaseResponse):
                        return self.tree.session.client.lease(self.tree, ctx)
            else:
                self.arm_oplock_future()

    @is_durable.default
    def is_durable(self):
        if self._previous_open is not None:
            return self._previous_open.is_durable
        return (
            self.durable_handle_ctx is not None
            or self.durable_handle_v2_ctx is not None
        )

    @is_resilient.default
    def is_resilient(self):
        if self._previous_open is not None:
            return self._previous_open.is_resilient
        return False

    @property
    def channel(self):
        if not self.closed:
            return self.tree.session.first_channel()
        raise ValueError("I/O operation on closed file")

    @property
    def file_id(self):
        return self.create_response.file_id

    @property
    def durable_handle_ctx(self):
        for ctx in self.create_response:
            if isinstance(ctx, smb2.DurableHandleResponse):
                return ctx

    @property
    def durable_handle_v2_ctx(self):
        for ctx in self.create_response:
            if isinstance(ctx, smb2.DurableHandleV2Response):
                return ctx

    @property
    def durable_timeout(self):
        ctx = self.durable_handle_v2_ctx
        if ctx:
            return ctx.durable_timeout
        elif self._previous_open is not None:
            return self._previous_open.durable_timeout

    @property
    def durable_flags(self):
        ctx = self.durable_handle_v2_ctx
        if ctx:
            return ctx.durable_flags
        elif self._previous_open is not None:
            return self._previous_open.durable_flags
        return 0

    @property
    def is_persistent(self):
        return self.durable_flags & smb2.SMB2_DHANDLE_FLAG_PERSISTENT != 0

    @property
    def closed(self):
        return self.tree is None

    @property
    def end_of_file(self):
        return self.create_response.end_of_file

    def arm_oplock_future(self):
        """
        (Re)arm the oplock future for this open. This function should be called
        when an oplock changes level to anything except SMB2_OPLOCK_LEVEL_NONE
        """
        self.oplock_future = self.tree.session.client.oplock_break_future(self.file_id)

    def on_oplock_break(self, cb):
        """
        Simple oplock break callback handler.
        @param cb: callable taking 1 parameter: the break request oplock level
                   should return the desired oplock level to break to
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
        @param cb: callable taking 3 parameters:
                        L{Open}
                        L{Smb2} containing the break request
                        L{object} arbitrary context
                   should handle breaking the oplock in some way
                   callback is also responsible for re-arming the future
                   and updating the oplock_level (if changed)
        """

        def handle_break(f):
            smb_res = f.result()
            cb(self, smb_res, cb_ctx)

        self.oplock_future.then(handle_break)

    def dispose(self):
        self.tree = None
        if self.lease is not None:
            self.lease.dispose()
            self.lease = None

    def close(self):
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


class CompatOpen(_Open):
    def __init__(self, tree, smb_res, create_guid=None, prev=None):
        super(CompatOpen, self).__init__(tree, smb_res[0], create_guid, prev)


@attr.s
class Open(_Open, io.RawIOBase):
    _offset = attr.ib(default=0, init=False)

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self._offset = offset
        elif whence == io.SEEK_CUR:
            self._offset += offset
        elif whence == io.SEEK_END:
            self._offset = self.end_of_file + offset
        return self._offset

    def seekable(self):
        return True

    def tell(self):
        return self._offset

    def truncate(self, size=None):
        raise NotImplementedError("truncate() not supported")

    def _has_access(self, access):
        return self.create_request.desired_access & access

    def readable(self):
        return any(
            self._has_access(a)
            for a in (smb2.FILE_READ_DATA, smb2.GENERIC_READ, smb2.GENERIC_ALL)
        )

    def _read_range(self, start=0, end=None):
        offset = start
        if end is None:
            end = self.end_of_file
        response_buffers = []
        while offset < end:
            available = min(
                self.channel.connection.credits * smb2.BYTES_PER_CREDIT,
                self.channel.connection.negotiate_response.max_read_size,
            )
            try:
                read_resp = self.channel.read(self, available, offset)
                response_buffers.append(read_resp)
                offset += len(read_resp)
            except model.ResponseError as re:
                if re.response.status == ntstatus.STATUS_END_OF_FILE:
                    return ""
                raise
        return b"".join(rb.tobytes() for rb in response_buffers)

    def readall(self):
        return self._read_range(self._offset)

    def readinto(self, b):
        read_resp = self._read_range(self._offset, len(b))
        bytes_read = len(read_resp)
        self._offset += bytes_read
        b[:bytes_read] = read_resp
        return bytes_read

    def _write_at(self, data, offset):
        n_data = len(data)
        bytes_written = 0
        while bytes_written < n_data:
            available = min(
                self.channel.connection.credits * smb2.BYTES_PER_CREDIT,
                self.channel.connection.negotiate_response.max_write_size,
            )
            chunk = data[offset + bytes_written : offset + bytes_written + available]
            count = self.channel.write(self, offset + bytes_written, chunk)
            bytes_written += count
        return bytes_written

    def writable(self):
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
        bytes_written = self._write_at(b, self._offset)
        self._offset += bytes_written
        return bytes_written
