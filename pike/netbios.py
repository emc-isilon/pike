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
#        netbios.py
#
# Abstract:
#
#        NETBios frame support
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#
from __future__ import absolute_import

from . import core
from . import crypto
from . import smb2

class Netbios(core.Frame):
    LOG_CHILDREN_COUNT = False
    LOG_CHILDREN_EXPAND = True

    def __init__(self, context=None):
        core.Frame.__init__(self, None, context)
        self.len = None
        self.conn = context
        self.transform = None
        self._smb2_frames = []

    def _log_str(self):
        components = []
        if self.transform:
            return self.transform._log_str()
        if not self.children:
            components.append(type(self).__name__)
        else:
            components.append(", ".join(self._log_str_children()))
        return " ".join(components)

    def _children(self):
        return self._smb2_frames

    def _encode(self, cur):
        # Frame length (0 for now)
        len_hole = cur.hole.encode_uint32be(0)
        base = cur.copy()
        if self.transform is not None:
            # performing encryption
            self.transform.encode(cur)
        else:
            for child in self.children:
                child.encode(cur)

        if self.len is None:
            self.len = cur - base
        len_hole(self.len)

    def _decode(self, cur):
        self.len = cur.decode_uint32be()
        end = cur + self.len

        with cur.bounded(cur, end):
            while (cur < end):
                signature = cur.copy().decode_bytes(4)
                if (signature.tobytes() == b'\xfdSMB'):
                    crypto.TransformHeader(self).decode(cur)
                else:
                    smb2.Smb2(self).decode(cur)

    def append(self, smb2_frame):
        self._smb2_frames.append(smb2_frame)

    def adopt(self, child, related=True):
        """
        become the parent of child

        :param related: if True and child is an Smb2 frame, set the flag
                        SMB2_FLAGS_RELATED_OPERATIONS
        """
        self.append(child)
        child.parent = self
        if related and isinstance(child, smb2.Smb2):
            child.flags |= smb2.SMB2_FLAGS_RELATED_OPERATIONS
