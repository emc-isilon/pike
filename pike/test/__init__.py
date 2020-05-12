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
import gc
import logging
import os
import unittest
import sys

import pike.model as model
import pike.smb2 as smb2


class PikeTest(unittest.TestCase):
    init_done = False

    @staticmethod
    def option(name, default=None):
        if name in os.environ:
            value = os.environ[name]
            if len(value) == 0:
                value = default
        else:
            value = default

        return value

    @staticmethod
    def booloption(name, default='no'):
        table = {'yes': True, 'no': False, '': False}
        return table[PikeTest.option(name, 'no')]

    @staticmethod
    def smb2constoption(name, default=None):
        return getattr(smb2, PikeTest.option(name, '').upper(), default)

    @staticmethod
    def init_once():
        if not PikeTest.init_done:
            PikeTest.loglevel = getattr(logging, PikeTest.option('PIKE_LOGLEVEL', 'NOTSET').upper())
            PikeTest.handler = logging.StreamHandler()
            PikeTest.handler.setLevel(PikeTest.loglevel)
            PikeTest.handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
            PikeTest.logger = logging.getLogger('pike')
            PikeTest.logger.addHandler(PikeTest.handler)
            PikeTest.logger.setLevel(PikeTest.loglevel)
            PikeTest.trace = PikeTest.booloption('PIKE_TRACE')
            model.trace = PikeTest.trace
            PikeTest.init_done = True

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.init_once()
        self.server = self.option('PIKE_SERVER')
        self.port = int(self.option('PIKE_PORT', '445'))
        self.creds = self.option('PIKE_CREDS')
        self.share = self.option('PIKE_SHARE', 'c$')
        self.signing = self.booloption('PIKE_SIGN')
        self.encryption = self.booloption('PIKE_ENCRYPT')
        self.min_dialect = self.smb2constoption('PIKE_MIN_DIALECT')
        self.max_dialect = self.smb2constoption('PIKE_MAX_DIALECT')
        self._connections = []
        self.default_client = model.Client()
        if self.min_dialect is not None:
            self.default_client.dialects = [d for d in self.default_client.dialects if d >= self.min_dialect]
        if self.max_dialect is not None:
            self.default_client.dialects = [d for d in self.default_client.dialects if d <= self.max_dialect]
        if self.signing:
            self.default_client.security_mode = (smb2.SMB2_NEGOTIATE_SIGNING_ENABLED |
                                                 smb2.SMB2_NEGOTIATE_SIGNING_REQUIRED)

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

    def tree_connect(self, client=None, resume=None):
        dialect_range = self.required_dialect()
        req_caps = self.required_capabilities()
        req_share_caps = self.required_share_capabilities()

        if client is None:
            client = self.default_client

        conn = client.connect(self.server, self.port).negotiate()

        if (conn.negotiate_response.dialect_revision < dialect_range[0] or
            conn.negotiate_response.dialect_revision > dialect_range[1]):
            self.skipTest("Dialect required: %s" % str(dialect_range))

        if conn.negotiate_response.capabilities & req_caps != req_caps:
            self.skipTest("Capabilities missing: %s " %
                          str(req_caps & ~conn.negotiate_response.capabilities))

        chan = conn.session_setup(self.creds, resume=resume)
        if self.encryption:
            chan.session.encrypt_data = True

        tree = chan.tree_connect(self.share)

        if tree.tree_connect_response.capabilities & req_share_caps != req_share_caps:
            self.skipTest("Share capabilities missing: %s" %
                          str(req_share_caps & ~tree.tree_connect_response.capabilities))
        self._connections.append(conn)
        return (chan,tree)

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
                raise_from(self.failureException(
                    '"%s" raised when "%s" expected' % (err.response.status, status),
                    err,
                ))

    def setUp(self):
        if self.loglevel != logging.NOTSET:
            print(file=sys.stderr)

        if hasattr(self, 'setup'):
            self.setup()

    def tearDown(self):
        if hasattr(self, 'teardown'):
            self.teardown()

        for conn in self._connections:
            conn.close()
        del self._connections[:]
        # Reference cycles are common in pike. so garbage collect aggressively
        gc.collect()

    def _get_decorator_attr(self, name, default):
        name = '__pike_test_' + name
        test_method = getattr(self, self._testMethodName)

        if hasattr(test_method, name):
            return getattr(test_method, name)
        elif hasattr(self.__class__, name):
            return getattr(self.__class__, name)
        else:
            return default

    def required_dialect(self):
        return self._get_decorator_attr('RequireDialect', (0, float('inf')))

    def required_capabilities(self):
        return self._get_decorator_attr('RequireCapabilities', 0)

    def required_share_capabilities(self):
        return self._get_decorator_attr('RequireShareCapabilities', 0)

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
            if buf1[chunk_1[0]:chunk_1[1]] != buf2[chunk_1[0]:chunk_1[1]]:
                low, high = chunk_1
            elif buf1[chunk_2[0]:chunk_2[1]] != buf2[chunk_2[0]:chunk_2[1]]:
                low, high = chunk_2
            else:
                break
        if high - low <= 1:
            raise AssertionError("Block mismatch at byte {0}: "
                                 "{1} != {2}".format(low, buf1[low], buf2[low]))

class _Decorator(object):
    def __init__(self, value):
        self.value = value

    def __call__(self, thing):
        setattr(thing, '__pike_test_' + self.__class__.__name__, self.value)
        return thing


class _RangeDecorator(object):
    def __init__(self, minvalue=0, maxvalue=float('inf')):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def __call__(self, thing):
        setattr(thing, '__pike_test_' + self.__class__.__name__,
                (self.minvalue, self.maxvalue))
        return thing


class RequireDialect(_RangeDecorator): pass
class RequireCapabilities(_Decorator): pass
class RequireShareCapabilities(_Decorator): pass


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
                    self._raise_skip(
                        self.skip_tests_reasons[testMethodName]))
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
        "test_qfid_diff_file": "returns fail agains dperson/samba:7767ceb85af2e5254477357976feee49ca7eab3a",
    }


def suite(clz=PikeTestSuite):
    test_loader = unittest.TestLoader()
    test_loader.suiteClass = clz
    test_suite = test_loader.discover(
            os.path.abspath(os.path.dirname(__file__)),
            "*.py")
    return test_suite


def samba_suite():
    return suite(SambaPikeTestSuite)


if __name__ == '__main__':
    test_runner = unittest.TextTestRunner()
    test_runner.run(suite())
