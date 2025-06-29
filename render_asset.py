bl_info = {
    "name": "Render Asset",
    "author": "Mox Alehin",
    "version": (2, 16),
    "blender": (3, 0, 0),
    "location": "Object Menu > Render Asset, 3D Viewport Context Menu (when objects selected)",
    "description": "Fixes UV channels, bakes albedo texture, prepares material, and marks selected objects as assets",
    "category": "Object",
}

import bpy
import os
import tempfile
import time
from bpy.types import Operator, AddonPreferences
from bpy.props import EnumProperty, FloatProperty

class RenderAssetPreferences(AddonPreferences):
    bl_idname = __name__

    texture_resolution: EnumProperty(
        name="Texture Resolution",
        description="Resolution of the baked texture",
        items=[
            ('32', "32x32", "Very low resolution"),
            ('64', "64x64", "Low resolution"),
            ('128', "128x128", "Low-medium resolution"),
            ('256', "256x256", "Medium resolution"),
            ('512', "512x512", "Medium-high resolution"),
            ('1024', "1024x1024", "High resolution"),
            ('2048', "2048x2048", "Very high resolution"),
            ('4096', "4096x4096", "Ultra high resolution"),
        ],
        default='1024',
    )

    sleep_time: FloatProperty(
        name="Sleep Time",
        description="Delay before deleting temporary file (seconds)",
        default=0.01,
        min=0.0,
        max=10.0,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "texture_resolution")
        layout.prop(self, "sleep_time")

class OBJECT_OT_RenderAsset(Operator):
    bl_idname = "object.render_asset"
    bl_label = "Render Asset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        texture_size = int(prefs.texture_resolution)
        sleep_time = prefs.sleep_time

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        processed_objects = 0

        for obj in selected_objects:
            for o in selected_objects:
                o.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj

            if not obj.material_slots or not obj.material_slots[0].material:
                self.report({'WARNING'}, f"No material on object {obj.name}")
                continue

            if not obj.data.uv_layers:
                self.report({'WARNING'}, f"Object {obj.name} has no UV map after fixing")
                continue

            original_mat = obj.material_slots[0].material
            
            uv_layers = obj.data.uv_layers
            original_active_uv = None
            original_active_render_uv = None
            for uv_layer in uv_layers:
                if uv_layer.active:
                    original_active_uv = uv_layer
                if uv_layer.active_render:
                    original_active_render_uv = uv_layer
            
            new_mat = original_mat.copy()
            new_mat.name = f"{original_mat.name}_{obj.name}_Bake"
            new_mat.use_nodes = True
            
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            
            if nodes:
                min_y = min(node.location.y for node in nodes)
            else:
                min_y = 0
            
            temp_image_name = f"T_{obj.name}_Bake_D"
            temp_image = bpy.data.images.new(temp_image_name, width=texture_size, height=texture_size)
            
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = temp_image
            tex_node.select = True
            nodes.active = tex_node
            uv_node = nodes.new('ShaderNodeUVMap')
            
            tex_node.location = (0, min_y - 120)
            uv_node.location = (-200, min_y - 120)
            
            selected_uv = None
            for uv_layer in uv_layers:
                if uv_layer.name == "Unwrap":
                    selected_uv = uv_layer
                    break
            if not selected_uv:
                selected_uv = uv_layers[0]
            
            selected_uv.active_render = True
            selected_uv.active = True
            
            uv_node.uv_map = selected_uv.name
            
            links.new(uv_node.outputs['UV'], tex_node.inputs['Vector'])
            
            obj.material_slots[0].material = new_mat
            
            scene = context.scene
            scene.render.engine = 'CYCLES'
            original_bake_type = scene.cycles.bake_type
            scene.cycles.bake_type = 'DIFFUSE'
            
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            
            try:
                bpy.ops.object.bake(type='DIFFUSE')
            except Exception as e:
                self.report({'WARNING'}, f"Baking failed for {obj.name}: {str(e)}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, f"{temp_image_name}.png")
            try:
                temp_image.save(filepath=temp_filepath)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to save texture for {obj.name}: {str(e)}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            if not os.path.exists(temp_filepath):
                self.report({'WARNING'}, f"Texture file not found for {obj.name}: {temp_filepath}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            nodes_to_keep = {tex_node, uv_node}
            for node in list(nodes):
                if node not in nodes_to_keep:
                    nodes.remove(node)
            
            diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
            diffuse_node.inputs['Roughness'].default_value = 1.0
            output_node = nodes.new('ShaderNodeOutputMaterial')
            
            diffuse_node.location = (300, min_y - 120)
            output_node.location = (500, min_y - 120)
            
            links.new(tex_node.outputs['Color'], diffuse_node.inputs['Color'])
            links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])
            
            try:
                obj.asset_clear()
                obj.asset_mark()
                obj.asset_generate_preview()
            except Exception as e:
                self.report({'WARNING'}, f"Failed to mark {obj.name} as asset: {str(e)}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            time.sleep(sleep_time)
            
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            obj.material_slots[0].material = original_mat
            
            if original_active_uv:
                original_active_uv.active = True
            if original_active_render_uv:
                original_active_render_uv.active_render = True
            
            scene.cycles.bake_type = original_bake_type
            
            processed_objects += 1

        for o in selected_objects:
            o.select_set(True)

        self.report({'INFO'}, f"Processed {processed_objects} objects as assets")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RenderAssetPreferences)
    bpy.utils.register_class(OBJECT_OT_RenderAsset)

def unregister():
    bpy.utils.unregister_class(RenderAssetPreferences)
    bpy.utils.unregister_class(OBJECT_OT_RenderAsset)

if __name__ == "__main__":
    register()