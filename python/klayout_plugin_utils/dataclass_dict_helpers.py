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
from pathlib import Path
from typing import Dict, Union, get_origin, get_type_hints, get_args


#--------------------- dataclass serializiation ---------------------------
def dataclass_from_dict(cls, data: Dict):
    origin = get_origin(cls)
    args = get_args(cls)

    if origin is Union:  # handle Union types
        last_error = None
        for arg in args:
            try:
                return dataclass_from_dict(arg, data)
            except Exception as e:
                last_error = e
        raise TypeError(f"Cannot match Union type {cls} with data {data}") from last_error

    elif origin is list:  # handle lists
        item_type = args[0]
        return [dataclass_from_dict(item_type, v) for v in data]

    elif is_dataclass(cls):  # normal dataclass
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict to instantiate {cls}, got {type(data).__name__}")
        kwargs = {}
        hints = get_type_hints(cls)
        for f in fields(cls):
            if f.name not in data:
                raise TypeError(f"Missing field {f.name} for dataclass {cls}")
            field_type = hints[f.name]
            try:
                value = dataclass_from_dict(field_type, data[f.name])
            except Exception as e:
                raise TypeError(f"Field {f.name} in {cls} failed to parse") from e
            kwargs[f.name] = value
        
        # extra check: make sure data does not contain unexpected keys
        extra_keys = set(data) - set(f.name for f in fields(cls))
        if extra_keys:
            raise TypeError(f"Extra keys {extra_keys} for dataclass {cls}")
        
        return cls(**kwargs)
    elif cls is Path:
        return Path(data)
    else:  # primitive type
        return data
