bl_info = {
    "name": "Keep File Clean",
    "description": "Cleans up unused data blocks on save and renames numbered materials",
    "author": "Mox Alehin",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "category": "System",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons/tree/master?tab=readme-ov-file#multi-import",
}

import bpy
import re
from bpy.app.handlers import persistent

@persistent
def recursive_cleanup_handler(dummy):
    # Сначала переименовываем материалы
    renamed_count = rename_numbered_materials()
    # Затем выполняем очистку
    cleaned_count = recursive_cleanup()
    # Формируем сообщение для popup
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

def rename_numbered_materials():
    count = 0
    # Регулярное выражение для поиска .XXX в конце имени
    pattern = r'\.\d{3}$'
    
    # Проходим по всем выделенным объектам
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
            
        # Проходим по всем материалам объекта
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                material = mat_slot.material
                # Проверяем, соответствует ли имя материала шаблону
                if re.search(pattern, material.name):
                    # Формируем новое имя: убираем .XXX и добавляем имя объекта
                    new_name = re.sub(pattern, '', material.name) + '_' + obj.name
                    # Проверяем, нет ли уже материала с таким именем
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
        layout.label(text="This addon cleans up unused data blocks and renames numbered materials on save.")

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