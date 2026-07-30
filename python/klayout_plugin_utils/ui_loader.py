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
import inspect
from typing import *

import pya

#--------------------------------------------------------------------------------

def load_ui(ui_filename: str, parent=None, base_dir: Optional[str] = None) -> pya.QWidget:
    """Load a .ui file and return its root widget.

    ui_filename is resolved relative to base_dir if given, otherwise
    relative to the caller's own file location (so this works no matter
    which package load_ui itself lives in).
    """
    if base_dir is None:
        caller_file = inspect.stack()[1].filename
        base_dir = os.path.dirname(os.path.abspath(caller_file))

    ui_path = os.path.join(base_dir, ui_filename)
    ui_file = pya.QFile(ui_path)
    if not ui_file.exists():
        raise FileNotFoundError(f"UI file not found: {ui_path}")
    
    loader = pya.QUiLoader()
    try:
        ui_file.open(pya.QFile.ReadOnly)
        widget = loader.load(ui_file, parent)
        if widget is None:
            raise RuntimeError(f"QUiLoader failed to load {ui_path}: {loader.errorString()}")
    finally:
        ui_file.close()
    return widget

