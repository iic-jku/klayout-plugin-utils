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
import pya


# NOTE: always add an additional guard `if debugging.DEBUG: debug(f"...")` at each call site,
#       otherwise the eager f-string eager evaluation can be costly,
#       even when debugging is turned off, especially in hot spots 
def debug(*args, **kwargs):
    if Debugging.DEBUG:
        print(*args, **kwargs)


class Debugging:
    CONFIG_KEY__ENABLE_DEBUG_LOGGING = 'developer.enable_debug_logging'
    DEBUG = False
    ENV_VAR__KLAYOUT_DEVELOPER_MODE = 'KLAYOUT_DEVELOPER_MODE'

    # NOTE: we no longer use global variable DEBUG,
    #       because users could do "from debugging import DEBUG",
    #       and this will be a copy of the variable at import time,
    #       therefore changes triggered by toggling menu item Macros → Debug Logging won't propagate
    #
        
    @staticmethod
    def developer_mode() -> bool:
        kdm = os.getenv(Debugging.ENV_VAR__KLAYOUT_DEVELOPER_MODE, None)
        if kdm is None or kdm == '' or kdm == '0' or kdm.lower() == 'false':
            return False
        return True
    
    @staticmethod
    def debug_logging_enabled() -> bool:
        mw = pya.MainWindow.instance()
        enable_debug_logging = mw.get_config(Debugging.CONFIG_KEY__ENABLE_DEBUG_LOGGING)
        return enable_debug_logging == 'true'
    
    @staticmethod
    def install_developer_menu():
        mw = pya.MainWindow.instance()
            
        def toggle_debug_logging(action: pya.Action):
            Debugging.DEBUG = action.checked
            print(f"toggle debug logging: {Debugging.DEBUG}")
            mw.set_config(Debugging.CONFIG_KEY__ENABLE_DEBUG_LOGGING, 'true' if Debugging.DEBUG else 'false')
        
        menu = mw.menu()
        action = pya.Action()
        action.title = "Debug Logging"
        action.checkable = True
        action.checked = Debugging.debug_logging_enabled()
        action.on_triggered += lambda: toggle_debug_logging(action)
        menu.insert_item("macros_menu.end", "toggle_debug_logging", action)
        action.is_checked = Debugging.debug_logging_enabled()
        
    @staticmethod
    def init_debugging():
        if not Debugging.developer_mode():
            Debugging.DEBUG = False
            return
    
        Debugging.DEBUG = Debugging.debug_logging_enabled()
        print(f"Debug logging turned {'on' if Debugging.DEBUG else 'off'}. "
              f"Export the environmental variable {Debugging.ENV_VAR__KLAYOUT_DEVELOPER_MODE}=1 "
              f"to get access to menu item Macros→Debug Logging)")
        Debugging.install_developer_menu()
        