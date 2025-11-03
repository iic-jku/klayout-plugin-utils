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

from pathlib import Path
from typing import *

import pya


class FileSystemHelpers:
    CONFIG_KEY__LEAST_RECENT_DIRECTORY = 'KLayoutLibraryManager__lru_directory'
    
    @classmethod
    def least_recent_directory(cls) -> str:
        mw = pya.MainWindow.instance()
        lru_dir = mw.get_config(cls.CONFIG_KEY__LEAST_RECENT_DIRECTORY)
        if lru_dir is None:
            return ''
        lru_path = Path(lru_dir)
        if not lru_path.exists():
            return ''
        return lru_dir
        
    @classmethod
    def set_least_recent_directory(cls, path: str | Path):
        path = Path(path)
        mw = pya.MainWindow.instance()
        mw.set_config(cls.CONFIG_KEY__LEAST_RECENT_DIRECTORY, path)
