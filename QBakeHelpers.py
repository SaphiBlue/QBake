import bpy

def get_uv_layers(self, context):
    obj = bpy.context.object
    if obj and obj.type == 'MESH' and obj.data.uv_layers:
        return [(uv.name, uv.name, "") for uv in obj.data.uv_layers]
    else:
        return [("None", "None", "")]