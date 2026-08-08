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

import os
import bpy
import subprocess

from ..classes import qbake_bake
from ..classes import status

class qbake_operator_background(bpy.types.Operator):
    """Bake All nodes in Background"""
    bl_idname = "render.qbake_operator_background"
    bl_label = "Bake all Nodes in Background"

    _timer = None
    status = None
    process = None
    finished = False
    attemps = 0

    @classmethod
    def poll(cls, context):
        return True

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        self.get_status()

        if self.finished:
            self.done(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}
        

    def execute(self, context):
        self.init()

        wm = context.window_manager
        self._timer = wm.event_timer_add(1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}
    
    def done(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.status = None

    def init(self):
        self.report({'INFO'}, f"QBake: initialization")
        self.attemps = 0
        self.finished = False
        self.status = status.status()

        blend_file = bpy.data.filepath
        addon_dir = os.path.dirname(os.path.dirname(__file__))

        worker = os.path.join(
            addon_dir,
            "worker",
            "bake_worker.py"
        )

        self.process = subprocess.Popen([
            bpy.app.binary_path,
            "--background",
            blend_file,
            "--python",
            worker
        ])

    def get_status(self):
        if(self.attemps > 10):
            self.finished = True

        
        current_status = self.status.read()
        if(current_status is False):
            self.attemps += 1
            return

        self.attemps = 0

        if(current_status['status'] == 'INIT'):
            self.report({'INFO'}, f"QBake: worker initialization")
            return

        if(current_status['status'] == 'BAKING'):
            self.report({'INFO'}, f"QBake: baking {current_status['current']} / {current_status['total']}")
            return

        if(current_status['status'] == 'DONE'):
            self.report({'INFO'}, f"QBake: done")
            self.status.delete()
            self.finished = True
            return
        

def register():
    bpy.utils.register_class(qbake_operator_background)


def unregister():
    bpy.utils.unregister_class(qbake_operator_background)