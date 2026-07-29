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

import os
from typing import *

import pya

#--------------------------------------------------------------------------------

path_containing_this_script = os.path.realpath(os.path.join(os.path.dirname(__file__)))


def load_ui(ui_filename: str, parent=None) -> pya.QWidget:
    """Load a .ui file and return its root widget."""
    loader = pya.QUiLoader()
    ui_path = os.path.join(path_containing_this_script, ui_filename)
    ui_file = pya.QFile(ui_path)
    try:
        ui_file.open(pya.QFile.ReadOnly)
        widget = loader.load(ui_file, parent)
    finally:
        ui_file.close()
    return widget

