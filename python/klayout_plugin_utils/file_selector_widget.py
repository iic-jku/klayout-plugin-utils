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
import sys
from typing import *

import pya

from klayout_plugin_utils.event_loop import EventLoop
from klayout_plugin_utils.file_system_helpers import FileSystemHelpers


class FileSelectorWidget(pya.QWidget):
    def __init__(self, 
                 parent: pya.QWidget,
                 editable: bool,
                 file_dialog_title: str = "Select File",
                 file_types: List[str] = ["All Files (*.*)"],
                 path_transformer: Optional[Callable[Path, Path]] = None):
        super().__init__(parent)
        
        self.editable = editable
        self.file_dialog_title = file_dialog_title
        self.file_type_filter = ';;'.join(file_types)
        self.path_transformer = path_transformer
        
        self.layout = pya.QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Line edit to show file path
        self.line_edit = pya.QLineEdit()
        self.line_edit.setReadOnly(not editable)
        self.line_edit.setSizePolicy(pya.QSizePolicy.Expanding, pya.QSizePolicy.Preferred)
        self.layout.addWidget(self.line_edit)
        
        # Action button (Browse or Clear)
        self.action_btn = pya.QPushButton("…")
        self.action_btn.setSizePolicy(pya.QSizePolicy.Fixed, pya.QSizePolicy.Preferred)
        
        self.layout.addWidget(self.action_btn)
        self.action_btn.clicked.connect(self.on_button_clicked)
        
        self.setSizePolicy(pya.QSizePolicy.Expanding, pya.QSizePolicy.Preferred)

        self.update_button()
    
        # NOTE: here widget users can register callback for effective path change
        self.on_path_changed: List[Callable[FileSelectorWidget]] = []

        self.line_edit.editingFinished.connect(self.emit_path_changed)
        self.line_edit.returnPressed.connect(self.emit_path_changed)
    
    @property
    def path(self) -> str:
        return self.line_edit.text.strip()
    
    @path.setter
    def path(self, new_path: str):
        effective_path = new_path
        if self.path_transformer is not None:
            effective_path = str(self.path_transformer(Path(new_path)))
        self.line_edit.setText(effective_path)
        self.update_button()
    
    def on_button_clicked(self):
        if self.line_edit.text:
            self.line_edit.setText('')
        else:
            old_path = self.path
            
            fname = None
            lru_path = FileSystemHelpers.least_recent_directory()
            
            fname = pya.QFileDialog.getOpenFileName(self, self.file_dialog_title, lru_path, self.file_type_filter)
            if fname:
                self.path = fname
            if old_path == self.path:
                return
                
        self.emit_path_changed()
    
    def emit_path_changed(self):
        self.update_button()
        
        def notify_listeners():
            for c in self.on_path_changed:
                c(self)

        if self.on_path_changed:
            EventLoop.defer(notify_listeners)
    
    def update_button(self):
        if self.line_edit.text:
            self.action_btn.text = ''
            self.action_btn.icon = pya.QIcon(':clear_edit_16px')
        else:
            self.action_btn.setText("…")
            self.action_btn.icon = pya.QIcon()

    def validate(self):
        if self.validator is None:
            return
        self.validator(self)

    def set_valid(self, valid: bool):
        color = 'white' if valid else '#FFCCCC'
        self.line_edit.setStyleSheet(f"background-color: {color};")


if __name__ == "__main__":
    mw = pya.MainWindow.instance()
    window = pya.QWidget(mw)
    window.setWindowTitle('File Selector Example')
    layout = pya.QVBoxLayout(window)
    widget = FileSelectorWidget(window)
    layout.addWidget(widget)
    window.resize(400, 50)
    window.show()
    