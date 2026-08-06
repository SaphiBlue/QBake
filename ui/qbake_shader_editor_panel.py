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

class qbake_shader_editor_panel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "QBake"
    bl_label = "QBake"
    bl_idname = "QBAKE_PT_UI_Editor_Panel"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree' and cls.get_material(context) is not None

    @classmethod
    def get_material(cls, context):
        node_tree = context.space_data.edit_tree

        material = None

        for mat in bpy.data.materials:
            if mat.node_tree == node_tree:
                material = mat
                break

        return material

    def draw(self, context):
        material = self.get_material(context)
        if(material is None):
            return


        operator = self.layout.operator("render.qbake_operator_material", text="Bake Material")
        
        

def register():
    bpy.utils.register_class(qbake_shader_editor_panel)

def unregister():
    bpy.utils.unregister_class(qbake_shader_editor_panel)