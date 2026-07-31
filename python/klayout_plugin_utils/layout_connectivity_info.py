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

from __future__ import annotations

from dataclasses import dataclass, field
from typing import *

import pya
    
from klayout_plugin_utils.debugging import debug, Debugging
from klayout_plugin_utils.str_enum_compat import DualStrEnum

# ---------------------------------------------------------------------------

# property keys for connectivity information (pins)
PROPERTY_KEY__PIN_INFO__VERSION = 'PIN_INFO__VERSION'
PROPERTY_KEY__PIN_INFO__LIB_NAME = 'PIN_INFO__LIB_NAME'
PROPERTY_KEY__PIN_INFO__CELL_NAME = 'PIN_INFO__CELL_NAME'
PROPERTY_KEY__PIN_INFO__PIN_NAME = 'PIN_INFO__PIN_NAME'
PROPERTY_KEY__PIN_INFO__TERM_NAME = 'PIN_INFO__TERM_NAME'

# property keys for connectivity information (instances)
PROPERTY_KEY__INSTANCE_INFO__VERSION = 'INSTANCE_INFO__VERSION'
PROPERTY_KEY__INSTANCE_INFO__LIB_NAME = 'INSTANCE_INFO__LIB_NAME'
PROPERTY_KEY__INSTANCE_INFO__CELL_NAME = 'INSTANCE_INFO__CELL_NAME'
PROPERTY_KEY__INSTANCE_INFO__INSTANCE_NAME = 'INSTANCE_INFO__INSTANCE_NAME'
PROPERTY_KEY__INSTANCE_INFO__HIERARCHY_PATH = 'INSTANCE_INFO__HIERARCHY_PATH'  # e.g. top.X3.X1
PROPERTY_KEY__INSTANCE_INFO__ORIGINAL_INSTANCE_PARAMS = 'INSTANCE_INFO__ORIGINAL_INSTANCE_PARAMS'
PROPERTY_KEY__INSTANCE_INFO__LOCAL_NET_MAP = 'INSTANCE_INFO__LOCAL_NET_MAP'  # JSON with pins->nets
PROPERTY_KEY__INSTANCE_INFO__GLOBAL_NET_MAP = 'INSTANCE_INFO__GLOBAL_NET_MAP'  # JSON with pins->nets

# ---------------------------------------------------------------------------

@dataclass
class Context:
    layout_view: pya.LayoutView

    @property
    def cell_view(self) -> pya.CellView:
        return self.layout_view.active_cellview()
    
    @property
    def layout(self) -> pya.Layout:
        return self.cell_view.layout()


@dataclass
class PinInfo:
    name: str
    term_name: str
    bbox: pya.DBox   # local (PCell) coordinates
    layers: List[pya.LayerInfo] = field(default_factory=list)


@dataclass 
class PCellInstanceConnectivityInfo:
    inst: pya.Instance
    inst_name: str
    cell_name: str
    lib_name: Optional[str] = None
    pin_infos: List[PinInfo] = field(default_factory=list)

    @classmethod
    def for_pcell(cls, 
                  inst: pya.Instance, 
                  outer_trans: pya.ICplxTrans,
                  ctx: Context) -> Optional[PCellInstanceConnectivityInfo]:
        pcell_decl = inst.pcell_declaration()
            
        # cell_name: the PCell's declared name (e.g. "nmos"), not the mangled
        # variant name klayout may show (like "nmos$1")
        cell_name = pcell_decl.name() if pcell_decl is not None else inst.cell.name
    
        # lib_name: resolve the owning pya.Library, if any. A PCell instantiated
        # from a Library shows up as cell.library() != None; local/embedded
        # PCells (no separate Library) return None here.
        lib = inst.cell.library()
        lib_name = lib.name() if lib is not None else None
    
        result = PCellInstanceConnectivityInfo(
            inst=inst,
            inst_name=inst.cell.name,
            cell_name=inst.cell.name,
            lib_name=lib_name
        )
        
        layout = ctx.layout
        
        siter = pya.RecursiveShapeIterator(layout, inst.cell, layout.layer_indexes())   # TODO: optimize, only shapes in pin layers
        siter.shape_flags = pya.Shapes.SAllWithProperties | pya.Shapes.SPolygons
        siter.enable_properties()
        while not siter.at_end():
            sh = siter.shape()
            layer_info = layout.get_info(siter.layer())
            properties = sh.properties()
            
            if Debugging.DEBUG:
                debug(f"Pin Info: {sh.to_s()} on layer {siter.layer()} ({layer_info})")
            
            version = properties.get(PROPERTY_KEY__PIN_INFO__VERSION)
            # lib_name = properties.get(PROPERTY_KEY__PIN_INFO__LIB_NAME)
            # cell_name = properties.get(PROPERTY_KEY__PIN_INFO__CELL_NAME)
            pin_name = properties.get(PROPERTY_KEY__PIN_INFO__PIN_NAME)
            term_name = properties.get(PROPERTY_KEY__PIN_INFO__TERM_NAME)
            
            if version is not None and\
               pin_name is not None and\
               term_name is not None:
                full_trans = outer_trans * siter.itrans()
                bbox = sh.box.transformed(full_trans).to_dtype(layout.dbu)
                
                pi = PinInfo(
                    name=pin_name, 
                    term_name=term_name,
                    bbox=bbox,
                    layers=[layer_info]
                )
                result.pin_infos.append(pi)
            
            siter.next()

        return result


@dataclass
class CellConnectivityInfo:
    cell: pya.Cell    # potentially destroyed, so cache cell_name
    cell_name: str
    pcell_infos: List[PCellInstanceConnectivityInfo] = field(default_factory=list)

    @classmethod
    def for_cell_instance(cls, cell: pya.Cell, ctx: Context) -> CellConnectivityInfo:
        result = cls(cell=cell, cell_name=cell.name)
        
        lv = ctx.layout_view
        cv = lv.active_cellview()
        layout = cv.layout()
        
        iter = cell.begin_instances_rec()
        # iter.min_depth = max(self.view.max_hier_levels-1, 0)
        # iter.max_depth = max(self.view.max_hier_levels-1, 0)
        
        while not iter.at_end():
            inst = iter.current_inst_element().inst()
            hidden = lv.is_cell_hidden(inst.cell.cell_index(), lv.active_cellview_index)
            if not hidden and inst.is_pcell():
                pi = PCellInstanceConnectivityInfo.for_pcell(inst, iter.inst_trans(), ctx)
                result.pcell_infos.append(pi)
            iter.next()
        
        return result


@dataclass
class LayoutConnectivityInfo:
    cell_infos: List[CellConnectivityInfo] = field(default_factory=list)

    @classmethod
    def for_layout_view(cls, layout_view: pya.LayoutView) -> LayoutConnectivityInfo:
        result = cls()
        
        ctx = Context(layout_view=layout_view)
        lv = ctx.layout_view
        cv = lv.active_cellview()

        # ensure PCells were evaluated
        pya.Library.refresh_all()
        
        top_cell = cv.cell
        if cv.is_cell_hidden(top_cell):
            return lci
        
        ci = CellConnectivityInfo.for_cell_instance(top_cell, ctx)
        result.cell_infos.append(ci)
        
        return result
