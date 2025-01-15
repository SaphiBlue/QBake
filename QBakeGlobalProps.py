import bpy

class QBakeGlobalProps(bpy.types.PropertyGroup):
    imageSize: bpy.props.IntProperty(
        name = "Image Size",
        description = "Default Image size, if no image reference is given",
        min= 1,
        default = 1024)
    margin: bpy.props.IntProperty(
        name = "Baked Margin",
        description = "Default Margin",
        min=0,
        default = 64)
    samples: bpy.props.IntProperty(
        name = "Samples",
        description = "Samples during Bake",
        min= 1,
        default = 1)
    export: bpy.props.BoolProperty(
        name = "Export Images after Bake",
        description = "Save a Copy of the Baked images to a Path",
        default = False)
    exportDir: bpy.props.StringProperty(
        name = "Export File Path",
        description = "Name of output directory",
        default = "//Baked/",
        subtype = 'DIR_PATH',)
    

def register():
    bpy.utils.register_class(QBakeGlobalProps)
    bpy.types.Scene.qbake = bpy.props.PointerProperty(type = QBakeGlobalProps)

def unregister():
    bpy.utils.unregister_class(QBakeGlobalProps)
    del bpy.types.Scene.qbake