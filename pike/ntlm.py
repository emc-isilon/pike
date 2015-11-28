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
#        ntlm.py
#
# Abstract:
#
#        Pure python NTLM authentication provider
#
# Authors: Masen Furer (masen.furer@emc.com)
#

import array
import random
import hmac
from socket import gethostname
import Crypto.Cipher.DES as DES
import Crypto.Hash.MD4 as MD4
import Crypto.Hash.MD5 as MD5
import core

def DESL(K, D):
    d1 = DES.new(K[:7] + "\0")
    d2 = DES.new(K[7:14] + "\0")
    d3 = DES.new(K[14:16] + "\0"*6)
    return d1.encrypt(D) + d2.encrypt(D) + d3.encrypt(D)

def nonce(length):
    return array.array("B", [random.getrandbits(8) for x in xrange(length) ])

NTLM_SIGNATURE = "NTLMSSP\x00"

class MessageType(core.ValueEnum):
    NtLmNegotiate = 0x1
    NtLmChallenge = 0x2
    NtLmAuthenticate = 0x3

MessageType.import_items(globals())

class Ntlm(core.Frame):

    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        self.message = None

    def _encode(self, cur):
        cur.encode_bytes(NTLM_SIGNATURE)
        if self.message is not None:
            self.message.encode(cur)

    def _decode(self, cur):
        signature = cur.decode_bytes(8)
        if signature.tostring() != NTLM_SIGNATURE:
            raise core.BadPacket("Packet signature does not match")
        # determine the message type to pass off decoding
        message_type = cur.decode_uint32le()
        if message_type == NtLmChallenge:
            self.message = NtLmChallengeMessage(self)
            self.message.decode(cur)
        else:
            raise core.BadPacket("Unknown response message type: {0}".format(message_type))

class NegotiateFlags(core.FlagEnum):
    NTLMSSP_NEGOTIATE_UNICODE                   = 0x00000001
    NTLM_NEGOTIATE_OEM                          = 0x00000002
    NTLMSSP_REQUEST_TARGET                      = 0x00000004
    NTLM_NEGOTIATE_SIGN                         = 0x00000010
    NTLM_NEGOTIATE_SEAL                         = 0x00000020
    NTLMSSP_NEGOTIATE_DATAGRAM                  = 0x00000040
    NTLMSSP_NEGOTIATE_LM_KEY                    = 0x00000080
    NTLMSSP_NEGOTIATE_NTLM                      = 0x00000200
    ANONYMOUS                                   = 0x00000800
    NTLMSSP_NEGOTIATE_OEM_DOMAIN_SUPPLIED       = 0x00001000
    NTLMSSP_NEGOTIATE_OEM_WORKSTATION_SUPPLIED  = 0x00002000
    NTLMSSP_NEGOTIATE_ALWAYS_SIGN               = 0x00008000
    NTLMSSP_TARGET_TYPE_DOMAIN                  = 0x00010000
    NTLMSSP_TARGET_TYPE_SERVER                  = 0x00020000
    NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY  = 0x00080000
    NTLMSSP_NEGOTIATE_IDENTIFY                  = 0x00100000
    NTLMSSP_REQUEST_NON_NT_SESSION_KEY          = 0x00400000
    NTLMSSP_NEGOTIATE_TARGET_INFO               = 0x00800000
    NTLMSSP_NEGOTIATE_VERSION                   = 0x02000000
    NTLMSSP_NEGOTIATE_128                       = 0x20000000
    NTLMSSP_NEGOTIATE_KEY_EXCH                  = 0x40000000
    NTLMSSP_NEGOTIATE_56                        = 0x80000000

NegotiateFlags.import_items(globals())

class ProductMajorVersionFlags(core.ValueEnum):
    WINDOWS_MAJOR_VERSION_5     = 0x5
    WINDOWS_MAJOR_VERSION_6     = 0x6
    WINDOWS_MAJOR_VERSION_10    = 0xA

ProductMajorVersionFlags.import_items(globals())

class ProductMinorVersionFlags(core.ValueEnum):
    WINDOWS_MINOR_VERSION_0     = 0x0
    WINDOWS_MINOR_VERSION_1     = 0x1
    WINDOWS_MINOR_VERSION_2     = 0x2
    WINDOWS_MINOR_VERSION_3     = 0x3

ProductMinorVersionFlags.import_items(globals())

class NTLMRevisionCurrentFlags(core.ValueEnum):
    NTLMSSP_REVISION_W2K3       = 0x0F

NTLMRevisionCurrentFlags.import_items(globals())

class Version(core.Frame):
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.version = self
        self.product_major_version = WINDOWS_MAJOR_VERSION_5
        self.product_minor_version = WINDOWS_MINOR_VERSION_0
        self.product_build = 0
        self.ntlm_revision_current = NTLMSSP_REVISION_W2K3
    def _encode(self, cur):
        cur.encode_uint8le(self.product_major_version)
        cur.encode_uint8le(self.product_minor_version)
        cur.encode_uint16le(self.product_build)
        cur.encode_uint16le(0)  # reserved
        cur.encode_uint8le(0)   # reserved
        cur.encode_uint8le(self.ntlm_revision_current)
    def _decode(self, cur):
        self.product_major_version = ProductMajorVersionFlags(cur.decode_uint8le())
        self.product_minor_version = ProductMinorVersionFlags(cur.decode_uint8le())
        self.product_build = cur.decode_uint16le()
        reserved = cur.decode_uint16le()
        reserved = cur.decode_uint8le()
        self.ntlm_revision_current = NTLMRevisionCurrentFlags(cur.decode_uint8le())

class NtLmNegotiateMessage(core.Frame):
    message_type = NtLmNegotiate
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.message = self
        self.negotiate_flags = 0
        self.domain_name = ""
        self.workstation_name = gethostname()
        self.version = None

    def _encode(self, cur):
        is_unicode = self.negotiate_flags & NTLMSSP_NEGOTIATE_UNICODE

        message_start = cur - 8
        cur.encode_uint32le(self.message_type)
        cur.encode_uint32le(self.negotiate_flags)

        if self.negotiate_flags & NTLMSSP_NEGOTIATE_OEM_DOMAIN_SUPPLIED:
            domain_name_len = len(self.domain_name)
        else:
            domain_name_len = 0
        if is_unicode:
            domain_name_len = domain_name_len * 2
        cur.encode_uint16le(domain_name_len)
        cur.encode_uint16le(domain_name_len)
        domain_name_offset_hole = cur.hole.encode_uint32le(0)

        if self.negotiate_flags & NTLMSSP_NEGOTIATE_OEM_WORKSTATION_SUPPLIED:
            workstation_name_len = len(self.workstation_name)
        else:
            workstation_name_len = 0
        if is_unicode:
            workstation_name_len = workstation_name_len * 2
        cur.encode_uint16le(workstation_name_len)
        cur.encode_uint16le(workstation_name_len)
        workstation_name_offset_hole = cur.hole.encode_uint32le(0)

        if self.negotiate_flags & NTLMSSP_NEGOTIATE_VERSION and \
           self.version is not None:
            self.version.encode(cur)
        else:
            cur.encode_uint64le(0)

        domain_name_offset_hole(cur - message_start)
        if domain_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.domain_name)
            else:
                cur.encode_bytes(self.domain_name)

        workstation_name_offset_hole(cur - message_start)
        if workstation_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.workstation_name)
            else:
                cur.encode_bytes(self.workstation_name)

class AvId(core.ValueEnum):
    MsvAvEOL                = 0x0
    MsvAvNbComputerName     = 0x1
    MsvAvNbDomainName       = 0x2
    MsvAvDnsComputerName    = 0x3
    MsvAvDnsDomainName      = 0x4
    MsvAvDnsTreeName        = 0x5
    MsvAvFlags              = 0x6
    MsvAvTimestamp          = 0x7
    MsvAvSingleHost         = 0x8
    MsvAvTargetName         = 0x9
    MsvChannelBindings      = 0xA

AvId.import_items(globals())

class AvPair(core.Frame):
    text_fields = [ MsvAvNbComputerName, MsvAvNbDomainName,
                    MsvAvDnsComputerName, MsvAvDnsDomainName, MsvAvDnsTreeName,
                    MsvAvTargetName ]
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.target_info.append(self)
        self.av_id = None
        self.value = None
    def _decode(self, cur):
        self.av_id = AvId(cur.decode_uint16le())
        av_len = cur.decode_uint16le()
        if av_len > 0:
            if self.av_id in self.text_fields:
                self.value = cur.decode_utf16le(av_len)
            else:
                self.value = cur.decode_bytes(av_len)

class NtLmChallengeMessage(core.Frame):
    message_type = NtLmChallenge
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.message = self
        self.target_name = None
        self.negotiate_flags = 0
        self.server_challenge = array.array('B', [0]*8)
        self.target_info = []
        self.version = None
    def _decode(self, cur):
        message_start = cur.copy() - 12
        target_name_len = cur.decode_uint16le()
        target_name_max_len = cur.decode_uint16le()
        target_name_offset = cur.decode_uint32le()
        self.negotiate_flags = NegotiateFlags(cur.decode_uint32le())
        self.server_challenge = cur.decode_bytes(8)
        reserved = cur.decode_bytes(8)
        target_info_len = cur.decode_uint16le()
        target_info_max_len = cur.decode_uint16le()
        target_info_offset = cur.decode_uint32le()
        if self.negotiate_flags & NTLMSSP_NEGOTIATE_VERSION:
            with cur.bounded(cur, cur+8):
                self.version = Version(self)
                self.version.decode(cur)
        else:
            cur.decode_uint64le()

        is_unicode = self.negotiate_flags & NTLMSSP_NEGOTIATE_UNICODE

        cur.seekto(message_start + target_name_offset)
        if target_name_len > 0:
            if is_unicode:
                self.target_name = cur.decode_utf16le(target_name_len)
            else:
                self.target_name = cur.decode_bytes(target_name_len)

        cur.seekto(message_start + target_info_offset)
        end = cur + target_info_len
        if target_info_len > 0:
            while cur < end:
                this_av = AvPair(self)
                with cur.bounded(cur,end):
                    this_av.decode(cur)
                if this_av.av_id == MsvAvEOL:
                    break

class NtLmAuthenticateMessage(core.Frame):
    message_type = NtLmAuthenticate
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.message = self
        self.lm_challenge_response = None
        self.nt_challenge_response = None
        self.domain_name = None
        self.user_name = None
        self.workstation_name = gethostname()
        self.encrypted_random_session_key = None
        self.negotiate_flags = None
        self.version = None
        self.mic = None

    def _encode(self, cur):
        is_unicode = self.negotiate_flags & NTLMSSP_NEGOTIATE_UNICODE

        message_start = cur - 8
        cur.encode_uint32le(self.message_type)

        if self.lm_challenge_response is not None:
            lm_challenge_response_len = len(self.lm_challenge_response)
        else:
            lm_challenge_response_len = 0
        cur.encode_uint16le(lm_challenge_response_len)
        cur.encode_uint16le(lm_challenge_response_len)
        lm_challenge_response_offset_hole = cur.hole.encode_uint32le(0)

        if self.nt_challenge_response is not None:
            nt_challenge_response_len = len(self.nt_challenge_response)
        else:
            nt_challenge_response_len = 0
        cur.encode_uint16le(nt_challenge_response_len)
        cur.encode_uint16le(nt_challenge_response_len)
        nt_challenge_response_offset_hole = cur.hole.encode_uint32le(0)

        if self.domain_name is not None:
            domain_name_len = len(self.domain_name)
        else:
            domain_name_len = 0
        if is_unicode:
            domain_name_len = domain_name_len * 2
        cur.encode_uint16le(domain_name_len)
        cur.encode_uint16le(domain_name_len)
        domain_name_offset_hole = cur.hole.encode_uint32le(0)

        if self.user_name is not None:
            user_name_len = len(self.user_name)
        else:
            user_name_len = 0
        if is_unicode:
            user_name_len = user_name_len * 2
        cur.encode_uint16le(user_name_len)
        cur.encode_uint16le(user_name_len)
        user_name_offset_hole = cur.hole.encode_uint32le(0)

        if self.workstation_name is not None:
            workstation_name_len = len(self.workstation_name)
        else:
            workstation_name_len = 0
        if is_unicode:
            workstation_name_len = workstation_name_len * 2
        cur.encode_uint16le(workstation_name_len)
        cur.encode_uint16le(workstation_name_len)
        workstation_name_offset_hole = cur.hole.encode_uint32le(0)

        if self.negotiate_flags & NTLMSSP_NEGOTIATE_KEY_EXCH and \
           self.encrypted_random_session_key is not None:
            encrypted_random_session_key_len = len(self.encrypted_random_session_key)
        else:
            encrypted_random_session_key_len = 0
        cur.encode_uint16le(encrypted_random_session_key_len)
        cur.encode_uint16le(encrypted_random_session_key_len)
        encrypted_random_session_key_offset_hole = cur.hole.encode_uint32le(0)

        cur.encode_uint32le(self.negotiate_flags)

        if self.negotiate_flags & NTLMSSP_NEGOTIATE_VERSION and \
           self.version is not None:
            self.version.encode(cur)
        else:
            cur.encode_uint64le(0)

        if self.mic is not None:
            cur.encode_bytes(self.mic[:16])

        lm_challenge_response_offset_hole(cur - message_start)
        if lm_challenge_response_len > 0:
            cur.encode_bytes(self.lm_challenge_response)

        nt_challenge_response_offset_hole(cur - message_start)
        if nt_challenge_response_len > 0:
            cur.encode_bytes(self.nt_challenge_response)

        domain_name_offset_hole(cur - message_start)
        if domain_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.domain_name)
            else:
                cur.encode_bytes(self.domain_name)

        user_name_offset_hole(cur - message_start)
        if user_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.user_name)
            else:
                cur.encode_bytes(self.user_name)

        workstation_name_offset_hole(cur - message_start)
        if workstation_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.workstation_name)
            else:
                cur.encode_bytes(self.workstation_name)

        encrypted_random_session_key_offset_hole(cur - message_start)
        if encrypted_random_session_key_len > 0:
            cur.encode_bytes(self.encrypted_random_session_key)

class NtlmVersion(core.ValueEnum):
    NTLMv1      = 0x1
    NTLMv2      = 0x2

NtlmVersion.import_items(globals())

class NtlmProvider(object):
    """
    State machine for conducting ntlm authentication
    """
    neg_flags = NTLMSSP_NEGOTIATE_UNICODE |\
                NTLMSSP_REQUEST_TARGET |\
                NTLMSSP_NEGOTIATE_NTLM |\
                NTLMSSP_NEGOTIATE_OEM_DOMAIN_SUPPLIED |\
                NTLMSSP_NEGOTIATE_OEM_WORKSTATION_SUPPLIED |\
                NTLM_NEGOTIATE_SIGN |\
                NTLMSSP_NEGOTIATE_VERSION |\
                NTLMSSP_NEGOTIATE_128 |\
                NTLMSSP_NEGOTIATE_56

    auth_flags = NTLMSSP_NEGOTIATE_UNICODE |\
                 NTLMSSP_REQUEST_TARGET |\
                 NTLMSSP_NEGOTIATE_NTLM |\
                 NTLM_NEGOTIATE_SIGN |\
                 NTLMSSP_NEGOTIATE_TARGET_INFO |\
                 NTLMSSP_NEGOTIATE_VERSION |\
                 NTLMSSP_NEGOTIATE_128 |\
                 NTLMSSP_NEGOTIATE_56

    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password
        self.version = Version()
        self.version.product_build = 9999
        self.ntlm_version = NTLMv1

        self.client_challenge = nonce(8)
        self.session_base_key = nonce(16)

    def lm_hash_v1(self):
        lm_passwd = (self.password.upper() + "\0"*14)[:14]
        magic = "KGS!@#$%"
        d1 = DES.new(lm_passwd[:7] + "\0")
        d2 = DES.new(lm_passwd[7:14] + "\0")
        return d1.encrypt(magic) + d2.encrypt(magic)

    def nt_hash_v1(self):
        nt_passwd = self.password.encode("utf-16-le")
        return MD4.new("nt_passwd").digest()

    def compute_response(self, server_challenge):
        response_key_nt = self.nt_hash_v1()
        response_key_lm = self.lm_hash_v1()
        if self.auth_flags & NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY:
            nt_challenge_response = DESL(response_key_nt,
                                         MD5.new(server_challenge.tostring() + \
                                                 self.client_challenge.tostring()).digest()[:8])
            lm_challenge_response = self.client_challenge.tostring() + "\0"*16
        else:
            nt_challenge_response = DESL(response_key_nt, server_challenge.tostring())
            lm_challenge_response = DESL(response_key_lm, server_challenge.tostring())
        self.session_base_key = MD4.new(response_key_nt).digest()
        return nt_challenge_response, lm_challenge_response

    def negotiate(self):
        ntlm = Ntlm()
        neg = NtLmNegotiateMessage(ntlm)
        neg.negotiate_flags = self.neg_flags
        neg.domain_name = self.domain
        neg.version = self.version
        buffer = array.array('B')
        ntlm.encode(core.Cursor(buffer, 0))
        return buffer

    def parse_challenge(self, sec_buf):
        ntlm = Ntlm()
        ntlm.decode(core.Cursor(sec_buf, 0))
        return ntlm

    def authenticate(self, challenge):
        ntlm = Ntlm()
        auth = NtLmAuthenticateMessage(ntlm)
        auth.negotiate_flags = self.auth_flags
        auth.version = self.version
        auth.domain_name = self.domain
        auth.user_name = self.username
        nt_resp, lm_resp = self.compute_response(challenge.message.server_challenge)
        auth.nt_challenge_response = nt_resp
        auth.lm_challenge_response = lm_resp
        buffer = array.array('B')
        ntlm.encode(core.Cursor(buffer, 0))
        return buffer
