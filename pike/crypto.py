#
# Copyright (c) 2016, EMC Corporation
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
#        crypto.py
#
# Abstract:
#
#        SMB3 Encryption
#
# Authors: Masen Furer (masen.furer@dell.com)
#
import core
import digest
import smb2

import array
import random

from Cryptodome.Cipher import AES

class Ciphers(core.ValueEnum):
    SMB2_AES_128_CCM = 0x0001
    SMB2_AES_128_GCM = 0x0002

Ciphers.import_items(globals())

class EncryptionCapabilities(core.Frame):
    context_type = smb2.SMB2_ENCRYPTION_CAPABILITIES
    def __init__(self):
        self.ciphers = []
        self.ciphers_count = None

    def _encode(self, cur):
        if self.ciphers_count is None:
            self.ciphers_count = len(self.ciphers)
        cur.encode_uint16le(self.ciphers_count)
        for c in self.ciphers:
            cur.encode_uint16le(c)

    def _decode(self, cur):
        self.ciphers_count = cur.decode_uint16le()
        for ix in xrange(self.ciphers_count):
            self.ciphers.append(Ciphers(cur.decode_uint16le()))


class EncryptionCapabilitiesRequest(smb2.NegotiateRequestContext,
                                    EncryptionCapabilities):
    def __init__(self, parent):
        smb2.NegotiateRequestContext.__init__(self, parent)
        EncryptionCapabilities.__init__(self)


class EncryptionCapabilitiesResponse(smb2.NegotiateResponseContext,
                                     EncryptionCapabilities):
    def __init__(self, parent):
        smb2.NegotiateResponseContext.__init__(self, parent)
        EncryptionCapabilities.__init__(self)


class TransformHeader(core.Frame):
    """
    TransformHeader is designed to be a transparent slip attached to a Netbios
    frame object (specified as parent). During serialization, if a Netbios frame
    contains an attribute "transform", then that object's encode method will be
    called instead of each child frames' encode method. This frame is responsible
    for both encrypting and decrypting Smb2 frames according to an attached
    encryption context.

    If the encryption_context is not explicitly specified, then it will be looked
    up based on session_id from the parent Netbios frame's connection reference
    """
    def __init__(self, parent):
        core.Frame.__init__(self, parent)
        self.protocol_id = array.array('B', "\xfdSMB")
        self.signature = None
        self.nonce = array.array('B',
                                 map(random.randint, [0]*16, [255]*16))
        self.original_message_size = 0
        self.flags = 0x1
        self.session_id = None
        self.encryption_context = None
        if parent is not None:
            parent.transform = self
        else:
            self._smb2_frames = []

    def _children(self):
        if self.parent is not None:
            return self.parent._children()
        else:
            return self._smb2_frames

    def append(self, smb2_frame):
        if self.parent is not None:
            self.parent.append(smb2_frame)
        else:
            self._smb2_frames.append(smb2_frame)

    def _encode(self, cur):
        self._encode_header(cur)
        self._encode_smb2(cur)

    def _encode_header(self, cur):
        # look up the encryption context if not specified
        if self.encryption_context is None and self.parent is not None:
            self.encryption_context = self.parent.conn.encryption_context(self.session_id)
        cur.encode_bytes(self.protocol_id)

        # the signature will be written in _encode_smb2
        self.signature_offset = cur.offset
        cur.advanceto(cur + 16)

        # the following fields are part of AdditionalAuthenticatedData and are
        # used as inputs to the AES cipher
        self.crypto_header_start = cur.offset
        # nonce field size is 16 bytes right padded with zeros
        if len(self.nonce) > 16:
            self.nonce = self.nonce[:16]
        elif len(self.nonce) < 16:
            self.nonce = self.nonce + array.array('B', "\0"*(16-len(self.nonce)))
        cur.encode_bytes(self.nonce)
        self.original_message_size_hole = cur.hole.encode_uint32le(0)
        cur.encode_uint16le(0)  # reserved
        cur.encode_uint16le(self.flags)
        cur.encode_uint64le(self.session_id)
        self.crypto_header_end = cur.offset

    def _encode_smb2(self, cur):
        # serialize all chained Smb2 commands into one buffer
        original_message_buf = array.array('B')
        original_message_cur = core.Cursor(original_message_buf, 0)
        for smb_frame in self.parent:
            smb_frame.encode(original_message_cur)
        self.original_message_size = len(original_message_buf)
        self.original_message_size_hole(self.original_message_size)
        crypto_header = cur.array[self.crypto_header_start:self.crypto_header_end]
        (self.ciphertext,
         self.signature) = self.encryption_context.encrypt(
                                original_message_buf,
                                crypto_header,
                                self.nonce)
        cur.encode_bytes(self.ciphertext)

        # fill in the signature hole
        sig_cur = core.Cursor(cur.array, self.signature_offset)
        sig_cur.encode_bytes(self.signature)

    def _decode(self, cur):
        self._decode_header(cur)
        self._decode_smb2(cur)

    def _decode_header(self, cur):
        self.protocol_id = cur.decode_bytes(4)
        self.signature = cur.decode_bytes(16)
        # the following fields are part of AdditionalAuthenticatedData and are
        # used as inputs to the AES cipher
        self.crypto_header_start = cur.offset
        self.nonce = cur.decode_bytes(16)
        self.original_message_size = cur.decode_uint32le()
        cur.decode_uint16le()   # reserved
        self.flags = cur.decode_uint16le()
        self.session_id = cur.decode_uint64le()
        self.crypto_header_end = cur.offset
        if self.encryption_context is None and self.parent is not None:
            self.encryption_context = self.parent.conn.encryption_context(self.session_id)

    def _decode_smb2(self, cur):
        self.encrypted_data = cur.decode_bytes(self.original_message_size)
        crypto_header = cur.array[self.crypto_header_start:self.crypto_header_end]
        self.plaintext = self.encryption_context.decrypt(
                        self.encrypted_data,
                        self.signature,
                        crypto_header,
                        self.nonce)
        # scan through the plaintext for chained messages
        pt_cur = core.Cursor(self.plaintext, 0)
        end = pt_cur + len(self.plaintext)
        with pt_cur.bounded(pt_cur, end):
            while (pt_cur < end):
                start = pt_cur.offset
                message = smb2.Smb2(self.parent)
                message.decode(pt_cur)
                message.buf = pt_cur.array[start:pt_cur.offset]

    def verify(self, *args, **kwds):
        pass        # verification occurs at the point of decryption


class CryptoKeys300(object):
    """ Key generation for SMB 0x300 and 0x302 """
    def __init__(self, session_key, *args, **kwds):
        self.encryption = digest.derive_key(
            session_key, "SMB2AESCCM", "ServerIn \0")[:16].tostring()
        self.decryption = digest.derive_key(
            session_key, "SMB2AESCCM", "ServerOut\0")[:16].tostring()


class CryptoKeys311(object):
    """ Key generation for SMB 0x311 + """
    def __init__(self, session_key, pre_auth_integrity_hash, *args, **kwds):
        self.encryption = digest.derive_key(
            session_key, "SMBC2SCipherKey", pre_auth_integrity_hash)[:16].tostring()
        self.decryption = digest.derive_key(
            session_key, "SMBS2CCipherKey", pre_auth_integrity_hash)[:16].tostring()


class EncryptionContext(object):
    """
    Encapsulates all information needed to encrypt and decrypt messages.
    This context is attached to an SMB Session object
    """
    def __init__(self, keys, ciphers):
        self.keys = keys
        self.cipher = ciphers[0]
        if self.cipher == SMB2_AES_128_CCM:
            self.aes_mode = AES.MODE_CCM
            self.nonce_length = 11
        elif self.cipher == SMB2_AES_128_GCM:
            self.aes_mode = AES.MODE_GCM
            self.nonce_length = 12

    def encrypt(self, plaintext, authenticated_data, nonce):
        enc_cipher = AES.new(self.keys.encryption,
                             self.aes_mode,
                             nonce=nonce[:self.nonce_length].tostring())
        enc_cipher.update(authenticated_data.tostring())
        ciphertext, signature = enc_cipher.encrypt_and_digest(plaintext.tostring())
        return array.array('B', ciphertext), array.array('B', signature)

    def decrypt(self, ciphertext, signature, authenticated_data, nonce):
        dec_cipher = AES.new(self.keys.decryption,
                             self.aes_mode,
                             nonce=nonce[:self.nonce_length].tostring())
        dec_cipher.update(authenticated_data.tostring())
        return array.array('B',
                dec_cipher.decrypt_and_verify(ciphertext.tostring(),
                                              signature.tostring()))
