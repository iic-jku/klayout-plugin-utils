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

import sys


if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum
    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)


class DualStrEnum(StrEnum):
    """StrEnum with separate UI labels and CLI/serialization keys."""
    
    def __new__(cls, cli_value: str, ui_label: str):
        obj = str.__new__(cls, cli_value)
        obj._value_ = cli_value
        obj.ui_label = ui_label
        return obj
    
    @classmethod
    def from_ui_label(cls, label: str) -> "DualStrEnum":
        for member in cls:
            if member.ui_label == label:
                return member
        raise ValueError(f"No member with UI label {label!r}")
