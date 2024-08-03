bl_info = {
    "name": "Keep File Clean",
    "description": "Cleans up unused data blocks on save",
    "author": "Mox Alehin",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "category": "System",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons/tree/master?tab=readme-ov-file#multi-import",
}

import bpy
from bpy.app.handlers import persistent

@persistent
def recursive_cleanup_handler(dummy):
    cleaned_count = recursive_cleanup()
    if cleaned_count > 0:
        bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=f"Cleaned up {cleaned_count} unused data blocks"), title="Cleanup Report", icon='INFO')

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
        layout.label(text="This addon cleans up unused data blocks on save.")

def register():
    bpy.utils.register_class(CleanupOnSavePreferences)
    if recursive_cleanup_handler not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(recursive_cleanup_handler)

def unregister():
    if recursive_cleanup_handler in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(recursive_cleanup_handler)
    bpy.utils.unregister_class(CleanupOnSavePreferences)

if __name__ == "__main__":
    register()
