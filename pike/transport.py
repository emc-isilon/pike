#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        transport.py
#
# Abstract:
#
#        Async event loop, socket handling, and polling mechanisms
#
# Authors: Masen Furer (masen.furer@dell.com)
#

from builtins import object
from errno import (
    errorcode,
    EBADF,
    ECONNRESET,
    ENOTCONN,
    ESHUTDOWN,
    ECONNABORTED,
    EISCONN,
    EINPROGRESS,
    EALREADY,
    EWOULDBLOCK,
    EAGAIN,
)
import select
import socket
import time

_reraised_exceptions = (KeyboardInterrupt, SystemExit)


class Transport(object):
    """
    Transport is responsible for managing the underlying socket, registering
    for socket events, dispatching read, write, and errors to higher layers.
    It is analogous to asyncore.dispatcher and is a drop in replacement for
    most purposes.

    If the alternate_poller is specified on instantiation, then the connection
    will register for events on that poller as opposed to the global poller.
    """

    def __init__(self, alternate_poller=None):
        self.addr = None
        self.connected = False
        self.socket = None
        self._fileno = None
        if alternate_poller is not None:
            self.poller = alternate_poller
        else:
            self.poller = poller  # global poller

    def create_socket(self, family, type):
        """
        Creates the underlying non-blocking socket and associates it with this
        Transport's underlying poller
        """
        self.family_and_type = family, type
        sock = socket.socket(family, type)
        sock.setblocking(0)
        self.set_socket(sock)

    def set_socket(self, sock):
        """
        mirror the given Socket sock's file descriptor on the Transport and
        register this Transport with the underlying poller
        """
        self.socket = sock
        self._fileno = sock.fileno()
        self.poller.add_channel(self)

    def connect(self, address):
        """
        begin establishing a connection to the (host, port) address tuple.

        must call create_socket first. if the underlying socket is non-blocking
        then this command may return before the connection is established.

        higher level code should wait for the handle_connect event to signal
        that the endpoint is successfully connected
        """
        self.connected = False
        err = self.socket.connect_ex(address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
            return
        if err in (0, EISCONN):
            self.addr = address
            self.handle_connect_event()
        else:
            raise socket.error(err, errorcode[err])

    def close(self):
        """
        close the underlying socket connection and unregister this Transport
        from the underlying poller
        """
        self.socket.close()
        self.connected = False
        self.poller.del_channel(self)

    def send(self, data):
        """
        send data bytes over the connection. if the socket would block,
        schedule this Transport to be notified when the socket is available
        for writing. handle_write will be called in this case.

        returns the number of bytes sent or zero if the write would block
        """
        result = 0
        try:
            result = self.socket.send(data)
        except socket.error as err:
            if err.errno == EAGAIN:
                # reschedule the send when the socket is ready
                self.poller.defer_write(self)
            else:
                # raise non-retryable errors
                raise
        return result

    def recv(self, bufsize):
        """
        recv bufsize bytes over the connection. if the socket would block,
        then return an empty buffer. When the socket is available for reading
        handle_read will be called.

        returns a string representing the bytes received
        """
        result = ""
        try:
            result = self.socket.recv(bufsize)
            if result == "":
                raise EOFError("Remote host closed connection")
        except socket.error as err:
            # raise non-retryable errors
            if err.errno != EAGAIN:
                raise
        return result

    def handle_connect_event(self):
        """
        called internally when the socket becomes connected
        """
        self.connected = True
        self.handle_connect()

    def handle_connect(self):
        """
        callback fired when connection is established
        """
        pass

    def handle_read(self):
        """
        callback fired when the socket has data available
        """
        pass

    def handle_write(self):
        """
        callback fired when the socket is available for writing

        note: unlike asyncore, write notifications are not provided by default.
        this is a performance optimization because the socket is usually
        available for writing, and the application usually knows when it wants
        to write. There is no point in filling the event queues with
        write ready messages that will be ignored if the client has no data to
        send.

        Instead, applications are expected to implement handle_write, but to
        call it directly when data is to be sent. IF the socket would block,
        EALREADY will be handled by the Transport. The Transport requests a
        single write notification from the pollwer; when received, handle_write
        will be called once signalling that the socket may now be ready to retry

        If the application would prefer to be notified when the socket is ready
        to write, transport.poller.defer_write(transport) may be called to
        schedule a single handle_write callback.
        """
        pass

    def handle_close(self):
        """
        callback fired when the socket is closed
        """
        pass

    def handle_error(self):
        """
        callback fired if a non-recoverable exception is raised
        """
        pass


class BasePoller(object):
    """
    A poller is an underlying event monitoring system. This generic class
    can be built upon to implement efficient file descriptor polling methods
    which are available on various platforms.

    A minimal subclass must implement the poll() function which performs a
    single iteration of the event loop across all monitored Transports and
    calls process_readables and process_writables with the correct values.

    Subclasses should, in most cases call, into BasePoller methods in order
    to maintain proper accounting structures. The exception is when the poller
    handles accounting itself.
    """

    def __init__(self):
        """
        initialize the poller and register any kernel global structures
        necessary to monitor the file descriptors
        """
        self.connections = {}
        self.deferred_writers = set()

    def add_channel(self, transport):
        """
        begin monitoring the transport socket for read/connect events

        the underlying poller should not monitor Transports for writability
        except when:
            * the Transport's connection has not yet been established
            * the Transport has been passed as an argument to defer_write
        """
        self.connections[transport._fileno] = transport
        transport.poller = self

    def del_channel(self, transport):
        """
        stop monitoring the transport socket
        """
        del self.connections[transport._fileno]

    def defer_write(self, transport):
        """
        defers a write on the given transport. once the async poller determines
        that the transport can be written to, handle_write will be called
        """
        self.deferred_writers.add(transport._fileno)

    def loop(self, timeout=None, count=None):
        """
        enter the async event loop for the given timeout or number of iterations
        """
        start = time.time()
        complete_iterations = 0
        while True:
            if count is not None and complete_iterations >= count:
                break
            self.poll()
            if timeout is not None and time.time() > start + timeout:
                break
            complete_iterations += 1

    def poll(self):
        """
        Must be implemented by subclasses to execute a single iteration of the
        event loop. Based on the outcome of the events, the following actions
        MUST be performed

            * process_readables is called with a list of file descriptors which
              have data available for reading
            * process_writables is called with a list of file descriptors which
              have data available for writing
        """
        raise NotImplementedError("BasePoller does not have a polling mechanism")

    def process_readables(self, readables):
        """
        call handle_read on each applicable fd in the readables sequence and
        subsequently handle_error if any exception is raised or handle_close
        if the underlying socket is no longer connected
        """
        for fileno in readables:
            t = self.connections[fileno]
            try:
                t.handle_read()
            except socket.error as e:
                if e.args[0] not in (
                    EBADF,
                    ECONNRESET,
                    ENOTCONN,
                    ESHUTDOWN,
                    ECONNABORTED,
                ):
                    t.handle_error()
                else:
                    t.handle_close()
            except _reraised_exceptions:
                raise
            except:
                t.handle_error()

    def process_writables(self, writables):
        """
        for each Transport t corresponding to an fd in the writables sequence,
            if t is not marked as connected, call handle_connect_event
            otherwise call handle_write and remove the Transport from the set
            of deferred writers
            process close and error events if exception is encountered
        """
        for fileno in writables:
            t = self.connections[fileno]
            try:
                if not t.connected:
                    t.handle_connect_event()
                else:
                    if fileno in self.deferred_writers:
                        self.deferred_writers.remove(fileno)
                    t.handle_write()
            except socket.error as e:
                if e.args[0] not in (
                    EBADF,
                    ECONNRESET,
                    ENOTCONN,
                    ESHUTDOWN,
                    ECONNABORTED,
                ):
                    t.handle_error()
                else:
                    t.handle_close()
            except _reraised_exceptions:
                raise
            except:
                t.handle_error()


class KQueuePoller(BasePoller):
    """
    Implementation of KQueue, available on Mac OS and BSD derivatives
    """

    def __init__(self):
        super(KQueuePoller, self).__init__()
        self.kq = select.kqueue()
        self.batch_size = 10

    def add_channel(self, transport):
        super(KQueuePoller, self).add_channel(transport)
        events = [
            select.kevent(
                transport._fileno,
                filter=select.KQ_FILTER_READ,
                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE,
            ),
            select.kevent(
                transport._fileno,
                filter=select.KQ_FILTER_WRITE,
                flags=(select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT),
            ),
        ]
        self.kq.control(events, 0)

    def defer_write(self, transport):
        super(KQueuePoller, self).defer_write(transport)
        events = [
            select.kevent(
                transport._fileno,
                filter=select.KQ_FILTER_WRITE,
                flags=(select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT),
            )
        ]
        self.kq.control(events, 0)

    def poll(self):
        events = self.kq.control(None, self.batch_size, 0)
        readables = []
        writables = []
        for ev in events:
            if ev.filter == select.KQ_FILTER_READ:
                readables.append(ev.ident)
            elif ev.filter == select.KQ_FILTER_WRITE:
                writables.append(ev.ident)
        self.process_readables(readables)
        self.process_writables(writables)


class SelectPoller(BasePoller):
    """
    Implementation of select, available on most platforms as a fallback.

    Roughly equivalent performance to using asyncore
    """

    def poll(self):
        non_connected = [
            t._fileno for t in self.connections.values() if not t.connected
        ]
        readers = list(self.connections.keys())
        writers = non_connected + list(self.deferred_writers)
        readables, writables, _ = select.select(readers, writers, [], 0)
        self.process_readables(readables)
        self.process_writables(writables)


class PollPoller(BasePoller):
    """
    Implementation of poll, available on Linux
    """

    def __init__(self):
        super(PollPoller, self).__init__()
        self.p = select.poll()
        self.read_events = (
            select.POLLIN
            | select.POLLERR
            | select.POLLHUP
            | select.POLLNVAL
            | select.POLLMSG
            | select.POLLPRI
        )
        self.write_events = select.POLLOUT

    def add_channel(self, transport):
        super(PollPoller, self).add_channel(transport)
        self.p.register(transport._fileno, self.read_events | self.write_events)

    def del_channel(self, transport):
        super(PollPoller, self).del_channel(transport)
        self.p.unregister(transport._fileno)

    def defer_write(self, transport):
        super(PollPoller, self).defer_write(transport)
        self.p.modify(transport._fileno, self.read_events | self.write_events)

    def poll(self):
        events = self.p.poll(0)
        readables = []
        writables = []
        for fd, event in events:
            if event & self.read_events:
                readables.append(fd)
            elif event & self.write_events:
                writables.append(fd)
                self.p.modify(fd, self.read_events)
        self.process_readables(readables)
        self.process_writables(writables)


# Global poller / loop function for simple use cases
# more advanced tests or frameworks may use a custom
# poller implementation by setting a poller object onto
# a group of transports.
# The global poller will use the best polling mechanism available on the system
if hasattr(select, "kqueue"):
    poller = KQueuePoller()
elif hasattr(select, "poll"):
    poller = PollPoller()
else:
    poller = SelectPoller()


def loop(timeout=None, count=None):
    poller.loop(timeout, count)
