#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        digest.py
#
# Abstract:
#
#        Message digest and key derivation (for SMB2/3)
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#

from __future__ import absolute_import
from __future__ import division
from builtins import range

import array

import Cryptodome.Hash.HMAC as HMAC
import Cryptodome.Hash.SHA256 as SHA256
import Cryptodome.Hash.SHA512 as SHA512
import Cryptodome.Cipher.AES as AES

from . import core


def sha256_hmac(key, message):
    return array.array("B", HMAC.new(key.tobytes(), message.tobytes(), SHA256).digest())


def aes128_cmac(key, message):
    aes = AES.new(key.tobytes(), mode=AES.MODE_ECB)

    def shiftleft(data):
        cin = 0
        cout = 0
        for i in reversed(range(0, len(data))):
            cout = (data[i] & 0x80) >> 7
            data[i] = ((data[i] << 1) | cin) & 0xFF
            cin = cout

        return cout

    def xor(data1, data2):
        for i in range(0, len(data1)):
            data1[i] ^= data2[i]

    def subkeys(key):
        zero = array.array("B", [0] * 16)
        rb = array.array("B", [0] * 15 + [0x87])

        key1 = array.array("B", aes.encrypt(zero.tobytes()))

        if shiftleft(key1):
            xor(key1, rb)

        key2 = array.array("B", key1)

        if shiftleft(key2):
            xor(key2, rb)

        return (key1, key2)

    message = array.array("B", message)
    mac = array.array("B", [0] * 16)
    scratch = array.array("B", [0] * 16)
    n = (len(message) + 16 - 1) // 16
    rem = len(message) % 16
    last_complete = n != 0 and rem == 0
    i = 0

    if n == 0:
        n = 1

    subkey1, subkey2 = subkeys(array.array("B", key))

    for i in range(0, n - 1):
        xor(mac, message[i * 16 : i * 16 + 16])
        mac = array.array("B", aes.encrypt(mac.tobytes()))

    if last_complete:
        scratch[0:16] = message[-16:]
        xor(scratch, subkey1)
    else:
        scratch[0:rem] = message[-rem:]
        scratch[rem] = 0x80
        xor(scratch, subkey2)

    xor(mac, scratch)
    mac = array.array("B", aes.encrypt(mac.tobytes()))

    return mac


def smb3_sha512(message):
    return array.array("B", SHA512.new(message.tobytes()).digest())


def derive_key(key, label, context):
    message = array.array("B")
    cur = core.Cursor(message, 0)

    cur.encode_uint32be(1)
    cur.encode_bytes(label)
    cur.encode_uint8be(0)
    cur.encode_uint8be(0)
    cur.encode_bytes(context)
    cur.encode_uint32be(len(key) * 8)

    return sha256_hmac(key, message)
