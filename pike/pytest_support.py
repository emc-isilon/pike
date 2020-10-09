#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

"""Pike/pytest integration."""

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
    marks = (
        ("require_dialect", (0, float("inf"))),
        ("require_capabilities", 0),
        ("require_share_capabilities", 0),
    )

    def TreeConnect(*args, **kwargs):
        # update requirements from markers
        for mark_name, default_value in marks:
            kwargs[mark_name] = kwargs.get(
                mark_name, get_mark_value(request.node, mark_name, default_value),
            )
        # special case dialect range (must be a 2-tuple)
        if not isinstance(kwargs["require_dialect"], tuple):
            kwargs["require_dialect"] = (kwargs["require_dialect"], float("inf"))
        return pike.test.TreeConnect(*args, **kwargs)

    return TreeConnect
