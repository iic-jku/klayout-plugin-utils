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

from typing import Any, Callable, Generic, Optional, Type, TypeVar

T = TypeVar("T")
C = TypeVar("C", bound=type)

class cached_classproperty(Generic[T]):
    def __init__(self, func: Callable[[Type[Any]], T]):
        self.func = func
        self._cache_name: str = f"_{func.__name__}_cache"

    def __set_name__(self, owner: Type[Any], name: str):
        # Ensures the cache name matches the actual attribute name if needed
        self._cache_name = f"_{name}_cache"

    def __get__(self, instance: Optional[Any], owner: Type[Any]) -> T:
        if hasattr(owner, self._cache_name):
            return getattr(owner, self._cache_name)
        value = self.func(owner)
        setattr(owner, self._cache_name, value)
        return value
