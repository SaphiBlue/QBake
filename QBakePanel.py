import bpy

class QBakePanel(bpy.types.Panel):
    """QBake Panel"""
    bl_label = "QBake"
    bl_idname = "QBAKE_PT_UI_Panel"
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
            

            row = layout.row()
            if(not bpy.context.active_object or bpy.context.active_object.type != 'MESH'):
                row.label(text="Select an Object to Bake")
            else:
                if not bpy.context.active_object.hide_render:
                    row.operator("render.qbake_operator")    
                else:
                    row.label(text="Object is not active for rendering", icon='ERROR')
                

        else:
            row.label(text="Only works with CYCLES")

def register():
    bpy.utils.register_class(QBakePanel)

def unregister():
    bpy.utils.unregister_class(QBakePanel)