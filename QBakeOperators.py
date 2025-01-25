import bpy
import os
from . import ImageUtils

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
    for node in material.node_tree.nodes:     
        if(node.label == 'QBakeDummy'):
            material.node_tree.nodes.active = node


def QBakeBakeTargetPrepare(context, obj, material, qBakeNode):
    bake_mode = qBakeNode.bake_mode
    defaultSize = context.scene.qbake.imageSize

    if(context.scene.qbake.regenerateImages and qBakeNode.image):
        qBakeNode.image.source = 'GENERATED'
        qBakeNode.image.generated_width = defaultSize
        qBakeNode.image.generated_height = defaultSize

    if(not qBakeNode.image):
        userImageName = qBakeNode.image_name.strip()
        if(not userImageName):
            userImageName = 'Result'

        imgName = "Baked_" + obj.name.strip() + "_" + material.name.strip() + "_" + userImageName
        qBakeNode.image = bpy.data.images.new(imgName, width=defaultSize, height=defaultSize, alpha=True)
        
        if(bake_mode == 'NORMAL'):
            qBakeNode.image.colorspace_settings.name = 'Non-Color'
        elif(bake_mode == 'PACKED'):
            qBakeNode.image.colorspace_settings.name = 'Non-Color'
            qBakeNode.alpha_mode = 'CHANNEL_PACKED'
        elif(bake_mode == 'COLOR'):
            qBakeNode.image.colorspace_settings.name = qBakeNode.image_colorspace
            qBakeNode.alpha_mode = qBakeNode.alpha_mode
        else:
            qBakeNode.image.colorspace_settings.name = 'sRGB'
            qBakeNode.alpha_mode = qBakeNode.alpha_mode

def QBakeExportLogic(operator, context, images):
    
    if(bpy.data.filepath == ''):
        return    
    
    if(not context.scene.qbake.export):
        return
    
    for image in images:
        try:
            if (context.scene.qbake.removeAfterExport):
                image.file_format = 'PNG'
                image.filepath = os.path.join(context.scene.qbake.exportDir, image.name + ".png")
                image.save()
                bpy.data.images.remove(image)
            else:
                tempImage = image.copy()
                tempImage.file_format = 'PNG'
                tempImage.filepath = os.path.join(context.scene.qbake.exportDir, image.name + ".png")
                tempImage.save()
                bpy.data.images.remove(tempImage)

        except:
            print("Unable to export" + image.name) 

def QBakeLogic(operator, context, node_id = None):
    
    if(not bpy.context.active_object or not hasattr(bpy.context.active_object.data, 'materials') or bpy.context.active_object.hide_render):
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
    
    bakedImages = []

    QBakePrepareMaterials(obj, dummyImage)    

    countTotal = 0
    countCurrent = 0

    #get number of bakes
    for material in obj.data.materials:
        for node in material.node_tree.nodes:
            if(node_id != None and hasattr(node, 'unique_id') and node.unique_id != node_id):
                continue

            outNode = None
            dummy = None

            for _node in material.node_tree.nodes:
                if(_node.label == 'QBakeOut'):
                    outNode = _node
                if(_node.label == 'QBakeDummy'):
                    dummy = _node
            
            if(dummy == None):
                continue

            if(node.bl_idname == 'QBakeShaderNodeType'):
                countTotal += 1

    # main bake loop
    for material in obj.data.materials:
        for node in material.node_tree.nodes:
            if(node_id != None and hasattr(node, 'unique_id') and node.unique_id != node_id):
                continue
            
            outNode = None
            dummy = None

            for _node in material.node_tree.nodes:
                if(_node.label == 'QBakeOut'):
                    outNode = _node
                if(_node.label == 'QBakeDummy'):
                    dummy = _node
            
            if(dummy == None):
                continue

            if(node.bl_idname == 'QBakeShaderNodeType'):
                
                countCurrent +=1 
                material.node_tree.nodes.active = dummy

                print('QBake: Baking ' + str(countCurrent) + ' / ' + str(countTotal))
                operator.report({'INFO'}, 'QBake: Baking ' + str(countCurrent) + ' / ' + str(countTotal))

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

                    redImage = bpy.data.images.new(qBakeNode.image.name + "QBakeRed", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    redImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name
                    redTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    redTarget.image = redImage


                    greenImage = bpy.data.images.new(qBakeNode.image.name + "QBakeGreen", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    greenImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name
                    greenTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    greenTarget.image = greenImage


                    blueImage = bpy.data.images.new(qBakeNode.image.name + "QBakeBlue", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    blueImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name
                    blueTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    blueTarget.image = blueImage


                    alphaImage = bpy.data.images.new(qBakeNode.image.name + "QBakeAlpha", width=qBakeNode.image.size[0], height=qBakeNode.image.size[1])
                    alphaImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name
                    alphaTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    alphaTarget.image = alphaImage

                    if(qBakeNode.inputs['Red'].is_linked):
                        fromNodeSocket = qBakeNode.inputs['Red'].links[0].from_socket
                        fromNode = qBakeNode.inputs['Red'].links[0].from_node
                        link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)
                        
                        material.node_tree.nodes.active = redTarget
                        bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    

                    if(qBakeNode.inputs['Green'].is_linked):
                        fromNodeSocket = qBakeNode.inputs['Green'].links[0].from_socket
                        fromNode = qBakeNode.inputs['Green'].links[0].from_node
                        link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)
                    
                        material.node_tree.nodes.active = greenTarget
                        bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                        


                    if(qBakeNode.inputs['Blue'].is_linked):
                        fromNodeSocket = qBakeNode.inputs['Blue'].links[0].from_socket
                        fromNode = qBakeNode.inputs['Blue'].links[0].from_node
                        link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                        material.node_tree.nodes.active = blueTarget
                        bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                        

                    if(qBakeNode.inputs['Alpha'].is_linked):
                        fromNodeSocket = qBakeNode.inputs['Alpha'].links[0].from_socket
                        fromNode = qBakeNode.inputs['Alpha'].links[0].from_node
                        link = material.node_tree.links.new(outNode.inputs[0], fromNodeSocket)

                        material.node_tree.nodes.active = alphaTarget
                        bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                        

                    packedImage = ImageUtils.channel_pack(redImage, greenImage, blueImage, alphaImage)
                    qBakeNode.image.pixels[:] = packedImage.pixels[:]
                    qBakeNode.image.pack()

                    material.node_tree.nodes.remove(redTarget)
                    material.node_tree.nodes.remove(greenTarget)
                    material.node_tree.nodes.remove(blueTarget)
                    material.node_tree.nodes.remove(alphaTarget)

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

                    if (bake_mode == 'COLOR' and qBakeNode.alpha_non_color):
                        alphaImage.colorspace_settings.name = 'Non-Color'
                    else:
                        alphaImage.colorspace_settings.name = qBakeNode.image.colorspace_settings.name

                    alphaTarget = material.node_tree.nodes.new('ShaderNodeTexImage')
                    alphaTarget.image = alphaImage
                    material.node_tree.nodes.active = alphaTarget
                    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND')
                    material.node_tree.nodes.remove(alphaTarget)
                    
                    packedImage = ImageUtils.alpha_pack(qBakeNode.image, alphaImage)
                    qBakeNode.image.pixels[:] = packedImage.pixels[:]
                    qBakeNode.image.pack()

                    bpy.data.images.remove(packedImage)
                    bpy.data.images.remove(alphaImage)

                material.node_tree.nodes.active = dummy
                bakedImages.append(qBakeNode.image)

    QBakeCleanupMaterials(obj, dummyImage)
    bpy.data.images.remove(dummyImage)

    bpy.context.scene.render.engine = initialEngine
    bpy.context.scene.cycles.samples = initialSamples
    
    if(context.scene.qbake.export):
        QBakeExportLogic(operator, context, bakedImages)

    return


class QBakeOperator(bpy.types.Operator):
    """Bake All nodes"""
    bl_idname = "render.qbake_operator"
    bl_label = "Bake all Nodes"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        QBakeLogic(self, context)
        return {'FINISHED'}

class QBakeOperatorSingle(bpy.types.Operator):
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
        QBakeLogic(self, context, self.node_id)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(QBakeOperator)
    bpy.utils.register_class(QBakeOperatorSingle)


def unregister():
    bpy.utils.unregister_class(QBakeOperator)
    bpy.utils.unregister_class(QBakeOperatorSingle)