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

import os
from pathlib import Path
from typing import *
import unittest


def stem_without_suffixes(path: Union[str, Path], allowed_suffixes: List[str]) -> str:
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


# deprecated
strip_all_suffixes = stem_without_suffixes


def expand_path(path: Union[str, Path]) -> Path:
    path = Path(path)
    return Path(os.path.expandvars(str(path.expanduser())))


def abbreviate_path(path: Union[str, Path],
                    env_vars: Optional[List[str]],
                    base_folder: Optional[Union[str, Path]]) -> Path:
    """
    Return a human-readable, environment-aware abbreviation of `path`.
    """
    path = Path(path).expanduser().resolve()
    
    candidates: Dict[str, int] = {}
    
    if base_folder:
        try:
            base = Path(base_folder).expanduser().resolve()
            rel = path.relative_to(base)
            candidates[str(rel)] = len(rel.parts)
        except ValueError:
            pass
    
    env_vars = env_vars or []
    for var in env_vars:
        val = os.getenv(var)
        if not val:
            continue
        val_path = Path(val).expanduser().resolve()
        try:
            rel = path.relative_to(val_path)
            abbrev = f"${var}/{rel}" if str(rel) != "." else f"${var}"
            candidates[abbrev] = len(Path(abbrev).parts)
        except ValueError:
            pass  # not relative to this variable
    
    # full path as a fallback
    candidates[str(path)] = len(path.parts)

    shortest = min(candidates, key=lambda k: candidates[k])
    return shortest


def normalize_path(path: Path) -> Path:
    """
    Collapse '.' and '..' without following symlinks.
    """
    parts = []
    for part in path.parts:
        if part == ".":
            continue
        elif part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append("..")
        else:
            parts.append(part)
    return Path(*parts)


def pathlib_relpath(target: Path, base: Path) -> Path:
    """
    Pure pathlib replacement for os.path.relpath.
    Returns minimal relative path from base to target.
    Works cross-platform (POSIX + Windows).
    """
    
    # On Windows, paths on different drives are not relative
    if target.drive != base.drive:
        # Cannot compute relative path between drives
        return target

    target_parts = target.parts
    base_parts = base.parts

    # Find common ancestor
    i = 0
    while i < min(len(target_parts), len(base_parts)) and target_parts[i] == base_parts[i]:
        i += 1

    # Steps up from base to common ancestor
    ups = len(base_parts) - i
    rel_parts = [".."] * ups + list(target_parts[i:])

    return Path(*rel_parts) if rel_parts else Path(".")


def rebase_relative_path(relative_path: str | Path,
                         old_base_folder: str | Path,
                         new_base_folder: str | Path) -> Path:
    """
    Rebase a path relative to old_base_folder so that it works under new_base_folder.
    Fully pathlib-based, cross-platform.
    """
    relative_path = Path(relative_path)
    old_base_folder = Path(old_base_folder)
    new_base_folder = Path(new_base_folder)
    
    target = relative_path if relative_path.is_absolute() \
             else (old_base_folder / relative_path)
    target = normalize_path(target)
    new_base_folder = normalize_path(new_base_folder)
    new_relative_path = pathlib_relpath(target, new_base_folder)
    return new_relative_path


#--------------------------------------------------------------------------------

class PathHelperTests(unittest.TestCase):
    def test_strip_all_suffixes(self):
        allowed_suffixes = ('.gds', '.gds.gz', '.klay.gds', '.klay.gds.gz')
        self.assertEqual('layout', stem_without_suffixes('layout.gds', allowed_suffixes))
        self.assertEqual('layout', stem_without_suffixes('layout.gds.gz', allowed_suffixes))
        self.assertEqual('layout', stem_without_suffixes('layout.klay.gds', allowed_suffixes))
        self.assertEqual('layout', stem_without_suffixes('layout.klay.gds.gz', allowed_suffixes))
        self.assertEqual('layout', stem_without_suffixes('/tmp/layout.klay.gds.gz', allowed_suffixes))
        
    def test_expand_path(self):
        self.assertEqual(f"{os.environ['HOME']}/layout.gds", str(expand_path('$HOME/layout.gds')))
        self.assertEqual(f"{os.environ['HOME']}/layout.gds", str(expand_path('~/layout.gds')))

    def test_abbreviate_path__env_var(self):
        self.assertEqual('$HOME/layout.gds', str(abbreviate_path(
            path=f"{os.environ['HOME']}/layout.gds",
            env_vars=['HOME'],
            base_folder=None
        )))

    def test_abbreviate_path__base_folder(self):
        self.assertEqual('layout.gds', str(abbreviate_path(
            path='/foss/designs/layout.gds',
            env_vars=[],
            base_folder='/foss/designs'
        )))

    def test_abbreviate_path__combined(self):
        self.assertEqual('layout.gds', str(abbreviate_path(
            path=f"{os.environ['HOME']}/base_folder/layout.gds",
            env_vars=['HOME'],
            base_folder=f"{os.environ['HOME']}/base_folder/"
        )))

#--------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
