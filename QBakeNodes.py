import bpy
import uuid
from nodeitems_utils import NodeCategory, NodeItem
from bpy.props import EnumProperty

class QBakeShaderNode(bpy.types.Node):
    '''QBake: Bake Node'''
    bl_idname = "QBakeShaderNodeType"
    bl_label = "Q Baker Container"
    # Icon identifier
    bl_icon = 'TEXTURE'

    # Define an image property
    image: bpy.props.PointerProperty(
        name="Image",
        type=bpy.types.Image,
        description="Image used by this shader"
    )

    unique_id: bpy.props.StringProperty(
        name="unique_id",
        description="internal use"
    )

    image_name: bpy.props.StringProperty(
        name="Image name",
        description="Image name if no Reference is given"
    )
    
    image_colorspace: bpy.props.EnumProperty(
        name="Image Colorspace",
        description="Image Color Space",
        items=[
            ('sRGB', "sRGB", "Non-Color"),
            ('Non-Color', "Non-Color", "sRGB"),
        ],
        default='sRGB'
    )

    alpha_mode: bpy.props.EnumProperty(
        name="Alpha Mode",
        description="Representation of alpha in the image file, to convert to and from when saving and loading the image",
        items=[
            ('STRAIGHT', "Straight", "Store RGB and alpha channels separately with alpha acting as a mask, also known as unassociated alpha. Commonly used by image editing applications and file formats like PNG."),
            ('PREMUL', "Premul", "Store RGB channels with alpha multiplied in, also known as associated alpha. The natural format for renders and used by file formats like OpenEXR."),
            ('CHANNEL_PACKED', "Channel Packed", "Different images are packed in the RGB and alpha channels, and they should not affect each other. Channel packing is commonly used by game engines to save memory."),
        ],
        default='STRAIGHT'
    )

    alpha_non_color: bpy.props.BoolProperty(
        name="Non-Color Alpha",
        description="Bake Alpha as Non-Color",
        default = True
    )

    def update_inputs(self, context):
        
        self.inputs.clear()
        
        if(self.bake_mode == 'COLOR'):
            self.inputs.new('NodeSocketColor', "Color")
            self.inputs.new('NodeSocketFloat', "Alpha")
        elif(self.bake_mode == 'PACKED'):
            self.inputs.new('NodeSocketFloat', "Red")
            self.inputs.new('NodeSocketFloat', "Green")
            self.inputs.new('NodeSocketFloat', "Blue")
            self.inputs.new('NodeSocketFloat', "Alpha")
        elif(self.bake_mode == 'NORMAL'):
            self.inputs.new('NodeSocketShader', "Shader")

    bake_mode: bpy.props.EnumProperty(
        name="Bake Mode",
        description="Bake mode Preset",
        items=[
            ('COLOR', "Color", "Use for baking Colors and Properties"),
            ('PACKED', "Packed", "Use for Baking Properties"),
            ('NORMAL', "Normal", "Use for Baking Normalmaps"),
        ],
        default='COLOR',
        update=update_inputs
    )


    uv_map_index: bpy.props.IntProperty(
        name="UV Map Index",
        description="UV Map Index"
    )

    def get_uv_layers(self, context):
        obj = context.object
        if obj and obj.type == 'MESH' and obj.data.uv_layers:
            return [(uv.name, uv.name, "") for uv in obj.data.uv_layers]
        else:
            return [("None", "None", "")]
    
    def update_uv_index(self, context):
        obj = context.object
        if obj and obj.type == 'MESH' and obj.data.uv_layers:
            self.uv_map_index = 0
            _uv_map_index = 0
            for uv in obj.data.uv_layers:
                if(uv.name == self.uv_map):
                    self.uv_map_index = _uv_map_index 
                _uv_map_index += 1

    uv_map: bpy.props.EnumProperty(
        name="UV Map",
        description="Choose UV map",
        items=get_uv_layers,
        update=update_uv_index
    )


    def get_uv_map_index(self):
        return self.uv_map_index

    def init(self, context):
        self.update_inputs(context)
        self.unique_id = str(uuid.uuid4())
        
    def copy(self, node):
        self.unique_id = str(uuid.uuid4())
        

    def draw_buttons(self, context, layout):
        #if(self.unique_id == ""):
            #self.unique_id = str(uuid.uuid4())

        operator = layout.operator("render.qbake_operator_single", text="Bake Node")
        operator.node_id = self.unique_id

        layout.template_ID(self, "image", open="image.open", new="image.new")

        layout.prop(self, "bake_mode", text="Bake Mode")
        layout.prop(self, "uv_map", text="UV Map")
        if(self.bake_mode == 'COLOR'):
            layout.prop(self, "alpha_non_color", text="Non-Color Alpha")
            
        if(not self.image):
            imageBox = layout.box()
            imageBox.label(text="Initial Image Settings")
            imageBox.prop(self, "image_name", text="Image name")
            
            if(self.bake_mode == 'COLOR'):
                imageBox.prop(self, "image_colorspace", text="Image Colorspace")
                imageBox.prop(self, "alpha_mode", text="Alpha Mode")
                
                
                

        if ('Color' in self.inputs and not self.inputs["Color"].is_linked):
            layout.label(text="Warning: Color is not linked! Bake will not work", icon='ERROR')

    def draw_label(self):
        return self.bl_label

def addQBakeNodeMenu(self, context):
    if getattr(context.space_data, "shader_type", None) == 'OBJECT':
        self.layout.separator()
        op_props = self.layout.operator("node.add_node", text=QBakeShaderNode.bl_label)
        op_props.type = QBakeShaderNode.bl_idname
        op_props.use_transform = True

def register():
    bpy.types.NODE_MT_category_shader_output.append(addQBakeNodeMenu)
    bpy.utils.register_class(QBakeShaderNode)

def unregister():
    bpy.types.NODE_MT_category_shader_output.remove(addQBakeNodeMenu)
    bpy.utils.unregister_class(QBakeShaderNode)