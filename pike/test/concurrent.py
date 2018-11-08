"""
This test serves as an example for writing high-scale workflow tests utilizing
thousands of connections and a fully asynchrounous chained-callback style using
Future completion to chain events.

The test leverages pike.concurrent hacks in order to spin off packet encoding/decoding
and callbacks/future completion to work threads in order to keep the event thread
clear for processing incoming data.

There is still room for improvement, as this can really only generate 5-10mb of
traffic as it is.

Example usage::

    python -m unittest -c pike.test.concurrent.TestConnectScale
    python -m unittest -c pike.test.concurrent.TestBFLG

ConnectScale - establish a given number of connections and keep them idle for
    a given period of time
BFLG - baby's first load generator. super simple example of how to slam as many
    WRITE requests as possible as a server

Pike is designed to be an extensible test framework -- there are many
bottlenecks in the system that slow us down extensively in exchange for
flexibility. Pike is not designed to be a stress or load generation tool.
However, it is extensible enough, that one theoretically could optimize
some of the data paths in handle_read/handle_write and in the Smb2 / Command
encode/decode routines to trade flexibility for speed.
"""

import pike.concurrent
import pike.model
import pike.smb2 as smb2
import pike.test
import pike.transport

import array
import time
import threading

class ConnectScaleClient(object):
    def __init__(self, server, creds, share, connect_time, keepalive_time, work_pool):
        """
        Establish the connection
        """
        # if killswitch gets set, abort processing and complete the future
        self.killswitch = threading.Event()
        # when all iterations have completed, this future will complete
        # client_future is also used to bubble exceptions to the top level
        self.client_future = pike.model.Future()
        self.creds = creds
        self.share = share
        self.stop_time = time.time() + connect_time
        self.keepalive_time = keepalive_time
        self.keepalive_timer = None
        self.connection = None

        pike.concurrent.ThreadedClient(work_pool=work_pool).connect_submit(server).then(
                self.step_1_on_connect_send_negotiate)

    def result(self, *args, **kwds):
        return self.client_future.result(*args, **kwds)

    def send_echo_async(self):
        """
        Send an echo request and return a future for the response
        """
        smb_req = self.channel.request()
        enum_req = smb2.EchoRequest(smb_req)
        return self.connection.submit(smb_req.parent)[0]

    def fire_echo_async(self):
        """
        Send an echo request and set the callback to step_5
        """
        echo_future = self.send_echo_async()
        echo_future.then(self.step_5_send_echo_loop)
        self.keepalive_timer = None

    def _internal_abort(self):
        self.client_future.complete(False)
        if self.connection is not None:
            self.connection.close()

    def step_1_on_connect_send_negotiate(self, connect_future):
        """
        Send the negotiate request
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.connection = connect_future.result()
            self.connection.negotiate_submit(self.connection.negotiate_request()).then(
                    self.step_2_on_negotiate_send_session_setup)

    def step_2_on_negotiate_send_session_setup(self, negotiate_future):
        """
        Send the session setup request(s)
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.connection.SessionSetupContext(
                    self.connection,
                    self.creds).submit().then(
                            self.step_3_on_session_send_tree_connect)

    def step_3_on_session_send_tree_connect(self, channel_future):
        """
        Send the tree connect
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.channel = channel_future.result()
            self.channel.tree_connect_submit(self.channel.tree_connect_request(self.share)).then(
                    self.step_4_finish_tree_connect)

    def step_4_finish_tree_connect(self, tree_future):
        """
        Save a reference to the tree and send first keepalive
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.tree = tree_future.result()
            self.fire_echo_async()

    def step_5_send_echo_loop(self, echo_future):
        """
        If the timeout has not expired, schedule an echo to be sent
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            # call .result() in the unlikely event that echo failed
            echo_future.result()
            if time.time() + self.keepalive_time < self.stop_time:
                # the only time we should re-enter this function is when
                # the timer has expired AND the echo result is available
                if self.keepalive_timer and self.keepalive_timer.is_alive():
                    raise AssertionError("keepalive_timer is active when it shouldn't be")
                self.keepalive_timer = threading.Timer(self.keepalive_time, self.fire_echo_async)
                self.keepalive_timer.start()
            else:
                self.client_future.complete(True)


class TestConnectScale(pike.test.PikeTest):
    def setUp(self):
        self.work_pool = pike.concurrent.ThreadPool(16)
    def tearDown(self):
        self.work_pool.abort()
    def _gen_connection_scale(self, n_connections, connect_time, keepalive_time):
        """
        Establish multiple connections to the server, negotiate, session_setup,
        tree_connect and then send echo commands until the timeout expires
        """
        clients = []
        for ix in xrange(n_connections):
            clients.append(ConnectScaleClient(self.server, self.creds, self.share, connect_time, keepalive_time, self.work_pool))

        # poll the clients and raise errors
        while clients:
            for c in clients[:]:
                try:
                    self.assertTrue(c.result(timeout=1))
                    clients.remove(c)
                except pike.model.TimeoutError:
                    pass    # result not yet available
                except:
                    print("Unexpected error, setting killswitch")
                    # unexpected error is encountered, kill all clients and bail
                    map(lambda c: c.killswitch.set(), clients[:])
                    pike.transport.loop(timeout=5)
                    raise
    def _test_1_30_5_connection_scale(self):
        self._gen_connection_scale(1, 30, 5)
    def test_1000_30_5_connection_scale(self):
        self._gen_connection_scale(1000, 30, 5)

class BFLGClient(object):
    buf = array.array("B", "\0\1\2\3\4\5\6\7"*8192)
    def __init__(self, server, creds, share, load_time, io_file_name, io_block_size, work_pool):
        """
        Establish the connection
        """
        # if killswitch gets set, abort processing and complete the future
        self.killswitch = threading.Event()
        # when all iterations have completed, this future will complete
        # client_future is also used to bubble exceptions to the top level
        self.client_future = pike.model.Future()
        self.creds = creds
        self.share = share
        self.io_file_name = io_file_name
        self.io_block_size = io_block_size
        self.stop_time = time.time() + load_time
        self.connection = None

        pike.concurrent.ThreadedClient(work_pool=work_pool).connect_submit(server).then(
                self.step_1_on_connect_send_negotiate)

    def result(self, *args, **kwds):
        return self.client_future.result(*args, **kwds)

    def fire_write_async(self):
        """
        Send an write request and set the callback to step_6
        """
        write_future = self.connection.submit(self.channel.write_request(self.fh, 0, self.buf[:self.io_block_size]).parent.parent)[0]
        write_future.then(self.step_6_send_write_loop)

    def _internal_abort(self):
        self.client_future.complete(False)
        if self.connection is not None:
            self.connection.close()

    def step_1_on_connect_send_negotiate(self, connect_future):
        """
        Send the negotiate request
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.connection = connect_future.result()
            self.connection.negotiate_submit(self.connection.negotiate_request()).then(
                    self.step_2_on_negotiate_send_session_setup)

    def step_2_on_negotiate_send_session_setup(self, negotiate_future):
        """
        Send the session setup request(s)
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.connection.SessionSetupContext(
                    self.connection,
                    self.creds).submit().then(
                            self.step_3_on_session_send_tree_connect)

    def step_3_on_session_send_tree_connect(self, channel_future):
        """
        Send the tree connect
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.channel = channel_future.result()
            self.channel.tree_connect_submit(self.channel.tree_connect_request(self.share)).then(
                    self.step_4_on_tree_connect_send_create)

    def step_4_on_tree_connect_send_create(self, tree_future):
        """
        Save a reference to the tree and send create request
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            self.tree = tree_future.result()
            create_future = self.connection.submit(self.channel.create_request(self.tree, self.io_file_name, share=0x7).parent.parent)[0]
            create_future.then(self.step_5_on_create_begin_write_loop)

    def step_5_on_create_begin_write_loop(self, create_future):
        """
        Create an Open from the create response and start the write loop
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            create_resp = create_future.result()
            self.fh = pike.model.Open(self.tree, create_resp)
            self.fire_write_async()

    def step_6_send_write_loop(self, write_future):
        """
        If the timeout has not expired, schedule a write to be sent
        """
        if self.killswitch.is_set():
            self._internal_abort()
            return
        with self.client_future:
            # call .result() in the unlikely event that write failed
            write_future.result()
            if time.time() < self.stop_time:
                self.fire_write_async()
            else:
                self.client_future.complete(True)

class TestBFLG(pike.test.PikeTest):
    def setUp(self):
        self.work_pool = pike.concurrent.ThreadPool(16)
    def tearDown(self):
        self.work_pool.abort()
    def _gen_write_load(self, n_connections, load_time, io_block_size):
        """
        Establish multiple connections to the server, negotiate, session_setup,
        tree_connect, create and then send write commands until the timeout expires
        """
        clients = []
        for ix in xrange(n_connections):
            clients.append(BFLGClient(self.server, self.creds, self.share, load_time, "target_file_{0}".format(ix), io_block_size, self.work_pool))

        # poll the clients and raise errors
        while clients:
            for c in clients[:]:
                try:
                    self.assertTrue(c.result(timeout=1))
                    clients.remove(c)
                except pike.model.TimeoutError:
                    pass    # result not yet available
                except:
                    print("Unexpected error, setting killswitch")
                    # unexpected error is encountered, kill all clients and bail
                    map(lambda c: c.killswitch.set(), clients[:])
                    pike.transport.loop(timeout=5)
                    raise
    def _test_1_30_8192_write_load(self):
        self._gen_write_load(1, 30, 8192)
    def test_512_30_65536_write_load(self):
        self._gen_write_load(512, 30, 65536)
