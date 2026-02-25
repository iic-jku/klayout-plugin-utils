# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2026 Martin Jan Köhler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
# base39 encoding / decoding methods:
#    given a sequence of bytes, convert them to [0-9][a-z]
#
# why not use base64?
#    some filesystems are not case sensitive or case preserving
#--------------------------------------------------------------------------------

import unittest


# Base36 helper functions
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def int_to_base36(n: int, width: int = 0) -> str:
    """Convert int to base36 string, optionally zero-padded to width."""
    if n == 0:
        return "0".rjust(width, '0')
    chars = []
    while n > 0:
        n, r = divmod(n, 36)
        chars.append(_ALPHABET[r])
    s = ''.join(reversed(chars))
    return s.rjust(width, '0')


def base36_to_int(s: str) -> int:
    return sum(_ALPHABET.index(c) * (36 ** i)\
           for i, c in enumerate(reversed(s)))


def bytes_to_base36(data: bytes) -> str:
    # encode each byte as 2-character base36
    return ''.join(int_to_base36(b, 2) for b in data)


def base36_to_bytes(s: str) -> bytes:
    # decode every 2 chars as one byte
    return bytes(base36_to_int(s[i:i+2]) for i in range(0, len(s), 2))


#--------------------------------------------------------------------------------

class Base36HelperTests(unittest.TestCase):

    # ----------------------------------------
    # int_to_base36 / base36_to_int
    # ----------------------------------------
    
    def test_int_to_base36_basic(self):
        self.assertEqual(int_to_base36(0), "0")
        self.assertEqual(int_to_base36(1), "1")
        self.assertEqual(int_to_base36(35), "z")
        self.assertEqual(int_to_base36(36), "10")
        self.assertEqual(int_to_base36(71), "1z")
        self.assertEqual(int_to_base36(1295), "zz")
        self.assertEqual(int_to_base36(1296), "100")

    def test_int_to_base36_with_width(self):
        self.assertEqual(int_to_base36(5, width=3), "005")
        self.assertEqual(int_to_base36(1295, width=4), "00zz")

    def test_base36_to_int_basic(self):
        self.assertEqual(base36_to_int("0"), 0)
        self.assertEqual(base36_to_int("1"), 1)
        self.assertEqual(base36_to_int("z"), 35)
        self.assertEqual(base36_to_int("10"), 36)
        self.assertEqual(base36_to_int("1z"), 71)
        self.assertEqual(base36_to_int("zz"), 1295)
        self.assertEqual(base36_to_int("100"), 1296)

    def test_int_to_base36_round_trip(self):
        for n in range(0, 1000):
            s = int_to_base36(n)
            n2 = base36_to_int(s)
            self.assertEqual(n, n2)

    # ----------------------------------------
    # bytes_to_base36 / base36_to_bytes
    # ----------------------------------------
    
    def test_bytes_to_base36_basic(self):
        self.assertEqual(bytes_to_base36(b'\x00'), "00")
        self.assertEqual(bytes_to_base36(b'\x01'), "01")
        self.assertEqual(bytes_to_base36(b'\x0f'), "0f")
        self.assertEqual(bytes_to_base36(b'\xff'), "73")
        self.assertEqual(bytes_to_base36(b'\x01\x02\x03'), "010203")

    def test_base36_to_bytes_basic(self):
        self.assertEqual(base36_to_bytes("00"), b'\x00')
        self.assertEqual(base36_to_bytes("01"), b'\x01')
        self.assertEqual(base36_to_bytes("0f"), b'\x0f')
        self.assertEqual(base36_to_bytes("73"), b'\xff')
        self.assertEqual(base36_to_bytes("010203"), b'\x01\x02\x03')

    def test_bytes_round_trip(self):
        import itertools
        # Test a few sample sequences
        samples = [
            b'',
            b'\x00',
            b'\x01\x02\x03',
            b'\x00\xff\x7f\x80',
            b''.join(bytes([i]) for i in range(16))  # 0..15
        ]
        for data in samples:
            s = bytes_to_base36(data)
            data2 = base36_to_bytes(s)
            self.assertEqual(data, data2)

    def test_large_bytes_round_trip(self):
        import os
        data = os.urandom(256)  # 256 random bytes
        s = bytes_to_base36(data)
        data2 = base36_to_bytes(s)
        self.assertEqual(data, data2)
        

if __name__ == "__main__":
    unittest.main()
