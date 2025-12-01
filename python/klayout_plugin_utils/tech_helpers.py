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

import pya

def drc_tech_grid_um() -> float:
    """
    Return tech grid of current cell view's layout's technology.
    Used for DRC (offgrid errors)
    """
    cv = pya.CellView.active()
    default_grid = cv.layout().technology().default_grid()
    # FIXME: there should be a KLayout API method for getting the effective DRC default grid
    #        for now we just use the default grid list (the entry with !)
    if default_grid <= 0.00001:  # some technologies have no default grid, e.g. GF180mcuD
        default_grid = 0.005  # fallback to 5nm
    return default_grid
