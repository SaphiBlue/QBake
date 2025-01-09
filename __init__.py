bl_info = {
    "name": "Quantum Bake",
    "description": "Bakes Textures in bulk",
    "author": "Saphi",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "category": "Render",
}

import bpy
import numpy
import uuid
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories


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

#https://blender.stackexchange.com/questions/274712/how-to-channel-pack-texture-in-python

def pack_image_channels(pack_order):
    dst_array = None
    has_alpha = False
    colorspace = 'Non-Color'
    alphamode = 'STRAIGHT'
    # Build the packed pixel array
    for pack_item in pack_order:
        image = pack_item[0]
        alphamode = image.alpha_mode
        colorspace = image.colorspace_settings.name
        
        # Initialize arrays on the first iteration
        if dst_array is None:
            w, h = image.size
            src_array = numpy.empty(w * h * 4, dtype=numpy.float32)
            dst_array = numpy.ones(w * h * 4, dtype=numpy.float32)

        assert image.size[:] == (w, h), "Images must be same size"

        # Fetch pixels from the source image and copy channels
        image.pixels.foreach_get(src_array)
        for src_chan, dst_chan in pack_item[1:]:
            if dst_chan == 3:
                has_alpha = True
            dst_array[dst_chan::4] = src_array[src_chan::4]

    # Create image from the packed pixels
    dst_image = bpy.data.images.new("Packed Image", w, h, alpha=has_alpha)
    
    dst_image.colorspace_settings.name = colorspace;
    dst_image.alpha_mode = alphamode;
    dst_image.pixels.foreach_set(dst_array)

    # Since the image doesn't exist on disk, we need to pack it into the .blend
    # or it won't exist after the .blend is closed
    dst_image.pack()

    return dst_image


# Pack four monochrome images into RGBA
def channel_pack(r: bpy.types.Image, g: bpy.types.Image, b: bpy.types.Image, a: bpy.types.Image):
    pack_order = [
        (r, (0, 0)),
        (g, (0, 1)),
        (b, (0, 2)),
        (a, (0, 3)),
    ]
    return pack_image_channels(pack_order)

# Pack the RGB of one an image into the RGB of the output, with a
# monochrome image packed into the alpha.
def alpha_pack(rgb: bpy.types.Image, a: bpy.types.Image):
    pack_order = [
        (rgb, (0, 0), (1, 1), (2, 2)),
        (a, (0, 3)),
    ]
    return pack_image_channels(pack_order)


class QBakePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
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
            row.prop(context.scene.qbake, "margin")
            row = layout.row()
            row.prop(context.scene.qbake, "samples")
            row = layout.row()
            if(not bpy.context.active_object or bpy.context.active_object.type != 'MESH'):
                row.label(text="Select an Object to Bake")
            else:
                row.operator("render.qbake_operator")
                
            
        else:
            row.label(text="Only works with CYCLES")

def QBakePrepareMaterials(obj, dummyImage):
    for material in obj.data.materials:
        out = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        out.label = "QBakeOut"
        img = material.node_tree.nodes.new('ShaderNodeTexImage')
        img.label = "QBakeDummy"
        img.image = dummyImage
        img.select = True
        material.node_tree.nodes.active = out
        material.node_tree.nodes.active = img

def QBakeCleanupMaterials(obj, dummyImage):
    for material in obj.data.materials:
        for node in material.node_tree.nodes:
            if(node.label == 'QBakeOut'):
                material.node_tree.nodes.remove(node)
                continue;        
            if(node.label == 'QBakeDummy'):
                material.node_tree.nodes.remove(node)
                continue

def QBakeBakeNodeLogic(material, qBakeNode, outNode, socketName):
    fromNodeSocket = qBakeNode.inputs[socketName].links[0].from_socket
    fromNode = qBakeNode.inputs[socketName].links[0].from_node
    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

    target = material.node_tree.nodes.new('ShaderNodeTexImage')
    target.image = qBakeNode.image
    material.node_tree.nodes.active = target

    return target

def QBakeBakeNodeLogicAfterBake(material, target):
    target.image.pack()
    material.node_tree.nodes.remove(target)    


def QBakeBakeTargetPrepare(context, obj, material, qBakeNode):
    bake_mode = qBakeNode.bake_mode
    defaultSize = context.scene.qbake.imageSize

    if(not qBakeNode.image):
        userImageName = qBakeNode.image_name.strip()
        if(not userImageName):
            userImageName = 'Result'

        imgName = "Baked_" + obj.name.strip() + "_" + material.name.strip() + "_" + userImageName
        qBakeNode.image = bpy.data.images.new(imgName, width=defaultSize, height=defaultSize)
        
        qBakeNode.alpha_mode = qBakeNode.alpha_mode

        if(bake_mode == 'NORMAL'):
            qBakeNode.image.colorspace_settings.name = 'Non-Color'
        elif(bake_mode == 'PACK'):
            qBakeNode.image.colorspace_settings.name = 'Non-Color'
        elif(bake_mode == 'COLOR'):
            qBakeNode.image.colorspace_settings.name = 'sRGB'
        else:
            qBakeNode.image.colorspace_settings.name = 'sRGB'

def QBakeLogic(operator, context, node_id = None):
    
    if(not bpy.context.active_object or not hasattr(bpy.context.active_object.data, 'materials')):
        return

    bpy.context.active_object.select_set(True);
    bpy.context.view_layer.objects.active = bpy.context.active_object;

    margin = context.scene.qbake.margin

    dummyImage = bpy.data.images.new("QBakeDummy", width=1, height=1)
    obj = bpy.context.active_object

    initialEngine = bpy.context.scene.render.engine
    initialSamples = bpy.context.scene.cycles.samples

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = context.scene.qbake.samples
    


    QBakePrepareMaterials(obj, dummyImage)

    for material in obj.data.materials:
        for node in material.node_tree.nodes:
            if(node_id != None and hasattr(node, 'unique_id') and node.unique_id != node_id):
                continue
            
            outNode = None;    

            for _node in material.node_tree.nodes:
                if(_node.label == 'QBakeOut'):
                    outNode = _node
    
            if(node.bl_idname == 'QBakeShaderNodeType'):
                qBakeNode = node
                QBakeBakeTargetPrepare(context, obj, material, qBakeNode)
                bake_mode = node.bake_mode
                
                if(bake_mode == 'NORMAL' and qBakeNode.inputs['Shader'].is_linked):
                    target = QBakeBakeNodeLogic(material, qBakeNode, outNode, 'Shader')
                    bpy.ops.object.bake(type='NORMAL', margin=margin, margin_type='EXTEND')
                    QBakeBakeNodeLogicAfterBake(material, target)


                if(bake_mode == 'COLOR' and qBakeNode.inputs['Color'].is_linked):
                    target = QBakeBakeNodeLogic(material, qBakeNode, outNode, 'Color')
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    QBakeBakeNodeLogicAfterBake(material, target)

                if(bake_mode == 'PACKED'):


                    fromNodeSocket = qBakeNode.inputs['Red'].links[0].from_socket
                    fromNode = qBakeNode.inputs['Red'].links[0].from_node
                    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                    redImage = bpy.data.images.new(qBakeNode.image.name + "QBakeRed", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    redImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name;
                    redTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    redTarget.image = redImage

                    material.node_tree.nodes.active = redTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(redTarget)

                    fromNodeSocket = qBakeNode.inputs['Green'].links[0].from_socket
                    fromNode = qBakeNode.inputs['Green'].links[0].from_node
                    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)
                    
                    greenImage = bpy.data.images.new(qBakeNode.image.name + "QBakeGreen", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    greenImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name;
                    greenTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    greenTarget.image = greenImage

                    material.node_tree.nodes.active = greenTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(greenTarget)

                    fromNodeSocket = qBakeNode.inputs['Blue'].links[0].from_socket
                    fromNode = qBakeNode.inputs['Blue'].links[0].from_node
                    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                    blueImage = bpy.data.images.new(qBakeNode.image.name + "QBakeBlue", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    blueImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name;
                    blueTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    blueTarget.image = blueImage

                    material.node_tree.nodes.active = blueTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(blueTarget)

                    fromNodeSocket = qBakeNode.inputs['Alpha'].links[0].from_socket
                    fromNode = qBakeNode.inputs['Alpha'].links[0].from_node
                    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                    alphaImage = bpy.data.images.new(qBakeNode.image.name + "QBakeAlpha", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    alphaImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name;
                    alphaTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    alphaTarget.image = alphaImage

                    material.node_tree.nodes.active = alphaTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(alphaTarget)

                    packedImage = channel_pack(redImage, greenImage, blueImage, alphaImage)
                    qBakeNode.image.pixels[:] = packedImage.pixels[:]
                    qBakeNode.image.pack()

                    bpy.data.images.remove(packedImage)
                    bpy.data.images.remove(redImage)
                    bpy.data.images.remove(greenImage)
                    bpy.data.images.remove(blueImage)
                    bpy.data.images.remove(alphaImage)

                if(bake_mode != 'NORMAL' and bake_mode != 'PACKED'  and qBakeNode.inputs['Alpha'].is_linked):

                    fromNodeSocket = qBakeNode.inputs['Alpha'].links[0].from_socket
                    fromNode = qBakeNode.inputs['Alpha'].links[0].from_node
                    link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                    alphaImage = bpy.data.images.new(qBakeNode.image.name + "QBakeAlpha", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    alphaImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name;
                    alphaTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    alphaTarget.image = alphaImage
                    material.node_tree.nodes.active = alphaTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(alphaTarget)
                    
                    packedImage = alpha_pack(qBakeNode.image, alphaImage)
                    qBakeNode.image.pixels[:] = packedImage.pixels[:]
                    qBakeNode.image.pack()

                    bpy.data.images.remove(packedImage)
                    bpy.data.images.remove(alphaImage)
                

    QBakeCleanupMaterials(obj, dummyImage);
    bpy.data.images.remove(dummyImage)

    bpy.context.scene.render.engine = initialEngine
    bpy.context.scene.cycles.samples = initialSamples
    
    return


class QBakeOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "render.qbake_operator"
    bl_label = "Bake all Nodes"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        QBakeLogic(self, context)
        return {'FINISHED'}

class QBakeOperatorSingle(bpy.types.Operator):
    """Tooltip"""
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
        print(self.node_id)
        QBakeLogic(self, context, self.node_id)
        return {'FINISHED'}

# Define the custom node
class QBakeShaderNode(bpy.types.Node):
    '''Bake Node'''
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

    def update_inputs(self, context):
        
        self.inputs.clear()
        print('test');
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

        if(not self.image):
            layout.prop(self, "image_name", text="Image name")

        layout.prop(self, "alpha_mode", text="Alpha Mode")
        layout.prop(self, "bake_mode", text="Baked Mode")

        if ('Color' in self.inputs and not self.inputs["Color"].is_linked):
            layout.label(text="Warning: Color is not linked! Bake will not work", icon='ERROR')

    def draw_label(self):
        return self.bl_label

# Define the custom category
class MyCustomNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

node_categories = [
    MyCustomNodeCategory("QBAKE_NODES", "QBake Nodes", items=[
        NodeItem("QBakeShaderNodeType"),
    ]),
]

def addQBakeNodeMenu(self, context):
    if getattr(context.space_data, "shader_type", None) == 'OBJECT':
        self.layout.separator()
        op_props = self.layout.operator("node.add_node", text=QBakeShaderNode.bl_label)
        op_props.type = QBakeShaderNode.bl_idname
        op_props.use_transform = True

def register():
    #register_node_categories("QBAKE_NODES", node_categories)
    bpy.types.NODE_MT_category_shader_output.append(addQBakeNodeMenu)
    
    bpy.utils.register_class(QBakeOperator)
    bpy.utils.register_class(QBakeOperatorSingle)
    bpy.utils.register_class(QBakeShaderNode)
    bpy.utils.register_class(QBakePanel)
    bpy.utils.register_class(QBakeGlobalProps)
    bpy.types.Scene.qbake = bpy.props.PointerProperty(type = QBakeGlobalProps)

def unregister():
    #unregister_node_categories("QBAKE_NODES")
    bpy.types.NODE_MT_category_shader_output.remove(addQBakeNodeMenu)
    
    bpy.utils.unregister_class(QBakeOperator)
    bpy.utils.unregister_class(QBakeOperatorSingle)
    bpy.utils.unregister_class(QBakeShaderNode)
    bpy.utils.unregister_class(QBakePanel)
    bpy.utils.unregister_class(QBakeGlobalProps)
    del bpy.types.Scene.qbake
    

if __name__ == "__main__":
    register()