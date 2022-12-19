#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        echo.py
#
# Abstract:
#
#        Basic echo send/recv testing
#
# Authors: Angela Bartholomaus (angela.bartholomaus@emc.com)
#

import pike.test


class EchoTest(pike.test.PikeTest):
    # Test that ECHO works
    def test_echo(self):
        chan, tree = self.tree_connect()
        chan.echo()
