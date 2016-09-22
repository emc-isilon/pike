from errno import errorcode, EBADF, ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EISCONN, EINPROGRESS, EALREADY, EWOULDBLOCK
import select
import socket
import time

_reraised_exceptions = (KeyboardInterrupt, SystemExit)

class KQueuePoller(object):
    def __init__(self):
        self.kq = select.kqueue()
        self.connections = {}

    def add_channel(self, transport):
        """
        begin monitoring the transport socket for read/write/error events
        """
        self.connections[transport._fileno] = transport
        events = [select.kevent(transport._fileno,
                                filter=select.KQ_FILTER_READ, # we are interested in reads
                                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE),
                  select.kevent(transport._fileno,
                                filter=select.KQ_FILTER_WRITE, # we are interested in writes
                                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE)]
        self.kq.control(events, 0)

    def del_channel(self, transport):
        """
        stop monitoring the transport socket
        """
        del self.connections[transport._fileno]

    def poll(self, n_events=10):
        # Process events
        events = self.kq.control(None, n_events, 0)
        for ev in events:
            t = self.connections[ev.ident]
            try:
                if ev.filter == select.KQ_FILTER_READ and t.readable():
                    t.handle_read()
                elif ev.filter == select.KQ_FILTER_WRITE:
                    if not t.connected:
                        t.connected = True
                        t.handle_connect_event()
                    kevent = select.kevent(t._fileno,
                                  filter=select.KQ_FILTER_WRITE,
                                  flags=select.KQ_EV_DELETE)
                    self.kq.control([kevent],0)
            except socket.error, e:
                if e.args[0] not in (EBADF, ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
                    t.handle_error()
                else:
                    t.handle_close()
            except _reraised_exceptions:
                raise
            except:
                t.handle_error()

        # Process pending writes
        for t in self.connections.values():
            try:
                if t.writable():
                    t.handle_write()
            except socket.error, e:
                if e.args[0] not in (EBADF, ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
                    t.handle_error()
                else:
                    t.handle_close()
            except _reraised_exceptions:
                raise
            except:
                t.handle_error()

poller = KQueuePoller()

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
        # XXX Should interpret Winsock return values
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

    def readable(self):
        return True
    def writable(self):
        return True

    def handle_connect_event(self):
        self.connected = True
        self.handle_connect()

    def handle_connect(self):
        pass
    def handle_read(self):
        pass
    def handle_write(self):
        pass
    def handle_close(self):
        pass
    def handle_error(self):
        pass
