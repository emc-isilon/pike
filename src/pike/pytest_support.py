#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
"""
Pike/pytest integration

Available markers:

    - ``require_dialect(min_dialect, max_dialect)``: raise a
      :py:class:`~pike.test.DialectMissing` exception if the target server does
      not support a dialect in the given range. This exception will be raised
      after Negotiate.
    - ``require_capability(global_capabilities)``: raise a
      :py:class:`~pike.test.CapabilityMissing` exception if the target server
      does not support all of the OR'd global capability flags.  This exception
      will be raised after Negotiate.
    - ``require_share_capability(share_capabilities)``: raise a
      :py:class:`~pike.test.ShareCapabilityMissing` exception if the target
      share does not support all of the OR'd share capability flags.  This
      exception will be raised after Tree Connect.
"""

import uuid
import time

import pytest

import pike.test


# pytest API
def pytest_configure(config):
    """
    register the marks so that they show up in `pytest --markers` as well as
    not raising errors in strict marker mode
    """
    config.addinivalue_line(
        "markers",
        (
            "require_dialect(min_dialect, max_dialect): "
            "when using the TreeConnect fixture, if the remote server "
            "does not advertise a dialect within the given range "
            "then skip the test."
        ),
    )
    config.addinivalue_line(
        "markers",
        (
            "require_capabilities(global_capabilities): "
            "when using the TreeConnect fixture, if the remote server "
            "does not advertise support for all capabilities "
            "then skip the test."
        ),
    )
    config.addinivalue_line(
        "markers",
        (
            "require_share_capabilities(share_capabilities): "
            "when using the TreeConnect fixture, if the remote share "
            "does not advertise support for all share capabilities "
            "then skip the test."
        ),
    )


def get_mark_value(item, mark_name, default):
    for mark in item.iter_markers(name=mark_name):
        if len(mark.args) > 1:
            return mark.args
        return mark.args[0]
    return default


@pytest.fixture
def pike_TreeConnect(request):
    """
    Function-scope fixture returns a wrapper function around
    :py:class:`pike.TreeConnect`.

    The wrapper-function must be called to establish the connection and the
    returned object may be used as a contextmanager.

    The wrapper-function will pass through any ``require_dialect``,
    ``require_capabilities``, and ``require_share_capabilities`` marks on the
    test item and raise an exception if the target server doesn't support the
    required values.

    :return: Callable[..., pike.TreeConnect]
    """
    marks = (
        ("require_dialect", (0, float("inf"))),
        ("require_capabilities", 0),
        ("require_share_capabilities", 0),
    )

    def TreeConnect(*args, **kwargs):
        # update requirements from markers
        for mark_name, default_value in marks:
            kwargs[mark_name] = kwargs.get(
                mark_name,
                get_mark_value(request.node, mark_name, default_value),
            )
        # special case dialect range (must be a 2-tuple)
        if not isinstance(kwargs["require_dialect"], tuple):
            kwargs["require_dialect"] = (kwargs["require_dialect"], float("inf"))
        return pike.test.TreeConnect(*args, **kwargs)

    # carry the docstring to the wrapper function
    TreeConnect.__doc__ = pike.TreeConnect.__doc__

    return TreeConnect


@pytest.fixture
def pike_tmp_path(pike_TreeConnect):
    """
    Function-scope fixture reaturns a :py:class:`~pike.path.PikePath` rooted at
    a timestamped subdirectory of the share.

    The temporary directory is not deleted during tearDown and should be
    removed by the test case itself.

    A function's :py:func:`pike_TreeConnect` fixture will access the same
    share, however, via a separate SMB2 session.
    """
    with pike_TreeConnect() as tc:
        test_root = tc / "pike_{}_{}".format(
            time.strftime("%Y-%m-%d_%H%M%S"), str(uuid.uuid4())[:5]
        )
        test_root.mkdir()
        yield test_root
