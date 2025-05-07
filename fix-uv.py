bl_info = {
    "name": "Fix UV Plugin",
    "author": "Your Name",
    "version": (1, 5, 6),
    "blender": (3, 0, 0),
    "location": "View3D > Tools > Fix UV, Object Context Menu",
    "description": "Fixes UV channels for selected mesh objects, keeping Unwrap and Gradients at the top",
    "category": "UV"
}

import bpy
import bmesh
from bpy.types import Operator, Panel
from math import radians

class OBJECT_OT_FixUV(Operator):
    bl_idname = "object.fix_uv"
    bl_label = "Fix UV"
    bl_description = "Fix UV channels for selected objects, keeping Unwrap and Gradients at the top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if any selected objects are meshes
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        # Store the original active object and selected objects
        original_active = context.view_layer.objects.active
        original_selected = context.selected_objects[:]

        # Filter selected objects to include only meshes
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        for obj in selected_objects:
            # Deselect all objects
            for o in context.scene.objects:
                o.select_set(False)
            # Select only the current object
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # Ensure we are in Object Mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            uv_layers = obj.data.uv_layers

            # Check if the object has exactly three UV maps with Unwrap and Gradients in correct order
            if len(uv_layers) == 3 and uv_layers[0].name == "Unwrap" and uv_layers[1].name == "Gradients":
                # Only recalculate Unwrap with Smart UV Project
                uv_layers.active_index = 0  # Set Unwrap as active
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.reveal()  # Unhide all faces
                bpy.context.scene.tool_settings.use_uv_select_sync = False
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.smart_project(angle_limit=radians(66))
                bpy.ops.object.mode_set(mode='OBJECT')
                uv_layers.active_index = 1  # Set Gradients as active for display
                continue

            # Store data of the first and second UV channels before any modifications
            first_uv_data = None
            first_uv_name = None
            second_uv_data = None
            second_uv_name = None
            if len(uv_layers) > 0:
                first_uv_name = uv_layers[0].name
                first_uv_data = [(uv.uv[0], uv.uv[1]) for uv in uv_layers[0].data]
                if len(uv_layers) > 1:
                    second_uv_name = uv_layers[1].name
                    second_uv_data = [(uv.uv[0], uv.uv[1]) for uv in uv_layers[1].data]

            # Create or configure UV channels
            if len(uv_layers) == 0:
                # No UV channels: create Unwrap and Gradients
                unwrap_layer = uv_layers.new(name="Unwrap")
                gradients_layer = uv_layers.new(name="Gradients")
            else:
                # UV channels exist
                if first_uv_name != "Unwrap":
                    # Rename the first channel to Gradients
                    uv_layers[0].name = "Gradients"
                else:
                    # Create Gradients if the first channel is Unwrap
                    uv_layers.new(name="Gradients")
                    if second_uv_data:
                        # Use second UV channel's data for Gradients
                        gradients_layer = uv_layers[1]
                        for i, uv_coord in enumerate(second_uv_data):
                            gradients_layer.data[i].uv = uv_coord
                # Ensure Gradients exists
                gradients_layer = next(layer for layer in uv_layers if layer.name == "Gradients")

            # Store data of Gradients and second UV map for reordering
            temp_uv_data = {}
            if gradients_layer:
                temp_uv_data["Gradients"] = [(uv.uv[0], uv.uv[1]) for uv in gradients_layer.data]
            if second_uv_name and second_uv_name not in ["Unwrap", "Gradients"]:
                temp_uv_data[second_uv_name] = second_uv_data

            # Clear all UV channels
            while len(uv_layers) > 0:
                uv_layers.remove(uv_layers[0])

            # Create UV channels in the correct order: Unwrap first, Gradients second
            unwrap_layer = uv_layers.new(name="Unwrap")
            # Unwrap will be populated by Smart UV Project, no need to copy data

            gradients_layer = uv_layers.new(name="Gradients")
            if "Gradients" in temp_uv_data:
                for i, uv_coord in enumerate(temp_uv_data["Gradients"]):
                    gradients_layer.data[i].uv = uv_coord
            elif first_uv_data:
                # Use data from the original first UV channel
                for i, uv_coord in enumerate(first_uv_data):
                    gradients_layer.data[i].uv = uv_coord

            # Restore the second UV map if it exists
            if second_uv_name and second_uv_name not in ["Unwrap", "Gradients"]:
                second_layer = uv_layers.new(name=second_uv_name)
                for i, uv_coord in enumerate(temp_uv_data[second_uv_name]):
                    second_layer.data[i].uv = uv_coord

            # Set active_render: disable for all except Gradients
            for layer in uv_layers:
                layer.active_render = (layer.name == "Gradients")

            # Switch to Edit Mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Unhide all faces before Smart UV Project
            bpy.ops.mesh.reveal()
            
            # Perform Smart UV Project for Unwrap
            bpy.context.scene.tool_settings.use_uv_select_sync = False
            uv_layers.active_index = 0  # Unwrap (first)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=radians(66))
            
            # Return to Object Mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Set active UV channel to Gradients for display
            uv_layers.active_index = 1  # Gradients (second)

        # Restore original selection
        for obj in context.scene.objects:
            obj.select_set(obj in original_selected)
        context.view_layer.objects.active = original_active

        self.report({'INFO'}, f"Processed {len(selected_objects)} objects")
        return {'FINISHED'}

class VIEW3D_PT_FixUVPanel(Panel):
    bl_label = "Fix UV"
    bl_idname = "VIEW3D_PT_fix_uv"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.fix_uv")

def context_menu_func(self, context):
    # Add operator to context menu
    self.layout.operator("object.fix_uv")
    self.layout.separator()

def register():
    # Register classes and append to menus
    bpy.utils.register_class(OBJECT_OT_FixUV)
    bpy.utils.register_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(context_menu_func)
    bpy.types.VIEW3D_MT_object.append(context_menu_func)

def unregister():
    # Unregister classes and remove from menus
    bpy.utils.unregister_class(OBJECT_OT_FixUV)
    bpy.utils.unregister_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object_context_menu.remove(context_menu_func)
    bpy.types.VIEW3D_MT_object.remove(context_menu_func)

if __name__ == "__main__":
    register()