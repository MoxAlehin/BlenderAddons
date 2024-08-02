import bpy
import os

bl_info = {
    "name": "Mox Export",
    "description": "Export selected objects to FBX in the same directory as the .blend file",
    "author": "Mox Alehin",
    "blender": (2, 80, 0),
    "version": (1, 2),
    "category": "Import-Export",
    "doc-url": "https://github.com/MoxAlehin/Blender-Addons",
    "location": "File > Export",
}

class ExportSelectedToFBX(bpy.types.Operator):
    """Export selected objects to FBX in the same directory as the .blend file"""
    bl_idname = "export_scene.selected_to_fbx"
    bl_label = "Export Selected to FBX"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    
    def execute(self, context):

        # Get the current .blend file path
        blend_filepath = bpy.data.filepath

        # Check if the file is saved
        if not blend_filepath:
            self.report({'ERROR'}, "The current .blend file has not been saved yet.")
            return {'CANCELLED'}
        
        # Get the directory and file name without extension
        blend_dir = os.path.dirname(blend_filepath)
        blend_name = os.path.splitext(os.path.basename(blend_filepath))[0]
        
        selected_objects = bpy.context.selected_objects
        if len(selected_objects) == 1:
            fbx_name = selected_objects[0].name
        else:
            fbx_name = blend_name

        # Form the path to save the .fbx file
        fbx_filepath = os.path.join(blend_dir, fbx_name + ".fbx")

        # Export selected objects to FBX
        bpy.ops.export_scene.fbx(
            filepath=fbx_filepath,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            use_space_transform=True,
            bake_space_transform=False,
            use_mesh_modifiers=True,
            use_mesh_modifiers_render=True,
            mesh_smooth_type='FACE',
            colors_type='SRGB',
            prioritize_active_color=False,
            use_subsurf=False,
            use_mesh_edges=False,
            use_tspace=False,
            use_triangles=False,
            use_custom_props=True,
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            use_armature_deform_only=True,
            armature_nodetype='NULL',
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=True,
            bake_anim_use_all_actions=True,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=1.0,
            embed_textures=False,
            batch_mode='OFF',
            use_batch_own_dir=True,
            axis_forward='-Z',
            axis_up='Y'
        )

        self.report({'INFO'}, f"Selected objects exported to: {fbx_filepath}")
        return {'FINISHED'}

# Register the operator
def menu_func(self, context):
    self.layout.operator(ExportSelectedToFBX.bl_idname)

addon_keymaps = []

def register():
    bpy.utils.register_class(ExportSelectedToFBX)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

    # Register hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(ExportSelectedToFBX.bl_idname, 'S', 'PRESS', ctrl=True, shift=True, alt=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(ExportSelectedToFBX)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

    # Remove hotkey
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
