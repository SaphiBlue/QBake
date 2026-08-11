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
    node_id: bpy.props.StringProperty(
        name="unique_id of node",
        description="internal use"
    )
    material_name: bpy.props.StringProperty(
        name="material name",
        description="internal use"
    )

    _timer = None
    status = None
    
    finished = False
    attemps = 0

    process = None
    bake_progress = 0
    bake_msg = ""
    bake_info = ""

    @classmethod
    def poll(cls, context):
        if(bpy.data.filepath == ""):
            return False
        if(qbake_operator_background.process is not None):
            return False
        if(qbake_operator_background.status is not None):
            return False        
        
        return True

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        self.get_status(context)

        if self.finished:
            self.done(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}
        

    def execute(self, context):
        self.init(context)

        wm = context.window_manager
        self._timer = wm.event_timer_add(1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}
    
    def done(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        qbake_operator_background.stop_worker()
        qbake_operator_background.status = None
        self.finished = True
        self.redraw(context)

    def init(self, context):
        self.attemps = 0
        self.finished = False

        self.report({'INFO'}, f"QBake: initialization")

        material_name = self.material_name
        node_id = self.node_id

        qbake_operator_background.bake_progress = 0
        qbake_operator_background.bake_msg = "initialization"

        qbake_operator_background.status = status.status()
        qbake_operator_background.status.delete()

        qbake_operator_background.bake_info = f"Bake nodes of {bpy.context.view_layer.objects.active.name}"
        if material_name is not "":
            qbake_operator_background.bake_info += f" material: {material_name}"

        blend_file = bpy.data.filepath
        addon_dir = os.path.dirname(os.path.dirname(__file__))

        worker = os.path.join(
            addon_dir,
            "worker",
            "bake_worker.py"
        )

        qbake_operator_background.status.write({
            'status': 'INIT'
        })

        qbake_operator_background.process = subprocess.Popen([
            bpy.app.binary_path,
            "--background",
            blend_file,
            "--python",
            worker,
            "--",
            "--material",
            material_name,
        ])
        
    def get_status(self, context):
        if(self.attemps > 20):
            self.finished = True
            

        
        current_status = qbake_operator_background.status.read()
        if(current_status is False):
            print('Read Error')
            self.attemps += 1
            return

        self.attemps = 0

        if(qbake_operator_background.process is None):
            self.report({'INFO'}, f"QBake: Canceld")
            qbake_operator_background.bake_msg = ""
            qbake_operator_background.bake_progress = 1
            qbake_operator_background.status.delete()
            self.finished = True
            self.redraw(context)
            return

        if(current_status['status'] == 'INIT'):
            self.report({'INFO'}, f"QBake: Worker initialization")
            qbake_operator_background.bake_progress = 0
            qbake_operator_background.bake_msg = "Worker initialization"
            self.redraw(context)
            return

        if(current_status['status'] == 'BAKING'):
            self.report({'INFO'}, f"QBake: Baking {current_status['current']} / {current_status['total']}")
            qbake_operator_background.bake_msg = f"Baking {current_status['current']} / {current_status['total']}"
            qbake_operator_background.bake_progress = (current_status['current'] / current_status['total'])
            self.redraw(context)
            return

        if(current_status['status'] == 'EXPORT'):
            self.report({'INFO'}, f"QBake: Exporting")
            qbake_operator_background.bake_msg = f"Exporting {current_status['current']} / {current_status['total']}"
            qbake_operator_background.bake_progress = (current_status['current'] / current_status['total'])
            self.redraw(context)
            return

        if(current_status['status'] == 'DONE'):
            self.report({'INFO'}, f"QBake: done")
            qbake_operator_background.process = None
            qbake_operator_background.bake_msg = ""
            qbake_operator_background.bake_progress = 1
            qbake_operator_background.status.delete()
            self.finished = True
            self.redraw(context)
            return

    def redraw(self, context):
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                if area.spaces.active.context == 'RENDER':
                    area.tag_redraw()

            if area.type == 'NODE_EDITOR':
                if area.ui_type == 'ShaderNodeTree':
                    area.tag_redraw()

    @classmethod
    def stop_worker(cls):
        if qbake_operator_background.process is None:
            return

        if qbake_operator_background.process.poll() is None:
            print("QBake: Stopping worker")

            qbake_operator_background.process.terminate()

            try:
                qbake_operator_background.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("QBake: Worker did not terminate, killing...")
                qbake_operator_background.process.kill()

        qbake_operator_background.process = None

        try:
            qbake_operator_background.status.delete()
        except:
            pass
        

def register():
    bpy.utils.register_class(qbake_operator_background)


def unregister():
    qbake_operator_background.stop_worker()
    bpy.utils.unregister_class(qbake_operator_background)