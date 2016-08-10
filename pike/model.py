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
#        model.py
#
# Abstract:
#
#        Transport and object model
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

"""
SMB2 Object Model.

This module contains an implementation of the SMB2 client object model,
allowing channels, sessions, tree connections, opens, and leases
to be established and tracked.  It provides convenience functions
for exercising common elements of the protocol without manually
constructing packets.
"""

import sys
import socket
import asyncore
import array
import struct
import random
import logging
import time
import operator
import contextlib

import core
import netbios
import smb2
import ntstatus
try:
    import kerberos
except ImportError:
    kerberos = None
import ntlm
import digest

default_timeout = 30
trace = False

class TimeoutError(Exception):
    pass

class StateError(Exception):
    pass

class ResponseError(Exception):
    def __init__(self, response):
        Exception.__init__(self, response.command, response.status)
        self.response = response

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

    def wait(self, timeout=default_timeout):
        """
        Wait for future result to become available.

        @param timeout: The time in seconds before giving up and raising TimeoutError
        """
        deadline = time.time() + timeout
        while self.response is None:
            now = time.time()
            if now > deadline:
                raise TimeoutError('Timed out after %s seconds' % timeout)
            asyncore.loop(timeout=deadline-now, count=1)

        return self

    def wait_interim(self, timeout=default_timeout):
        """
        Wait for interim response or actual result to become available.

        @param timeout: The time in seconds before giving up and raising TimeoutError
        """
        deadline = time.time() + timeout
        while self.response is None and self.interim_response is None:
            now = time.time()
            if now > deadline:
                raise TimeoutError('Timed out after %s seconds' % timeout)
            asyncore.loop(timeout=deadline-now, count=1)

        return self

    def result(self, timeout=default_timeout):
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
            raise self.response, None, traceback
        else:
            return self.response

    def then(self, notify):
        """
        Set notification function.

        @param notify: A function which will be invoked with this future as a parameter
                       when its result becomes available.  If it is already available,
                       it will be called immediately.
        """
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
    def __init__(self,
                 dialects=[smb2.DIALECT_SMB2_002, smb2.DIALECT_SMB2_1, smb2.DIALECT_SMB3_0],
                 capabilities=smb2.GlobalCaps(reduce(operator.or_, smb2.GlobalCaps.values())),
                 security_mode=smb2.SMB2_NEGOTIATE_SIGNING_ENABLED,
                 client_guid=None):
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
            client_guid = array.array('B',map(random.randint, [0]*16, [255]*16))

        self.dialects = dialects
        self.capabilities = capabilities
        self.security_mode = security_mode
        self.client_guid = client_guid
        self.channel_sequence = 0

        self._oplock_break_map = {}
        self._lease_break_map = {}
        self._oplock_break_queue = []
        self._lease_break_queue = []
        self._connections = []
        self._leases = {}

        self.logger = logging.getLogger('pike')

    def connect(self, server, port=445):
        """
        Create a connection.

        Returns a new L{Connection} object connected to the given
        server and port.

        @param server: The server to connect to.
        @param port: The port to connect to.
        """
        return Connection(self, server, port)

    # Do not use, may be removed.  Use oplock_break_future.
    def next_oplock_break(self):
        while len(self._oplock_break_queue) == 0:
            asyncore.loop(count=1)
        return self._oplock_break_queue.pop()
    
    # Do not use, may be removed.  Use lease_break_future.
    def next_lease_break(self):
        while len(self._lease_break_queue) == 0:
            asyncore.loop(count=1)
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
        
        future = Future(None)

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

        future = Future(None)

        for smb_res in self._lease_break_queue[:]:
            if smb_res[0].lease_key == lease_key:
                future.complete(smb_res)
                self._lease_break_queue.remove(smb_res)
                break

        if future.response is None:
            self._lease_break_map[lease_key.tostring()] = future

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

        lease_key = lease_res.lease_key.tostring()
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
        del self._leases[lease.lease_key.tostring()]


class KerberosProvider(object):
    def __init__(self, conn, creds=None):
        if creds:
            nt4, password = creds.split('%')
            domain, user = nt4.split('\\')
            (self.result,
             self.context) = kerberos.authGSSClientInit(
                "cifs/" + conn.server,
                gssmech=2,
                user=user,
                password=password,
                domain=domain)
        else:
            (self.result,
             self.context) = kerberos.authGSSClientInit("cifs/" + conn.server,
                                                        gssmech=1)

    def step(self, sec_buf):
        self.result = kerberos.authGSSClientStep(
                self.context,
                sec_buf.tostring())
        if self.result == 0:
            return (array.array(
                    'B',
                    kerberos.authGSSClientResponse(self.context)),
                    None)
        else:
            kerberos.authGSSClientSessionKey(self.context)
            return (None, kerberos.authGSSClientResponse(self.context)[:16])

class Connection(asyncore.dispatcher):
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
        asyncore.dispatcher.__init__(self)
        self._in_buffer = array.array('B')
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
        
        self.client = client
        self.server = server
        self.port = port
        self.remote_addr = None
        self.local_addr = None

        self.error = None
        self.traceback = None
    
        for result in socket.getaddrinfo(server, port,
                                         0,
                                         socket.SOCK_STREAM,
                                         socket.IPPROTO_TCP):
            family, socktype, proto, canonname, sockaddr = result
            break
        self.create_socket(family, socktype)
        self.connect(sockaddr)
        self.client._connections.append(self)

    def next_mid(self):
        while self._next_mid in self._mid_blacklist:
            self._next_mid += 1
        result = self._next_mid
        self._next_mid += 1

        return result

    def reserve_mid(mid):
        self._mid_blacklist.add(mid)

    #
    # async dispatcher callbacks
    #
    def readable(self):
        # Always want to read if possible
        return True

    def writable(self):
        # Do we have data to send?
        # FIXME: credit tracking
        return self._out_buffer != None or len(self._out_queue) != 0

    def handle_connect(self):
        self.local_addr = self.socket.getsockname()
        self.remote_addr = self.socket.getpeername()

        self.client.logger.debug('connect: %s/%s -> %s/%s',
                                 self.local_addr[0], self.local_addr[1],
                                 self.remote_addr[0], self.remote_addr[1])
        pass

    def handle_read(self):
        # Try to read the next netbios frame
        remaining = self._watermark - len(self._in_buffer)
        data = self.recv(remaining)
        self._in_buffer.extend(array.array('B', data))
        avail = len(self._in_buffer)
        if avail >= 4:
            self._watermark = 4 + struct.unpack('>L', self._in_buffer[0:4])[0]
        if avail == self._watermark:
            nb = self.frame()
            nb.parse(self._in_buffer)
            self._in_buffer = array.array('B')
            self._watermark = 4
            self._dispatch_incoming(nb)

    def handle_write(self):
        # Try to write out more data
        # FIXME: credit tracking
        while self._out_buffer is None and len(self._out_queue):
            self._out_buffer = self._prepare_outgoing()
        sent = self.send(self._out_buffer)
        del self._out_buffer[:sent]
        if len(self._out_buffer) == 0:
            self._out_buffer = None

    def handle_close(self):
        self.close()

    def handle_error(self):
        (_,self.error,self.traceback) = sys.exc_info()
        self.close()

    def close(self):
        """
        Close connection.

        This unceremoniously terminates the connection and fails all
        outstanding requests with EOFError.
        """
        if self not in self.client._connections:
            return

        asyncore.dispatcher.close(self)

        # Run down connection
        if self.error is None:
            self.error = EOFError("close")

        if self.remote_addr is not None:
            self.client.logger.debug("disconnect (%s/%s -> %s/%s): %s",
                                     self.local_addr[0], self.local_addr[1],
                                     self.remote_addr[0], self.remote_addr[1],
                                     self.error)

        self.client._connections.remove(self)

        for future in self._out_queue:
            future.complete(self.error, self.traceback)
        del self._out_queue[:]

        for future in self._future_map.itervalues():
            future.complete(self.error, self.traceback)
        self._future_map.clear()

        for session in self._sessions.values():
            session.delchannel(self)

        self.traceback = None

    def _prepare_outgoing(self):
        # Try to prepare an outgoing packet

        # Grab an outgoing smb2 request
        future = self._out_queue[0]
        del self._out_queue[0]

        with future:
            req = future.request
            
            # Assign message id
            # FIXME: credit tracking
            if req.message_id is None:
                req.message_id = self.next_mid()
            req.credit_request = 10

            if req.credit_charge == None:
                req.credit_charge = 1

            if req.is_last_child():
                # Last command in chain, ready to send packet
                buf = req.parent.serialize()
                if trace: 
                    self.client.logger.debug('send (%s/%s -> %s/%s): %s',
                                             self.local_addr[0], self.local_addr[1],
                                             self.remote_addr[0], self.remote_addr[1],
                                             req.parent)
                else:
                    self.client.logger.debug('send (%s/%s -> %s/%s): %s',
                                             self.local_addr[0], self.local_addr[1],
                                             self.remote_addr[0], self.remote_addr[1],
                                             ', '.join(f[0].__class__.__name__ for f in req.parent))
                result = buf
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
        lease_key = lease_key.tostring()
        if lease_key in self.client._lease_break_map:
            return self.client._lease_break_map.pop(lease_key)
        return None

    def _dispatch_incoming(self, res):
        if trace:
            self.client.logger.debug('recv (%s/%s -> %s/%s): %s',
                                     self.remote_addr[0], self.remote_addr[1],
                                     self.local_addr[0], self.local_addr[1],
                                     res)
        else:
            self.client.logger.debug('recv (%s/%s -> %s/%s): %s',
                                     self.remote_addr[0], self.remote_addr[1],
                                     self.local_addr[0], self.local_addr[1],
                                     ', '.join(f[0].__class__.__name__ for f in res))
        for smb_res in res:
            # Verify non-session-setup-response signatures
            if not isinstance(smb_res[0], smb2.SessionSetupResponse):
                key = self.signing_key(smb_res.session_id)
                if key:
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
                elif isinstance(smb_res[0], smb2.ErrorResponse) or \
                     smb_res.status not in smb_res[0].allowed_status:
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
        if self.error is not None:
            raise self.error
        futures = []
        for smb_req in req:
            if isinstance(smb_req[0], smb2.Cancel):
                # Find original future being canceled to return
                if smb_req.async_id is not None:
                    # Cancel by async ID
                    future = filter(lambda f: f.interim_response.async_id == smb_req.async_id, self._future_map.itervalues())[0]
                elif smb_req.message_id in self._future_map:
                    # Cancel by message id, already in future map
                    future = self._future_map[smb_req.message_id]
                else:
                    # Cancel by message id, still in send queue
                    future = filter(lambda f: f.request.message_id == smb_req.message_id, self._out_queue)[0]
                # Add fake future for cancel since cancel has no response
                self._out_queue.append(Future(smb_req))
                futures.append(future)
            else:
                future = Future(smb_req)
                self._out_queue.append(future)
                futures.append(future)
        return futures

    def transceive(self, req):
        """
        Submit request and wait for responses.

        Submits a L{netbios.Netbios} frame for sending.  Waits for
        and returns a list of L{smb2.Smb2} response objects, one for each
        corresponding L{smb2.Smb2} frame in the request.
        """
        return map(Future.result, self.submit(req))

    def negotiate(self):
        """
        Perform dialect negotiation.

        This must be performed before setting up a session with
        L{Connection.session_setup}().
        """
        smb_req = self.request()
        neg_req = smb2.NegotiateRequest(smb_req)
        
        neg_req.dialects = self.client.dialects
        neg_req.security_mode = self.client.security_mode
        neg_req.capabilities = self.client.capabilities
        neg_req.client_guid = self.client.client_guid

        self.negotiate_response = self.transceive(smb_req.parent)[0][0]

        return self

    class SessionSetupContext(object):
        def __init__(self, conn, creds=None, bind=None, resume=None,
                     ntlm_version=None):
            assert conn.negotiate_response is not None

            self.conn = conn
            self.bind = bind
            self.resume = resume

            if creds and ntlm is not None:
                nt4, password = creds.split('%')
                domain, user = nt4.split('\\')
                self.auth = ntlm.NtlmProvider(domain, user, password)
                if ntlm_version is not None:
                    self.auth.ntlm_version = ntlm_version
            elif kerberos is not None:
                self.auth = KerberosProvider(self, creds)
            else:
                raise ImportError("Neither ntlm nor kerberos authentication "
                                  "methods are available")

            self.prev_session_id = 0
            self.session_id = 0
            self.requests = []
            self.responses = []
            self.session_future = Future()
            self.interim_future = None

            if bind:
                assert conn.negotiate_response.dialect_revision >= 0x300
                self.session_id = bind.session_id
                conn._binding = bind
                conn._binding_key = digest.derive_key(
                        bind.session_key,
                        'SMB2AESCMAC',
                        'SmbSign')[:16]
            elif resume:
                assert conn.negotiate_response.dialect_revision >= 0x300
                self.prev_session_id = resume.session_id

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

            self.requests.append(smb_req)
            return self.conn.submit(smb_req.parent)[0]

        def _finish(self, smb_res):
            sec_buf = smb_res[0].security_buffer
            out_buf, self.session_key = self.auth.step(sec_buf)

            if self.conn.negotiate_response.dialect_revision >= 0x300:
                signing_key = digest.derive_key(
                        self.session_key, 'SMB2AESCMAC', 'SmbSign')[:16]
            else:
                signing_key = self.session_key

            # Verify final signature
            smb_res.verify(self.conn.signing_digest(), signing_key)

            if self.bind:
                self.conn._binding = None
                self.conn._binding_key = None
                session = self.bind
            else:
                session = Session(self.conn.client,
                                  self.session_id,
                                  self.session_key)

            return session.addchannel(self.conn, signing_key)

        def __iter__(self):
            return self

        def submit(self, f=None):
            """
            Submit rounds of SessionSetupRequests

            Returns a L{Future} object, for the L{Channel} object
            """
            try:
                res = self.next()
                res.then(self.submit)
            except StopIteration:
                pass
            return self.session_future

        def next(self):
            out_buf = None
            if not self.interim_future and not self.responses:
                # send the initial request
                out_buf, self.session_key = self.auth.step(
                        self.conn.negotiate_response.security_buffer)

            elif self.interim_future:
                smb_res = self.interim_future.result()
                self.interim_future = None
                self.responses.append(smb_res)

                if smb_res.status == ntstatus.STATUS_SUCCESS:
                    # session is established
                    self.session_future.complete(
                            self._finish(smb_res))
                    return self.session_future
                else:
                    # process interim request
                    session_res = smb_res[0]
                    self.session_id = smb_res.session_id
                    if self.bind:
                        # Need to verify intermediate signatures
                        smb_res.verify(self.conn.signing_digest(),
                                       self.conn._binding_key)
                    out_buf, self.session_key = self.auth.step(
                            session_res.security_buffer)
            if out_buf:
                # submit additional requests if necessary
                self.interim_future = self._send_session_setup(out_buf)
                return self.interim_future
            raise StopIteration()

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

        for (attr,value) in self._settings.iteritems():
            setattr(req, attr, value)

        return req

    def let(self, **kwargs):
        return self._Let(self, kwargs)

    class _Let(object):
        def __init__(self, conn, settings):
            self.conn = conn
            self.settings = settings

        def __enter__(self):
            self.backup = dict(self.conn._settings)
            self.conn._settings.update(self.settings)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn._settings = self.backup

    #
    # SMB2 context upcalls
    #
    def signing_key(self, session_id):
        if session_id in self._sessions:
            session = self._sessions[session_id]
            channel = session._channels[id(self)]
            return channel.signing_key
        elif self._binding and self._binding.session_id == session_id:
            return self._binding_key

    def signing_digest(self):
        assert self.negotiate_response is not None
        if self.negotiate_response.dialect_revision >= 0x300:
            return digest.aes128_cmac
        else:
            return digest.sha256_hmac

    def get_request(self, message_id):
        if message_id in self._future_map:
            return self._future_map[message_id].request
        else:
            return None

class Session(object):
    def __init__(self, client, session_id, session_key):
        object.__init__(self)
        self.client = client
        self.session_id = session_id
        self.session_key = session_key
        self._channels = {}

    def addchannel(self, conn, signing_key):
        channel = Channel(conn, self, signing_key)
        self._channels[id(conn)] = channel
        conn._sessions[self.session_id] = self
        return channel

    def delchannel(self, conn):
        del conn._sessions[self.session_id]
        del self._channels[id(conn)]

    def first_channel(self):
        return self._channels.itervalues().next()

class Channel(object):
    def __init__(self, connection, session, signing_key):
        object.__init__(self)
        self.connection = connection
        self.session = session
        self.signing_key = signing_key

    def cancel(self, future):
        if (future.response is not None):
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

        return self.connection.submit(smb_req.parent)[0]

    def tree_connect_request(self, path):
        self.smb_req = self.request()
        tree_req = smb2.TreeConnectRequest(self.smb_req)
        tree_req.path = "\\\\" + self.connection.server + "\\" + path
        return tree_req

    def tree_connect_submit(self, tree_req):
        tree_future = Future()
        resp_future = self.connection.submit(tree_req.parent.parent)[0]
        resp_future.then(lambda f: tree_future.complete(Tree(self.session,
                                                             tree_req.path,
                                                             f.result())))
        return tree_future

    def tree_connect(self, path):
        return self.tree_connect_submit(
                self.tree_connect_request(
                    path)).result()

    def tree_disconnect_request(self, tree):
        smb_req = self.request(obj=tree)
        tree_req = smb2.TreeDisconnectRequest(smb_req)
        return tree_req

    def tree_disconnect(self, tree):
        return self.connection.transceive(
                self.tree_disconnect_request(tree).parent.parent)[0]

    def logoff_request(self):
        smb_req = self.request()
        logoff_req = smb2.LogoffRequest(smb_req)
        return logoff_req

    def logoff_submit(self, logoff_req):
        def logoff_finish(f):
            for channel in self.session._channels.itervalues():
                del channel.connection._sessions[self.session.session_id]
        logoff_future = self.connection.submit(logoff_req.parent.parent)[0]
        logoff_future.then(logoff_finish)
        return logoff_future

    def logoff(self):
        return self.logoff_submit(
                self.logoff_request()).result()

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
            extended_attributes=None):

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
                create_guid = array.array('B',map(random.randint, [0]*16, [255]*16))
            durable_req.create_guid = create_guid

        if app_instance_id:
            app_instance_id_req = smb2.AppInstanceIdRequest(create_req)
            app_instance_id_req.app_instance_id = app_instance_id

        if query_on_disk_id:
            query_on_disk_id_req = smb2.QueryOnDiskIDRequest(create_req)

        if extended_attributes:
            ext_attr_len = len(extended_attributes.keys())
            for name, value in extended_attributes.iteritems():
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

        open_future = Future(None)
        def finish(f):
            with open_future: open_future(
                    Open(
                        tree,
                        f.result(),
                        create_guid=create_guid,
                        prev=prev_open))
        create_req.open_future = open_future
        create_req.finish = finish

        return create_req

    def create_submit(self, create_req):
        open_future = create_req.open_future
        open_future.request_future = self.connection.submit(
                create_req.parent.parent)[0]
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
            extended_attributes=None):
        return self.create_submit(self.create_request(
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
                extended_attributes))

    def close_request(self, handle):
        smb_req = self.request(obj=handle)
        close_req = smb2.CloseRequest(smb_req)

        close_req.file_id = handle.file_id
        close_req.handle = handle
        return close_req

    def close_submit(self, close_req):
        resp_future = self.connection.submit(close_req.parent.parent)[0]
        resp_future.then(close_req.handle.dispose())
        return resp_future

    def close(self, handle):
        return self.close_submit(
                self.close_request(handle)).result()

    def query_directory_request(
            self,
            handle,
            file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
            flags=0,
            file_index=0,
            file_name='*',
            output_buffer_length=8192):
        smb_req = self.request(obj=handle)
        enum_req = smb2.QueryDirectoryRequest(smb_req)
        enum_req.file_id = handle.file_id
        enum_req.file_name = file_name
        enum_req.output_buffer_length = output_buffer_length
        enum_req.file_information_class = file_information_class
        enum_req.flags = flags
        enum_req.file_index = file_index
        return enum_req

    def query_directory(self,
                        handle,
                        file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
                        flags=0,
                        file_index=0,
                        file_name='*',
                        output_buffer_length=8192):
        return self.connection.transceive(
                self.query_directory_request(
                    handle,
                    file_information_class,
                    flags,
                    file_index,
                    file_name,
                    output_buffer_length).parent.parent)[0][0]

    def enum_directory(self,
                       handle,
                       file_information_class=smb2.FILE_DIRECTORY_INFORMATION,
                       file_name = '*',
                       output_buffer_length=8192):
        while True:
            try:
                for info in self.query_directory(handle,
                                                 file_information_class=file_information_class,
                                                 file_name=file_name,
                                                 output_buffer_length=output_buffer_length):
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
            output_buffer_length=4096):
        smb_req = self.request(obj=create_res)
        query_req = smb2.QueryInfoRequest(smb_req)
        
        query_req.info_type = info_type
        query_req.file_information_class = file_information_class        
        query_req.file_id = create_res.file_id
        query_req.output_buffer_length = output_buffer_length
        return query_req

    def query_file_info(self,
                        create_res,
                        file_information_class=smb2.FILE_BASIC_INFORMATION,
                        info_type=smb2.SMB2_0_INFO_FILE,
                        output_buffer_length=4096):
        return self.connection.transceive(
                self.query_file_info_request(
                    create_res,
                    file_information_class,
                    info_type,
                    output_buffer_length).parent.parent)[0][0][0]
    
    @contextlib.contextmanager
    def set_file_info(self, handle, cls):
        smb_req = self.request(obj=handle)
        set_req = smb2.SetInfoRequest(smb_req)
        set_req.file_id = handle.file_id
        yield cls(set_req)
        self.connection.transceive(smb_req.parent)[0]

    # Send an echo request and get a response
    def echo(self):
        # Create request structure
        smb_req = self.request()
        # Make the request struct have an ECHO_REQUEST
        enum_req = smb2.EchoRequest(smb_req)
        # Get response  first [0] = first response, 2nd [0] = echo response
        # frame
        self.connection.transceive(smb_req.parent)[0][0]

    def flush(self, file):
        smb_req = self.request(obj=file)
        flush_req = smb2.FlushRequest(smb_req)
        flush_req.file_id = file.file_id

        self.connection.transceive(smb_req.parent)

    def read_request(
            self,
            file,
            length,
            offset,
            minimum_count=0,
            remaining_bytes=0):
        smb_req = self.request(obj=file)
        read_req = smb2.ReadRequest(smb_req)

        read_req.length = length
        read_req.offset = offset
        read_req.minimum_count = minimum_count
        read_req.remaining_bytes = remaining_bytes
        read_req.file_id = file.file_id
        return read_req

    def read(
            self,
            file,
            length,
            offset,
            minimum_count=0,
            remaining_bytes=0):
        return self.connection.transceive(
                self.read_request(
                    file,
                    length,
                    offset,
                    minimum_count,
                    remaining_bytes).parent.parent)[0][0].data

    def write_request(
            self,
            file,
            offset,
            buffer=None,
            remaining_bytes=0,
            flags=0):
        smb_req = self.request(obj=file)
        write_req = smb2.WriteRequest(smb_req)

        write_req.offset = offset
        write_req.file_id = file.file_id
        write_req.buffer = buffer
        write_req.remaining_bytes = remaining_bytes
        write_req.flags = flags
        return write_req

    def write(self,
              file,
              offset,
              buffer=None,
              remaining_bytes=0,
              flags=0):
        smb_res = self.connection.transceive(
                self.write_request(
                    file,
                    offset,
                    buffer,
                    remaining_bytes,
                    flags).parent.parent)

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
                self.lock_request(
                    handle,
                    locks,
                    sequence).parent.parent)[0]

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

    def resume_key(self, file):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        resumekey_req = smb2.RequestResumeKeyRequest(ioctl_req)

        ioctl_req.file_id = file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL

        return self.connection.transceive(smb_req.parent)[0]

    def copychunk_request(self, source_file, target_file, chunks):
        """
        @param source_file: L{Open}
        @param target_file: L{Open}
        @param chunks: sequence of tuples (source_offset, target_offset, length)
        """
        resume_key = self.resume_key(source_file)[0][0].resume_key

        smb_req = self.request(obj=target_file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        copychunk_req = smb2.CopyChunkCopyRequest(ioctl_req)

        ioctl_req.max_output_response = 16384
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

    def copychunk(self, source_file, target_file, chunks):
        """
        @param source_file: L{Open}
        @param target_file: L{Open}
        @param chunks: sequence of tuples (source_offset, target_offset, length)
        """
        return self.connection.transceive(
                self.copychunk_request(
                    source_file,
                    target_file,
                    chunks).parent.parent)[0]

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
                self.set_symlink_request(
                    file,
                    target_name,
                    flags).parent.parent)[0]

    def get_symlink_request(self, file):
        smb_req = self.request(obj=file.tree)
        ioctl_req = smb2.IoctlRequest(smb_req)
        set_reparse_req = smb2.GetReparsePointRequest(ioctl_req)

        ioctl_req.file_id = file.file_id
        ioctl_req.flags |= smb2.SMB2_0_IOCTL_IS_FSCTL
        return ioctl_req

    def get_symlink(self, file):
        return self.connection.transceive(
                self.get_symlink_request(file).parent.parent)[0]

    def frame(self):
        return self.connection.frame()

    def request(self, nb=None, obj=None):
        smb_req = self.connection.request(nb)
        smb_req.session_id = self.session.session_id
        
        if self.connection.negotiate_response.security_mode & smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED or \
           self.connection.client.security_mode & smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED:
            smb_req.flags |= smb2.SMB2_FLAGS_SIGNED

        if isinstance(obj, Tree):
            smb_req.tree_id = obj.tree_id
        elif isinstance(obj, Open):
            smb_req.tree_id = obj.tree.tree_id

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

class Open(object):
    def __init__(self, tree, smb_res, create_guid=None, prev=None):
        object.__init__(self)

        create_res = smb_res[0]

        self.tree = tree
        self.file_id = create_res.file_id
        self.oplock_level = create_res.oplock_level
        self.lease = None
        self.durable_timeout = None
        self.durable_flags = None
        self.create_guid = create_guid

        if prev is not None:
            self.durable_timeout = prev.durable_timeout
            self.durable_flags = prev.durable_flags

        if self.oplock_level != smb2.SMB2_OPLOCK_LEVEL_NONE:
            if self.oplock_level == smb2.SMB2_OPLOCK_LEVEL_LEASE:
                lease_res = filter(lambda c: isinstance(c, smb2.LeaseResponse), create_res)[0]
                self.lease = tree.session.client.lease(tree, lease_res)
            else:
                self.oplock_future = tree.session.client.oplock_break_future(self.file_id)

        durable_v2_res = filter(lambda c: isinstance(c, smb2.DurableHandleV2Response), create_res)
        if durable_v2_res != []:
            self.durable_timeout = durable_v2_res[0].timeout
            self.durable_flags = durable_v2_res[0].flags

    def on_oplock_break(self, cb):
        def handle_break(f):
            notify = f.result()[0]
            if self.oplock_level != smb2.SMB2_OPLOCK_LEVEL_II:
                chan = self.tree.session.first_channel()
                req = chan.request(obj=self)
                ack = smb2.OplockBreakAcknowledgement(req)
                ack.file_id = notify.file_id
                ack.oplock_level = cb(notify.oplock_level)
                ack_res = chan.connection.transceive(req.parent)[0][0]
                if ack.oplock_level != smb2.SMB2_OPLOCK_LEVEL_NONE:
                    self.oplock_future = self.tree.session.client.oplock_break_future(self.file_id)
                    self.on_oplock_break(cb)
                self.oplock_level = ack_res.oplock_level
            else:
                self.oplock_level = notify.oplock_level

        self.oplock_future.then(handle_break)

    def dispose(self):
        self.tree = None
        if self.lease is not None:
            self.lease.dispose()
            self.lease = None

class Lease(object):
    def __init__(self, tree):
        self.tree = tree
        self.refs = 1
        self.future = None

    def update(self, lease_res):
        self.lease_key = lease_res.lease_key
        self.lease_state = lease_res.lease_state
        if self.future is None:
            self.future = self.tree.session.client.lease_break_future(self.lease_key)

    def ref(self):
        self.refs += 1

    def dispose(self):
        self.refs -= 1
        if self.refs == 0:
            self.tree.session.client.dispose_lease(self)

    def on_break(self, cb):
        def handle_break(f):
            notify = f.result()[0]
            if notify.flags & smb2.SMB2_NOTIFY_BREAK_LEASE_FLAG_ACK_REQUIRED:
                chan = self.tree.session.first_channel()
                req = chan.request(obj=self.tree)
                ack = smb2.LeaseBreakAcknowledgement(req)
                ack.lease_key = notify.lease_key
                ack.lease_state = cb(notify.new_lease_state)
                ack_res = chan.connection.transceive(req.parent)[0][0]
                if ack_res.lease_state != smb2.SMB2_LEASE_NONE:
                    self.future = self.tree.session.client.lease_break_future(self.lease_key)
                    self.on_break(cb)
                self.lease_state = ack_res.lease_state
            else:
                self.lease_state = notify.new_lease_state

        self.future.then(handle_break)
