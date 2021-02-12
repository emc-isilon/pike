#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        oplock.py
#
# Abstract:
#
#        Oplock tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test


class OplockTest(pike.test.PikeTest):
    # Open a handle with an oplock and break it
    def test_oplock_break(self):
        chan, tree = self.tree_connect()

        share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )

        handle1 = chan.create(
            tree,
            "oplock.txt",
            share=share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
        ).result()

        handle1.on_oplock_break(lambda level: level)

        handle2 = chan.create(
            tree,
            "oplock.txt",
            share=share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II,
        ).result()

        chan.close(handle1)
        chan.close(handle2)
