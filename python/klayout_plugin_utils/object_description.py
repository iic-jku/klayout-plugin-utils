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

from typing import *

import pya


def describe_shape_name(shape: pya.Shape) -> str:
    if shape.is_point():
        return "Point"
    elif shape.is_box():
        return "Box"
    elif shape.is_path():
        return "Path"
    elif shape.is_simple_polygon():
        return "Polygon"
    elif shape.is_polygon():
        return "Polygon"
    elif shape.is_edge():
        return "Edge"
    elif shape.is_edge_pair():
        return "EdgePair"
    elif shape.is_null():
        return "none"
    elif shape.is_text():
        return "Text"
    elif shape.is_user_object():
        return "User Defined Object"

def describe_shape_geometry(shape: pya.Shape) -> str:
    if shape.is_point():
        p = shape.dpoint
        return f"at ({p.x}, {p.y})"
    elif shape.is_box():
        return f"box {shape.dbox}"
    elif shape.is_path():
        return f"path {shape.dpath}"
    elif shape.is_simple_polygon():
        return f"polygon {shape.dsimple_polygon}"
    elif shape.is_polygon():
        return f"polygon {shape.dpolygon}"
    elif shape.is_edge():
        return f"edge {shape.dedge}"
    elif shape.is_edge_pair():
        return f"edge pair {shape.dedge_pair}"
    elif shape.is_null():
        return ''
    elif shape.is_text():
        return f"text {shape.dtext}"
    else:
        return f"bbox {shape.dbbox}"

def describe_shape(shape: Optional[pya.Shape]) -> str:
    if shape is None:
        return 'none'
    li = shape.layer_info
    return f"{describe_shape_name(shape)} (layer {li}) "\
           f"{describe_shape_geometry(shape)}"
    
def describe_instance(inst: Optional[pya.Instance]) -> str:
    if inst is None:
        return 'none'
    return f"Instance ({inst.cell.name}) "\
           f"bbox {inst.dbbox()}"

def describe_object(o: pya.ObjectInstPath) -> str:
    sh = o.shape
    if sh is not None:
        return describe_shape(sh)
    else:
        inst = o.inst()
        if inst is not None:
            return describe_instance(inst)
    return "unknown"
    