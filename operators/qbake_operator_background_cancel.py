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

from ..classes import qbake_bake
from ..operators import qbake_operator_background

class qbake_operator_background_cancel(bpy.types.Operator):
    """Cancel Bake"""
    bl_idname = "render.qbake_operator_background_cancel"
    bl_label = "Cancel Bake"

    _timer = None
    qbake = None
    state = ''

    @classmethod
    def poll(cls, context):
        if qbake_operator_background.qbake_operator_background.process is None:
            return False
        return True


    def execute(self, context):
        qbake_operator_background.qbake_operator_background.stop_worker()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(qbake_operator_background_cancel)


def unregister():
    bpy.utils.unregister_class(qbake_operator_background_cancel)