#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_oplock.py
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


share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)


def test_oplock_break(pike_tmp_path):
    """Open a handle with an exclusive oplock and break it."""
    oplock_file = pike_tmp_path / "oplock.txt"
    with oplock_file.create(
        share=share_all,
        oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE,
    ) as handle1:
        assert handle1.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE
        handle1.on_oplock_break(lambda level: level)

        with oplock_file.create(
            share=share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II,
        ) as handle2:
            assert handle2.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_II
            assert handle1.oplock_level == pike.smb2.SMB2_OPLOCK_LEVEL_II
