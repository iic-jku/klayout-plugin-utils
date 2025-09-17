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

from dataclasses import dataclass, asdict, fields, is_dataclass
from typing import Dict, get_type_hints


#--------------------- dataclass serializiation ---------------------------
def dataclass_from_dict(cls, data: Dict):
    if not is_dataclass(cls):
        return data
    kwargs = {}
    hints = get_type_hints(cls)
    for f in fields(cls):
        if f.name in data:
            field_type = hints[f.name]
            value = data[f.name]
            # handle lists of dataclasses
            origin = getattr(field_type, '__origin__', None)
            if origin is list:
                item_type = field_type.__args__[0]
                value = [dataclass_from_dict(item_type, v) for v in value]
            else:
                value = dataclass_from_dict(field_type, value)
            kwargs[f.name] = value
    return cls(**kwargs)
