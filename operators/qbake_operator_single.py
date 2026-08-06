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

class qbake_operator_single(bpy.types.Operator):
    """Bake this Node"""
    bl_idname = "render.qbake_operator_single"
    bl_label = "Bake"
    node_id: bpy.props.StringProperty(
        name="unique_id of node",
        description="internal use"
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(context.material.name_full)
        qbake =  qbake_bake.qbake_bake(operator=self, context=context, node_id=self.node_id)
        qbake.bake_all()
        return {'FINISHED'}



def register():
    bpy.utils.register_class(qbake_operator_single)


def unregister():
    bpy.utils.unregister_class(qbake_operator_single)