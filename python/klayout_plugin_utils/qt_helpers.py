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
from typing import *
import traceback

import pya


def qt_major_version() -> int:
    qt_major = int(pya.Qt.QT_VERSION_STR.split('.')[0])
    return qt_major


def compat_QShortCut(key_sequence: pya.QKeySequence,
              widget: pya.QWidget,
              on_trigger: Callable) -> pya.QShortCut:
    if qt_major_version() >= 6:
        sc = pya.QShortcut(key_sequence, widget)
        sc.activated.connect(on_trigger)
        return sc
    elif qt_major_version() == 5:
        return pya.QShortcut(key_sequence, widget, on_trigger)
    else:
        raise NotImplementedError()


def compat_QTreeWidgetItem_setBackground(tvi: pya.QTreeWidgetItem,
                                         column: int,
                                         color: pya.QColor):
    if qt_major_version() >= 6:
        brush = pya.QBrush(color)
        tvi.setBackground(column, brush)
    elif qt_major_version() == 5:
        tvi.setBackgroundColor(column, color)
    else:
        raise NotImplementedError()
