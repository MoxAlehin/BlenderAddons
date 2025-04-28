bl_info = {
    "name": "Mox Fix Object",
    "author": "Mox Alehin",
    "version": (1, 7),
    "blender": (3, 0, 0),
    "location": "Object Context Menu",
    "description": "Fixes UV, scales small objects, clears custom normals, recalculates normals, and applies a material from Asset Library",
    "category": "Object",
}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, FloatProperty
import os

class MoxFixObjectPreferences(AddonPreferences):
    bl_idname = __name__

    material_name: StringProperty(
        name="Material Name",
        description="Name of the material to apply from Asset Library",
        default="MI_Gradient1x4",
    )

    library_path: StringProperty(
        name="Library Path",
        description="Path to the .blend file containing the material (optional)",
        default="C:/Users/moxal/Brain/Activities/Content/LowPoly/Materials/Gradients.blend",
        subtype='FILE_PATH',
    )

    size_threshold: FloatProperty(
        name="Size Threshold (cm)",
        description="Objects smaller than this size (in centimeters) will be scaled up by 100x",
        default=5.0,  # 1 cm
        min=0.0,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mox Fix Object Settings")
        layout.prop(self, "material_name")
        layout.prop(self, "library_path")
        layout.prop(self, "size_threshold")

class OBJECT_OT_MoxFixObject(Operator):
    bl_idname = "object.mox_fix_object"
    bl_label = "Mox Fix Object"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0
    
    def execute(self, context):
        # Force unit settings to centimeters
        context.scene.unit_settings.scale_length = 0.01
        context.scene.unit_settings.length_unit = 'CENTIMETERS'

        addon_prefs = context.preferences.addons[__name__].preferences
        material_name = addon_prefs.material_name
        library_path = addon_prefs.library_path
        size_threshold = addon_prefs.size_threshold
        
        # Find material in linked libraries
        material = None
        for mat in bpy.data.materials:
            if mat.name == material_name and mat.library is not None:
                material = mat
                break
        
        # Import material from library path if not found
        if not material and library_path and os.path.exists(library_path):
            try:
                with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
                    if material_name in data_from.materials:
                        data_to.materials = [material_name]
                for mat in bpy.data.materials:
                    if mat.name == material_name and mat.library is not None:
                        material = mat
                        break
            except Exception as e:
                self.report({'ERROR'}, f"Failed to import material: {str(e)}")
                return {'CANCELLED'}
        
        if not material:
            self.report({'ERROR'}, f"Material '{material_name}' not found in Asset Library")
            return {'CANCELLED'}
        
        scaled_objects = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Set object as active
                bpy.context.view_layer.objects.active = obj
                
                # Fix UV
                try:
                    bpy.ops.object.fix_uv()
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to fix UV for {obj.name}: {str(e)}")
                
                # Switch to Edit Mode for normals operations
                bpy.ops.object.mode_set(mode='EDIT')
                try:
                    # Clear custom split normals
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                    # Select all faces for normals recalculation
                    bpy.ops.mesh.select_all(action='SELECT')
                    # Recalculate normals outside
                    bpy.ops.mesh.normals_make_consistent(inside=False) #recalc normals
                    # Deselect all faces
                    bpy.ops.mesh.select_all(action='DESELECT')
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to process normals for {obj.name}: {str(e)}")

                context.scene.tool_settings.use_uv_select_sync = True
                # Switch back to Object Mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
                # Check object size (dimensions in meters, convert to cm)
                if max(obj.dimensions) < size_threshold:
                    obj.scale *= 100
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    scaled_objects += 1
                
                # Apply material
                obj.data.materials.clear()
                obj.data.materials.append(material)
                obj.data.materials[0].use_fake_user = True

        context.scene.tool_settings.use_uv_select_sync = True
        
        self.report({'INFO'}, f"Processed {len(context.selected_objects)} objects, scaled {scaled_objects}, applied '{material_name}'")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_MoxFixObject.bl_idname, text="Mox Fix Object")
    self.layout.separator()

def register():
    bpy.utils.register_class(MoxFixObjectPreferences)
    bpy.utils.register_class(OBJECT_OT_MoxFixObject)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_MoxFixObject)
    bpy.utils.unregister_class(MoxFixObjectPreferences)

if __name__ == "__main__":
    register()