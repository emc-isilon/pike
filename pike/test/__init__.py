#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test.py
#
# Abstract:
#
#        Test infrastructure
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

from __future__ import print_function
from __future__ import division
from builtins import object
from builtins import str
from future.utils import raise_from

import contextlib
import enum
import gc
import logging
import os
import unittest
import sys

import attr

import pike.model as model
import pike.ntstatus as ntstatus
import pike.smb2 as smb2


_NotSet = object()
_Required = object()


class MissingArgument(Exception):
    pass


class SequenceError(Exception):
    """Raised when calling TreeConnect helpers in the wrong state"""


class TestRequirementNotMet(Exception):
    """The test requires some dialect or capability that was not met"""


class DialectMissing(TestRequirementNotMet):
    pass


class CapabilityMissing(TestRequirementNotMet):
    pass


class ShareCapabilityMissing(TestRequirementNotMet):
    pass


class Options(enum.Enum):
    PIKE_LOGLEVEL = "PIKE_LOGLEVEL"
    PIKE_TRACE = "PIKE_TRACE"
    PIKE_SERVER = "PIKE_SERVER"
    PIKE_PORT = "PIKE_PORT"
    PIKE_CREDS = "PIKE_CREDS"
    PIKE_SHARE = "PIKE_SHARE"
    PIKE_SIGN = "PIKE_SIGN"
    PIKE_ENCRYPT = "PIKE_ENCRYPT"
    PIKE_MIN_DIALECT = "PIKE_MIN_DIALECT"
    PIKE_MAX_DIALECT = "PIKE_MAX_DIALECT"

    @classmethod
    def option(cls, name, default=None):
        if isinstance(name, cls):
            # convert from Enum type to str
            name = name.value
        value = os.environ.get(name, _NotSet)
        if value is _NotSet or len(value) == 0:
            if default is _Required:
                raise MissingArgument(
                    "Environment variable {!r} must be set".format(name)
                )
            value = default
        return value

    @classmethod
    def booloption(cls, name, default="no"):
        table = {"yes": True, "true": True, "no": False, "false": False, "": False}
        return table[cls.option(name, default=default).lower()]

    @classmethod
    def smb2constoption(cls, name, default=None):
        return getattr(smb2, cls.option(name, "").upper(), default)

    @classmethod
    def loglevel(cls):
        return getattr(logging, cls.option(cls.PIKE_LOGLEVEL, default="NOTSET").upper())

    @classmethod
    def trace(cls):
        return cls.booloption(cls.PIKE_TRACE)

    @classmethod
    def server(cls):
        return cls.option(cls.PIKE_SERVER, default=_Required)

    @classmethod
    def port(cls):
        return int(cls.option(cls.PIKE_PORT, default="445"))

    @classmethod
    def creds(cls):
        return cls.option(cls.PIKE_CREDS)

    @classmethod
    def share(cls):
        return cls.option(cls.PIKE_SHARE, "c$")

    @classmethod
    def signing(cls):
        return cls.booloption(cls.PIKE_SIGN)

    @classmethod
    def encryption(cls):
        return cls.booloption(cls.PIKE_ENCRYPT)

    @classmethod
    def min_dialect(cls):
        return cls.smb2constoption(cls.PIKE_MIN_DIALECT, default=0)

    @classmethod
    def max_dialect(cls):
        return cls.smb2constoption(cls.PIKE_MAX_DIALECT, default=float("inf"))


def default_client(signing=None):
    client = model.Client()
    min_dialect = Options.min_dialect()
    max_dialect = Options.max_dialect()
    client.restrict_dialects(min_dialect, max_dialect)
    if signing is None:
        signing = Options.signing()
    if signing:
        client.security_mode = (
            smb2.SMB2_NEGOTIATE_SIGNING_ENABLED | smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED
        )
    return client


@attr.s
class TreeConnect(object):
    """
    Combines a Client, Connection, Channel, and Tree for simple access to an SMB share.
    """

    _client = attr.ib(default=None)
    server = attr.ib(factory=Options.server)
    port = attr.ib(factory=Options.port)
    creds = attr.ib(factory=Options.creds)
    share = attr.ib(factory=Options.share)
    resume = attr.ib(default=None)
    signing = attr.ib(factory=Options.signing)
    encryption = attr.ib(factory=Options.encryption)
    require_dialect = attr.ib(default=None)
    require_capabilities = attr.ib(default=None)
    require_share_capabilities = attr.ib(default=None)
    conn = attr.ib(default=None, init=False)
    chan = attr.ib(default=None, init=False)
    tree = attr.ib(default=None, init=False)

    @require_dialect.validator
    def _require_dialect_validator(self, attribute, value):
        if value and len(value) != 2:
            raise TypeError(
                "require_dialect must be specified as a 2-tuple of (min_dialect, "
                "max_dialect), not {!r}".format(value)
            )

    @property
    def client(self):
        return self._client or default_client(signing=self.signing)

    def connect(self):
        """
        Establish a connection to the server and complete SMB2 NEGOTIATE.

        If a require_dialect or require_capability is specified to __init__, then
        an exception will be raised if the server does not support the required dialect
        or does not advertise the required capability.

        :return: connected pike.model.Connection
        """
        if self.conn and self.conn.connected:
            raise SequenceError(
                "Already connected: {!r}. Must call close() before reconnecting".format(
                    self.conn
                )
            )
        self.conn = self.client.connect(server=self.server, port=self.port).negotiate()
        negotiated_dialect = self.conn.negotiate_response.dialect_revision
        if self.require_dialect and (
            negotiated_dialect < self.require_dialect[0]
            or negotiated_dialect > self.require_dialect[1]
        ):
            self.close()
            raise DialectMissing("Dialect required: {}".format(self.require_dialect))

        capabilities = self.conn.negotiate_response.capabilities
        if self.require_capabilities and (
            capabilities & self.require_capabilities != self.require_capabilities
        ):
            self.close()
            raise CapabilityMissing(
                "Server does not support: %s "
                % str(self.require_capabilities & ~capabilities)
            )
        return self.conn

    def session_setup(self):
        """
        Establish a session on the connection and complete SMB2 SESSION_SETUP.

        If resume is specified to __init__, the new session will include the resumed
        session as previous_session_id.

        If encryption is specified to __init__ (or with PIKE_ENCRYPT environment var)
        the new session will encrypt data by default.

        :return: pike.model.Channel
        """
        if not self.conn or not self.conn.connected:
            raise SequenceError("Not connected. Must call connect() first")
        if self.chan:
            raise SequenceError(
                "Channel already established: {!r}. Must call close() before reconnecting".format(
                    self.chan
                )
            )
        self.chan = self.conn.session_setup(self.creds, resume=self.resume)
        if self.encryption:
            self.chan.session.encrypt_data = True
        return self.chan

    def tree_connect(self):
        """
        Establish a tree connection on the session and complete SMB2 TREE_CONNECT.

        If require_share_capability is specified to __init__, then
        an exception will be raised if the share does not does not advertise the
        required capability.

        :return: pike.model.Tree
        """
        if not self.chan:
            raise SequenceError(
                "Channel not established. Must call session_setup() first"
            )
        if self.tree:
            raise SequenceError(
                "Tree already connected: {!r}. Must call close() before reconnecting".format(
                    self.tree
                )
            )
        self.tree = self.chan.tree_connect(self.share)
        capabilities = self.tree.tree_connect_response.capabilities
        if self.require_share_capabilities and (
            capabilities & self.require_share_capabilities
            != self.require_share_capabilities
        ):
            self.close()
            raise ShareCapabilityMissing(
                "Share does not support: %s"
                % str(self.require_share_capabilities & ~capabilities)
            )
        return self.tree

    def __call__(self):
        """
        Perform all initialization steps (if needed). If the connection, channel, or
        tree is already established, this call is a no-op for those objects.

        :return: the established TreeConnect instance
        """
        if not self.conn:
            self.connect()
        if not self.chan:
            self.session_setup()
        if not self.tree:
            self.tree_connect()
        return self

    def close(self):
        """
        Perform de-initialization for all established objects. If any object has
        already been disconnected or set to None, then nothing will happen.

        For example, to perform SESSION_LOGOFF without first doing a TREE_DISCONNECT,
        simply set self.tree = None before calling close().

        Additionally, to disconnect without SESSION_LOGOFF, set self.chan = None.

        If the tree has already been disconnected or channel already closed, then
        errors related to cleaning up twice are suppressed.
        """
        if not self.conn or not self.conn.connected:
            self.conn = self.chan = self.tree = None
            return
        if self.tree and self.chan:
            try:
                self.chan.tree_disconnect(self.tree)
            except model.ResponseError as err:
                if err.response.status == ntstatus.STATUS_USER_SESSION_DELETED:
                    self.chan = None
                elif err.response.status != ntstatus.STATUS_NETWORK_NAME_DELETED:
                    raise
            except EOFError:
                self.chan = None
            self.tree = None
        if self.chan:
            try:
                self.chan.logoff()
            except model.ResponseError as err:
                if err.response.status != ntstatus.STATUS_USER_SESSION_DELETED:
                    raise
            except EOFError:
                pass
            self.chan = self.tree = None
        if self.conn.connected:
            self.conn.close()
            self.conn = self.chan = self.tree = None

    def __enter__(self):
        """
        Context manager protocol. Establish connection, channel, and tree if not
        already established.

        :return: self
        """
        return self()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager protocol. Calls close() to close any open objects.
        """
        self.close()

    def __del__(self):
        """
        Garbage collection. Calls close() to close any open objects.
        """
        self.close()

    def __iter__(self):
        """
        Compatibility shim to mirror the previous return value of PikeTest.tree_connect
        """
        yield self.chan
        yield self.tree

    def __getitem__(self, item):
        """
        Compatibility shim to mirror the previous return value of PikeTest.tree_connect
        """
        return tuple(self)[item]


class PikeTest(unittest.TestCase):
    init_done = False

    @staticmethod
    def init_once():
        if not PikeTest.init_done:
            PikeTest.loglevel = Options.loglevel()
            PikeTest.handler = logging.StreamHandler()
            PikeTest.handler.setLevel(PikeTest.loglevel)
            PikeTest.handler.setFormatter(
                logging.Formatter("%(asctime)s:%(name)s:%(levelname)s: %(message)s")
            )
            PikeTest.logger = logging.getLogger("pike")
            PikeTest.logger.addHandler(PikeTest.handler)
            PikeTest.logger.setLevel(PikeTest.loglevel)
            model.trace = PikeTest.trace = Options.trace()
            PikeTest.init_done = True

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.init_once()
        self._connections = []
        self.default_client = default_client()
        self.server = Options.server()
        self.port = Options.port()
        self.creds = Options.creds()
        self.share = Options.share()
        self.signing = Options.signing()
        self.encryption = Options.encryption()
        self.min_dialect = Options.min_dialect()
        self.max_dialect = Options.max_dialect()

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def warn(self, *args, **kwargs):
        self.logger.warn(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        self.logger.critical(*args, **kwargs)

    def set_client_dialect(self, min_dialect=None, max_dialect=None, client=None):
        if client is None:
            client = self.default_client
        client.restrict_dialects(min_dialect, max_dialect)

    def tree_connect(self, client=None, resume=None):
        tc = TreeConnect(
            client=client or self.default_client,
            server=self.server,
            port=self.port,
            creds=self.creds,
            share=self.share,
            resume=resume,
            encryption=self.encryption,
            require_dialect=self.required_dialect(),
            require_capabilities=self.required_capabilities(),
            require_share_capabilities=self.required_share_capabilities(),
        )
        try:
            tc()
        except TestRequirementNotMet as err:
            raise_from(unittest.SkipTest(str(err)), err)
        # save a reference to the TreeConnect object to avoid it being __del__'d
        self._connections.append(tc)
        return tc

    class _AssertErrorContext(object):
        pass

    @contextlib.contextmanager
    def assert_error(self, status):
        e = None
        o = PikeTest._AssertErrorContext()

        try:
            yield o
            raise self.failureException('No error raised when "%s" expected' % status)
        except model.ResponseError as err:
            o.response = err.response
            if err.response.status != status:
                raise_from(
                    self.failureException(
                        '"%s" raised when "%s" expected'
                        % (err.response.status, status),
                    ),
                    err,
                )

    def setUp(self):
        if self.loglevel != logging.NOTSET:
            print(file=sys.stderr)

        if hasattr(self, "setup"):
            self.setup()

    def tearDown(self):
        if hasattr(self, "teardown"):
            self.teardown()

        for conn in self._connections:
            conn.close()
        del self._connections[:]
        # Reference cycles are common in pike. so garbage collect aggressively
        gc.collect()

    def _get_decorator_attr(self, name, default):
        name = "__pike_test_" + name
        test_method = getattr(self, self._testMethodName)

        if hasattr(test_method, name):
            return getattr(test_method, name)
        elif hasattr(self.__class__, name):
            return getattr(self.__class__, name)
        else:
            return default

    def required_dialect(self):
        return self._get_decorator_attr("RequireDialect", (0, float("inf")))

    def required_capabilities(self):
        return self._get_decorator_attr("RequireCapabilities", 0)

    def required_share_capabilities(self):
        return self._get_decorator_attr("RequireShareCapabilities", 0)

    def assertBufferEqual(self, buf1, buf2):
        """
        Compare two sequences using a binary diff to efficiently determine
        the first offset where they differ
        """
        if len(buf1) != len(buf2):
            raise AssertionError("Buffers are not the same size")
        low = 0
        high = len(buf1)
        while high - low > 1:
            # XXX: consider usage of stdlib bisect module
            chunk_1 = (low, low + ((high - low) // 2))
            chunk_2 = (chunk_1[1], high)
            if buf1[chunk_1[0] : chunk_1[1]] != buf2[chunk_1[0] : chunk_1[1]]:
                low, high = chunk_1
            elif buf1[chunk_2[0] : chunk_2[1]] != buf2[chunk_2[0] : chunk_2[1]]:
                low, high = chunk_2
            else:
                break
        if high - low <= 1:
            raise AssertionError(
                "Block mismatch at byte {0}: "
                "{1} != {2}".format(low, buf1[low], buf2[low])
            )


class _Decorator(object):
    def __init__(self, value):
        self.value = value

    def __call__(self, thing):
        setattr(thing, "__pike_test_" + self.__class__.__name__, self.value)
        return thing


class _RangeDecorator(object):
    def __init__(self, minvalue=0, maxvalue=float("inf")):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def __call__(self, thing):
        setattr(
            thing,
            "__pike_test_" + self.__class__.__name__,
            (self.minvalue, self.maxvalue),
        )
        return thing


class RequireDialect(_RangeDecorator):
    pass


class RequireCapabilities(_Decorator):
    pass


class RequireShareCapabilities(_Decorator):
    pass


class PikeTestSuite(unittest.TestSuite):
    """
    Custom test suite for easily patching in skip tests in downstream
    distributions of these test cases
    """

    skip_tests_reasons = {
        "test_to_be_skipped": "This test should be skipped",
    }

    @staticmethod
    def _raise_skip(reason):
        def inner(*args, **kwds):
            raise unittest.SkipTest(reason)

        return inner

    def addTest(self, test):
        testMethodName = getattr(test, "_testMethodName", None)
        if testMethodName in self.skip_tests_reasons:
            setattr(
                test,
                testMethodName,
                self._raise_skip(self.skip_tests_reasons[testMethodName]),
            )
        super(PikeTestSuite, self).addTest(test)


class SambaPikeTestSuite(PikeTestSuite):
    skip_tests_reasons = {
        # ERROR
        "test_resiliency_reconnect_after_timeout": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_resiliency_reconnect_before_timeout": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_resiliency_upgrade_reconnect_after_timeout": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_resiliency_upgrade_reconnect_before_timeout": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_bogus_resume_key": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_bogus_resume_key": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_other_resume_key": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_other_resume_key": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_ssc_in_compound_req": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_ssc_in_compound_req": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_dacl": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_dacl_append_ace": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_dacl_new": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_dacl_partial_copy": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_group": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_owner": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_sec_same": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_downlevel": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_downlevel": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_downlevel": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_treeconnect": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_write_none": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_write_none_lease": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_write_none_oplock": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_allow_zero_byte_write": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_set_get_reparse_point": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_symbolic_link_error_response": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb_3_0_encryption": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb_3_0_2_encryption": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb_3_1_1_compound": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb_3_1_1_encryption_ccm": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb_3_1_1_encryption_gcm": "returns error against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        # FAIL
        "test_resiliency_buffer_too_small": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_resiliency_upgrade_buffer_too_small": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_neg_dst_exc_brl": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_neg_dst_is_a_dir": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_neg_src_exc_brl": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb3": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_smb3_many_capabilities": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_encryption_capabilities_both_prefer_gcm": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_write_none_access": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_query_interface_info_smb3": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_create_failed_and_query": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_deny_write": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_async_lock": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_async_write": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_sequence_number_wrap": "returns fail against dperson/samba:d1a453d8123e462b0ad0ca8df51fb8ac0e5716b9",
        "test_qfid_diff_file": "returns fail against dperson/samba:7767ceb85af2e5254477357976feee49ca7eab3a",
        "test_qfid_same_file_seq_delete": "returns fail against dperson/samba:7767ceb85af2e5254477357976feee49ca7eab3a",
        "test_encryption_capabilities_both_prefer_ccm": "returns fail against dperson/samba:197dd6dac98274109c9c9c024f2bb1ebe2e075fa1ab901640a8fe94e875007d1",
    }


def suite(clz=PikeTestSuite):
    test_loader = unittest.TestLoader()
    test_loader.suiteClass = clz
    test_suite = test_loader.discover(
        os.path.abspath(os.path.dirname(__file__)), "*.py"
    )
    return test_suite


def samba_suite():
    return suite(SambaPikeTestSuite)


if __name__ == "__main__":
    test_runner = unittest.TextTestRunner()
    test_runner.run(suite())
