#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

from __future__ import unicode_literals
from builtins import str

import array

import pytest

import pike.model
import pike.smb2


@pytest.fixture
def mock_chan():
    mock_chan = pike.model.Channel(None, None, None)
    mock_chan.request = lambda *args, **kwargs: pike.smb2.Smb2(None)
    return mock_chan


class MockOpen(object):
    file_id = None


@pytest.mark.parametrize(
    "buf,expected_exception",
    (
            (None, None),
            ("unicode", UnicodeWarning),
            (b"literal bytes", None),
            (array.array("B", b"byte array"), None),
            (array.array("b", b"little byte array"), ValueError),
            ([], TypeError),
            (["foo"], TypeError),
            ([b"foo"], TypeError),
            (False, TypeError),
            (True, TypeError),
            (42, TypeError),
    ),
    ids=(
            "none",
            "unicode",
            "bytes",
            "byte array",
            "signed byte array",
            "empty list",
            "list of unicode",
            "list of bytes",
            "false",
            "true",
            "int",
    ),
)
def test_write_request_buffer_type(mock_chan, buf, expected_exception, recwarn):
    try:
        write_req = mock_chan.write_request(MockOpen, 0, buf)
        if expected_exception is not None and expected_exception not in [
            wm.category for wm in recwarn.list
        ]:
            pytest.fail("Did not raise {!r}".format(expected_exception))
        if isinstance(buf, str):
            buf = buf.encode("ascii")
        assert write_req.buffer == buf
    except expected_exception:
        pass
