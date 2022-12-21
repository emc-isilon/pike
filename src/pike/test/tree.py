#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        tree.py
#
# Abstract:
#
#        Tree tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.test


class TreeTest(pike.test.PikeTest):
    # Connect a tree, then disconnect it
    def test_tree(self):
        chan, tree = self.tree_connect()

        chan.tree_disconnect(tree)
