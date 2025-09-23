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
from enum import IntFlag, auto
from typing import *

import pya

from klayout_plugin_utils.debugging import debug, Debugging


class SelectionFilterOptions(IntFlag):
    NONE = 0
    RULERS_AND_ANNOTATIONS = auto()
    IMAGES = auto()
    POLYGONS = auto()
    BOXES = auto()
    TEXTS = auto()
    PATHS = auto()
    POINTS = auto()
    INSTANCES = auto()
    PARTIAL_SHAPES = auto()
    
    def include_instances(self) -> bool:
        return SelectionFilterOptions.INSTANCES in self 
    
    def include_shapes(self) -> bool:
        shape_flags = (
            SelectionFilterOptions.POLYGONS 
            | SelectionFilterOptions.BOXES
            | SelectionFilterOptions.PATHS
            | SelectionFilterOptions.POINTS
            | SelectionFilterOptions.PARTIAL_SHAPES
        )
        return bool(self & shape_flags)
    
    def include_shape(self, shape: pya.Shape) -> bool:
        if shape.is_point():
            return SelectionFilterOptions.POINTS in self
        elif shape.is_box():
            return SelectionFilterOptions.BOXES in self
        elif shape.is_path():
            return SelectionFilterOptions.PATHS in self
        elif shape.is_simple_polygon():
            return SelectionFilterOptions.POLYGONS in self
        elif shape.is_polygon():
            return SelectionFilterOptions.POLYGONS in self
        elif shape.is_text():
            return SelectionFilterOptions.TEXTS in self
        elif shape.is_user_object():
            return SelectionFilterOptions.PARTIAL_SHAPES in self
        elif shape.is_edge():
            return False
        elif shape.is_edge_pair():
            return False
        elif shape.is_null():
            return False
        return False
    
    @classmethod
    def option_by_menu_path(cls) -> Dict[str, SelectionFilterOptions]:
        return {
            'edit_menu.select_menu.pi_enable_15': SelectionFilterOptions.RULERS_AND_ANNOTATIONS,
            'edit_menu.select_menu.pi_enable_16': SelectionFilterOptions.IMAGES,
            'edit_menu.select_menu.pi_enable_17': SelectionFilterOptions.POLYGONS,
            'edit_menu.select_menu.pi_enable_18': SelectionFilterOptions.BOXES,
            'edit_menu.select_menu.pi_enable_19': SelectionFilterOptions.TEXTS,
            'edit_menu.select_menu.pi_enable_20': SelectionFilterOptions.PATHS,
            'edit_menu.select_menu.pi_enable_21': SelectionFilterOptions.POINTS,
            'edit_menu.select_menu.pi_enable_22': SelectionFilterOptions.INSTANCES,
            'edit_menu.select_menu.pi_enable_24': SelectionFilterOptions.PARTIAL_SHAPES,
        }
    
    @classmethod
    def from_ui(cls) -> SelectionFilterOptions:
        options = SelectionFilterOptions.NONE
    
        mw = pya.Application.instance().main_window()
        menu = mw.menu()
        for p, o in cls.option_by_menu_path().items():
            action = menu.action(p)
            if action.checked:
                options |= o

        return options
        
#--------------------------------------------------------------------------------

if __name__ == "__main__":
    options = SelectionFilterOptions.from_ui()
    print(list(options))

