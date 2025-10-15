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


def strip_all_suffixes(path: Union[str, Path], allowed_suffixes: List[str]) -> str:
    """
    Normal pathlib.Path.stem would return 'layout.gds' for 'layout.gds.gz',
    What we want in this case is to get 'layout'.
    
    Return filename with any known hierarchical layout suffix removed.
    """
    path = Path(path)
    descending_len_suffixes = sorted(list(allowed_suffixes), key=len, reverse=True)
    for suffix in descending_len_suffixes:
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)]
    return path.stem  # fallback: just strip last suffix

