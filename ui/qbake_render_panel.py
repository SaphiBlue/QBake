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

class qbake_render_panel(bpy.types.Panel):
    """QBake Panel"""
    bl_label = "QBake"
    bl_idname = "QBAKE_PT_UI_Render_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        obj = bpy.context.active_object

        row = layout.row()
        if bpy.context.scene.render.engine == 'CYCLES':

            row.label(text="Active object is: " + obj.name)
            row = layout.row()
            row.prop(context.scene.qbake, "defaultImgName")
            row = layout.row()
            row.prop(context.scene.qbake, "imageSize")
            row = layout.row()
            row.prop(context.scene.qbake, "regenerateImages")            
            row = layout.row()
            row.prop(context.scene.qbake, "margin")
            row = layout.row()
            row.prop(context.scene.qbake, "samples")
            
            exportBox = layout.box()       
            exportBox.label(text="Export Settings")
            if(bpy.data.filepath == ""):
                exportBox.label(text="Blender File File is not saved, export might not work", icon='ERROR')
                
            exportBox.prop(context.scene.qbake, "export")
            exportBox.prop(context.scene.qbake, "exportDir")
            exportBox.prop(context.scene.qbake, "removeAfterExport")
            
            if bpy.data.is_dirty:
                row = layout.row()
                row.label(text="The Blender file has unsaved changes.", icon='ERROR')
            
            hasUnsavedImages = False
            for image in bpy.data.images:
                if image.is_dirty:
                    hasUnsavedImages = True
            if (hasUnsavedImages):
                row = layout.row()
                row.label(text="The Blender file has unsaved Images.", icon='ERROR')

            if context.scene.qbake.imageSize > 1024 or context.scene.qbake.samples > 1:
                box = layout.box()
                box.label(
                    text="Baking might take some time",
                    icon='INFO'
                )

            row = layout.row()
            if(not bpy.context.active_object or bpy.context.active_object.type != 'MESH'):
                row.label(text="Select an Object to Bake")
            else:
                if not bpy.context.active_object.hide_render:
                    row.operator("render.qbake_operator")
                    row.operator("render.qbake_operator_background")
                else:
                    row.label(text="Object is not active for rendering", icon='ERROR')

            if context.scene.qbake.progess_bake_is_running:
                row = layout.progress(
                    factor=context.scene.qbake.progess_bake_progress,
                    text=context.scene.qbake.progess_bake_msg
                )
                

        else:
            row.label(text="Only works with CYCLES")
        
        

def register():
    bpy.utils.register_class(qbake_render_panel)

def unregister():
    bpy.utils.unregister_class(qbake_render_panel)