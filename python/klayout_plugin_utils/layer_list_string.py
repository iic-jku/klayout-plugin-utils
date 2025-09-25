# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2025 Martin Jan Köhler
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

from __future__ import annotations
from dataclasses import dataclass, field
from typing import *
import traceback
import re
import unittest

import pya


@dataclass
class ParserError:
    msg: str
    column: int


@dataclass
class ParseResult:
    result: Optional[LayerList] = field(default_factory=list)
    errors: List[ParserError] = field(default_factory=list)


@dataclass
class LayerList:
    layers: List[pya.LayerInfo] = field(default_factory=list)
    
    def __str__(self) -> str:
        return ' '.join([l.to_s() for l in self.layers])
    
    @classmethod
    def parse_layer_list_string(cls, s: str) -> ParseResult:
        """
        Parse LayerList from a string:
        
        A comma or blank separated list of layers to create in the usual layer notation, 
        e.g. "1/0 2/0 3/0", "metal1 via1 metal2" or "metal1 (1/0) via1 (2/0) metal2 (3/0)"

        Returns either a valid LayerList, or a list of parser errors
        """
        layers = []
        errors = []
        
        # Regex matches:
        # 1) name + (layer/datatype)
        # 2) bare (layer/datatype)
        # 3) bare numeric layer/datatype (L/D)
        # 4) name only
        layer_pattern = re.compile(r"""
            (?:
                (?P<name>[A-Za-z_]\w*)?                # optional symbolic name
                \s*
                \(                                      # opening parenthesis
                    \s*(?P<layer1>\d+)\s*/\s*(?P<dtype1>\d+)\s*   # L/D inside ()
                \)
            )
            |
            (?:
                (?P<layer2>\d+)\s*/\s*(?P<dtype2>\d+)  # bare numeric L/D
            )
            |
            (?:
                (?P<name_only>[A-Za-z_]\w*)            # name only
            )
        """, re.VERBOSE)
        
        pos = 0
        while pos < len(s):
            m = layer_pattern.match(s, pos)
            if not m:
                # Skip whitespace and commas
                if s[pos] in " ,":
                    pos += 1
                    continue
                errors.append(ParserError(f"Unexpected token at position {pos}", pos))
                # Skip this character to avoid infinite loop
                pos += 1
                continue
        
            gd = m.groupdict()
            if gd["layer2"]:  # numeric only
                li = pya.LayerInfo(int(gd["layer2"]), int(gd["dtype2"]))
            elif gd["layer1"]:  # name + (layer/datatype)
                name = gd["name"] if gd["name"] else ""
                if name == '':
                    li = pya.LayerInfo(int(gd["layer1"]), int(gd["dtype1"]))
                else:
                    li = pya.LayerInfo(int(gd["layer1"]), int(gd["dtype1"]), name)
            elif gd["name_only"]:  # name only
                li = pya.LayerInfo(gd["name_only"])
            else:
                # Should never happen
                errors.append(ParserError(f"Invalid token at position {pos}", pos))
                pos = m.end()
                continue
            layers.append(li)
            pos = m.end()
            
        if errors:
            return ParseResult(errors=errors)
            
        return ParseResult(result=LayerList(layers=layers))
        
    @classmethod
    def is_valid_layer_list_string(cls, s: str) -> bool:
        r = cls.parse_layer_list_string(s)
        return not r.errors
        
#--------------------------------------------------------------------------------

class LayerListTests(unittest.TestCase):
    def _expect_parse_result(self, s: str, expected: ParseResult):
        obtained = LayerList.parse_layer_list_string(s)
        self.assertEqual(expected, obtained)

    def test_parse_empty(self):
        self._expect_parse_result('', ParseResult(result=LayerList(layers=[])))

    def test_parse_only_name(self):
        self._expect_parse_result('met1', ParseResult(result=LayerList(layers=[pya.LayerInfo('met1')])))

    def test_parse_only_gds_pair(self):
        self._expect_parse_result('(3/10)', ParseResult(result=LayerList(layers=[pya.LayerInfo(3, 10)])))
        
    def test_zzz_parse_mix(self):
        self._expect_parse_result(
            'metal1 (1/0) via1 (2/0) metal2 (3/0) 1/0 99/42',
            ParseResult(result=LayerList(layers=[
                pya.LayerInfo(1, 0, 'metal1'),
                pya.LayerInfo(2, 0, 'via1'),
                pya.LayerInfo(3, 0, 'metal2'),
                pya.LayerInfo(1, 0),
                pya.LayerInfo(99, 42),
            ]))
        )
        
#--------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
        