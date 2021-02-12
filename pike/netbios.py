#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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
            while cur < end:
                signature = cur.copy().decode_bytes(4)
                if signature.tobytes() == b"\xfdSMB":
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
