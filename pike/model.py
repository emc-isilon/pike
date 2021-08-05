#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        model.py
#
# Abstract:
#
#        Transport and object model
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#          Masen Furer (masen.furer@dell.com)
#

"""
SMB2 Object Model.

This module contains an implementation of the SMB2 client object model,
allowing channels, sessions, tree connections, opens, and leases
to be established and tracked.  It provides convenience functions
for exercising common elements of the protocol without manually
constructing packets.
"""

from __future__ import absolute_import
from builtins import next
from builtins import map
from builtins import range
from builtins import object
from builtins import str
from future.utils import raise_
from future.utils import raise_from

import array
import contextlib
from functools import reduce
import logging
import operator
import random
import socket
import struct
import sys
import time
import warnings

from . import auth
from . import core
from . import crypto
from . import netbios
from . import nttime
from . import smb2
from . import transport
from . import ntstatus
from . import digest

default_credit_request = 10
default_timeout = 30
trace = False


def loop(timeout=None, count=None):
    """
    wrapper for blocking on the underlying event loop for the given timeout
    or given count of iterations
    """
    if timeout is None:
        timeout = default_timeout
    transport.loop(timeout=timeout, count=count)


class TimeoutError(Exception):
    """Future completion timed out"""

    future = None

    @classmethod
    def with_future(cls, future, *args):
        """
        Instantiate TimeoutError from a given future.

        :param future: Future that timed out
        :param args: passed to Exception.__init__
        :return: TimeoutError
        """
        ex = cls(*args)
        ex.future = future
        return ex

    def __str__(self):
        s = super(TimeoutError, self).__str__()
        if self.future is not None:
            if self.future.request is not None:
                requests = [str(self.future.request)]
                if not isinstance(self.future.request, (core.Frame, str, bytes)):
                    # attempt to recursively str format other iterables
                    try:
                        requests = [str(r) for r in self.future.request]
                    except TypeError:
                        pass
                s += "\nRequest: {}".format("\n".join(requests))
            if self.future.interim_response is not None:
                s += "\nInterim: {}".format(self.future.interim_response)
        return s


class StateError(Exception):
    pass


class CreditError(Exception):
    pass


class RequestError(Exception):
    def __init__(self, request, message=None):
        if message is None:
            message = "Could not send {0}".format(repr(request))
        Exception.__init__(self, message)
        self.request = request


class CallbackError(Exception):
    """
    the callback was not suitable
    """


class ResponseError(Exception):
    def __init__(self, response):
        Exception.__init__(self, response.command, response.status)
        self.response = response


class AssertNtstatusContext(object):
    response = None
    exception = None


@contextlib.contextmanager
def pike_status(exp_status):
    obj = AssertNtstatusContext()
    try:
        yield obj
        if exp_status != ntstatus.STATUS_SUCCESS:
            raise AssertionError(
                "No error raised when " "ResponseError({}) expected.".format(exp_status)
            )
    except ResponseError as err:
        obj.exception = err
        obj.response = err.response
        if err.response.status != exp_status:
            raise_from(
                AssertionError(
                    "{} raised when "
                    "expecting ResponseError({})".format(
                        err.response.status, exp_status
                    )
                ),
                err,
            )


class Events(core.ValueEnum):
    """ Events used for callback functions """

    EV_REQ_PRE_SERIALIZE = 0x1  # cb expects Netbios frame
    EV_REQ_POST_SERIALIZE = 0x2  # cb expects Netbios frame
    EV_REQ_PRE_SEND = 0x3  # cb expects a buffer to send
    EV_REQ_POST_SEND = 0x4  # cb expects an integer of bytes sent
    EV_RES_PRE_RECV = 0x5  # cb expects an integer of bytes to read
    EV_RES_POST_RECV = 0x6  # cb expects a buffer that was read
    EV_RES_PRE_DESERIALIZE = 0x7  # cb expects a complete netbios buffer
    EV_RES_POST_DESERIALIZE = 0x8  # cb expects a Netbios frame


Events.import_items(globals())


class Future(object):
    """
    Result of an asynchronous operation.

    Futures represent the result of an operation that has not yet completed.
    In Pike, they are most commonly used to track SMB2 request/response pairs,
    but they can be used for any asynchronous operation.

    The result of a future can be waited for synchronously by simply calling
    L{Future.result}, or a notification callback can be set with L{Future.then}.

    Futures implement the context manager interface so that they can be used
    as the context for a with block.  If an exception is raised from the block,
    it will automatically be set as the result of the future.

    @ivar request: The request associated with the future, usually an SMB2 request frame.
    @ivar response: The result of the future, usually an SMB2 response frame.
    @ivar interim_response: The interim response, usually an SMB2 response frame.
    @ivar traceback: The traceback of an exception result, if applicable.
    """

    def __init__(self, request=None):
        """
        Initialize future.

        @param request: The request associated with the response.
        """
        self.request = request
        self.interim_response = None
        self.response = None
        self.notify = None
        self.traceback = None

    def complete(self, response, traceback=None):
        """
        Completes the future with the given result.

        Calling a future as a function is equivalent to calling this method.

        @param response: The result of the future.
        @param traceback: If response is an exception, an optional traceback
        """
        self.response = response
        self.traceback = traceback
        if self.notify is not None:
            self.notify(self)

    def interim(self, response):
        """
        Set interim response.

        @param response: The interim response.
        """
        self.interim_response = response

    def wait(self, timeout=None):
        """
        Wait for future result to become available.

        @param timeout: The time in seconds before giving up and raising TimeoutError
        """
        if timeout is None:
            timeout = default_timeout
        deadline = time.time() + timeout
        while self.response is None:
            now = time.time()
            if now > deadline:
                raise TimeoutError.with_future(
                    self, "Timed out after %s seconds" % timeout
                )
            loop(timeout=deadline - now, count=1)

        return self

    def wait_interim(self, timeout=None):
        """
        Wait for interim response or actual result to become available.

        @param timeout: The time in seconds before giving up and raising TimeoutError
        """
        if timeout is None:
            timeout = default_timeout
        deadline = time.time() + timeout
        while self.response is None and self.interim_response is None:
            now = time.time()
            if now > deadline:
                raise TimeoutError.with_future(
                    self, "Timed out after %s seconds" % timeout
                )
            loop(timeout=deadline - now, count=1)

        return self

    def result(self, timeout=None):
        """
        Return result of future.

        If the result is not yet available, this function will wait for it.
        If the result is an exception, this function will raise it instead of
        returning it.

        @param timeout: The time in seconds before giving up and raising TimeoutError
        """
        self.wait(timeout)

        if isinstance(self.response, BaseException):
            traceback = self.traceback
            self.traceback = None
            raise_(self.response, None, traceback)
        else:
            return self.response

    def then(self, notify):
        """
        Set notification function.

        @param notify: A function which will be invoked with this future as a parameter
                       when its result becomes available.  If it is already available,
                       it will be called immediately.
        """
        if not callable(notify):
            raise CallbackError("{0} is not a callable object".format(notify))
        if self.response is not None:
            notify(self)
        else:
            self.notify = notify

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.complete(exc_value, traceback)
            return True

    def __call__(self, *params, **kwparams):
        self.complete(*params, **kwparams)


class Client(object):
    """
    Client

    Maintains all state associated with an SMB2/3 client.

    @type dialects: [number]
    @ivar dialects: A list of supported dialects
    @ivar capabilities: Capabilities flags
    @ivar security_mode: Security mode flags
    @ivar client_guid: Client GUID
    @ivar channel_sequence: Current channel sequence number
    """

    def __init__(
        self,
        dialects=[
            smb2.DIALECT_SMB2_002,
            smb2.DIALECT_SMB2_1,
            smb2.DIALECT_SMB3_0,
            smb2.DIALECT_SMB3_0_2,
            smb2.DIALECT_SMB3_1_1,
        ],
        capabilities=smb2.GlobalCaps(reduce(operator.or_, smb2.GlobalCaps.values())),
        security_mode=smb2.SMB2_NEGOTIATE_SIGNING_ENABLED,
        client_guid=None,
    ):
        """
        Constructor.

        @type dialects: [number]
        @param dialects: A list of supported dialects.
        @param capabilities: Client capabilities flags
        @param security_mode: Client security mode flags
        @param client_guid: Client GUID.  If None, a new one will be generated at random.
        """
        object.__init__(self)

        if client_guid is None:
            client_guid = array.array("B", map(random.randint, [0] * 16, [255] * 16))

        self.dialects = dialects
        self.capabilities = capabilities
        self.security_mode = security_mode
        self.client_guid = client_guid
        self.channel_sequence = 0
        self.callbacks = {}
        self._oplock_break_map = {}
        self._lease_break_map = {}
        self._oplock_break_queue = []
        self._lease_break_queue = []
        self._connections = []
        self._leases = {}

        self.logger = logging.getLogger("pike")

    @contextlib.contextmanager
    def callback(self, event, cb):
        """
        Register a callback function for the context block, then unregister it
        """
        self.register_callback(event, cb)
        try:
            yield
        finally:
            self.unregister_callback(event, cb)

    def register_callback(self, event, cb):
        """
        Registers a callback function, cb for the given event.
        When the event fires, cb will be called with the relevant top-level
        Netbios frame as the single paramter.
        """
        ev = Events(event)
        if ev not in self.callbacks:
            self.callbacks[ev] = []
        self.callbacks[ev].append(cb)

    def unregister_callback(self, event, cb):
        """
        Unregisters a callback function, cb for the given event.
        """
        ev = Events(event)
        if ev not in self.callbacks:
            return
        if cb not in self.callbacks[ev]:
            return
        self.callbacks[ev].remove(cb)

    def restrict_dialects(self, min_dialect=None, max_dialect=None):
        """
        Update the list of SMB2 dialects this Client will advertise support for.

        This call will only remove dialects from the list.

        Dialects should be from pike.smb2.Dialect enum, but technically may be any
        int or float.

        If either of min_dialect or max_dialect is None, the minimum or maximum dialect
        supported will be used.

        @param min_dialect: The minimum dialect to support (inclusive)
        @param max_dialect: The maximum dialect to support (inclusive)
        """
        if min_dialect is None:
            min_dialect = min(smb2.Dialect.values())
        if max_dialect is None:
            max_dialect = max(smb2.Dialect.values())
        self.dialects = [d for d in self.dialects if min_dialect <= d <= max_dialect]

    def connect(self, server, port=445):
        """
        Create a connection.

        Returns a new L{Connection} object connected to the given server and port.

        @param server: The server to connect to.
        @param port: The port to connect to.
        """
        return self.connect_submit(server, port).result()

    def connect_submit(self, server, port=445):
        """
        Create a connection.

        Returns a new L{Future} object for the L{Connection} being established
        asynchronously to the given server and port.

        @param server: The server to connect to.
        @param port: The port to connect to.
        """
        return Connection(self, server, port).connection_future

    # Do not use, may be removed.  Use oplock_break_future.
    def next_oplock_break(self):
        while len(self._oplock_break_queue) == 0:
            loop(count=1)
        return self._oplock_break_queue.pop()

    # Do not use, may be removed.  Use lease_break_future.
    def next_lease_break(self):
        while len(self._lease_break_queue) == 0:
            loop(count=1)
        return self._lease_break_queue.pop()

    def oplock_break_future(self, file_id):
        """
        Create future for oplock break.

        Returns a L{Future} object which will be completed when
        an oplock break occurs.  The result will be the L{smb2.Smb2} frame
        of the break notification packet.

        @type file_id: (number, number)
        @param file_id: The file ID of the oplocked file.
        """

        future = Future(request=("OplockBreak", file_id))

        for smb_res in self._oplock_break_queue[:]:
            if smb_res[0].file_id == file_id:
                future.complete(smb_res)
                self._oplock_break_queue.remove(smb_res)
                break

        if future.response is None:
            self._oplock_break_map[file_id] = future

        return future

    def lease_break_future(self, lease_key):
        """
        Create future for lease break.

        Returns a L{Future} object which will be completed when
        a lease break occurs.  The result will be the L{smb2.Smb2} frame
        of the break notification packet.

        @param lease_key: The lease key for the lease.
        """

        future = Future(request=("LeaseBreak", core.Frame._value_str(lease_key)))

        for smb_res in self._lease_break_queue[:]:
            if smb_res[0].lease_key == lease_key:
                future.complete(smb_res)
                self._lease_break_queue.remove(smb_res)
                break

        if future.response is None:
            self._lease_break_map[lease_key.tobytes()] = future

        return future

    def oplock_break(self, file_id):
        """
        Wait for and return oplock break notification.

        Equivalent to L{oplock_break_future}(file_id).result()
        """

        return self.oplock_break_future(file_id).result()

    def lease_break(self, lease_key):
        """
        Wait for and return lease break notification.

        Equivalent to L{lease_break_future}(lease_key).result()
        """

        return self.lease_break_future(lease_key).result()

    def lease(self, tree, lease_res):
        """
        Create or look up lease object.

        Returns a lease object based on a L{Tree} and a
        L{smb2.LeaseResponse}.  The lease object is created
        if it does not already exist.

        @param tree: The tree on which the lease request was issued.
        @param lease_res: The lease create context response.
        """

        lease_key = lease_res.lease_key.tobytes()
        if lease_key not in self._leases:
            lease = Lease(tree)
            self._leases[lease_key] = lease
        else:
            lease = self._leases[lease_key]
            lease.ref()

        lease.update(lease_res)
        return lease

    # Internal function to remove lease from table
    def dispose_lease(self, lease):
        del self._leases[lease.lease_key.tobytes()]


class Connection(transport.Transport):
    """
    Connection to server.

    Represents a connection to a server and handles all socket operations
    and request/response dispatch.

    @type client: Client
    @ivar client: The Client object associated with this connection.
    @ivar server: The server name or address
    @ivar port: The server port
    """

    def __init__(self, client, server, port=445):
        """
        Constructor.

        This should generally not be used directly.  Instead,
        use L{Client.connect}().
        """
        super(Connection, self).__init__()
        self._no_delay = True
        self._in_buffer = array.array("B")
        self._watermark = 4
        self._out_buffer = None
        self._next_mid = 0
        self._mid_blacklist = set()
        self._out_queue = []
        self._future_map = {}
        self._sessions = {}
        self._binding = None
        self._binding_key = None
        self._settings = {}
        self._pre_auth_integrity_hash = array.array("B", b"\0" * 64)
        self._negotiate_request = None
        self._negotiate_response = None
        self.callbacks = {}
        self.connection_future = Future(request=(server, port))
        self.credits = 0
        self.client = client
        self.server = server
        self.port = port
        self.remote_addr = None
        self.local_addr = None
        self.verify_signature = True

        self.error = None
        self.traceback = None

        for result in socket.getaddrinfo(
            server, port, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP
        ):
            family, socktype, proto, canonname, sockaddr = result
            break
        self.create_socket(family, socktype)
        self.connect(sockaddr)

    @contextlib.contextmanager
    def callback(self, event, cb):
        """
        Register a callback function for the context block, then unregister it
        """
        self.register_callback(event, cb)
        try:
            yield
        finally:
            self.unregister_callback(event, cb)

    def register_callback(self, event, cb):
        """
        Registers a callback function, cb for the given event.
        When the event fires, cb will be called with the relevant top-level
        Netbios frame as the single paramter.
        """
        ev = Events(event)
        if ev not in self.callbacks:
            self.callbacks[ev] = []
        self.callbacks[ev].append(cb)

    def unregister_callback(self, event, cb):
        """
        Unregisters a callback function, cb for the given event.
        """
        ev = Events(event)
        if ev not in self.callbacks:
            return
        if cb not in self.callbacks[ev]:
            return
        self.callbacks[ev].remove(cb)

    def process_callbacks(self, event, obj):
        """
        Fire callbacks for the given event, passing obj as the parameter

        Connection-specific callbacks will be fired first, followed by client
        callbacks
        """
        ev = Events(event)
        all_callbacks = [self.callbacks]
        if hasattr(self.client, "callbacks"):
            all_callbacks.append(self.client.callbacks)
        for callbacks in all_callbacks:
            if ev not in callbacks:
                continue
            for cb in callbacks[ev]:
                cb(obj)

    @property
    def negotiate_response(self):
        return self._negotiate_response

    @negotiate_response.setter
    def negotiate_response(self, value):
        if self._negotiate_response is not None:
            raise AssertionError("Attempting to overwrite negotiate response")
        self._negotiate_response = value
        # pre-auth integrity hash processing
        if value.dialect_revision < smb2.DIALECT_SMB3_1_1:
            return
        self._pre_auth_integrity_hash = digest.smb3_sha512(
            self._pre_auth_integrity_hash + self._negotiate_request.parent.serialize()
        )
        self._pre_auth_integrity_hash = digest.smb3_sha512(
            self._pre_auth_integrity_hash + value.parent.parent.buf[4:]
        )

    @property
    def dialect_revision(self):
        return (
            self.negotiate_response.dialect_revision
            if self.negotiate_response is not None
            else 0x0
        )

    def next_mid_range(self, length):
        """
        multicredit requests must reserve 1 message id per credit charged.
        the message id of the request should be the first id of the range.
        """
        if length < 1:
            length = 1
        start_range = self._next_mid
        while True:
            r = set(range(start_range, start_range + length))
            if not r.intersection(self._mid_blacklist):
                break
            start_range += 1
        self._next_mid = sorted(list(r))[-1] + 1
        return start_range

    def next_mid(self):
        return self.next_range(1)

    def reserve_mid(mid):
        self._mid_blacklist.add(mid)

    def handle_connect(self):
        self.client._connections.append(self)
        with self.connection_future:
            self.local_addr = self.socket.getsockname()
            self.remote_addr = self.socket.getpeername()

            self.client.logger.debug(
                "connect: %s/%s -> %s/%s",
                self.local_addr[0],
                self.local_addr[1],
                self.remote_addr[0],
                self.remote_addr[1],
            )
        self.connection_future(self)

    def handle_read(self):
        # Try to read the next netbios frame
        remaining = self._watermark - len(self._in_buffer)
        self.process_callbacks(EV_RES_PRE_RECV, remaining)
        data = array.array("B", self.recv(remaining))
        self.process_callbacks(EV_RES_POST_RECV, data)
        self._in_buffer.extend(data)
        avail = len(self._in_buffer)
        if avail >= 4:
            self._watermark = 4 + struct.unpack(">L", self._in_buffer[0:4])[0]
        if avail == self._watermark:
            nb = self.frame()
            self.process_callbacks(EV_RES_PRE_DESERIALIZE, self._in_buffer)
            nb.parse(self._in_buffer)
            self._in_buffer = array.array("B")
            self._watermark = 4
            self._dispatch_incoming(nb)

    def handle_write(self):
        # Try to write out more data
        while self._out_buffer is None and len(self._out_queue):
            self._out_buffer = self._prepare_outgoing()
            while self._out_buffer is not None:
                self.process_callbacks(EV_REQ_PRE_SEND, self._out_buffer)
                sent = self.send(self._out_buffer)
                del self._out_buffer[:sent]
                if len(self._out_buffer) == 0:
                    self._out_buffer = None
                self.process_callbacks(EV_REQ_POST_SEND, sent)

    def handle_close(self):
        self.close()

    def handle_error(self):
        (_, self.error, self.traceback) = sys.exc_info()
        self.close()

    def close(self):
        """
        Close connection.

        This unceremoniously terminates the connection and fails all
        outstanding requests with EOFError.
        """
        # If there is no error, propagate EOFError
        if self.error is None:
            self.error = EOFError("close")

        # if the connection hasn't been established, raise the error
        if self.connection_future.response is None:
            self.connection_future(self.error)

        # otherwise, ignore this connection since it's not associated with its client
        if self not in self.client._connections:
            return

        super(Connection, self).close()

        if self.remote_addr is not None:
            self.client.logger.debug(
                "disconnect (%s/%s -> %s/%s): %s",
                self.local_addr[0],
                self.local_addr[1],
                self.remote_addr[0],
                self.remote_addr[1],
                self.error,
            )

        self.client._connections.remove(self)

        for future in self._out_queue:
            future.complete(self.error, self.traceback)
        del self._out_queue[:]

        for future in self._future_map.values():
            future.complete(self.error, self.traceback)
        self._future_map.clear()

        for session in list(self._sessions.values()):
            session.delchannel(self)

        self.traceback = None

    def _prepare_outgoing(self):
        # Try to prepare an outgoing packet

        # Grab an outgoing smb2 request
        future = self._out_queue[0]

        result = None
        with future:
            req = future.request
            self.process_callbacks(EV_REQ_PRE_SERIALIZE, req.parent)

            if req.credit_charge is None:
                req.credit_charge = 0
                for cmd in req:
                    if isinstance(cmd, smb2.ReadRequest) and cmd.length > 0:
                        # special handling, 1 credit per 64k
                        req.credit_charge, remainder = divmod(cmd.length, 2 ** 16)
                    elif isinstance(cmd, smb2.WriteRequest) and cmd.buffer is not None:
                        # special handling, 1 credit per 64k
                        if cmd.length is None:
                            cmd.length = len(cmd.buffer)
                        req.credit_charge, remainder = divmod(cmd.length, 2 ** 16)
                    else:
                        remainder = 1  # assume 1 credit per command
                    if remainder > 0:
                        req.credit_charge += 1
            # do credit accounting based on our calculations (MS-SMB2 3.2.5.1)
            self.credits -= req.credit_charge

            if req.credit_request is None:
                req.credit_request = default_credit_request
                if req.credit_charge > req.credit_request:
                    req.credit_request = req.credit_charge  # try not to fall behind

            del self._out_queue[0]

            # Assign message id
            if req.message_id is None:
                req.message_id = self.next_mid_range(req.credit_charge)

            if req.is_last_child():
                # Last command in chain, ready to send packet
                result = req.parent.serialize()
                self.process_callbacks(EV_REQ_POST_SERIALIZE, req.parent)
                if trace:
                    self.client.logger.debug(
                        "send (%s/%s -> %s/%s): %s",
                        self.local_addr[0],
                        self.local_addr[1],
                        self.remote_addr[0],
                        self.remote_addr[1],
                        req.parent,
                    )
                else:
                    self.client.logger.debug(
                        "send (%s/%s -> %s/%s): %s",
                        self.local_addr[0],
                        self.local_addr[1],
                        self.remote_addr[0],
                        self.remote_addr[1],
                        req.parent._log_str(),
                    )
            else:
                # Not ready to send chain
                result = None

            # Move it to map for response waiters (but not cancel)
            if not isinstance(req[0], smb2.Cancel):
                self._future_map[req.message_id] = future

        return result

    def _find_oplock_future(self, file_id):
        if file_id in self.client._oplock_break_map:
            return self.client._oplock_break_map.pop(file_id)
        return None

    def _find_lease_future(self, lease_key):
        lease_key = lease_key.tobytes()
        if lease_key in self.client._lease_break_map:
            return self.client._lease_break_map.pop(lease_key)
        return None

    def _dispatch_incoming(self, res):
        if trace:
            self.client.logger.debug(
                "recv (%s/%s -> %s/%s): %s",
                self.remote_addr[0],
                self.remote_addr[1],
                self.local_addr[0],
                self.local_addr[1],
                res,
            )
        else:
            self.client.logger.debug(
                "recv (%s/%s -> %s/%s): %s",
                self.remote_addr[0],
                self.remote_addr[1],
                self.local_addr[0],
                self.local_addr[1],
                res._log_str(),
            )
        self.process_callbacks(EV_RES_POST_DESERIALIZE, res)
        for smb_res in res:
            # TODO: move credit tracking to callbacks
            self.credits += smb_res.credit_response

            # Verify non-session-setup-response signatures
            # session setup responses are verified in SessionSetupContext
            if not isinstance(smb_res[0], smb2.SessionSetupResponse):
                key = self.signing_key(smb_res.session_id)
                if key and self.verify_signature:
                    smb_res.verify(self.signing_digest(), key)

            if smb_res.message_id == smb2.UNSOLICITED_MESSAGE_ID:
                if isinstance(smb_res[0], smb2.OplockBreakNotification):
                    future = self._find_oplock_future(smb_res[0].file_id)
                    if future:
                        future.complete(smb_res)
                    else:
                        self.client._oplock_break_queue.append(smb_res)
                elif isinstance(smb_res[0], smb2.LeaseBreakNotification):
                    future = self._find_lease_future(smb_res[0].lease_key)
                    if future:
                        future.complete(smb_res)
                    else:
                        self.client._lease_break_queue.append(smb_res)
                else:
                    raise core.BadPacket()
            elif smb_res.message_id in self._future_map:
                future = self._future_map[smb_res.message_id]
                if smb_res.status == ntstatus.STATUS_PENDING:
                    future.interim(smb_res)
                elif (
                    isinstance(smb_res[0], smb2.ErrorResponse)
                    or smb_res.status not in smb_res[0].allowed_status
                ):
                    future.complete(ResponseError(smb_res))
                    del self._future_map[smb_res.message_id]
                else:
                    future.complete(smb_res)
                    del self._future_map[smb_res.message_id]

    def submit(self, req):
        """
        Submit request.

        Submits a L{netbios.Netbios} frame for sending.  Returns
        a list of L{Future} objects, one for each corresponding
        L{smb2.Smb2} frame in the request.
        """
        if not isinstance(req, netbios.Netbios):
            raise RequestError(
                req, "{0} is not a netbios.Netbios frame".format(repr(req))
            )
        if self.error is not None:
            raise_(self.error, None, self.traceback)
        futures = []
        for smb_req in req:
            if isinstance(smb_req[0], smb2.Cancel):
                # Find original future being canceled to return
                if smb_req.async_id is not None:
                    # Cancel by async ID
                    future = [
                        f
                        for f in iter(self._future_map.values())
                        if f.interim_response.async_id == smb_req.async_id
                    ][0]
                elif smb_req.message_id in self._future_map:
                    # Cancel by message id, already in future map
                    future = self._future_map[smb_req.message_id]
                else:
                    # Cancel by message id, still in send queue
                    future = [
                        f
                        for f in self._out_queue
                        if f.request.message_id == smb_req.message_id
                    ][0]
                # Add fake future for cancel since cancel has no response
                self._out_queue.append(Future(request=smb_req))
                futures.append(future)
            else:
                future = Future(request=smb_req)
                self._out_queue.append(future)
                futures.append(future)

        # don't wait for the callback, send the data now
        if self._no_delay:
            self.handle_write()
        return futures

    def transceive(self, req):
        """
        Submit request and wait for responses.

        Submits a L{netbios.Netbios} frame for sending.  Waits for
        and returns a list of L{smb2.Smb2} response objects, one for each
        corresponding L{smb2.Smb2} frame in the request.
        """
        return [f.result() for f in self.submit(req)]

    def negotiate_request(self, hash_algorithms=None, salt=None, ciphers=None):
        smb_req = self.request()
        smb_req.credit_charge = 0  # negotiate requests are free
        neg_req = smb2.NegotiateRequest(smb_req)

        neg_req.dialects = self.client.dialects
        neg_req.security_mode = self.client.security_mode
        neg_req.capabilities = self.client.capabilities
        neg_req.client_guid = self.client.client_guid

        if smb2.DIALECT_SMB3_1_1 in neg_req.dialects:
            if ciphers is None:
                ciphers = [crypto.SMB2_AES_128_GCM, crypto.SMB2_AES_128_CCM]
            if ciphers:
                encryption_req = crypto.EncryptionCapabilitiesRequest(neg_req)
                encryption_req.ciphers = ciphers

            preauth_integrity_req = smb2.PreauthIntegrityCapabilitiesRequest(neg_req)
            if hash_algorithms is None:
                hash_algorithms = [smb2.SMB2_SHA_512]
            preauth_integrity_req.hash_algorithms = hash_algorithms
            if salt is not None:
                preauth_integrity_req.salt = salt
            else:
                preauth_integrity_req.salt = array.array(
                    "B", map(random.randint, [0] * 32, [255] * 32)
                )
        self._negotiate_request = neg_req
        return neg_req

    def negotiate_submit(self, negotiate_request):
        negotiate_future = self.submit(negotiate_request.parent.parent)[0]

        def assign_response(f):
            self.negotiate_response = f.result()[0]

        negotiate_future.then(assign_response)
        return negotiate_future

    def negotiate(self, hash_algorithms=None, salt=None, ciphers=None):
        """
        Perform dialect negotiation.

        This must be performed before setting up a session with
        L{Connection.session_setup}().
        """
        self.negotiate_submit(
            self.negotiate_request(hash_algorithms, salt, ciphers)
        ).result()
        return self

    class SessionSetupContext(object):
        def __init__(self, conn, creds=None, bind=None, resume=None, ntlm_version=None):
            assert conn.negotiate_response is not None

            self.conn = conn
            self.dialect_revision = conn.negotiate_response.dialect_revision
            self.bind = bind
            self.resume = resume
            self._pre_auth_integrity_hash = conn._pre_auth_integrity_hash[:]

            if creds and auth.ntlm is not None:
                self.auth = auth.NtlmProvider(conn, creds)
                if ntlm_version is not None:
                    self.auth.authenticator.ntlm_version = ntlm_version
            elif auth.kerberos is not None:
                self.auth = auth.KerberosProvider(conn, creds)
            else:
                raise ImportError(
                    "Neither ntlm nor kerberos authentication methods are available"
                )

            self._settings = {}
            self.prev_session_id = 0
            self.session_id = 0
            self.requests = []
            self.responses = []
            self.session_future = Future(request=self.requests)
            self.interim_future = None

            if bind:
                assert conn.negotiate_response.dialect_revision >= 0x300
                self.session_id = bind.session_id
                conn._binding = bind
                # assume the signing key from the previous session
                conn._binding_key = bind.first_channel().signing_key
            elif resume:
                assert conn.negotiate_response.dialect_revision >= 0x300
                self.prev_session_id = resume.session_id

        def let(self, **kwargs):
            return core.Let(self, kwargs)

        def derive_signing_key(self, session_key=None, context=None):
            if session_key is None:
                session_key = self.session_key
            if self.dialect_revision >= smb2.DIALECT_SMB3_1_1:
                if context is None:
                    context = self._pre_auth_integrity_hash
                return digest.derive_key(session_key, b"SMBSigningKey", context)[:16]
            elif self.dialect_revision >= smb2.DIALECT_SMB3_0:
                if context is None:
                    context = b"SmbSign\0"
                return digest.derive_key(session_key, b"SMB2AESCMAC", context)[:16]
            else:
                return session_key

        def derive_encryption_keys(self, session_key=None, context=None):
            if self.dialect_revision >= smb2.DIALECT_SMB3_1_1:
                if context is None:
                    context = self._pre_auth_integrity_hash
                for nctx in self.conn.negotiate_response:
                    if isinstance(nctx, crypto.EncryptionCapabilitiesResponse):
                        try:
                            return crypto.EncryptionContext(
                                crypto.CryptoKeys311(self.session_key, context),
                                nctx.ciphers,
                            )
                        except crypto.CipherMismatch:
                            pass
            elif self.dialect_revision >= smb2.DIALECT_SMB3_0:
                if (
                    self.conn.negotiate_response.capabilities
                    & smb2.SMB2_GLOBAL_CAP_ENCRYPTION
                ):
                    return crypto.EncryptionContext(
                        crypto.CryptoKeys300(self.session_key),
                        [crypto.SMB2_AES_128_CCM],
                    )

        def _update_pre_auth_integrity(self, packet, data=None):
            if smb2.DIALECT_SMB3_1_1 not in self.conn.client.dialects:
                # hash only applies if client requests 3.1.1
                return
            neg_resp = self.conn.negotiate_response
            if (
                neg_resp is not None
                and neg_resp.dialect_revision < smb2.DIALECT_SMB3_1_1
            ):
                # hash only applies if server negotiates 3.1.1
                return
            if data is None:
                data = packet.serialize()
            self._pre_auth_integrity_hash = digest.smb3_sha512(
                self._pre_auth_integrity_hash + data
            )

        def _send_session_setup(self, sec_buf):
            smb_req = self.conn.request()
            session_req = smb2.SessionSetupRequest(smb_req)

            smb_req.session_id = self.session_id
            session_req.previous_session_id = self.prev_session_id
            session_req.security_mode = smb2.SMB2_NEGOTIATE_SIGNING_ENABLED
            session_req.security_buffer = sec_buf
            if self.bind:
                smb_req.flags = smb2.SMB2_FLAGS_SIGNED
                session_req.flags = smb2.SMB2_SESSION_FLAG_BINDING

            for (attr, value) in self._settings.items():
                setattr(session_req, attr, value)

            self.requests.append(smb_req)
            return self.conn.submit(smb_req.parent)[0]

        def _finish(self, smb_res):
            sec_buf = smb_res[0].security_buffer
            out_buf, self.session_key = self.auth.step(sec_buf)
            signing_key = self.derive_signing_key()
            encryption_context = self.derive_encryption_keys()

            # Verify final signature
            smb_res.verify(self.conn.signing_digest(), signing_key)

            if self.bind:
                self.conn._binding = None
                self.conn._binding_key = None
                session = self.bind
            else:
                session = Session(
                    self.conn.client,
                    self.session_id,
                    self.session_key,
                    encryption_context,
                    smb_res,
                )
                session.user = self.auth.username()

            return session.addchannel(self.conn, signing_key)

        def __iter__(self):
            return self

        def submit(self, f=None):
            """
            Submit rounds of SessionSetupRequests

            Returns a L{Future} object, for the L{Channel} object
            """
            try:
                res = next(self)
                res.then(self.submit)
            except StopIteration:
                pass
            return self.session_future

        def __next__(self):
            with self.session_future:
                res = self._process()
                if res is not None:
                    return res
            raise StopIteration()

        def _process(self):
            out_buf = None
            if not self.interim_future and not self.responses:
                # send the initial request
                out_buf, self.session_key = self.auth.step(
                    self.conn.negotiate_response.security_buffer
                )

            elif self.interim_future:
                # handle pre-auth integrity on the previous request
                previous_request = self.requests[-1]
                self._update_pre_auth_integrity(previous_request)

                smb_res = self.interim_future.result()
                self.interim_future = None
                self.responses.append(smb_res)
                self.session_id = smb_res.session_id

                if smb_res.status == ntstatus.STATUS_SUCCESS:
                    # session is established
                    with self.session_future:
                        self.session_future(self._finish(smb_res))
                    return self.session_future
                else:
                    # process interim request
                    self._update_pre_auth_integrity(smb_res, smb_res.parent.buf[4:])
                    session_res = smb_res[0]
                    if self.bind:
                        # Need to verify intermediate signatures
                        smb_res.verify(
                            self.conn.signing_digest(), self.conn._binding_key
                        )
                    out_buf, self.session_key = self.auth.step(
                        session_res.security_buffer
                    )
            if out_buf:
                # submit additional requests if necessary
                self.interim_future = self._send_session_setup(out_buf)
                return self.interim_future

    def session_setup(self, creds=None, bind=None, resume=None):
        """
        Establish a session.

        Establishes a session, performing GSS rounds as necessary.  Returns
        a L{Channel} object which can be used for further requests on the given
        connection and session.

        @type creds: str
        @param creds: A set of credentials of the form '<domain>\<user>%<password>'.
                      If specified, NTLM authentication will be used.  If None,
                      Kerberos authentication will be attempted.
        @type bind: L{Session}
        @param bind: An existing session to bind.
        @type resume: L{Session}
        @param resume: An previous session to resume.
        """
        session_context = self.SessionSetupContext(self, creds, bind, resume)
        return session_context.submit().result()

    # Return a fresh netbios frame with connection as context
    def frame(self):
        return netbios.Netbios(context=self)

    # Return a fresh smb2 frame with connection as context
    # Put it in a netbios frame automatically if none given
    def request(self, parent=None):
        if parent is None:
            parent = self.frame()
        req = smb2.Smb2(parent, context=self)
        req.channel_sequence = self.client.channel_sequence

        for (attr, value) in self._settings.items():
            setattr(req, attr, value)

        return req

    def let(self, **kwargs):
        return core.Let(self, kwargs)

    #
    # SMB2 context upcalls
    #
    def session(self, session_id):
        return self._sessions.get(session_id, None)

    def signing_key(self, session_id):
        if session_id in self._sessions:
            session = self._sessions[session_id]
            channel = session._channels[id(self)]
            return channel.signing_key
        elif self._binding and self._binding.session_id == session_id:
            return self._binding_key

    def encryption_context(self, session_id):
        if session_id in self._sessions:
            session = self._sessions[session_id]
            return session.encryption_context

    def signing_digest(self):
        assert self.negotiate_response is not None
        if self.negotiate_response.dialect_revision >= smb2.DIALECT_SMB3_0:
            return digest.aes128_cmac
        else:
            return digest.sha256_hmac

    def get_request(self, message_id):
        if message_id in self._future_map:
            return self._future_map[message_id].request
        else:
            return None


class Session(object):
    def __init__(self, client, session_id, session_key, encryption_context, smb_res):
        object.__init__(self)
        self.client = client
        self.session_id = session_id
        self.session_key = session_key
        self.encryption_context = encryption_context
        self.encrypt_data = False
        if (
            smb_res[0].session_flags & smb2.SMB2_SESSION_FLAG_ENCRYPT_DATA
            and self.encryption_context is not None
        ):
            self.encrypt_data = True
        self._channels = {}
        self._trees = {}
        self.user = None

    def addchannel(self, conn, signing_key):
        channel = Channel(conn, self, signing_key)
        self._channels[id(conn)] = channel
        conn._sessions[self.session_id] = self
        return channel

    def delchannel(self, conn):
        del conn._sessions[self.session_id]
        del self._channels[id(conn)]

    def first_channel(self):
        return next(iter(self._channels.values()))

    def tree(self, tree_id):
        return self._trees.get(tree_id, None)


class Channel(object):
    def __init__(self, connection, session, signing_key):
        object.__init__(self)
        self.connection = connection
        self.session = session
        self.signing_key = signing_key

    def cancel_request(self, future):
        if future.response is not None:
            raise StateError("Cannot cancel completed request")

        smb_req = self.request()
        cancel_req = smb2.Cancel(smb_req)

        # Don't bother trying to sign cancel
        smb_req.flags &= ~smb2.SMB2_FLAGS_SIGNED

        # Use async id to cancel if applicable:
        if future.interim_response is not None:
            smb_req.async_id = future.interim_response.async_id
            smb_req.tree_id = None
            smb_req.flags |= smb2.SMB2_FLAGS_ASYNC_COMMAND
            smb_req.message_id = 0
        else:
            smb_req.message_id = future.request.message_id

        return cancel_req

    def cancel(self, future):
        cancel_req = self.cancel_request(future)
        return self.connection.submit(cancel_req.parent.parent)[0]

    def tree_connect_request(self, path):
        smb_req = self.request()
        if self.connection.negotiate_response.dialect_revision >= smb2.DIALECT_SMB3_1_1:
            smb_req.flags |= smb2.SMB2_FLAGS_SIGNED
        tree_req = smb2.TreeConnectRequest(smb_req)
        tree_req.path = "\\\\" + self.connection.server + "\\" + path
        return tree_req

    def tree_connect_submit(self, tree_req):
        tree_future = Future(request=tree_req.parent)
        resp_future = self.connection.submit(tree_req.parent.parent)[0]
        resp_future.then(
            lambda f: tree_future.complete(
                Tree(self.session, tree_req.path, f.result())
            )
        )
        return tree_future

    def tree_connect(self, path):
        return self.tree_connect_submit(self.tree_connect_request(path)).result()

    def tree_disconnect_request(self, tree):
        smb_req = self.request(obj=tree)
        tree_req = smb2.TreeDisconnectRequest(smb_req)
        return tree_req

    def tree_disconnect(self, tree):
        return self.connection.transceive(
            self.tree_disconnect_request(tree).parent.parent
        )[0]

    def logoff_request(self):
        smb_req = self.request()
        logoff_req = smb2.LogoffRequest(smb_req)
        return logoff_req

    def logoff_submit(self, logoff_req):
        def logoff_finish(f):
            for channel in self.session._channels.values():
                del channel.connection._sessions[self.session.session_id]

        logoff_future = self.connection.submit(logoff_req.parent.parent)[0]
        logoff_future.then(logoff_finish)
        return logoff_future

    def logoff(self):
        return self.logoff_submit(self.logoff_request()).result()

    def create_request(
        self,
        tree,
        path,
        access=smb2.GENERIC_READ | smb2.GENERIC_WRITE,
        attributes=smb2.FILE_ATTRIBUTE_NORMAL,
        share=0,
        disposition=smb2.FILE_OPEN_IF,
        options=0,
        maximal_access=None,
        oplock_level=smb2.SMB2_OPLOCK_LEVEL_NONE,
        lease_key=None,
        lease_state=None,
        durable=False,
        persistent=False,
        create_guid=None,
        app_instance_id=None,
        query_on_disk_id=False,
        extended_attributes=None,
        timewarp=None,
    ):

        prev_open = None

        smb_req = self.request(obj=tree)
        create_req = smb2.CreateRequest(smb_req)

        create_req.name = path
        create_req.desired_access = access
        create_req.file_attributes = attributes
        create_req.share_access = share
        create_req.create_disposition = disposition
        create_req.create_options = options
        create_req.requested_oplock_level = oplock_level

        if maximal_access:
            max_req = smb2.MaximalAccessRequest(create_req)
            if maximal_access is not True:
                max_req.timestamp = maximal_access

        if oplock_level == smb2.SMB2_OPLOCK_LEVEL_LEASE:
            if lease_key is None:
                lease_key = crypto.random_bytes(16)
            if lease_state is None:
                lease_state = smb2.SMB2_LEASE_RWH
            lease_req = smb2.LeaseRequest(create_req)
            lease_req.lease_key = lease_key
            lease_req.lease_state = lease_state

        if isinstance(durable, Open):
            prev_open = durable
            if durable.durable_timeout is None:
                durable_req = smb2.DurableHandleReconnectRequest(create_req)
                durable_req.file_id = durable.file_id
            else:
                durable_req = smb2.DurableHandleReconnectV2Request(create_req)
                durable_req.file_id = durable.file_id
                durable_req.create_guid = durable.create_guid
                durable_req.flags = durable.durable_flags
        elif durable is True:
            durable_req = smb2.DurableHandleRequest(create_req)
        elif durable is not False:
            durable_req = smb2.DurableHandleV2Request(create_req)
            durable_req.timeout = durable
            if persistent:
                durable_req.flags = smb2.SMB2_DHANDLE_FLAG_PERSISTENT
            if create_guid is None:
                create_guid = array.array(
                    "B", map(random.randint, [0] * 16, [255] * 16)
                )
            durable_req.create_guid = create_guid

        if app_instance_id:
            app_instance_id_req = smb2.AppInstanceIdRequest(create_req)
            app_instance_id_req.app_instance_id = app_instance_id

        if query_on_disk_id:
            query_on_disk_id_req = smb2.QueryOnDiskIDRequest(create_req)

        if extended_attributes:
            ext_attr_len = len(extended_attributes)
            for name, value in extended_attributes.items():
                ext_attr = smb2.ExtendedAttributeRequest(create_req)
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

        if timewarp:
            timewarp_req = smb2.TimewarpTokenRequest(create_req)
            timewarp_req.timestamp = nttime.NtTime(timewarp)

        open_future = Future(request=create_req.parent)

        def finish(f):
            with open_future:
                open_future(
                    Open(tree, f.result(), create_guid=create_guid, prev=prev_open)
                )

        create_req.open_future = open_future
        create_req.finish = finish

        return create_req

    def create_submit(self, create_req):
        open_future = create_req.open_future
        open_future.request_future = self.connection.submit(create_req.parent.parent)[0]
        open_future.request_future.then(create_req.finish)

        return open_future

    def create(
        self,
        tree,
        path,
        access=smb2.GENERIC_READ | smb2.GENERIC_WRITE,
        attributes=smb2.FILE_ATTRIBUTE_NORMAL,
        share=0,
        disposition=smb2.FILE_OPEN_IF,
        options=0,
        maximal_access=None,
        oplock_level=smb2.SMB2_OPLOCK_LEVEL_NONE,
        lease_key=None,
        lease_state=None,
        durable=False,
        persistent=False,
        create_guid=None,
        app_instance_id=None,
        query_on_disk_id=False,
        extended_attributes=None,
        timewarp=None,
    ):
        return self.create_submit(
            self.create_request(
                tree,
                path,
                access,
                attributes,
                share,
                disposition,
                options,
                maximal_access,
                oplock_level,
                lease_key,
                lease_state,
                durable,
                persistent,
                create_guid,
                app_instance_id,
                query_on_disk_id,
                extended_attributes,
                timewarp,
            )
        )

    def close_request(self, handle):
        smb_req = self.request(obj=handle)
        close_req = smb2.CloseRequest(smb_req)

        close_req.file_id = handle.file_id
        close_req.handle = handle
        return close_req

    def close_submit(self, close_req):
        resp_future = self.connection.submit(close_req.parent.parent)[0]
        resp_future.then(lambda f: close_req.handle.dispose())
        return resp_future

    def close(self, handle):
        return self.close_submit(self.close_request(handle)).result()

    def query_directory_request(
        self,
        handle,
        file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
        flags=0,
        file_index=0,
        file_name="*",
        output_buffer_length=8192,
    ):
        smb_req = self.request(obj=handle)
        enum_req = smb2.QueryDirectoryRequest(smb_req)
        enum_req.file_id = handle.file_id
        enum_req.file_name = file_name
        enum_req.output_buffer_length = output_buffer_length
        enum_req.file_information_class = file_information_class
        enum_req.flags = flags
        enum_req.file_index = file_index
        return enum_req

    def query_directory(
        self,
        handle,
        file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
        flags=0,
        file_index=0,
        file_name="*",
        output_buffer_length=8192,
    ):
        return self.connection.transceive(
            self.query_directory_request(
                handle,
                file_information_class,
                flags,
                file_index,
                file_name,
                output_buffer_length,
            ).parent.parent
        )[0][0]

    def enum_directory(
        self,
        handle,
        file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
        file_name="*",
        output_buffer_length=8192,
    ):
        while True:
            try:
                for info in self.query_directory(
                    handle,
                    file_information_class=file_information_class,
                    file_name=file_name,
                    output_buffer_length=output_buffer_length,
                ):
                    yield info
            except ResponseError as e:
                if e.response.status == ntstatus.STATUS_NO_MORE_FILES:
                    return
                else:
                    raise

    def query_file_info_request(
        self,
        create_res,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        output_buffer_length=4096,
        additional_information=None,
    ):
        smb_req = self.request(obj=create_res)
        query_req = smb2.QueryInfoRequest(smb_req)

        query_req.info_type = info_type
        query_req.file_information_class = file_information_class
        query_req.file_id = create_res.file_id
        query_req.output_buffer_length = output_buffer_length
        if additional_information:
            query_req.additional_information = additional_information
        return query_req

    def query_file_info(
        self,
        create_res,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        output_buffer_length=4096,
        additional_information=None,
        first_result_only=None,
    ):
        if first_result_only is None:
            warnings.warn(
                "In a future release, query_file_info will return QueryInfoResponse "
                "instead of the first result from QueryInfoResponse. To maintain "
                "the previous behavior (and silence this warning) pass "
                "`first_result_only=True`. To opt-in to the new behavior, pass "
                "`first_result_only=False`, which will become the new default.",
                DeprecationWarning,
                stacklevel=2,
            )
            first_result_only = True
        resp = self.connection.transceive(
            self.query_file_info_request(
                create_res,
                file_information_class,
                info_type,
                output_buffer_length,
                additional_information,
            ).parent.parent
        )[0][0]
        if first_result_only:
            # only returning the first child info
            return resp[0]
        return resp

    def set_file_info_request(
        self,
        handle,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        input_buffer_length=4096,
        additional_information=None,
    ):
        smb_req = self.request(obj=handle)
        set_req = smb2.SetInfoRequest(smb_req)
        set_req.file_id = handle.file_id
        set_req.file_information_class = file_information_class
        set_req.info_type = info_type
        set_req.input_buffer_length = input_buffer_length
        if additional_information:
            set_req.additional_information = additional_information
        return set_req

    @contextlib.contextmanager
    def set_file_info(self, handle, cls, additional_information=None):
        info_type = file_information_class = None
        if hasattr(cls, "info_type"):
            info_type = cls.info_type
        if hasattr(cls, "file_information_class"):
            file_information_class = cls.file_information_class
        set_req = self.set_file_info_request(
            handle,
            file_information_class,
            info_type,
            additional_information=additional_information,
        )
        yield cls(set_req)
        self.connection.transceive(set_req.parent.parent)[0]

    def change_notify_request(
        self,
        handle,
        completion_filter=smb2.SMB2_NOTIFY_CHANGE_CREATION,
        flags=0,
        buffer_length=4096,
    ):
        smb_req = self.request(obj=handle)
        cnotify_req = smb2.ChangeNotifyRequest(smb_req)
        cnotify_req.file_id = handle.file_id
        cnotify_req.buffer_length = buffer_length
        cnotify_req.flags = flags
        cnotify_req.completion_filter = completion_filter
        return cnotify_req

    def change_notify(
        self,
        handle,
        completion_filter=smb2.SMB2_NOTIFY_CHANGE_CREATION,
        flags=0,
        buffer_length=4096,
    ):
        return self.connection.submit(
            self.change_notify_request(
                handle, completion_filter, flags, buffer_length=4096
            ).parent.parent
        )[0]

    # Send an echo request and get a response
    def echo(self):
        # Create request structure
        smb_req = self.request()
        # Make the request struct have an ECHO_REQUEST
        enum_req = smb2.EchoRequest(smb_req)
        # Get response  first [0] = first response, 2nd [0] = echo response
        # frame
        return self.connection.transceive(smb_req.parent)[0][0]

    def flush_request(self, file):
        smb_req = self.request(obj=file)
        flush_req = smb2.FlushRequest(smb_req)
        flush_req.file_id = file.file_id
        return flush_req

    def flush(self, file):
        self.connection.transceive(self.flush_request(file).parent.parent)

    def read_request(self, file, length, offset, minimum_count=0, remaining_bytes=0):
        smb_req = self.request(obj=file)
        read_req = smb2.ReadRequest(smb_req)

        read_req.length = length
        read_req.offset = offset
        read_req.minimum_count = minimum_count
        read_req.remaining_bytes = remaining_bytes
        read_req.file_id = file.file_id
        return read_req

    def read(self, file, length, offset, minimum_count=0, remaining_bytes=0):
        return self.connection.transceive(
            self.read_request(
                file, length, offset, minimum_count, remaining_bytes
            ).parent.parent
        )[0][0].data

    def write_request(self, file, offset, buffer=None, remaining_bytes=0, flags=0):
        """
        Create a pike.smb2.WriteRequest from the given parameters

        @param file: L{Open}
        @param offset: int offset into the file
        @param buffer: bytes or array.array('B'). If a unicode str is passed, it
            can only contain ascii characters and a warning will be raised.
        @param remaining_bytes:
        @param flags: L{pike.smb2.WriteFlags}
        """
        if isinstance(buffer, array.array) and buffer.typecode != "B":
            raise ValueError(
                "array.array must have typecode 'B', not {!r}".format(buffer.typecode)
            )
        elif isinstance(buffer, str):
            warnings.warn(
                "buffer must be bytes, got {!r}, casting as str and encoding "
                "with 'ascii'".format(type(buffer)),
                UnicodeWarning,
            )
            buffer = buffer.encode("ascii")
        if buffer is not None and not isinstance(buffer, (array.array, bytes)):
            raise TypeError(
                "buffer must be a byte string or byte array, not {!r}".format(
                    type(buffer)
                )
            )
        smb_req = self.request(obj=file)
        write_req = smb2.WriteRequest(smb_req)

        write_req.offset = offset
        write_req.file_id = file.file_id
        write_req.buffer = buffer
        write_req.remaining_bytes = remaining_bytes
        write_req.flags = flags
        return write_req

    def write(self, file, offset, buffer=None, remaining_bytes=0, flags=0):
        smb_res = self.connection.transceive(
            self.write_request(
                file, offset, buffer, remaining_bytes, flags
            ).parent.parent
        )

        return smb_res[0][0].count

    def lock_request(self, handle, locks, sequence=0):
        """
        @param locks: A list of lock tuples, each of which consists of (offset, length, flags).
        """
        smb_req = self.request(obj=handle)
        lock_req = smb2.LockRequest(smb_req)

        lock_req.file_id = handle.file_id
        lock_req.locks = locks
        lock_req.lock_sequence = sequence
        return lock_req

    def lock(self, handle, locks, sequence=0):
        """
        @param locks: A list of lock tuples, each of which consists of (offset, length, flags).
        """
        return self.connection.submit(
            self.lock_request(handle, locks, sequence).parent.parent
        )[0]

    def validate_negotiate_info(self, tree):
        smb_req = self.request(obj=tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        vni_req = smb2.ValidateNegotiateInfoRequest(ioctl_req)
        client = self.session.client

        # Validate negotiate must always be signed
        smb_req.flags |= smb2.SMB2_FLAGS_SIGNED
        ioctl_req.flags = smb2.SMB2_0_IOCTL_IS_FSCTL
        vni_req.capabilities = client.capabilities
        vni_req.client_guid = client.client_guid
        vni_req.security_mode = client.security_mode
        vni_req.dialects = client.dialects

        res = self.connection.transceive(smb_req.parent)[0]

        return res

    def query_network_interface_info_request(self, tree):
        smb_req = self.request(obj=tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        qni_req = smb2.QueryNetworkInterfaceInfoRequest(ioctl_req)
        client = self.session.client

        # Windows sends 65536 buffer
        ioctl_req.max_output_response = 65536
        ioctl_req.flags = smb2.SMB2_0_IOCTL_IS_FSCTL

        return ioctl_req

    def query_network_interface_info(self, tree):
        return self.connection.transceive(
            self.query_network_interface_info_request(tree).parent.parent
        )[0]

    def resume_key(self, file):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        resumekey_req = smb2.RequestResumeKeyRequest(ioctl_req)

        ioctl_req.file_id = file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL

        return self.connection.transceive(smb_req.parent)[0]

    def network_resiliency_request_request(self, file, timeout):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)

        nrr_req = smb2.NetworkResiliencyRequestRequest(ioctl_req)
        ioctl_req.file_id = file.file_id
        ioctl_req.max_output_response = 4096
        ioctl_req.flags = smb2.SMB2_0_IOCTL_IS_FSCTL
        nrr_req.timeout = timeout
        nrr_req.reserved = 0
        return ioctl_req

    def network_resiliency_request(self, file, timeout):
        def update_handle(resp_future):
            if resp_future.result().status == ntstatus.STATUS_SUCCESS:
                # 3.3.5.15.9 Handling a Resiliency Request
                file.is_durable = False
                file.is_resilient = True

        nrr_future = self.connection.submit(
            self.network_resiliency_request_request(file, timeout).parent.parent
        )[0]
        nrr_future.then(update_handle)
        return nrr_future.result()

    def copychunk_request(
        self, source_file, target_file, chunks, resume_key=None, write_flag=False
    ):
        """
        @param source_file: L{Open}
        @param target_file: L{Open}
        @param chunks: sequence of tuples (source_offset, target_offset, length)
        """
        if not resume_key:
            resume_key = self.resume_key(source_file)[0][0].resume_key

        smb_req = self.request(obj=target_file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        if write_flag:
            copychunk_req = smb2.CopyChunkCopyWriteRequest(ioctl_req)
        else:
            copychunk_req = smb2.CopyChunkCopyRequest(ioctl_req)

        ioctl_req.max_output_response = 12
        ioctl_req.file_id = target_file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL
        copychunk_req.source_key = resume_key
        copychunk_req.chunk_count = len(chunks)

        for source_offset, target_offset, length in chunks:
            chunk = smb2.CopyChunk(copychunk_req)
            chunk.source_offset = source_offset
            chunk.target_offset = target_offset
            chunk.length = length
        return ioctl_req

    def copychunk(
        self, source_file, target_file, chunks, resume_key=None, write_flag=False
    ):
        """
        @param source_file: L{Open}
        @param target_file: L{Open}
        @param chunks: sequence of tuples (source_offset, target_offset, length)
        """
        return self.connection.transceive(
            self.copychunk_request(
                source_file, target_file, chunks, resume_key, write_flag
            ).parent.parent
        )[0]

    def set_symlink_request(self, file, target_name, flags):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        set_reparse_req = smb2.SetReparsePointRequest(ioctl_req)
        symlink_buffer = smb2.SymbolicLinkReparseBuffer(set_reparse_req)

        ioctl_req.max_output_response = 0
        ioctl_req.file_id = file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL
        symlink_buffer.substitute_name = target_name
        symlink_buffer.flags = flags
        return ioctl_req

    def set_symlink(self, file, target_name, flags):
        return self.connection.transceive(
            self.set_symlink_request(file, target_name, flags).parent.parent
        )[0]

    def get_symlink_request(self, file):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        set_reparse_req = smb2.GetReparsePointRequest(ioctl_req)

        ioctl_req.file_id = file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL
        return ioctl_req

    def get_symlink(self, file):
        return self.connection.transceive(self.get_symlink_request(file).parent.parent)[
            0
        ]

    def fsctl_request(self, smb_req, fh, buflen=16384):
        ioctl_req = smb2.IoctlRequest(smb_req)
        ioctl_req.max_output_response = buflen
        ioctl_req.flags = smb2.SMB2_0_IOCTL_IS_FSCTL
        ioctl_req.file_id = fh.file_id
        return ioctl_req

    def enumerate_snapshots_request(
        self, fh, snap_request=smb2.EnumerateSnapshotsRequest, max_output_response=16384
    ):
        smb_req = self.request(obj=fh.tree)
        fsctl_req = self.fsctl_request(smb_req, fh, buflen=max_output_response)
        enum_req = snap_request(fsctl_req)
        return enum_req

    def enumerate_snapshots(self, fh, snap_request=smb2.EnumerateSnapshotsRequest):
        return self.connection.transceive(
            self.enumerate_snapshots_request(fh, snap_request).parent.parent.parent
        )[0]

    def enumerate_snapshots_list(self, fh, snap_request=smb2.EnumerateSnapshotsRequest):
        return self.enumerate_snapshots(fh, snap_request)[0][0].snapshots

    def zero_data(self, tree, src_offsets, dst_offsets, src_filename):
        """ Send a FSCTL_SET_ZERO_DATA ioctl request """
        fh_src = self.create(
            tree,
            src_filename,
            access=smb2.FILE_READ_DATA | smb2.FILE_WRITE_DATA,
            share=(
                smb2.FILE_SHARE_READ | smb2.FILE_SHARE_WRITE | smb2.FILE_SHARE_DELETE
            ),
            disposition=smb2.FILE_OPEN_IF,
        ).result()
        smb_req = self.request(obj=tree)
        fsctl_req = self.fsctl_request(smb_req, fh_src)
        smb2.SetSparseRequest(fsctl_req)
        try:
            results = self.connection.transceive(smb_req.parent)
        except Exception:
            self.close(fh_src)
            raise

        smb_req = self.request(obj=tree)
        fsctl_req = self.fsctl_request(smb_req, fh_src)
        zerodata_req = smb2.SetZeroDataRequest(fsctl_req)
        zerodata_req.file_offset = src_offsets
        zerodata_req.beyond_final_zero = dst_offsets
        try:
            results = self.connection.transceive(smb_req.parent)
            return results
        finally:
            self.close(fh_src)

    def lease_break_acknowledgement(self, tree, notify):
        """
        @param tree: L{Tree} which the lease is taken against
        @param notify: L{Smb2} frame containing a LeaseBreakRequest
        return a LeaseBreakAcknowledgement with some fields pre-populated
        """
        lease_break = notify[0]
        smb_req = self.request(obj=tree)
        ack_req = smb2.LeaseBreakAcknowledgement(smb_req)
        ack_req.lease_key = lease_break.lease_key
        ack_req.lease_state = lease_break.new_lease_state
        return ack_req

    def oplock_break_acknowledgement(self, fh, notify):
        """
        @param fh: Acknowledge break on this L{Open}
        @param notify: L{Smb2} frame containing a OplockBreakRequest
        return a OplockBreakAcknowledgement with some fields pre-populated
        """
        oplock_break = notify[0]
        smb_req = self.request(obj=fh)
        ack_req = smb2.OplockBreakAcknowledgement(smb_req)
        ack_req.file_id = oplock_break.file_id
        ack_req.oplock_level = oplock_break.oplock_level
        return ack_req

    def frame(self):
        return self.connection.frame()

    def request(self, nb=None, obj=None, encrypt_data=None):
        smb_req = self.connection.request(nb)
        smb_req.session_id = self.session.session_id

        if isinstance(obj, Tree):
            smb_req.tree_id = obj.tree_id
        elif isinstance(obj, Open):
            smb_req.tree_id = obj.tree.tree_id

        # encryption unspecified, follow session/tree negotiation
        if encrypt_data is None:
            encrypt_data = self.session.encrypt_data
            if isinstance(obj, Tree):
                encrypt_data |= obj.encrypt_data
            elif isinstance(obj, Open):
                encrypt_data |= obj.tree.encrypt_data

        # a packet is either encrypted or signed
        if encrypt_data and self.session.encryption_context is not None:
            transform = crypto.TransformHeader(smb_req.parent)
            transform.encryption_context = self.session.encryption_context
            transform.session_id = self.session.session_id
        elif (
            self.connection.negotiate_response.security_mode
            & smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED
            or self.connection.client.security_mode
            & smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED
        ):
            smb_req.flags |= smb2.SMB2_FLAGS_SIGNED

        return smb_req

    def let(self, **kwargs):
        return self.connection.let(**kwargs)


class Tree(object):
    def __init__(self, session, path, smb_res):
        object.__init__(self)
        self.session = session
        self.path = path
        self.tree_id = smb_res.tree_id
        self.tree_connect_response = smb_res[0]
        self.encrypt_data = False
        if smb_res[0].share_flags & smb2.SMB2_SHAREFLAG_ENCRYPT_DATA:
            self.encrypt_data = True
        self.session._trees[self.tree_id] = self


class Open(object):
    def __init__(self, tree, smb_res, create_guid=None, prev=None):
        self.create_response = smb_res[0]

        self.tree = tree
        self.file_id = self.create_response.file_id
        self.oplock_level = self.create_response.oplock_level
        self.lease = None
        self.is_durable = False
        self.is_resilient = False
        self.is_persistent = False
        self.durable_timeout = None
        self.durable_flags = None
        self.create_guid = create_guid

        if prev is not None:
            self.is_durable = prev.is_durable
            self.is_resilient = prev.is_resilient
            self.durable_timeout = prev.durable_timeout
            self.durable_flags = prev.durable_flags

        if self.oplock_level != smb2.SMB2_OPLOCK_LEVEL_NONE:
            if self.oplock_level == smb2.SMB2_OPLOCK_LEVEL_LEASE:
                lease_res = [
                    c for c in self.create_response if isinstance(c, smb2.LeaseResponse)
                ][0]
                self.lease = tree.session.client.lease(tree, lease_res)
            else:
                self.arm_oplock_future()

        durable_res = [
            c for c in self.create_response if isinstance(c, smb2.DurableHandleResponse)
        ]

        if durable_res != []:
            self.is_durable = True

        durable_v2_res = [
            c
            for c in self.create_response
            if isinstance(c, smb2.DurableHandleV2Response)
        ]
        if durable_v2_res != []:
            self.durable_timeout = durable_v2_res[0].timeout
            self.durable_flags = durable_v2_res[0].flags

        if self.durable_flags is not None:
            self.is_durable = True
            if self.durable_flags & smb2.SMB2_DHANDLE_FLAG_PERSISTENT != 0:
                self.is_persistent = True

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
                chan = self.tree.session.first_channel()
                ack = chan.oplock_break_acknowledgement(self, smb_res)
                ack.oplock_level = cb(notify.oplock_level)
                ack_res = chan.connection.transceive(ack.parent.parent)[0][0]
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            chan = self.tree.session.first_channel()
            chan.close(self)
        except StopIteration:
            # If the underlying connection for the channel is closed explicitly
            # open will not able to find an appropriate channel, to send close.
            pass


class RelatedOpen(object):
    """
    Use in place of a real `Open` object in compound requests to use a handle
    from previous Create in the chain
    """

    def __init__(self, tree=None):
        self.tree_id = tree.tree_id
        self.file_id = smb2.RELATED_FID


class Lease(object):
    def __init__(self, tree):
        self.tree = tree
        self.refs = 1
        self.future = None

    def update(self, lease_res):
        self.lease_key = lease_res.lease_key
        self.lease_state = lease_res.lease_state
        if self.future is None:
            self.arm_future()

    def arm_future(self):
        """
        (Re)arm the lease future for this Lease. This function should be called
        when a lease changes state to anything other than SMB2_LEASE_NONE
        """
        self.future = self.tree.session.client.lease_break_future(self.lease_key)

    def ref(self):
        self.refs += 1

    def dispose(self):
        self.refs -= 1
        if self.refs == 0:
            self.tree.session.client.dispose_lease(self)

    def on_break(self, cb):
        """
        Simple lease break callback handler.
        @param cb: callable taking 1 parameter: the break request lease state
                   should return the desired lease state to break to
        """

        def simple_handle_break(lease, smb_res, cb_ctx):
            """
            note that lease is not used in this callback,
            since it already closes over self
            """
            notify = smb_res[0]
            if notify.flags & smb2.SMB2_NOTIFY_BREAK_LEASE_FLAG_ACK_REQUIRED:
                chan = self.tree.session.first_channel()
                ack = chan.lease_break_acknowledgement(self.tree, smb_res)
                ack.lease_state = cb(notify.new_lease_state)
                ack_res = chan.connection.transceive(ack.parent.parent)[0][0]
                if ack_res.lease_state != smb2.SMB2_LEASE_NONE:
                    self.arm_future()
                    self.on_break(cb)
                self.lease_state = ack_res.lease_state
            else:
                self.lease_state = notify.new_lease_state

        self.on_break_request(simple_handle_break)

    def on_break_request(self, cb, cb_ctx=None):
        """
        Complex lease break callback handler.
        @param cb: callable taking 3 parameters:
                        L{Lease}
                        L{Smb2} containing the break request
                        L{object} arbitrary context
                   should handle breaking the lease in some way
                   callback is also responsible for re-arming the future
                   and updating the lease_state (if changed)
        """

        def handle_break(f):
            smb_res = f.result()
            cb(self, smb_res, cb_ctx)

        self.future.then(handle_break)
