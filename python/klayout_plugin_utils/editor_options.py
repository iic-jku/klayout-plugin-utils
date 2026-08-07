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

import math
from typing import *

import pya

from klayout_plugin_utils.debugging import debug, Debugging
from klayout_plugin_utils.event_loop import EventLoop
from klayout_plugin_utils.str_enum_compat import StrEnum


class AngleMode(StrEnum):
    ANY_ANGLE = 'any'      # any angle
    DIAGONAL = 'diagonal'  # horizontal / vertical and 45°
    MANHATTAN = 'ortho'    # only horizontal / vertical
    
    def constrain_angle(self, origin: pya.DPoint, destination: pya.DPoint) -> pya.DPoint:
        result: pya.DPoint
    
        dx = destination.x - origin.x
        dy = destination.y - origin.y
        
        if self == AngleMode.ANY_ANGLE:
            result = destination
                
        elif self == AngleMode.DIAGONAL:
            # Allowed directions: 0°, 90°, 180°, 270° and ±45°, ±135°
            candidates = [0, math.pi,
                          math.pi/2, -math.pi/2,
                          math.pi/4, -math.pi/4,
                          3*math.pi/4, -3*math.pi/4]

            angle = math.atan2(dy, dx)  # radians
            
            # Find closest allowed angle
            best = min(candidates, key=lambda a: abs((angle - a + math.pi) % (2*math.pi) - math.pi))
    
            # Project vector onto this direction
            ux = math.cos(best)
            uy = math.sin(best)
            dot = ux*dx + uy*dy
            result = pya.DPoint(origin.x + dot*ux, origin.y + dot*uy)
            
        elif self == AngleMode.MANHATTAN:
            # Snap to horizontal or vertical based on which component is larger
            if abs(dx) > abs(dy):
                result = pya.DPoint(origin.x + dx, origin.y)
            else:
                result = pya.DPoint(origin.x, origin.y + dy)
                
        else:
            raise NotImplementedError(f"unknown AngleMode {self}")
            
        # # Hotspot, don't log this
        # if Debugging.DEBUG:
        #     debug(f"Angle Constraint {self}: origin={origin} → destination={destination} = {result}")
            
        return result


class EditGridKind(StrEnum):
    NONE = 'none'
    GLOBAL = 'global'
    OTHER = 'other'


class EditorOptions:
    @classmethod
    def watched_config_keys(cls) -> Set[str]:
        return {
            'grid-micron',
            'edit-grid',
            'edit-snap-to-objects',
            'edit-snap-objects-to-grid',
            'edit-connect-angle-mode',
            'edit-move-angle-mode',
        }
    
    def __init__(self, view: pya.LayoutView):
        self.view = view

        for name in EditorOptions.watched_config_keys():
            self.plugin_configure(name, view.get_config(name))

    def plugin_configure(self, name: str, value: str):
        if name == 'edit-grid':
            if value == 'none':
                self._edit_grid_kind = EditGridKind.NONE
                self._edit_grid_value = None
            elif value in ('global', ''):  # NOTE: empty string if grid was never changed yet
                self._edit_grid_kind = EditGridKind.GLOBAL
                self._edit_grid_value = None  # we'll fetch it on demand in effective_edit_grid()
            else:
                try:
                    self._edit_grid_value = float(value)
                    self._edit_grid_kind = EditGridKind.OTHER
                except ValueError:
                    self._edit_grid_kind = EditGridKind.NONE
                    raise NotImplementedError(f"unknown value '{value}' for configuration key 'edit-grid'")
        elif name == 'edit-snap-to-objects':
            self._edit_snap_to_objects = value == 'true'
        elif name == 'edit-snap-objects-to-grid':
            self._edit_snap_objects_to_grid = value == 'true'
        elif name == 'edit-connect-angle-mode':
            self._edit_connect_angle_mode = AngleMode(value)
        elif name == 'edit-move-angle-mode':
            self._edit_move_angle_mode = AngleMode(value)
        # if Debugging.DEBUG:
        #    debug(f"Plugin reconfigured: EditorOptions are now {self.__dict__}")

    def save(self):
        v: str
        if self._edit_grid_kind == EditGridKind.NONE:
            v = 'none'
        elif self._edit_grid_kind == EditGridKind.GLOBAL:
            v = 'global'
        elif self._edit_grid_kind == EditGridKind.OTHER:
            v = str(self._edit_grid_value)
        self.view.set_config('edit-grid', v)
        
        self.view.set_config('edit-snap-to-objects', 'true' if self._edit_snap_to_objects else 'false')
        self.view.set_config('edit-snap-objects-to-grid', 'true' if self._edit_snap_objects_to_grid else 'false')
        self.view.set_config('edit-connect-angle-mode', self._edit_connect_angle_mode.value)
        self.view.set_config('edit-move-angle-mode', self._edit_move_angle_mode.value)
        
    @property
    def edit_grid_kind(self) -> EditGridKind:
        return self._edit_grid_kind

    @property
    def edit_grid_value(self) -> float:
        return self._edit_grid_value

    @property
    def edit_move_angle_mode(self) -> AngleMode:
        return self._edit_move_angle_mode

    @property
    def edit_connect_angle_mode(self) -> AngleMode:
        return self._edit_connect_angle_mode

    @property
    def edit_snap_to_objects(self) -> bool:
        return self._edit_snap_to_objects

    @property
    def edit_snap_objects_to_grid(self) -> bool:
        return self._edit_snap_objects_to_grid

    @property
    def global_grid(self) -> float:
        um = float(self.view.get_config('grid-micron'))
        return um

    def set_edit_grid_kind(self, kind: EditGridKind):
        self._edit_grid_kind = kind
        
    def set_edit_grid_value(self, value: float):
        self._edit_grid_value = value
        
    def set_edit_move_angle_mode(self, mode: AngleMode):
        self._edit_move_angle_mode = mode
        
    def set_edit_connect_angle_mode(self, mode: AngleMode):
        self._edit_connect_angle_mode = mode
        
    def set_edit_snap_to_objects(self, snap: bool):
        self._edit_snap_to_objects = snap
        
    def set_edit_snap_objects_to_grid(self, snap: bool):
        self._edit_snap_objects_to_grid = snap

    def effective_edit_grid(self) -> Optional[float]:
        if self._edit_grid_kind == EditGridKind.NONE:
            return None
        elif self._edit_grid_kind == EditGridKind.GLOBAL:
            return self.global_grid
        elif self._edit_grid_kind == EditGridKind.OTHER:
            return self._edit_grid_value
        else:
            raise NotImplementedError(f"unknown EditGridKind {self._edit_grid_kind}")
    
    @classmethod
    def show_editor_options(cls):
        # NOTE: if we directly call the Editor Options menu action
        #       the GUI immediately will switch back to the Librariew view
        #       so we enqueue it into the event loop
        EventLoop.defer(lambda: pya.MainWindow.instance().call_menu('cm_edit_options'))
    
    def snap_to_grid(self, point: pya.DPoint) -> pya.DPoint:
        grid_um = self.effective_edit_grid()
        if grid_um is None:
            return point
        else:
            return pya.DPoint(round(point.x / grid_um) * grid_um,
                              round(point.y / grid_um) * grid_um)
    
    def snap_to_grid_if_necessary(self, point: pya.DPoint) -> pya.DPoint:
        if self._edit_snap_objects_to_grid:
            return self.snap_to_grid(point=point)
        return point
    
    def constrain_angle(self, origin: pya.DPoint, destination: pya.DPoint) -> pya.DPoint:
        return self.edit_move_angle_mode.constrain_angle(origin=origin, destination=destination)
