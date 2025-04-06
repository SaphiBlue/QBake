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
        name = "Export images after Bake",
        description = "Save a Copy of the Baked images to a Path",
        default = False)
    removeAfterExport: bpy.props.BoolProperty(
        name = "Removes images after Bake",
        description = "Removes images from the Blend File after Bake",
        default = False)
    regenerateImages: bpy.props.BoolProperty(
        name = "Regenerate images before bake",
        description = "Clears images before bake and sets the resolution",
        default = False)    
    exportDir: bpy.props.StringProperty(
        name = "Export File Path",
        description = "Name of output directory",
        default = "//Baked/",
        subtype = 'DIR_PATH',)
    defaultImgName: bpy.props.StringProperty(
        name = "Default image name pattern",
        description = "Name Pattern of bake results\n{obj}: Name of the Object\n{mat}: Name of the material\n{img_name}: Given image name in 'Q Baker Container' node\n",
        default = "Baked_{obj}_{mat}_{img_name}",)
    

def register():
    bpy.utils.register_class(QBakeGlobalProps)
    bpy.types.Scene.qbake = bpy.props.PointerProperty(type = QBakeGlobalProps)

def unregister():
    bpy.utils.unregister_class(QBakeGlobalProps)
    del bpy.types.Scene.qbake