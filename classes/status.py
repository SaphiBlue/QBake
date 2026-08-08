##
# Blender Addon Qbake (Quantum Bake)
#Copyright (C) 2026 Saphi
##
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
from pathlib import Path
import os
import json


class status:

    def __init__(self):
        blend_file = bpy.data.filepath
        directory = os.path.dirname(blend_file)
        current_file = bpy.path.basename(bpy.context.blend_data.filepath).replace('.', '-')

        self.file = Path(os.path.join(directory, f"qbake_{current_file}_out.json"))

    def read(self) -> dict|bool:

        if not self.file.exists():
            return False

        try:
            data = json.loads(
                self.file.read_text(encoding="utf-8")
            )

            return data

        except (OSError, json.JSONDecodeError):
            pass      

        return False

    def write(self, data: dict) -> None:
        self.file.write_text(
            json.dumps(data),
            encoding="utf-8"
        )

    def delete(self) -> None:
        try:
            self.file.unlink()
        except:
            pass