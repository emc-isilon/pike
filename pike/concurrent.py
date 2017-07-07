#
# Copyright (c) 2017, Dell Technologies
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
#       concurrent.py
#
# Abstract:
#
#       Improved concurrency in multi-connection environments
#
# Authors: Masen J. Furer (masen.furer@dell.com)
#

"""
Connection concurrency hacks

This module defines L{ThreadedClient} and L{ThreadedConnection}
subclasses which provide additional locking and synchronization for use in a
multithreaded environment.

Specifically, encoding/decoding packets, sending/receiving data, and all
callbacks and internal future completions will be scheduled for execution
off of the main event loop.

Care must be taken to ensure that callbacks and future completions (and subsequent
notify functions) do not operate on unsynchronized data structures.
"""

import model
import smb2

import array
import operator
from Queue import Queue, Empty
import struct
import time
import threading

class WorkThread(threading.Thread):
    def __init__(self, work_queue, killswitch, work_timeout, *args, **kwds):
        """
        constructor, remaining arguments are passed to threading.Thread
        
        @type work_queue: L{Queue.Queue}
        @param work_queue: shared queue from the L{ThreadPool}
        @type killswitch: L{threading.Event}
        @param killswitch: signals to stop working
        @type work_timeout: positive number
        @param work_timeout: how long to wait on the queue
        """
        super(WorkThread, self).__init__(*args, **kwds)
        self.work_queue = work_queue
        self.killswitch = killswitch
        self.work_timeout = work_timeout
    def run(self):
        """
        Begin processing work from the queue
        """
        while not self.killswitch.is_set():
            try:
                func, future, lock = self.work_queue.get(timeout=self.work_timeout)
                lock.acquire()
                with future:
                    try:
                        future(func())
                    finally:
                        lock.release()
            except Empty:
                pass

class ThreadPool(object):
    def __init__(self, n_threads):
        self.work_timeout = 1
        self.killswitch = threading.Event()
        self.work_queue = Queue()
        self.work_threads = []
        for x in xrange(n_threads):
            t = WorkThread(self.work_queue, self.killswitch, self.work_timeout)
            t.start()
            self.work_threads.append(t)

    def schedule(self, func, future, lock):
        self.work_queue.put((func, future, lock))

    def abort(self):
        self.killswitch.set()
        for t in self.work_threads:
            t.join()

class ThreadedFuture(model.Future):
    """
    Threaded future adds locking around the response member to allow
    future completions to occur on arbitrary threads.

    To execute code in the threaded context, use L{Future.then} to schedule
    a completion routine.

    To execute code in the event context, use L{Future.result} from top level
    code. Never call L{Future.wait} from a callback or notify function

    XXX: if the future is already complete, calling L{Future.then} from an event
    context will run the completion routine on the event thread.
    """

    def __init__(self, request=None):
        """
        Initialize future.

        @param request: The request associated with the response.
        """
        super(ThreadedFuture, self).__init__(request)
        self.response_lock = threading.Lock()
    
    def complete(self, response, traceback=None):
        with self.response_lock:
            self.response = response
            self.traceback = traceback

        # run the callback functions outside of the lock
        for notify in self.notify:
            notify(self)

    def interim(self, *args, **kwds):
        with self.response_lock:
            super(ThreadedFuture, self).interim(*args, **kwds)

    def has_response(self):
        with self.response_lock:
            return self.response is not None

    def has_interim_response(self):
        with self.response_lock:
            return self.response is not None or self.interim_response is not None

class ThreadedClient(model.Client):

    def __init__(self,
                 dialects=[smb2.DIALECT_SMB2_002,
                           smb2.DIALECT_SMB2_1,
                           smb2.DIALECT_SMB3_0,
                           smb2.DIALECT_SMB3_0_2,
                           smb2.DIALECT_SMB3_1_1],
                 capabilities=smb2.GlobalCaps(reduce(operator.or_, smb2.GlobalCaps.values())),
                 security_mode=smb2.SMB2_NEGOTIATE_SIGNING_ENABLED,
                 client_guid=None,
                 work_pool=None):
        super(ThreadedClient, self).__init__(dialects, capabilities, security_mode, client_guid)
        self.cleanup_work_pool = False
        if work_pool is None:
            work_pool = ThreadPool(2)
            self.cleanup_work_pool = True
        self.work_pool = work_pool
    def __del__(self):
        if self.cleanup_work_pool:
            self.work_pool.abort()
    
    def connect_submit(self, server, port=445):
        """
        Create a threaded connection.

        Returns a new L{Future} object for the L{ThreadedConnection} being established
        asynchronously to the given server and port.

        @param server: The server to connect to.
        @param port: The port to connect to.
        """
        return ThreadedConnection(self, server, port).establish().connection_future

    ## TODO: oplock/lease break futures

class ThreadedConnection(model.Connection):

    def __init__(self, client, server, port=445):
        """
        Constructor.

        This should generally not be used directly.  Instead,
        use L{Client.connect}().
        """
        super(ThreadedConnection, self).__init__(client, server, port)
        self.connection_future = ThreadedFuture()
        self.work_pool = client.work_pool
        self.socket_lock = threading.Lock()
        self.work_futures = []

    def submit(self, req):
        """
        When submitting on a ThreadedConnection, an additional future
        will be returned for the completion of the work itself
        catching any additional errors in packet marshalling, sending, or
        user defined callbacks
        """
        self.raise_errors()
        if self.error is not None:
            raise self.error, None, self.traceback
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
                self._out_queue.append(ThreadedFuture(smb_req))
                futures.append(future)
            else:
                future = ThreadedFuture(smb_req)
                self._out_queue.append(future)
                futures.append(future)

        # schedule the packet marshalling and sending to the work pool
        write_future = ThreadedFuture()
        self.work_futures.append(write_future)
        self.work_pool.schedule(
                self.handle_write,
                write_future,
                self.socket_lock)
        return futures

    def handle_read(self):
        self.raise_errors()
        # Try to read the next netbios frame
        remaining = self._watermark - len(self._in_buffer)
        self.process_callbacks(model.EV_RES_PRE_RECV, remaining)
        data = array.array('B', self.recv(remaining))
        self.process_callbacks(model.EV_RES_POST_RECV, data)
        self._in_buffer.extend(data)
        avail = len(self._in_buffer)
        if avail >= 4:
            self._watermark = 4 + struct.unpack('>L', self._in_buffer[0:4])[0]
        if avail == self._watermark:
            self.process_callbacks(model.EV_RES_PRE_DESERIALIZE, self._in_buffer)
            nb_buf = self._in_buffer
            self._in_buffer = array.array('B')
            self._watermark = 4

            # spin off the parsing and future completion to work pool
            def do_parse():
                nb = self.frame()
                nb.parse(nb_buf)
                self._dispatch_incoming(nb)
            read_future = ThreadedFuture()
            self.work_futures.append(read_future)
            self.work_pool.schedule(
                    do_parse,
                    read_future,
                    self.socket_lock)

    def raise_errors(self):
        """
        sweep up errors returned from the work pool
        """
        for f in self.work_futures[:]:
            if f.has_response():
                f.result()
                self.work_futures.remove(f)

