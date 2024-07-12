# Copyright (c) 2024 Dell Inc. or its subsidiaries. All Rights Reserved.
from __future__ import absolute_import

import io
import string
import uuid

import pytest

import pike.ntstatus
import pike.smb2


@pytest.fixture
def filename():
    return "test_io_{}.txt".format(uuid.uuid4())


def test_basic_read_write(pike_TreeConnect, filename):
    with pike_TreeConnect() as tc:
        with tc.chan.create(
            tc.tree,
            filename,
            access=pike.smb2.GENERIC_READ | pike.smb2.GENERIC_WRITE | pike.smb2.DELETE,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result() as fh:
            buf = "test123"
            tc.chan.write(fh, 0, buf)
            assert tc.chan.read(fh, len(buf), 0).tobytes().decode() == buf
