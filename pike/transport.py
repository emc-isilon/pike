from errno import errorcode, EBADF, ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EISCONN, EINPROGRESS, EALREADY, EWOULDBLOCK
import select
import socket
import time

_reraised_exceptions = (KeyboardInterrupt, SystemExit)

class Transport(object):
    def __init__(self):
        self.addr = None
        self.connected = False
        self.socket = None
        self._fileno = None

    def create_socket(self, family, type):
        self.family_and_type = family, type
        sock = socket.socket(family, type)
        sock.setblocking(0)
        self.set_socket(sock)

    def set_socket(self, sock):
        self.socket = sock
        self._fileno = sock.fileno()
        poller.add_channel(self)

    def connect(self, address):
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
        self.socket.close()
        self.connected = False
        poller.del_channel(self)

    def send(self, data):
        return self.socket.send(data)

    def recv(self, bufsize):
        return self.socket.recv(bufsize)

    def handle_connect_event(self):
        self.connected = True
        self.handle_connect()

    def handle_connect(self):
        pass

    def handle_read(self):
        pass

    def handle_close(self):
        pass

    def handle_error(self):
        pass


class BasePoller(object):
    def __init__(self):
        self.connections = {}

    def add_channel(self, transport):
        """
        begin monitoring the transport socket for read/write/error events
        """
        self.connections[transport._fileno] = transport
        transport.poller = self

    def del_channel(self, transport):
        """
        stop monitoring the transport socket
        """
        del self.connections[transport._fileno]

    def poll(self):
        raise NotImplementedError("BasePoller does not have a polling mechanism")

    def process_readables(self, readables):
        for fileno in readables:
            t = self.connections[fileno]
            try:
                if t.readable():
                    t.handle_read()
            except socket.error, e:
                if e.args[0] not in (EBADF, ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
                    t.handle_error()
                else:
                    t.handle_close()
            except _reraised_exceptions:
                raise
            except:
                t.handle_error()


class KQueuePoller(BasePoller):
    def __init__(self):
        super(KQueuePoller, self).__init__()
        self.kq = select.kqueue()
        self.batch_size = 10

    def add_channel(self, transport):
        super(KQueuePoller, self).add_channel(transport)
        events = [select.kevent(transport._fileno,
                                filter=select.KQ_FILTER_READ, # we are interested in reads
                                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE),
                  select.kevent(transport._fileno,
                                filter=select.KQ_FILTER_WRITE, # we are interested in writes
                                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE)]
        self.kq.control(events, 0)

    def poll(self):
        events = self.kq.control(None, self.batch_size, 0)
        readables = []
        for ev in events:
            if ev.filter == select.KQ_FILTER_READ:
                readables.append(ev.ident)
            elif ev.filter == select.KQ_FILTER_WRITE:
                t = self.connections[ev.ident]
                if not t.connected:
                    t.handle_connect_event()
                kevent = select.kevent(t._fileno,
                              filter=select.KQ_FILTER_WRITE,
                              flags=select.KQ_EV_DELETE)
                self.kq.control([kevent],0)
        self.process_readables(readables)


class SelectPoller(BasePoller):
    def poll(self):
        non_connected = [t._fileno for t in self.connections.values() if not t.connected]
        readables, writables, _ = select.select(self.connections.keys(),
                                                non_connected,
                                                [], 0)
        for fd in writables:
            self.connections[fd].handle_connect_event()
        self.process_readables(readables)


class PollPoller(BasePoller):
    def __init__(self):
        super(PollPoller, self).__init__()
        self.p = select.poll()

    def add_channel(self, transport):
        super(PollPoller, self).add_channel(transport)
        self.p.register(
                transport._fileno,
                select.POLLIN | select.POLLOUT | select.POLLERR)

    def del_channel(self, transport):
        super(PollPoller, self).del_channel(transport)
        self.p.unregister(transport._fileno)

    def poll(self):
        events = self.p.poll(0)
        readables = []
        for fd, event in events:
            if event == select.POLLIN:
                readables.append(fd)
            elif event == select.POLLOUT:
                t = self.connections[fd]
                if not t.connected:
                    t.handle_connect_event()
                self.p.modify(fd, select.POLLIN | select.POLLERR)
            elif event == select.POLLERR:
                t = self.connections[fd]
                t.handle_error()
        self.process_readables(readables)


# use the best polling mechanism available on the system
if hasattr(select, "kqueue"):
    poller = KQueuePoller()
elif hasattr(select, "poll"):
    poller = PollPoller()
else:
    poller = SelectPoller()

def loop(timeout=None, count=None):
    start = time.time()
    complete_iterations = 0
    while True:
        if count is not None and complete_iterations >= count:
            break
        poller.poll()
        if timeout is not None and time.time() > start + timeout:
            break
        complete_iterations += 1
