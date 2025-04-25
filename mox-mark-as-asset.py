bl_info = {
    "name": "Mox Mark as Asset",
    "author": "Mox Alehin",
    "version": (2, 16),
    "blender": (3, 0, 0),
    "location": "Object Menu > Mox Mark as Asset, 3D Viewport Context Menu (when objects selected)",
    "description": "Fixes UV channels, bakes albedo texture, prepares material, and marks selected objects as assets",
    "category": "Object",
}

import bpy
import os
import tempfile
import time
from bpy.types import Operator, AddonPreferences
from bpy.props import EnumProperty, FloatProperty

# Addon preferences
class MoxMarkAsAssetPreferences(AddonPreferences):
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

class OBJECT_OT_MoxMarkAsAsset(Operator):
    bl_idname = "object.mox_mark_as_asset"
    bl_label = "Mox Mark as Asset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get addon preferences
        prefs = context.preferences.addons[__name__].preferences
        texture_size = int(prefs.texture_resolution)
        sleep_time = prefs.sleep_time

        # Get all selected mesh objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        processed_objects = 0

        for obj in selected_objects:
            # Set object as active
            context.view_layer.objects.active = obj

            # Call Fix UV operator
            try:
                bpy.ops.object.fix_uv()
            except Exception as e:
                self.report({'WARNING'}, f"Failed to fix UV channels for {obj.name}: {str(e)}")
                continue

            # Check for material
            if not obj.material_slots or not obj.material_slots[0].material:
                self.report({'WARNING'}, f"No material on object {obj.name}")
                continue

            # Check for UV maps
            if not obj.data.uv_layers:
                self.report({'WARNING'}, f"Object {obj.name} has no UV map after fixing")
                continue

            # Store original material
            original_mat = obj.material_slots[0].material
            
            # Store current active UV map
            uv_layers = obj.data.uv_layers
            original_active_uv = None
            original_active_render_uv = None
            for uv_layer in uv_layers:
                if uv_layer.active:
                    original_active_uv = uv_layer
                if uv_layer.active_render:
                    original_active_render_uv = uv_layer
            
            # Duplicate material with nodes
            new_mat = original_mat.copy()
            new_mat.name = f"{original_mat.name}_{obj.name}_Bake"
            new_mat.use_nodes = True
            
            # Get node tree of the new material
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            
            # Find minimum Y coordinate of existing nodes
            if nodes:
                min_y = min(node.location.y for node in nodes)
            else:
                min_y = 0
            
            # Create temporary texture
            temp_image_name = f"T_{obj.name}_Bake_D"
            temp_image = bpy.data.images.new(temp_image_name, width=texture_size, height=texture_size)
            
            # Create nodes
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = temp_image  # Assign temporary texture
            tex_node.select = True  # Make node active for baking
            nodes.active = tex_node  # Set active node
            uv_node = nodes.new('ShaderNodeUVMap')
            
            # Position nodes
            tex_node.location = (0, min_y - 120)  # Below minimum Y with 120 offset
            uv_node.location = (-200, min_y - 120)  # 200 units left of Image Texture
            
            # Find "Unwrap" UV map or use first one
            selected_uv = None
            for uv_layer in uv_layers:
                if uv_layer.name == "Unwrap":
                    selected_uv = uv_layer
                    break
            if not selected_uv:
                selected_uv = uv_layers[0]  # Default to first UV map
            
            # Set active UV map
            selected_uv.active_render = True  # For baking
            selected_uv.active = True  # For object
            
            # Set UV Map in node
            uv_node.uv_map = selected_uv.name
            
            # Connect UV output to Vector input
            links.new(uv_node.outputs['UV'], tex_node.inputs['Vector'])
            
            # Assign new material to object
            obj.material_slots[0].material = new_mat
            
            # Configure scene for baking
            scene = context.scene
            scene.render.engine = 'CYCLES'
            original_bake_type = scene.cycles.bake_type
            scene.cycles.bake_type = 'DIFFUSE'
            
            # Disable Direct and Indirect passes
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            
            # Perform baking
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
            
            # Save texture to temporary folder
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
            
            # Check if file exists
            if not os.path.exists(temp_filepath):
                self.report({'WARNING'}, f"Texture file not found for {obj.name}: {temp_filepath}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            # Edit material: remove all nodes except Image Texture and UV Map
            nodes_to_keep = {tex_node, uv_node}
            for node in list(nodes):
                if node not in nodes_to_keep:
                    nodes.remove(node)
            
            # Add new nodes
            diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
            diffuse_node.inputs['Roughness'].default_value = 1.0  # Set Roughness to 1
            output_node = nodes.new('ShaderNodeOutputMaterial')
            
            # Position new nodes
            diffuse_node.location = (300, min_y - 120)  # Right of Image Texture
            output_node.location = (500, min_y - 120)  # Right of Diffuse BSDF
            
            # Connect nodes
            links.new(tex_node.outputs['Color'], diffuse_node.inputs['Color'])
            links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])
            
            # Clear existing asset data and mark as asset
            try:
                obj.asset_clear()  # Clear asset data
                obj.asset_mark()  # Mark as asset
                obj.asset_generate_preview()  # Generate preview
            except Exception as e:
                self.report({'WARNING'}, f"Failed to mark {obj.name} as asset: {str(e)}")
                obj.material_slots[0].material = original_mat
                if original_active_uv:
                    original_active_uv.active = True
                if original_active_render_uv:
                    original_active_render_uv.active_render = True
                continue
            
            # Delay before deleting temporary file
            time.sleep(sleep_time)  # Wait for specified seconds
            
            # Delete temporary file
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            # Restore original material
            obj.material_slots[0].material = original_mat
            
            # Restore original active UV map
            if original_active_uv:
                original_active_uv.active = True
            if original_active_render_uv:
                original_active_render_uv.active_render = True
            
            # Restore scene settings
            scene.cycles.bake_type = original_bake_type
            
            processed_objects += 1

        self.report({'INFO'}, f"Processed {processed_objects} objects as assets")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_MoxMarkAsAsset.bl_idname)

def context_menu_func(self, context):
    if context.selected_objects:  # Show option only if at least one object is selected
        self.layout.operator(OBJECT_OT_MoxMarkAsAsset.bl_idname)
        self.layout.separator()  # Add separator for clarity

def register():
    bpy.utils.register_class(MoxMarkAsAssetPreferences)
    bpy.utils.register_class(OBJECT_OT_MoxMarkAsAsset)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(context_menu_func)

def unregister():
    bpy.utils.unregister_class(MoxMarkAsAssetPreferences)
    bpy.utils.unregister_class(OBJECT_OT_MoxMarkAsAsset)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.remove(context_menu_func)

if __name__ == "__main__":
    register()