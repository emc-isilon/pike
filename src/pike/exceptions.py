"""
Exceptions used by multiple modules are defined here
"""

from . import core


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
    """
    Raised when an Smb2 response contains an unexpected NTSTATUS.
    """

    def __init__(self, response):
        Exception.__init__(self, response.command, response.status)
        self.response = response
