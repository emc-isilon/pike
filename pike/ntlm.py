#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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

from __future__ import absolute_import
from builtins import object
from builtins import range

import array
import random
from socket import gethostname
import struct

import Cryptodome.Cipher.DES
import Cryptodome.Cipher.ARC4 as RC4
import Cryptodome.Hash.HMAC as HMAC
import Cryptodome.Hash.MD4 as MD4
import Cryptodome.Hash.MD5 as MD5

from . import core
from . import nttime


def des_key_64(K):
    """
    Return an 64-bit des key by adding a zero to the least significant bit
    of each character.
    K should be a 7 char string
    """
    in_key = K + "\0"
    out_key = array.array("B", K[0])
    for ix in range(1, len(in_key)):
        out_key.append(
            ((ord(in_key[ix - 1]) << (8 - ix)) & 0xFF) | (ord(in_key[ix]) >> ix)
        )
    return out_key.tobytes()


def DES(K, D):
    d1 = Cryptodome.Cipher.DES.new(des_key_64(K), Cryptodome.Cipher.DES.MODE_ECB)
    return d1.encrypt(D)


def DESL(K, D):
    return DES(K[:7], D) + DES(K[7:14], D) + DES(K[14:16] + "\0" * 5, D)


def nonce(length):
    return array.array("B", [random.getrandbits(8) for x in range(length)])


def encode_frame(frame):
    buffer = array.array("B")
    frame.encode(core.Cursor(buffer, 0))
    return buffer


NTLM_SIGNATURE = b"NTLMSSP\x00"


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
        if signature.tobytes() != NTLM_SIGNATURE:
            raise core.BadPacket("Packet signature does not match")
        # determine the message type to pass off decoding
        message_type = cur.decode_uint32le()
        if message_type == NtLmChallenge:
            self.message = NtLmChallengeMessage(self)
            self.message.decode(cur)
        else:
            raise core.BadPacket(
                "Unknown response message type: {0}".format(message_type)
            )


class NegotiateFlags(core.FlagEnum):
    NTLMSSP_NEGOTIATE_UNICODE = 0x00000001
    NTLM_NEGOTIATE_OEM = 0x00000002
    NTLMSSP_REQUEST_TARGET = 0x00000004
    NTLM_NEGOTIATE_SIGN = 0x00000010
    NTLM_NEGOTIATE_SEAL = 0x00000020
    NTLMSSP_NEGOTIATE_DATAGRAM = 0x00000040
    NTLMSSP_NEGOTIATE_LM_KEY = 0x00000080
    NTLMSSP_NEGOTIATE_NTLM = 0x00000200
    ANONYMOUS = 0x00000800
    NTLMSSP_NEGOTIATE_OEM_DOMAIN_SUPPLIED = 0x00001000
    NTLMSSP_NEGOTIATE_OEM_WORKSTATION_SUPPLIED = 0x00002000
    NTLMSSP_NEGOTIATE_ALWAYS_SIGN = 0x00008000
    NTLMSSP_TARGET_TYPE_DOMAIN = 0x00010000
    NTLMSSP_TARGET_TYPE_SERVER = 0x00020000
    NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY = 0x00080000
    NTLMSSP_NEGOTIATE_IDENTIFY = 0x00100000
    NTLMSSP_REQUEST_NON_NT_SESSION_KEY = 0x00400000
    NTLMSSP_NEGOTIATE_TARGET_INFO = 0x00800000
    NTLMSSP_NEGOTIATE_VERSION = 0x02000000
    NTLMSSP_NEGOTIATE_128 = 0x20000000
    NTLMSSP_NEGOTIATE_KEY_EXCH = 0x40000000
    NTLMSSP_NEGOTIATE_56 = 0x80000000


NegotiateFlags.import_items(globals())


class ProductMajorVersionFlags(core.ValueEnum):
    WINDOWS_MAJOR_VERSION_5 = 0x5
    WINDOWS_MAJOR_VERSION_6 = 0x6
    WINDOWS_MAJOR_VERSION_10 = 0xA


ProductMajorVersionFlags.import_items(globals())


class ProductMinorVersionFlags(core.ValueEnum):
    WINDOWS_MINOR_VERSION_0 = 0x0
    WINDOWS_MINOR_VERSION_1 = 0x1
    WINDOWS_MINOR_VERSION_2 = 0x2
    WINDOWS_MINOR_VERSION_3 = 0x3


ProductMinorVersionFlags.import_items(globals())


class NTLMRevisionCurrentFlags(core.ValueEnum):
    UNKNOWN = 0x0
    NTLMSSP_REVISION_W2K3 = 0x0F


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
        cur.encode_uint8le(0)  # reserved
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

        if (
            self.negotiate_flags & NTLMSSP_NEGOTIATE_VERSION
            and self.version is not None
        ):
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
    MsvAvEOL = 0x0
    MsvAvNbComputerName = 0x1
    MsvAvNbDomainName = 0x2
    MsvAvDnsComputerName = 0x3
    MsvAvDnsDomainName = 0x4
    MsvAvDnsTreeName = 0x5
    MsvAvFlags = 0x6
    MsvAvTimestamp = 0x7
    MsvAvSingleHost = 0x8
    MsvAvTargetName = 0x9
    MsvChannelBindings = 0xA


AvId.import_items(globals())


class AvPair(core.Frame):
    text_fields = [
        MsvAvNbComputerName,
        MsvAvNbDomainName,
        MsvAvDnsComputerName,
        MsvAvDnsDomainName,
        MsvAvDnsTreeName,
        MsvAvTargetName,
    ]

    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.target_info.append(self)
        self.av_id = None
        self.value = None

    def _encode(self, cur):
        cur.encode_uint16le(self.av_id)
        av_len_hole = cur.hole.encode_uint16le(0)
        av_start = cur.copy()
        if self.value is not None:
            if self.av_id in self.text_fields:
                cur.encode_utf16le(self.value)
            else:
                cur.encode_bytes(self.value)
        av_len_hole(cur - av_start)

    def _decode(self, cur):
        self.av_id = AvId(cur.decode_uint16le())
        av_len = cur.decode_uint16le()
        if av_len > 0:
            if self.av_id in self.text_fields:
                self.value = cur.decode_utf16le(av_len)
            else:
                self.value = cur.decode_bytes(av_len)


def extract_pair(av_pairs, av_id):
    for p in av_pairs:
        if p.av_id == av_id:
            return p


class NtLmChallengeMessage(core.Frame):
    message_type = NtLmChallenge

    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.message = self
        self.target_name = None
        self.negotiate_flags = 0
        self.server_challenge = array.array("B", [0] * 8)
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
            with cur.bounded(cur, cur + 8):
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
                with cur.bounded(cur, end):
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

        if (
            self.negotiate_flags & NTLMSSP_NEGOTIATE_KEY_EXCH
            and self.encrypted_random_session_key is not None
        ):
            encrypted_random_session_key_len = len(self.encrypted_random_session_key)
        else:
            encrypted_random_session_key_len = 0
        cur.encode_uint16le(encrypted_random_session_key_len)
        cur.encode_uint16le(encrypted_random_session_key_len)
        encrypted_random_session_key_offset_hole = cur.hole.encode_uint32le(0)

        cur.encode_uint32le(self.negotiate_flags)

        if (
            self.negotiate_flags & NTLMSSP_NEGOTIATE_VERSION
            and self.version is not None
        ):
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
                cur.encode_bytes(self.domain_name.encode("ascii"))

        user_name_offset_hole(cur - message_start)
        if user_name_len > 0:
            if is_unicode:
                cur.encode_utf16le(self.user_name)
            else:
                cur.encode_bytes(self.user_name.encode("ascii"))

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
    NTLMv1 = 0x1
    NTLMv2 = 0x2


NtlmVersion.import_items(globals())


########################
## NTLMv1 Implementation
########################


def LMOWFv1(password):
    lm_passwd = password.upper() + "\0" * 14
    magic = "KGS!@#$%"
    return DES(lm_passwd[:7], magic) + DES(lm_passwd[7:14], magic)


def NTOWFv1(password):
    nt_passwd = password.encode("utf-16-le")
    return MD4.new(nt_passwd).digest()


def ComputeResponsev1(
    NegFlg,
    ResponseKeyNT,
    ResponseKeyLM,
    ServerChallenge,
    ClientChallenge,
    Time=None,
    ServerName=None,
):
    if NegFlg & NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY:
        NtChallengeResponse = DESL(
            ResponseKeyNT, MD5.new(ServerChallenge + ClientChallenge).digest()[:8]
        )
        LmChallengeResponse = ClientChallenge + "\0" * 16
    else:
        NtChallengeResponse = DESL(ResponseKeyNT, ServerChallenge)
        LmChallengeResponse = DESL(ResponseKeyLM, ServerChallenge)
    SessionBaseKey = MD4.new(ResponseKeyNT).digest()
    return NtChallengeResponse, LmChallengeResponse, SessionBaseKey


def KXKEY(NegFlg, SessionBaseKey, LmChallengeResponse, ServerChallenge, ResponseKeyLM):
    if NegFlg & NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY:
        hm = HMAC.new(SessionBaseKey, ServerChallenge + LmChallengeResponse[:8], MD5)
        KeyExchangeKey = hm.digest()
    else:
        LMOWF = ResponseKeyLM
        if NegFlg & NTLMSSP_NEGOTIATE_LMKEY:
            data = LmChallengeResponse[:8]
            KeyExchangeKey = DES(LMOWF[:7], data) + DES(LMOWF[8] + "\xbd" * 6, data)
        else:
            if NegFlg & NTLMSSP_REQUEST_NON_NT_SESSION_KEY:
                KeyExchangeKey = LMOWF[:8] + "\0" * 8
            else:
                KeyExchangeKey = SessionBaseKey
    return KeyExchangeKey


########################
## NTLMv2 Implementation
########################


class NTLMv2Response(core.Frame):
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        self.response = None
        self.challenge = None

    def _encode(self, cur):
        cur.encode_bytes(self.response)
        self.challenge.encode(cur)


class NTLMv2ClientChallenge(core.Frame):
    def __init__(self, parent=None):
        core.Frame.__init__(self, parent)
        if parent is not None:
            parent.challenge = self
        self.time_stamp = array.array("B", b"\0" * 8)
        self.challenge_from_client = array.array("B", b"\0" * 8)
        self.av_pairs = []

    def _encode(self, cur):
        cur.encode_uint8le(1)  # RespType
        cur.encode_uint8le(1)  # HiRespType
        cur.encode_uint16le(0)  # Reserved
        cur.encode_uint32le(0)  # Reserved
        cur.encode_uint64le(self.time_stamp)
        cur.encode_bytes(self.challenge_from_client)
        cur.encode_uint32le(0)  # Reserved
        for p in self.av_pairs:
            p.encode(cur)


def NTOWFv2(password, user, userdom):
    nt_passwd = password.encode("utf-16-le")
    nt_hash_passwd = MD4.new(nt_passwd).digest()
    nt_userdom = (user.upper() + userdom).encode("utf-16-le")
    return HMAC.new(nt_hash_passwd, nt_userdom, MD5).digest()


def ComputeResponsev2(
    NegFlg,
    ResponseKeyNT,
    ResponseKeyLM,
    ServerChallenge,
    ClientChallenge,
    Time=None,
    ServerName=None,
    av_pairs=None,
):
    if Time is None:
        Time = nttime.NtTime(nttime.datetime.now())
    if ServerName is None:
        ServerName = "SERVER"
    ServerName = ServerName.encode("utf-16-le")

    TimeBuf = array.array("B")
    cur = core.Cursor(TimeBuf, 0)
    cur.encode_uint64le(Time)

    Responseversion = "\x01"
    HiResponseversion = "\x01"

    ntlmv2_client_challenge = NTLMv2ClientChallenge()
    ntlmv2_client_challenge.time_stamp = Time
    ntlmv2_client_challenge.challenge_from_client = ClientChallenge
    if av_pairs is not None:
        ntlmv2_client_challenge.av_pairs = av_pairs
    temp = encode_frame(ntlmv2_client_challenge).tobytes()
    NTProofStr = HMAC.new(ResponseKeyNT, ServerChallenge + temp, MD5).digest()
    NtChallengeResponse = NTProofStr + temp
    LmChallengeResponse = (
        HMAC.new(ResponseKeyLM, ServerChallenge + ClientChallenge, MD5).digest()
        + ClientChallenge
    )
    SessionBaseKey = HMAC.new(ResponseKeyNT, NTProofStr, MD5).digest()
    return NtChallengeResponse, LmChallengeResponse, SessionBaseKey


class NtlmAuthenticator(object):
    """
    State machine for conducting ntlm authentication
    """

    neg_flags = (
        NTLMSSP_NEGOTIATE_UNICODE
        | NTLM_NEGOTIATE_OEM
        | NTLMSSP_REQUEST_TARGET
        | NTLMSSP_NEGOTIATE_NTLM
        | NTLMSSP_NEGOTIATE_OEM_DOMAIN_SUPPLIED
        | NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY
        | NTLM_NEGOTIATE_SIGN
        | NTLM_NEGOTIATE_SEAL
        | NTLMSSP_NEGOTIATE_128
        | NTLMSSP_NEGOTIATE_56
        | NTLMSSP_NEGOTIATE_KEY_EXCH
    )

    auth_flags = (
        NTLMSSP_NEGOTIATE_UNICODE
        | NTLMSSP_REQUEST_TARGET
        | NTLMSSP_NEGOTIATE_NTLM
        | NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY
        | NTLM_NEGOTIATE_SIGN
        | NTLM_NEGOTIATE_SEAL
        | NTLMSSP_NEGOTIATE_TARGET_INFO
        | NTLMSSP_NEGOTIATE_128
        | NTLMSSP_NEGOTIATE_56
        | NTLMSSP_TARGET_TYPE_DOMAIN
        | NTLMSSP_NEGOTIATE_KEY_EXCH
    )

    def __init__(self, domain, username, password):
        self.messages = []
        self.domain = domain
        self.username = username
        self.password = password
        self.version = Version()
        self.version.product_build = 9999
        self.ntlm_version = NTLMv2

        self.client_challenge = nonce(8)
        self.session_base_key = nonce(16)

        self.negotiate_message = None
        self.negotiate_buffer = None
        self.challenge_message = None
        self.challenge_buffer = None
        self.authenticate_message = None
        self.authenticate_buffer = None

    def ntlmv1(self):
        self.lm_hash = LMOWFv1(self.password.encode("ascii"))
        self.nt_hash = NTOWFv1(self.password)
        (
            self.nt_challenge_response,
            self.lm_challenge_response,
            self.session_base_key,
        ) = ComputeResponsev1(
            self.auth_flags,
            self.nt_hash,
            self.lm_hash,
            self.server_challenge.tobytes(),
            self.client_challenge.tobytes(),
        )
        self.key_exchange_key = KXKEY(
            self.auth_flags,
            self.session_base_key,
            self.lm_challenge_response,
            self.server_challenge.tobytes(),
            self.lm_hash,
        )

    def ntlmv2(self):
        ctarget_info = self.challenge_message.message.target_info
        server_time = extract_pair(ctarget_info, MsvAvTimestamp)
        if server_time is not None:
            time = nttime.NtTime(struct.unpack("<Q", server_time.value)[0])
        else:
            time = nttime.NtTime(nttime.datetime.now())
        server_name = extract_pair(ctarget_info, MsvAvNbComputerName)
        if server_name is not None:
            server_name = server_name.value

        self.nt_hash = NTOWFv2(self.password, self.username, self.domain)
        (
            self.nt_challenge_response,
            self.lm_challenge_response,
            self.session_base_key,
        ) = ComputeResponsev2(
            self.auth_flags,
            self.nt_hash,
            self.nt_hash,
            self.server_challenge.tobytes(),
            self.client_challenge.tobytes(),
            time,
            server_name,
            ctarget_info,
        )
        self.key_exchange_key = self.session_base_key

        if extract_pair(ctarget_info, MsvAvTimestamp) is not None:
            self.lm_challenge_response = b"\0" * 24

    def session_key(self):
        if self.auth_flags & NTLMSSP_NEGOTIATE_KEY_EXCH:
            r = RC4.new(self.key_exchange_key)
            self.exported_session_key = nonce(16)
            return r.encrypt(self.exported_session_key.tobytes())
        else:
            self.exported_session_key = self.key_exchange_key

    def negotiate(self):
        ntlm = Ntlm()
        neg = NtLmNegotiateMessage(ntlm)
        neg.negotiate_flags = self.neg_flags
        neg.domain_name = self.domain
        neg.version = self.version
        self.negotiate_buffer = array.array("B")
        ntlm.encode(core.Cursor(self.negotiate_buffer, 0))
        self.negotiate_message = ntlm
        return self.negotiate_buffer

    def authenticate(self, challenge_buf):
        # parse the challenge message
        self.challenge_buffer = challenge_buf
        ntlm_challenge = Ntlm()
        ntlm_challenge.decode(core.Cursor(challenge_buf, 0))
        self.server_challenge = ntlm_challenge.message.server_challenge
        self.challenge_message = ntlm_challenge

        # build the auth message
        ntlm = Ntlm()
        auth = NtLmAuthenticateMessage(ntlm)
        auth.negotiate_flags = self.auth_flags
        auth.version = self.version
        auth.domain_name = self.domain
        auth.user_name = self.username

        # perform the NTLM
        if self.ntlm_version == NTLMv1:
            self.ntlmv1()
        elif self.ntlm_version == NTLMv2:
            self.ntlmv2()
        else:
            raise NotImplementedError(
                "Unknown NTLM version {0}".format(self.ntlm_version)
            )

        # fill in the challenge responses
        auth.nt_challenge_response = self.nt_challenge_response
        auth.lm_challenge_response = self.lm_challenge_response

        # generate the session key if requested
        session_key = self.session_key()
        if session_key is not None:
            auth.encrypted_random_session_key = session_key

        self.authenticate_buffer = array.array("B")
        ntlm.encode(core.Cursor(self.authenticate_buffer, 0))
        self.authenticate_message = ntlm
        return self.authenticate_buffer
