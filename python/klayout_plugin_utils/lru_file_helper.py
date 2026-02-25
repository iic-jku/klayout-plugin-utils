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

import json
from pathlib import Path
from typing import *

import pya


"""
Reusable LRU (Least-Recently-Used) file list helper.

Usage example
-------------
    lru = LRUFileHelper(config_key="vector_file_export/lru_runsets", max_entries=10)

    # After the user successfully loads/saves a runset:
    lru.push(path)

    # Retrieve ordered list (most-recent first):
    paths = lru.entries()          # -> list[Path]

    # Clear the list:
    lru.clear()
"""


class LRUFileHelper:
    """Manages a most-recently-used list of file paths stored in KLayout's
    persistent application configuration.

    Parameters
    ----------
    config_key:
        The dot-separated key used to persist the list inside KLayout's
        ``pya.Application.instance().get_config`` / ``set_config`` store.
        Use a plugin-specific prefix to avoid collisions, e.g.
        ``"my_plugin/lru_runsets"``.
    max_entries:
        Maximum number of paths to keep (oldest entries are dropped when the
        list grows beyond this limit).
    """

    def __init__(self, config_key: str, max_entries: int = 10):
        self._key = config_key
        self._max = max_entries

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def entries(self) -> List[Path]:
        """Return the LRU list as ``Path`` objects, most-recent first.

        Paths that no longer exist on disk are silently removed.
        """
        raw = self._load_raw()
        existing = [Path(p) for p in raw if Path(p).exists()]
        if len(existing) != len(raw):
            # Prune stale entries from storage
            self._save_raw([str(p) for p in existing])
        return existing

    def push(self, path: Path | str):
        """Record *path* as the most-recently used entry.

        If the path is already in the list it is moved to the front.
        The list is capped at ``max_entries``.
        """
        path = Path(path).resolve()
        raw = self._load_raw()
        path_str = str(path)
        # Remove duplicates, prepend
        raw = [p for p in raw if p != path_str]
        raw.insert(0, path_str)
        raw = raw[: self._max]
        self._save_raw(raw)

    def clear(self):
        """Wipe the entire LRU list."""
        self._save_raw([])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_raw(self) -> List[str]:
        try:
            app = pya.Application.instance()
            serialised = app.get_config(self._key)
            if serialised:
                data = json.loads(serialised)
                if isinstance(data, list):
                    return [str(x) for x in data]
        except Exception:
            pass
        return []

    def _save_raw(self, entries: List[str]):
        try:
            value = json.dumps(entries)
        
            app = pya.Application.instance()
            app.set_config(self._key, value)
        except Exception:
            pass

