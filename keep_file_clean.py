bl_info = {
    "name": "Keep File Clean",
    "description": "Cleans up unused data blocks, renames numbered materials, and removes blender_assets.cats.txt~ on save",
    "author": "Mox Alehin",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "category": "System",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons/tree/master?tab=readme-ov-file#multi-import",
}

import bpy
import re
import os
from bpy.app.handlers import persistent

@persistent
def recursive_cleanup_handler(dummy):
    renamed_count = rename_numbered_materials()
    cleaned_count = recursive_cleanup()
    message = []
    if renamed_count > 0:
        message.append(f"Renamed {renamed_count} materials")
    if cleaned_count > 0:
        message.append(f"Cleaned up {cleaned_count} unused data blocks")
    
    if message:
        message_text = ", ".join(message)
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message_text),
            title="Cleanup Report",
            icon='INFO'
        )

@persistent
def remove_cats_backup(scene):
    def delayed_remove():
        blend_file = bpy.data.filepath
        if not blend_file:
            return 0.0
        blend_dir = os.path.dirname(blend_file)
        cats_file = os.path.join(blend_dir, "blender_assets.cats.txt~")
        if os.path.exists(cats_file):
            try:
                os.remove(cats_file)
                print(f"Removed {cats_file}")
            except Exception as e:
                print(f"Error removing {cats_file}: {e}")
        return 0.0
    bpy.app.timers.register(delayed_remove, first_interval=0.1)

def rename_numbered_materials():
    count = 0
    pattern = r'\.\d{3}$'
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
            
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                material = mat_slot.material
                if re.search(pattern, material.name):
                    new_name = re.sub(pattern, '', material.name) + '_' + obj.name
                    if new_name not in bpy.data.materials:
                        material.name = new_name
                        count += 1    
    return count

def recursive_cleanup():
    categories = [
        "meshes", "objects", "materials", "textures", "images",
        "brushes", "scenes", "worlds", "paint_curves", "fonts", "grease_pencils",
        "collections", "masks", "movieclips", "sounds", "actions", "node_groups",
        "linestyles"
    ]
    initial_count = sum(len(getattr(bpy.data, cat)) for cat in categories)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    final_count = sum(len(getattr(bpy.data, cat)) for cat in categories)
    cleaned_count = initial_count - final_count
    return cleaned_count

class CleanupOnSavePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="This addon cleans up unused data blocks, renames numbered materials, and removes blender_assets.cats.txt~ on save.")

def register():
    bpy.utils.register_class(CleanupOnSavePreferences)
    if recursive_cleanup_handler not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(recursive_cleanup_handler)
    if remove_cats_backup not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(remove_cats_backup)

def unregister():
    if recursive_cleanup_handler in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(recursive_cleanup_handler)
    if remove_cats_backup in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(remove_cats_backup)
    bpy.utils.unregister_class(CleanupOnSavePreferences)

if __name__ == "__main__":
    register()