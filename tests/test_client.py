#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

import pytest

from pike.model import Client
from pike.smb2 import Dialect


@pytest.mark.parametrize(
    "min_dialect,max_dialect",
    (
        pytest.param(None, None, id="None/None"),
        pytest.param(Dialect.DIALECT_SMB2_1, None, id="lower bound"),
        pytest.param(None, Dialect.DIALECT_SMB2_1, id="upper bound"),
        pytest.param(Dialect.DIALECT_SMB3_1_1, Dialect.DIALECT_SMB2_002, id="inverted"),
        pytest.param(Dialect.DIALECT_SMB3_0, float("inf"), id="upper bound inf"),
        pytest.param(Dialect.DIALECT_SMB3_0, 0xFFFFFFFF, id="upper bound int"),
        pytest.param(float("-inf"), Dialect.DIALECT_SMB2_002, id="lower bound -inf"),
        pytest.param(0, Dialect.DIALECT_SMB3_0_2, id="lower bound zero"),
    ),
)
def test_restrict_dialect(min_dialect, max_dialect):
    c = Client()
    c.restrict_dialects(min_dialect, max_dialect)
    print(
        "restrict_dialects(min_dialect={}, max_dialect={}) => {}".format(
            min_dialect, max_dialect, c.dialects
        )
    )
    for d in c.dialects:
        if min_dialect is None:
            min_dialect = min(Dialect.values())
        if max_dialect is None:
            max_dialect = max(Dialect.values())
        assert d >= min_dialect
        assert d <= max_dialect
