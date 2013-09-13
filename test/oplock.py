#
# Copyright (c) 2013, EMC Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
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

        share_all = pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE

        handle1 = chan.create(tree,
                              'oplock.txt',
                              share=share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_EXCLUSIVE).result()
        
        handle1.on_oplock_break(lambda level: level)
        
        handle2 = chan.create(tree,
                              'oplock.txt',
                              share=share_all,
                              oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_II).result()
        
        chan.close(handle1)
        chan.close(handle2)
