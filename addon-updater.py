import bpy
import os
import shutil
import json
from bpy.types import Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper

# Класс для хранения информации об отслеживаемом плагине
class AddonUpdaterItem(PropertyGroup):
    path: StringProperty(
        name="File Path",
        description="Path to the local .py file",
        subtype='FILE_PATH'
    )
    module_name: StringProperty(
        name="Module Name",
        description="Module name of the addon",
    )

# Получение пути к JSON-файлу конфигурации
def get_config_path():
    addon_dir = os.path.dirname(__file__)
    return os.path.join(addon_dir, "addon_updater_config.json")

# Чтение конфигурации из JSON
def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Сохранение конфигурации в JSON
def save_config(addons):
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(addons, f, indent=4)

# Оператор для добавления нового плагина в список отслеживания
class ADDON_UPDATER_OT_AddAddon(Operator, ImportHelper):
    bl_idname = "addon_updater.add_addon"
    bl_label = "Add Addon"
    bl_description = "Add a .py addon file to track for updates"

    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})

    def execute(self, context):
        addons = load_config()
        new_addon = {
            "path": self.filepath,
            "module_name": os.path.splitext(os.path.basename(self.filepath))[0]
        }
        addons.append(new_addon)
        save_config(addons)
        # Обновляем временную коллекцию для UI
        preferences = context.preferences.addons[__name__].preferences
        preferences.addons.clear()
        for addon in addons:
            item = preferences.addons.add()
            item.path = addon["path"]
            item.module_name = addon["module_name"]
        return {'FINISHED'}

# Оператор для удаления плагина из списка отслеживания
class ADDON_UPDATER_OT_RemoveAddon(Operator):
    bl_idname = "addon_updater.remove_addon"
    bl_label = "Remove Addon"
    bl_description = "Remove an addon from the tracking list"

    index: bpy.props.IntProperty()

    def execute(self, context):
        addons = load_config()
        if 0 <= self.index < len(addons):
            addons.pop(self.index)
            save_config(addons)
        # Обновляем временную коллекцию для UI
        preferences = context.preferences.addons[__name__].preferences
        preferences.addons.clear()
        for addon in addons:
            item = preferences.addons.add()
            item.path = addon["path"]
            item.module_name = addon["module_name"]
        return {'FINISHED'}

# Оператор для обновления всех отслеживаемых плагинов
class ADDON_UPDATER_OT_UpdatePlugins(Operator):
    bl_idname = "addon_updater.update_plugins"
    bl_label = "Update Plugins"
    bl_description = "Check and update tracked addons if newer versions are available"

    def execute(self, context):
        addons = load_config()
        addons_dir = bpy.utils.user_resource('SCRIPTS', path="addons")
        updated_count = 0
        errors = []

        for item in addons:
            local_path = item["path"]
            module_name = item["module_name"]

            # Проверка существования локального файла
            if not os.path.isfile(local_path):
                errors.append(f"File not found: {local_path}")
                continue

            # Получение даты модификации локального файла
            local_mtime = os.path.getmtime(local_path)

            # Проверка установленной версии
            installed_path = os.path.join(addons_dir, f"{module_name}.py")
            installed_mtime = 0
            if os.path.isfile(installed_path):
                installed_mtime = os.path.getmtime(installed_path)

            # Если локальный файл новее, обновляем
            if local_mtime > installed_mtime:
                try:
                    # Деактивировать плагин, если он активен
                    if module_name in context.preferences.addons:
                        bpy.ops.preferences.addon_disable(module=module_name)

                    # Удалить старую версию
                    if os.path.isfile(installed_path):
                        os.remove(installed_path)

                    # Копировать новую версию
                    shutil.copy(local_path, installed_path)

                    # Активировать плагин
                    bpy.ops.preferences.addon_enable(module=module_name)
                    updated_count += 1
                    self.report({'INFO'}, f"Updated addon: {module_name}")
                except Exception as e:
                    errors.append(f"Failed to update {module_name}: {str(e)}")

        # Сообщение о результате
        if updated_count > 0:
            self.report({'INFO'}, f"Updated {updated_count} addon(s)")
        if errors:
            self.report({'WARNING'}, "\n".join(errors))
        if updated_count == 0 and not errors:
            self.report({'INFO'}, "No updates needed")

        return {'FINISHED'}

# Настройки аддона
class AddonUpdaterPreferences(AddonPreferences):
    bl_idname = __name__

    addons: CollectionProperty(type=AddonUpdaterItem)
    auto_update: BoolProperty(
        name="Auto Update on File Open",
        description="Automatically check for updates when opening a new file",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "auto_update")

        # Загружаем конфигурацию и синхронизируем с UI
        addons = load_config()
        self.addons.clear()
        for addon in addons:
            item = self.addons.add()
            item.path = addon["path"]
            item.module_name = addon["module_name"]

        box = layout.box()
        box.label(text="Tracked Addons:")
        for i, item in enumerate(self.addons):
            row = box.row()
            row.prop(item, "path", text="Path")
            row.prop(item, "module_name", text="Module")
            op = row.operator("addon_updater.remove_addon", text="", icon="X")
            op.index = i

        layout.operator("addon_updater.add_addon", text="Add Addon")
        layout.operator("addon_updater.update_plugins", text="Update All Addons")

# Обработчик для автоматического обновления при открытии файла
def handle_file_open(dummy):
    preferences = bpy.context.preferences.addons[__name__].preferences
    if preferences.auto_update:
        bpy.ops.addon_updater.update_plugins()

# Регистрация классов и горячей клавиши
def register():
    bpy.utils.register_class(AddonUpdaterItem)
    bpy.utils.register_class(ADDON_UPDATER_OT_AddAddon)
    bpy.utils.register_class(ADDON_UPDATER_OT_RemoveAddon)
    bpy.utils.register_class(ADDON_UPDATER_OT_UpdatePlugins)
    bpy.utils.register_class(AddonUpdaterPreferences)

    # Загружаем конфигурацию при регистрации
    preferences = bpy.context.preferences.addons.get(__name__)
    if preferences:
        addons = load_config()
        preferences = preferences.preferences
        preferences.addons.clear()
        for addon in addons:
            item = preferences.addons.add()
            item.path = addon["path"]
            item.module_name = addon["module_name"]

    # Регистрация горячей клавиши
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            "addon_updater.update_plugins",
            type='U',
            value='PRESS',
            ctrl=True,
            shift=True,
            alt=True
        )

    # Регистрация обработчика открытия файла
    bpy.app.handlers.load_post.append(handle_file_open)

def unregister():
    # Удаление обработчика
    if handle_file_open in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(handle_file_open)

    # Удаление горячей клавиши
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if kmi.idname == "addon_updater.update_plugins":
                    km.keymap_items.remove(kmi)

    bpy.utils.unregister_class(AddonUpdaterPreferences)
    bpy.utils.unregister_class(ADDON_UPDATER_OT_UpdatePlugins)
    bpy.utils.unregister_class(ADDON_UPDATER_OT_RemoveAddon)
    bpy.utils.unregister_class(ADDON_UPDATER_OT_AddAddon)
    bpy.utils.unregister_class(AddonUpdaterItem)

if __name__ == "__main__":
    register()

# Метаданные аддона
bl_info = {
    "name": "Local Addon Updater",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "Preferences > Add-ons",
    "description": "Tracks and updates local .py addons based on file modification time with JSON config",
    "category": "System",
}