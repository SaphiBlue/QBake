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
import os

from ..helper import image_utils

class qbake_bake:
    def __init__(self, operator, context, node_id: str = None, material: bpy.types.Material = None):
        self.operator = operator
        self.context = context
        self.node_id = node_id
        self.material = material
        self.prepared = False
        pass


    def prepare_bake(self):
        if(not bpy.context.active_object or not hasattr(bpy.context.active_object.data, 'materials') or bpy.context.active_object.hide_render):
            return

        self.obj = bpy.context.active_object
        self.select_obj()

        self.margin = self.context.scene.qbake.margin

        self.dummy_image = bpy.data.images.new("QBakeDummy", width=1, height=1)        

        self.initial_engine = bpy.context.scene.render.engine
        self.initial_samples = bpy.context.scene.cycles.samples

        self.initial_use_bake_multires = bpy.context.scene.render.bake.use_multires
        self.initial_use_selected_to_active = bpy.context.scene.render.bake.use_selected_to_active

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = self.context.scene.qbake.samples

        bpy.context.scene.render.bake.use_multires = False
        bpy.context.scene.render.bake.use_selected_to_active = False
        
        self.baked_images = []

        self.prepare_materials()    

        self.count_total = 0
        self.count_current = 0
        self.initial_uv_layer = ''
        self.initial_uv_layer_render = ''

        self.bake_nodes = {}

        for uv in self.obj.data.uv_layers:
            if(uv.active):
                self.initial_uv_layer = uv.name
            if(uv.active_render):
                self.initial_uv_layer_render = uv.name

        #get number of bakes
        for material in self.obj.data.materials:

            if(self.material != None and self.material != material):
                continue
            
            for node in material.node_tree.nodes:
                if(self.node_id != None and hasattr(node, 'unique_id') and node.unique_id != self.node_id):
                    continue

                if(self.node_id == None and hasattr(node, 'no_global') and node.no_global == True):
                    continue

                if(node.bl_idname == 'QBakeShaderNodeType'):
                    self.count_total += 1

                    self.bake_nodes[node.unique_id] = {
                        'material': material,
                        'bake_node': node,
                        'baked': False
                    }

        self.prepared = True

    def select_obj(self):
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(True)
        bpy.context.view_layer.objects.active = self.obj

    def prepage_bake_target(self, material, bake_node):
        bake_mode = bake_node.bake_mode
        defaultSize = self.context.scene.qbake.imageSize

        bpy.context.view_layer.objects.active = self.obj
        bpy.context.active_object.select_set(True)

        if(self.context.scene.qbake.regenerateImages and bake_node.image and bake_node.keep_interal == False and bake_node.no_global == False):
            bake_node.image.source = 'GENERATED'
            bake_node.image.generated_width = defaultSize
            bake_node.image.generated_height = defaultSize

        if(not bake_node.image):
            userImageName = bake_node.image_name.strip()
            if(not userImageName):
                userImageName = 'Result'

            imgName = self.context.scene.qbake.defaultImgName
            imgName = imgName.replace("{obj}", self.obj.name.strip())
            imgName = imgName.replace("{mat}", material.name.strip())
            imgName = imgName.replace("{img_name}", userImageName.strip())
            imgName = bpy.path.clean_name(imgName)
            
            bake_node.image = bpy.data.images.new(imgName, width=defaultSize, height=defaultSize, alpha=True)
            
            if(bake_mode == 'NORMAL'):
                bake_node.image.colorspace_settings.name = 'Non-Color'
            elif(bake_mode == 'PACKED'):
                bake_node.image.colorspace_settings.name = 'Non-Color'
                bake_node.alpha_mode = 'CHANNEL_PACKED'
            elif(bake_mode == 'COLOR'):
                bake_node.image.colorspace_settings.name = bake_node.image_colorspace
                bake_node.alpha_mode = bake_node.alpha_mode
            else:
                bake_node.image.colorspace_settings.name = 'sRGB'
                bake_node.alpha_mode = bake_node.alpha_mode

    def bake_node(self, node_id: str):

        self.select_obj()

        bake_node = self.bake_nodes[node_id]['bake_node']
        material = self.bake_nodes[node_id]['material']

        out_node = None
        dummy = None

        for _node in material.node_tree.nodes:
            if(_node.label == 'QBakeOut'):
                out_node = _node
            if(_node.label == 'QBakeDummy'):
                dummy = _node

        if(dummy == None):
            return

        if(bake_node.bl_idname == 'QBakeShaderNodeType'):

            material.node_tree.nodes.active = dummy
            
            self.prepage_bake_target(material, bake_node)

            bake_mode = bake_node.bake_mode
            
            if(self.initial_uv_layer != ''):
                for uv in self.obj.data.uv_layers:
                    if(uv.name == self.initial_uv_layer):
                        uv.active = True
            if(self.initial_uv_layer_render != ''):
                for uv in self.obj.data.uv_layers:
                    if(uv.name == self.initial_uv_layer_render):
                        uv.active_render = True

            
            uvTargetIndex = bake_node.get_uv_map_index()
            
            uv_index = 0
            for uv in self.obj.data.uv_layers:
                if(uv_index == uvTargetIndex):
                    uv.active = True
                    uv.active_render = True
                uv_index += 1

            if(bake_mode == 'NORMAL' and bake_node.inputs['Shader'].is_linked):
                target = self.bake_node_logic(material, bake_node, out_node, 'Shader')
                bpy.ops.object.bake(type='NORMAL', margin=self.margin, margin_type='EXTEND')
                self.bake_node_logic_after_bake(material, target)


            if(bake_mode == 'COLOR' and bake_node.inputs['Color'].is_linked):
                target = self.bake_node_logic(material, bake_node, out_node, 'Color')
                bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                self.bake_node_logic_after_bake(material, target)

            if(bake_mode == 'PACKED'):

                red_image = bpy.data.images.new(bake_node.image.name + "QBakeRed", width=bake_node.image.size[0], height=bake_node.image.size[1])
                red_image.colorspace_settings.name = bake_node.image.colorspace_settings.name
                red_target = material.node_tree.nodes.new('ShaderNodeTexImage')
                red_target.image = red_image


                green_image = bpy.data.images.new(bake_node.image.name + "QBakeGreen", width=bake_node.image.size[0], height=bake_node.image.size[1])
                green_image.colorspace_settings.name = bake_node.image.colorspace_settings.name
                green_target = material.node_tree.nodes.new('ShaderNodeTexImage')
                green_target.image = green_image


                blue_image = bpy.data.images.new(bake_node.image.name + "QBakeBlue", width=bake_node.image.size[0], height=bake_node.image.size[1])
                blue_image.colorspace_settings.name = bake_node.image.colorspace_settings.name
                blue_target = material.node_tree.nodes.new('ShaderNodeTexImage')
                blue_target.image = blue_image


                alpha_image = bpy.data.images.new(bake_node.image.name + "QBakeAlpha", width=bake_node.image.size[0], height=bake_node.image.size[1])
                alpha_image.colorspace_settings.name = bake_node.image.colorspace_settings.name
                alpha_target = material.node_tree.nodes.new('ShaderNodeTexImage')
                alpha_target.image = alpha_image

                if(bake_node.inputs['Red'].is_linked):
                    from_node_socket = bake_node.inputs['Red'].links[0].from_socket
                    from_node = bake_node.inputs['Red'].links[0].from_node
                    link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)
                    
                    material.node_tree.nodes.active = red_target
                    bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                

                if(bake_node.inputs['Green'].is_linked):
                    from_node_socket = bake_node.inputs['Green'].links[0].from_socket
                    from_node = bake_node.inputs['Green'].links[0].from_node
                    link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)
                
                    material.node_tree.nodes.active = green_target
                    bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                    


                if(bake_node.inputs['Blue'].is_linked):
                    from_node_socket = bake_node.inputs['Blue'].links[0].from_socket
                    from_node = bake_node.inputs['Blue'].links[0].from_node
                    link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)

                    material.node_tree.nodes.active = blue_target
                    bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                    

                if(bake_node.inputs['Alpha'].is_linked):
                    from_node_socket = bake_node.inputs['Alpha'].links[0].from_socket
                    from_node = bake_node.inputs['Alpha'].links[0].from_node
                    link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)

                    material.node_tree.nodes.active = alpha_target
                    bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                    

                packedImage = image_utils.channel_pack(red_image, green_image, blue_image, alpha_image)
                bake_node.image.pixels[:] = packedImage.pixels[:]
                bake_node.image.pack()

                material.node_tree.nodes.remove(red_target)
                material.node_tree.nodes.remove(green_target)
                material.node_tree.nodes.remove(blue_target)
                material.node_tree.nodes.remove(alpha_target)

                bpy.data.images.remove(packedImage)
                bpy.data.images.remove(red_image)
                bpy.data.images.remove(green_image)
                bpy.data.images.remove(blue_image)
                bpy.data.images.remove(alpha_image)

            if(bake_mode != 'NORMAL' and bake_mode != 'PACKED' and bake_node.inputs['Alpha'].is_linked):

                from_node_socket = bake_node.inputs['Alpha'].links[0].from_socket
                from_node = bake_node.inputs['Alpha'].links[0].from_node
                link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)

                alpha_image = bpy.data.images.new(bake_node.image.name + "QBakeAlpha", width=bake_node.image.size[0], height=bake_node.image.size[1])

                if (bake_mode == 'COLOR' and bake_node.alpha_non_color):
                    alpha_image.colorspace_settings.name = 'Non-Color'
                else:
                    alpha_image.colorspace_settings.name = bake_node.image.colorspace_settings.name

                alpha_target = material.node_tree.nodes.new('ShaderNodeTexImage')
                alpha_target.image = alpha_image
                material.node_tree.nodes.active = alpha_target
                bpy.ops.object.bake(type='EMIT', margin=self.margin, margin_type='EXTEND')
                material.node_tree.nodes.remove(alpha_target)
                
                packed_image = image_utils.alpha_pack(bake_node.image, alpha_image)
                bake_node.image.pixels[:] = packed_image.pixels[:]
                bake_node.image.pack()

                bpy.data.images.remove(packed_image)
                bpy.data.images.remove(alpha_image)

            material.node_tree.nodes.active = dummy
            
            if(bake_node.keep_interal == False and bake_node.no_global == False):
                self.baked_images.append(bake_node.image)

            self.bake_nodes[node_id]['baked'] = True


    def after_bake(self):
        self.cleanup_materials()
        bpy.data.images.remove(self.dummy_image)

        bpy.context.scene.render.engine = self.initial_engine
        bpy.context.scene.cycles.samples = self.initial_samples

        bpy.context.scene.render.bake.use_multires = self.initial_use_bake_multires
        bpy.context.scene.render.bake.use_selected_to_active = self.initial_use_selected_to_active
        
        for uv in self.obj.data.uv_layers:
            if(uv.name == self.initial_uv_layer):
                uv.active = True
            if(uv.name == self.initial_uv_layer_render):
                uv.active_render = True

        if(self.context.scene.qbake.export):
            self.export()

    def bake_node_logic(self, material, bake_node, out_node, socket_name):
        from_node_socket = bake_node.inputs[socket_name].links[0].from_socket
        from_node = bake_node.inputs[socket_name].links[0].from_node
        link = material.node_tree.links.new(out_node.inputs[0], from_node_socket)

        target = material.node_tree.nodes.new('ShaderNodeTexImage')
        target.image = bake_node.image
        material.node_tree.nodes.active = target

        return target

    def bake_node_logic_after_bake(self, material, target):
        target.image.pack()
        material.node_tree.nodes.remove(target)
        for node in material.node_tree.nodes:     
            if(node.label == 'QBakeDummy'):
                material.node_tree.nodes.active = node


    def prepare_materials(self):
        for material in self.obj.data.materials:
            out = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
            out.label = "QBakeOut"
            img = material.node_tree.nodes.new('ShaderNodeTexImage')
            img.label = "QBakeDummy"
            img.image = self.dummy_image
            img.select = True
            material.node_tree.nodes.active = out
            material.node_tree.nodes.active = img


    def cleanup_materials(self):
        for material in self.obj.data.materials:
            for node in material.node_tree.nodes:
                if(node.label == 'QBakeOut'):
                    material.node_tree.nodes.remove(node)
                    continue;        
                if(node.label == 'QBakeDummy'):
                    material.node_tree.nodes.remove(node)
                    continue

    def export(self):
        
        if(bpy.data.filepath == ''):
            return    
        
        if(not self.context.scene.qbake.export):
            return
        
        for image in self.baked_images:
            if(image): 
                try:
                    if (self.context.scene.qbake.removeAfterExport):
                        image.file_format = 'PNG'
                        image.filepath = os.path.join(self.context.scene.qbake.exportDir, image.name + ".png")
                        image.save()
                        bpy.data.images.remove(image)
                    else:
                        tempImage = image.copy()
                        tempImage.file_format = 'PNG'
                        tempImage.filepath = os.path.join(self.context.scene.qbake.exportDir, image.name + ".png")
                        tempImage.save()
                        bpy.data.images.remove(tempImage)

                except:
                    print("Unable to export" + image.name) 

    def bake_all(self):
        if not self.prepared:
            self.prepare_bake()


        for node_id, bake in self.bake_nodes.items():
            self.count_current +=1 
            print('QBake: Baking ' + str(self.count_current) + ' / ' + str(self.count_total))
            if self.operator:
                self.operator.report({'INFO'}, 'QBake: Baking ' + str(self.count_current) + ' / ' + str(self.count_total))
            self.bake_node(node_id)

        if(self.count_total <= 0):
            print('QBake: Nothing to bake')
            if self.operator:
                self.operator.report({'INFO'}, 'QBake: Nothing to bake')

        self.after_bake()

    def bake_sequence(self) -> int:

        if not self.prepared:
            self.prepare_bake()
        
        for node_id, bake in self.bake_nodes.items():
            if(not bake['baked']):
                self.count_current +=1 
                print('QBake: Baking ' + str(self.count_current) + ' / ' + str(self.count_total))
                if self.operator:
                    self.operator.report({'INFO'}, 'QBake: Baking ' + str(self.count_current) + ' / ' + str(self.count_total))
                self.bake_node(node_id)
                break

        remaining = self.count_total - self.count_current

        if(remaining <= 0):
            self.after_bake()

        return self.count_total - self.count_current