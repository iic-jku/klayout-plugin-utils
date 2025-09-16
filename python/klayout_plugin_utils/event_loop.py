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

import pya
import traceback
from typing import *

class EventLoop:
    @classmethod
    def defer(cls, callable: Callable):
        # NOTE: if we directly call the Editor Options menu action
        #       the GUI immediately will switch back to the Librariew view
        #       so we enqueue it into the event loop
    
        mw = pya.Application.instance().main_window()
    
        def on_timeout():
            try:
                callable()
            except Exception as e:
                print("EventLoop.defer():on_timeout() caught an exception", e)
                traceback.print_exc()
        
            if getattr(cls, "_defer_timer", None):
                try:
                    cls._defer_timer._destroy()
                except RuntimeError:
                    pass  # already deleted by Qt
                cls._defer_timer = None
        
        cls._defer_timer = pya.QTimer(mw)
        cls._defer_timer.setSingleShot(True)
        cls._defer_timer.timeout = on_timeout
        cls._defer_timer.start(0)
