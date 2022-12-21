#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_tree_connect.py
#
# Abstract:
#
#        Tree Connect tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#          Masen Furer (m_github@0x26.net)
#

from pike import TreeConnect
import pike.test


class TreeTest(pike.test.PikeTest):
    def test_tree(self):
        """Connect a tree, then disconnect it."""
        chan, tree = self.tree_connect()
        chan.tree_disconnect(tree)


def test_TreeConnect():
    """Connect a tree, then disconnect it, new style"""
    with TreeConnect() as tc:
        assert tc.tree
        assert tc.tree.path == r"\\{}\{}".format(tc.server, tc.share)
        tc.chan.tree_disconnect(tc.tree)
