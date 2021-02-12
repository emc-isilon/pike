#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

# test vectors from Microsoft openspecification group
# SMB 3.0 Encryption: https://blogs.msdn.microsoft.com/openspecification/2012/10/05/encryption-in-smb-3-0-a-protocol-perspective/
# SMB 3.1.1 Encryption: https://blogs.msdn.microsoft.com/openspecification/2015/09/09/smb-3-1-1-encryption-in-windows-10/
# SMB 3.1.1 Pre-auth integrity: https://blogs.msdn.microsoft.com/openspecification/2015/08/11/smb-3-1-1-pre-authentication-integrity-in-windows-10/
from builtins import object

import array
import unittest

import pike.crypto as crypto
import pike.digest as digest
import pike.netbios as netbios
import pike.smb2 as smb2

from binascii import unhexlify


class bogus_connection(object):
    def signing_key(self, *args, **kwds):
        return self._signing_key

    def encryption_context(self, *args, **kwds):
        return self._encryption_context

    def signing_digest(self, *args, **kwds):
        return digest.aes128_cmac


class bogus_300_connection(bogus_connection):
    def __init__(self, session_key):
        self._signing_key = digest.derive_key(
            session_key, b"SMB2AESCMAC", b"SmbSign\0"
        )[:16]
        self._encryption_context = crypto.EncryptionContext(
            crypto.CryptoKeys300(session_key), [crypto.SMB2_AES_128_CCM]
        )


class bogus_311_connection(bogus_connection):
    def __init__(self, session_key, pre_auth_integrity_value, ciphers):
        self._signing_key = digest.derive_key(
            session_key, b"SMBSigningKey", pre_auth_integrity_value
        )[:16]
        self._encryption_context = crypto.EncryptionContext(
            crypto.CryptoKeys311(session_key, pre_auth_integrity_value), ciphers
        )


class PAIntegrity(object):
    def __init__(self):
        self.hash = array.array("B", b"\0" * 64)

    def update(self, data):
        self.hash = digest.smb3_sha512(self.hash + data)


class TestVector(unittest.TestCase):
    def test_pre_auth_integrity(self):
        h = PAIntegrity()
        negotiate_request = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000000800000000000000000000100000000000000FFFE000000000000"
                "00000000000000000000000000000000000000000000000024000500000000003F000000ECD86F32"
                "6276024F9F7752B89BB33F3A70000000020000000202100200030203110300000100260000000000"
                "010020000100FA49E6578F1F3A9F4CD3E9CC14A67AA884B3D05844E0E5A118225C15887F32FF0000"
                "0200060000000000020002000100"
            ),
        )
        h.update(negotiate_request)
        exp_pae_1 = array.array(
            "B",
            unhexlify(
                "DD94EFC5321BB618A2E208BA8920D2F422992526947A409B5037DE1E0FE8C7362B8C47122594CDE0"
                "CE26AA9DFC8BCDBDE0621957672623351A7540F1E54A0426"
            ),
        )
        self.assertEqual(h.hash, exp_pae_1)
        negotiate_response = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000000010001000000000000000100000000000000FFFE000000000000"
                "000000000000000000000000000000000000000000000000410001001103020039CBCAF329714942"
                "BDCE5D60F09AB3FB2F000000000080000000800000008000D8DAE5ADCBAED00109094AB095AED001"
                "80004001C00100006082013C06062B0601050502A08201303082012CA01A3018060A2B0601040182"
                "3702021E060A2B06010401823702020AA282010C048201084E45474F455854530100000000000000"
                "60000000700000007C7CC0FD06D6362D02DDE1CF343BFE292900F49750B4AA97934D9C4296B26E51"
                "FD370471B235E15A50DAE15BD5489C87000000000000000060000000010000000000000000000000"
                "5C33530DEAF90D4DB2EC4AE3786EC3084E45474F4558545303000000010000004000000098000000"
                "7C7CC0FD06D6362D02DDE1CF343BFE295C33530DEAF90D4DB2EC4AE3786EC3084000000058000000"
                "3056A05430523027802530233121301F06035504031318546F6B656E205369676E696E6720507562"
                "6C6963204B65793027802530233121301F06035504031318546F6B656E205369676E696E67205075"
                "626C6963204B6579010026000000000001002000010060A3C3B95C3C7CCD51EC536648D9B3AC74C4"
                "83CA5B65385A251117BEB30712E50000020004000000000001000200"
            ),
        )
        h.update(negotiate_response)
        exp_pae_2 = array.array(
            "B",
            unhexlify(
                "324BFA92A4F3A190E466EBEA08D9C110DC88BFED758D9846ECC6F541CC1D02AE3C94A79F36011E99"
                "7E13F841B91B50957AD07B19C8E2539C0B23FDAE09D2C513"
            ),
        )
        self.assertEqual(h.hash, exp_pae_2)
        session_setup_request = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000100800000000000000000000200000000000000FFFE000000000000"
                "00000000000000000000000000000000000000000000000019000001010000000000000058004A00"
                "0000000000000000604806062B0601050502A03E303CA00E300C060A2B06010401823702020AA22A"
                "04284E544C4D5353500001000000978208E200000000000000000000000000000000060380250000"
                "000F"
            ),
        )
        h.update(session_setup_request)
        exp_pae_3 = array.array(
            "B",
            unhexlify(
                "AC0B0F2B9986257700365E416D142A6EDC96DF03594A19E52A15F6BD0D041CD5D432F8ED42C55E33"
                "197A50C9EC00F1462B50C592211B1471A04B56088FDFD5F9"
            ),
        )
        self.assertEqual(h.hash, exp_pae_3)
        session_setup_response = array.array(
            "B",
            unhexlify(
                "FE534D4240000100160000C00100010001000000000000000200000000000000FFFE000000000000"
                "190000000010000000000000000000000000000000000000090000004800B300A181B03081ADA003"
                "0A0101A10C060A2B06010401823702020AA281970481944E544C4D53535000020000000C000C0038"
                "00000015828AE20D1D8BA31179D008000000000000000050005000440000000A0092270000000F53"
                "005500540033003100310002000C0053005500540033003100310001000C00530055005400330031"
                "00310004000C0053005500540033003100310003000C0053005500540033003100310007000800A1"
                "A1F5ADCBAED00100000000"
            ),
        )
        h.update(session_setup_response)
        exp_pae_4 = array.array(
            "B",
            unhexlify(
                "2729E3440DFDDD839E37193F6E8F20C20CEFB3469E453A70CD980EEC06B8835740A7376008563336"
                "4C8989895ECE81BF102DEEB14D4B7D48AFA76901A7A38387"
            ),
        )
        self.assertEqual(h.hash, exp_pae_4)
        session_setup_response2 = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000100800000000000000000000300000000000000FFFE000000000000"
                "1900000000100000000000000000000000000000000000001900000101000000000000005800CF01"
                "0000000000000000A18201CB308201C7A0030A0101A28201AA048201A64E544C4D53535000030000"
                "001800180090000000EE00EE00A80000000C000C00580000001A001A0064000000120012007E0000"
                "001000100096010000158288E2060380250000000FECAC77A5F385A8BF9C38C706EEEDDCD3530055"
                "005400330031003100610064006D0069006E006900730074007200610074006F0072004400520049"
                "0056004500520033003100310000000000000000000000000000000000000000000000000063078E"
                "B639FE03E20A231C3AE3BF23080101000000000000A1A1F5ADCBAED001BC4AD05F223CC90F000000"
                "0002000C0053005500540033003100310001000C0053005500540033003100310004000C00530055"
                "00540033003100310003000C0053005500540033003100310007000800A1A1F5ADCBAED001060004"
                "00020000000800300030000000000000000000000000300000B61FEFCAA857EA57BF1EDCEBF8974B"
                "8E0EBA5A6DFD9D07A31D11B548F8C9D0CC0A00100000000000000000000000000000000000090016"
                "0063006900660073002F005300550054003300310031000000000000000000000000003B9BDFF38F"
                "5EE8F9663F11A0F4C03A78A31204100100000063775A9A5FD97F0600000000"
            ),
        )
        h.update(session_setup_response2)
        exp_pae_5 = array.array(
            "B",
            unhexlify(
                "0DD13628CC3ED218EF9DF9772D436D0887AB9814BFAE63A80AA845F36909DB7928622DDDAD522D97"
                "51640A459762C5A9D6BB084CBB3CE6BDADEF5D5BCE3C6C01"
            ),
        )
        self.assertEqual(h.hash, exp_pae_5)
        session_key = array.array("B", unhexlify("270E1BA896585EEB7AF3472D3B4C75A7"))
        signing_key = digest.derive_key(session_key, b"SMBSigningKey", h.hash)[:16]
        exp_signing_key = array.array(
            "B", unhexlify("73FE7A9A77BEF0BDE49C650D8CCB5F76")
        )
        self.assertEqual(signing_key, exp_signing_key)

    def test_encryption_smb_300(self):
        session_key = array.array("B", unhexlify("B4546771B515F766A86735532DD6C4F0"))
        session_id = 0x8E40014000011
        conn = bogus_300_connection(session_key)
        exp_encryption_key = unhexlify("261B72350558F2E9DCF613070383EDBF")
        self.assertEqual(conn.encryption_context().keys.encryption, exp_encryption_key)

        # construct the request
        nb = netbios.Netbios()
        th = crypto.TransformHeader(nb)
        th.nonce = array.array("B", unhexlify("66E69A111892584FB5ED524A744DA3EE"))
        th.session_id = session_id
        th.encryption_context = conn.encryption_context()

        smb_packet = smb2.Smb2(nb, conn)
        smb_packet.credit_charge = 1
        smb_packet.credit_request = 64
        smb_packet.channel_sequence = 0
        smb_packet.flags = smb2.SMB2_FLAGS_SIGNED
        smb_packet.message_id = 4
        smb_packet.tree_id = 1
        smb_packet.signature = b"\0" * 16
        smb_packet.session_id = session_id
        write_req = smb2.WriteRequest(smb_packet)
        write_req.file_id = (0x200003900000115, 0x23900000001)
        write_req.buffer = b"Smb3 encryption testing"
        write_req.write_channel_info_offset = 0x70

        exp_serialized = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000900400008000000000000000400000000000000"
                "FFFE0000010000001100001400E4080000000000000000000000000000000000"
                "3100700017000000000000000000000015010000390000020100000039020000"
                "00000000000000007000000000000000536D623320656E6372797074696F6E20"
                "74657374696E67"
            ),
        )
        serialized = smb_packet.serialize()
        self.assertEqual(serialized, exp_serialized)

        transformed_serial = th.serialize()

        exp_encrypted = array.array(
            "B",
            unhexlify(
                "25C8FEE16605A437832D1CD52DA9F4645333482A175FE5384563F45FCDAFAEF3"
                "8BC62BA4D5C62897996625A44C29BE5658DE2E6117585779E7B59FFD971278D0"
                "8580D7FA899E410E910EABF5AA1DB43050B33B49182637759AC15D84BFCDF5B6"
                "B238993C0F4CF4D6012023F6C627297075D84B7803912D0A9639634453595EF3"
                "E33FFE4E7AC2AB"
            ),
        )
        self.assertEqual(th.ciphertext, exp_encrypted)

        exp_transformed = array.array(
            "B",
            unhexlify(
                "FD534D4281A286535415445DAE393921E44FA42E66E69A111892584FB5ED524A"
                "744DA3EE87000000000001001100001400E4080025C8FEE16605A437832D1CD5"
                "2DA9F4645333482A175FE5384563F45FCDAFAEF38BC62BA4D5C62897996625A4"
                "4C29BE5658DE2E6117585779E7B59FFD971278D08580D7FA899E410E910EABF5"
                "AA1DB43050B33B49182637759AC15D84BFCDF5B6B238993C0F4CF4D6012023F6"
                "C627297075D84B7803912D0A9639634453595EF3E33FFE4E7AC2AB"
            ),
        )
        self.assertEqual(transformed_serial, exp_transformed)

    def test_decryption_smb_300(self):
        session_key = array.array("B", unhexlify("B4546771B515F766A86735532DD6C4F0"))
        session_id = 0x8E40014000011
        conn = bogus_300_connection(session_key)
        exp_decryption_key = unhexlify("8FE2B57EC34D2DB5B1A9727F526BBDB5")
        self.assertEqual(conn.encryption_context().keys.decryption, exp_decryption_key)
        transform_message = array.array(
            "B",
            unhexlify(
                "FD534D42A6015530A18F6D9AFFE22AFAE8E66484860000000000000011000014"
                "00E4080050000000000001001100001400E40800DBF46435C5F14169293CE079"
                "E344479BF670227E49873F458672C3098DAC467DD5809F369D67409166515787"
                "1483E01F7BECD02064EAC3E235F913668BBC2F097980D4B378F1993EFF6E60D1"
                "77309E5B"
            ),
        )
        nb = netbios.Netbios()
        th = crypto.TransformHeader(nb)
        th.encryption_context = conn.encryption_context()
        th.parse(transform_message)
        exp_smb_message = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000900210009000000000000000400000000000000"
                "FFFE0000010000001100001400E4080000000000000000000000000000000000"
                "11000000170000000000000000000000"
            ),
        )
        self.assertEqual(nb[0].buf, exp_smb_message)

    def test_encryption_smb_311(self):
        session_key = array.array("B", unhexlify("419FDDF34C1E001909D362AE7FB6AF79"))
        pre_auth_integrity_hash = array.array(
            "B",
            unhexlify(
                "B23F3CBFD69487D9832B79B1594A367CDD950909B774C3A4C412B4FCEA9EDDDBA7DB256BA2EA30E9"
                "77F11F9B113247578E0E915C6D2A513B8F2FCA5707DC8770"
            ),
        )
        session_id = 0x100000000025
        ciphers = [crypto.SMB2_AES_128_GCM]
        conn = bogus_311_connection(session_key, pre_auth_integrity_hash, ciphers)
        exp_encryption_key = unhexlify("A2F5E80E5D59103034F32E52F698E5EC")
        self.assertEqual(conn.encryption_context().keys.encryption, exp_encryption_key)

        # construct the request
        nb = netbios.Netbios()
        th = crypto.TransformHeader(nb)
        th.nonce = array.array("B", unhexlify("C7D6822D269CAF48904C664C"))
        th.session_id = session_id
        th.encryption_context = conn.encryption_context()

        smb_packet = smb2.Smb2(nb, conn)
        smb_packet.credit_charge = 1
        smb_packet.credit_request = 1
        smb_packet.channel_sequence = 0
        smb_packet.flags = smb2.SMB2_FLAGS_SIGNED
        smb_packet.message_id = 5
        smb_packet.tree_id = 1
        smb_packet.signature = b"\0" * 16
        smb_packet.session_id = session_id
        write_req = smb2.WriteRequest(smb_packet)
        write_req.file_id = (0x400000006, 0x400000001)
        write_req.buffer = b"Smb3 encryption testing"
        write_req.write_channel_info_offset = 0x70

        exp_serialized = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000900010008000000000000000500000000000000FFFE000001000000"
                "25000000001000000000000000000000000000000000000031007000170000000000000000000000"
                "0600000004000000010000000400000000000000000000007000000000000000536D623320656E63"
                "72797074696F6E2074657374696E67"
            ),
        )
        serialized = smb_packet.serialize()
        self.assertEqual(serialized, exp_serialized)

        transformed_serial = th.serialize()

        exp_encrypted = array.array(
            "B",
            unhexlify(
                "6ECDD2A7AFC7B47763057A041B8FD4DAFFE990B70C9E09D36C084E02D14EF247F8BDE38ACF6256F8"
                "B1D3B56F77FBDEB312FEA5E92CBCC1ED8FB2EBBFAA75E49A4A394BB44576545567C24D4C014D47C9"
                "FBDFDAFD2C4F9B72F8D256452620A299F48E29E53D6B61D1C13A19E91AF013F00D17E3ABC2FC3D36"
                "C8C1B6B93973253852DBD442E46EE8"
            ),
        )
        self.assertEqual(th.ciphertext, exp_encrypted)

        exp_transformed = array.array(
            "B",
            unhexlify(
                "FD534D42BD73D97D2BC9001BCAFAC0FDFF5FEEBCC7D6822D269CAF48904C664C0000000087000000"
                "0000010025000000001000006ECDD2A7AFC7B47763057A041B8FD4DAFFE990B70C9E09D36C084E02"
                "D14EF247F8BDE38ACF6256F8B1D3B56F77FBDEB312FEA5E92CBCC1ED8FB2EBBFAA75E49A4A394BB4"
                "4576545567C24D4C014D47C9FBDFDAFD2C4F9B72F8D256452620A299F48E29E53D6B61D1C13A19E9"
                "1AF013F00D17E3ABC2FC3D36C8C1B6B93973253852DBD442E46EE8"
            ),
        )
        self.assertEqual(transformed_serial, exp_transformed)

    def test_decryption_smb_311(self):
        session_key = array.array("B", unhexlify("419FDDF34C1E001909D362AE7FB6AF79"))
        pre_auth_integrity_hash = array.array(
            "B",
            unhexlify(
                "B23F3CBFD69487D9832B79B1594A367CDD950909B774C3A4C412B4FCEA9EDDDBA7DB256BA2EA30E9"
                "77F11F9B113247578E0E915C6D2A513B8F2FCA5707DC8770"
            ),
        )
        session_id = 0x100000000025
        ciphers = [crypto.SMB2_AES_128_GCM]
        conn = bogus_311_connection(session_key, pre_auth_integrity_hash, ciphers)
        exp_decryption_key = unhexlify("748C50868C90F302962A5C35F5F9A8BF")
        self.assertEqual(conn.encryption_context().keys.decryption, exp_decryption_key)

        transform_message = array.array(
            "B",
            unhexlify(
                "FD534D42ACBE1CB7ED343ADF1725EF144D90D4B0E06831DD2E8EB7B4000000000000000050000000"
                "00000100250000000010000026BBBF949983A6C1C796559D0F2C510CB651D1F7B6AC8DED32A2A0B8"
                "F2D793A815C6F6B848D69767A215841A42D400AE6DDB5F0B44173A014973321FDD7950DA6179159B"
                "82E03C9E18A050FF0EA1C967"
            ),
        )
        nb = netbios.Netbios()
        th = crypto.TransformHeader(nb)
        th.encryption_context = conn.encryption_context()
        th.parse(transform_message)
        exp_smb_message = array.array(
            "B",
            unhexlify(
                "FE534D4240000100000000000900010001000000000000000500000000000000FFFE000001000000"
                "25000000001000000000000000000000000000000000000011000000170000000000000000000000"
            ),
        )
        self.assertEqual(nb[0].buf, exp_smb_message)


if __name__ == "__main__":
    unittest.main()
