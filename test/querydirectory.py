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
#        querydirectory.py
#
# Abstract:
#
#        Query directory tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

import pike.model
import pike.smb2
import pike.test

class QueryDirectoryTest(pike.test.PikeTest):
    # Enumerate directory at FILE_DIRECTORY_INFORMATION level.
    # Test for presence of . and .. entries
    def test_file_directory_info(self):
        chan, tree = self.tree_connect()
        
        root = chan.create(tree, '', access=pike.smb2.GENERIC_READ, options=pike.smb2.FILE_DIRECTORY_FILE, share=pike.smb2.FILE_SHARE_READ).result()
        names = map(lambda info: info.file_name, chan.enum_directory(root))

        self.assertIn('.', names)
        self.assertIn('..', names)

        chan.close(root)
