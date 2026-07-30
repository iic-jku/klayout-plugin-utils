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

import traceback
from typing import *

import pya

from klayout_plugin_utils.debugging import debug, Debugging


class LibraryHelper:
    def __init__(self, tech: pya.Technology):
        self.tech = tech

    def get_library_names(self) -> List[str]:
        """Return sorted list of all registered KLayout library names."""
        try:
            names = sorted([
                l.name()
                for l in [
                    pya.Library.library_by_id(i) 
                    for i in pya.Library.library_ids()
                ]
                if self.tech.name in l.technologies() \
                   or not l.technologies()
            ])
            
            # if Debugging.DEBUG:
            #    debug(f"LibraryHelper.get_library_names: {names}")
            return names
        except Exception as e:
            if Debugging.DEBUG:
                debug(f"LibraryHelper.get_library_names FAILED: {e}")
            traceback.print_exc()
            return []
    
    def get_library_cell_names_with_type(self, lib_name: str) -> List[Tuple[str, bool]]:
        """Return sorted list of (cell_name, is_pcell) in the given library."""
        try:
            lib = pya.Library.library_by_name(lib_name, self.tech.name)
            if lib is None:
                if Debugging.DEBUG:
                    debug(f"LibraryHelper.get_library_cell_names_with_type: no lib '{lib_name}'")
                return []
            ly = lib.layout()
            
            result = {}
            
            # Collect PCell declarations (these don't appear in each_cell)
            for pcell_id in ly.pcell_ids():
                decl = ly.pcell_declaration(pcell_id)
                if decl:
                    result[decl.name()] = True
            
            # Collect static cells (skip PCell variants)
            for c in ly.each_cell():
                if c.name not in result and not c.is_pcell_variant():
                    result[c.name] = False
            
            return sorted(result.items(), key=lambda x: x[0])
        except Exception as e:
            print(f"LibraryHelper.get_library_cell_names_with_type FAILED: {e}")
            traceback.print_exc()
            return []
            
    def get_library_cell_names(self, lib_name: str) -> List[str]:
        """Return sorted list of cell names in the given library."""
        return [name for name, _ in self.get_library_cell_names_with_type(lib_name)]
