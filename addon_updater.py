bl_info = {
    "name": "Addon Updater",
    "author": "Mox Alehin",
    "version": (1, 14),
    "blender": (3, 0, 0),
    "location": "Preferences > Add-ons",
    "description": "Updates local addons (folders and single .py files) with JSON config",
    "category": "Development",
}

import bpy
import os
import shutil
import sys
import importlib
import zipfile
import tempfile
import json
from bpy.types import Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, CollectionProperty
from bpy.utils import register_class, unregister_class
from datetime import datetime
from bpy_extras.io_utils import ImportHelper

class AddonFolderPath(PropertyGroup):
    path: StringProperty(
        name="Path",
        description="Path to addon folder",
        default="",
        subtype='DIR_PATH',
        update=lambda self, context: update_folder_path(self, context)
    )

class AddonFilePath(PropertyGroup):
    path: StringProperty(
        name="File Path",
        description="Path to single .py addon file",
        default="",
        subtype='FILE_PATH'
    )
    module_name: StringProperty(
        name="Module Name",
        description="Module name of the addon",
    )

def update_folder_path(self, context):
    config = load_config()
    index = next((i for i, item in enumerate(context.preferences.addons[__name__].preferences.folder_paths) if item == self), -1)
    if index >= 0:
        if len(config["folders"]) <= index:
            config["folders"].extend([""] * (index + 1 - len(config["folders"])))
        config["folders"][index] = self.path
        save_config(config["folders"], config["files"])

def get_config_path():
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(addon_dir, "addon_updater_config.json")

def load_config():
    config_path = get_config_path()
    default_config = {"folders": [], "files": []}
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not isinstance(config.get("folders"), list):
                    config["folders"] = []
                    print(f"Warning: 'folders' in config is not a list, resetting to []")
                if not isinstance(config.get("files"), list):
                    config["files"] = []
                    print(f"Warning: 'files' in config is not a list, resetting to []")
                return config
        else:
            print(f"Config file not found at {config_path}, creating new one")
            save_config([], [])
            return default_config
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON config at {config_path}: {e}")
        return default_config
    except Exception as e:
        print(f"Unexpected error loading config at {config_path}: {e}")
        return default_config

def save_config(folders, files):
    config_path = get_config_path()
    config = {"folders": folders, "files": files}
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config to {config_path}: {e}")
        raise

class ADDONUPDATER_OT_select_folder(Operator):
    bl_idname = "addonupdater.select_folder"
    bl_label = "Select Addon Folder"
    index: bpy.props.IntProperty()

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.filepath:
            absolute_path = os.path.abspath(bpy.path.abspath(self.filepath))
            user_home = os.path.expanduser("~")
            if absolute_path.startswith(user_home):
                relative_path = os.path.relpath(absolute_path, user_home)
                path = os.path.join("~", relative_path)
            else:
                path = absolute_path
            addon_paths = context.preferences.addons[__name__].preferences.folder_paths
            if len(addon_paths) > self.index:
                addon_paths[self.index].path = path
                config = load_config()
                if len(config["folders"]) <= self.index:
                    config["folders"].extend([""] * (self.index + 1 - len(config["folders"])))
                config["folders"][self.index] = path
                save_config(config["folders"], config["files"])
        return {'FINISHED'}

class ADDONUPDATER_OT_add_file(Operator, ImportHelper):
    bl_idname = "addonupdater.add_file"
    bl_label = "Add Single-File Addon"
    bl_description = "Add a .py addon file to track for updates"

    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})

    def execute(self, context):
        if self.filepath:
            absolute_path = os.path.abspath(self.filepath)
            user_home = os.path.expanduser("~")
            if absolute_path.startswith(user_home):
                relative_path = os.path.relpath(absolute_path, user_home)
                path = os.path.join("~", relative_path)
            else:
                path = absolute_path
            module_name = os.path.splitext(os.path.basename(self.filepath))[0]
            preferences = context.preferences.addons[__name__].preferences
            item = preferences.file_paths.add()
            item.path = path
            item.module_name = module_name
            config = load_config()
            config["files"].append({"path": path, "module_name": module_name})
            save_config(config["folders"], config["files"])
        return {'FINISHED'}

class ADDONUPDATER_OT_add_folder_path(Operator):
    bl_idname = "addonupdater.add_folder_path"
    bl_label = "Add Addon Folder"

    def execute(self, context):
        context.preferences.addons[__name__].preferences.folder_paths.add()
        config = load_config()
        config["folders"].append("")
        save_config(config["folders"], config["files"])
        return {'FINISHED'}

class ADDONUPDATER_OT_remove_folder_path(Operator):
    bl_idname = "addonupdater.remove_folder_path"
    bl_label = "Remove Addon Folder"
    index: bpy.props.IntProperty()

    def execute(self, context):
        context.preferences.addons[__name__].preferences.folder_paths.remove(self.index)
        config = load_config()
        if 0 <= self.index < len(config["folders"]):
            config["folders"].pop(self.index)
            save_config(config["folders"], config["files"])
        return {'FINISHED'}

class ADDONUPDATER_OT_remove_file_path(Operator):
    bl_idname = "addonupdater.remove_file_path"
    bl_label = "Remove Addon File"
    index: bpy.props.IntProperty()

    def execute(self, context):
        context.preferences.addons[__name__].preferences.file_paths.remove(self.index)
        config = load_config()
        if 0 <= self.index < len(config["files"]):
            config["files"].pop(self.index)
            save_config(config["folders"], config["files"])
        return {'FINISHED'}

class ADDONUPDATER_OT_update_addons(Operator):
    bl_idname = "addonupdater.update_addons"
    bl_label = "Update All Addons"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        addons_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), 'addons')
        updated_addons = []
        errors = []

        for addon_path in preferences.folder_paths:
            expanded_path = os.path.expanduser(addon_path.path)
            if not os.path.exists(expanded_path):
                errors.append(f"Folder not found: {expanded_path}")
                continue

            addon_name = os.path.basename(expanded_path)
            installed_path = os.path.join(addons_dir, addon_name)
            addon_exists = os.path.exists(installed_path)

            try:
                src_mtime = max(os.path.getmtime(os.path.join(root, f))
                               for root, _, files in os.walk(expanded_path)
                               for f in files if f.endswith('.py') and '.git' not in root)
            except ValueError:
                errors.append(f"No .py files found in {expanded_path}")
                continue

            dst_mtime = 0
            if addon_exists:
                try:
                    dst_mtime = max(os.path.getmtime(os.path.join(root, f))
                                   for root, _, files in os.walk(installed_path)
                                   for f in files if f.endswith('.py') and '.git' not in root)
                except ValueError:
                    dst_mtime = 0

            if not addon_exists or src_mtime > dst_mtime:
                temp_dir = tempfile.gettempdir()
                zip_path = os.path.join(temp_dir, f"{addon_name}.zip")
                try:
                    if addon_name in sys.modules:
                        module = sys.modules[addon_name]
                        if hasattr(module, 'unregister'):
                            print(f"Unregistering folder addon: {addon_name}")
                            module.unregister()
                        for module_name in list(sys.modules.keys()):
                            if module_name.startswith(addon_name):
                                del sys.modules[module_name]

                    if addon_exists and addon_name in bpy.context.preferences.addons:
                        print(f"Disabling folder addon: {addon_name}")
                        bpy.ops.preferences.addon_disable(module=addon_name)

                    print(f"Zipping folder addon: {expanded_path}")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(expanded_path):
                            if '.git' in root:
                                continue
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, expanded_path)
                                zipf.write(file_path, os.path.join(addon_name, arcname))

                    print(f"Installing folder addon: {addon_name}")
                    bpy.ops.preferences.addon_install(
                        overwrite=True,
                        filepath=zip_path,
                        target='DEFAULT'
                    )
                    print(f"Enabling folder addon: {addon_name}")
                    bpy.ops.preferences.addon_enable(module=addon_name)
                    updated_addons.append(addon_name)

                except Exception as e:
                    errors.append(f"Error updating folder addon {addon_name}: {e}")
                finally:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)

        for item in preferences.file_paths:
            expanded_path = os.path.expanduser(item.path)
            module_name = item.module_name
            if not os.path.isfile(expanded_path):
                errors.append(f"File not found: {expanded_path}")
                continue

            installed_path = os.path.join(addons_dir, f"{module_name}.py")
            local_mtime = os.path.getmtime(expanded_path)
            installed_mtime = os.path.getmtime(installed_path) if os.path.isfile(installed_path) else 0

            if local_mtime > installed_mtime:
                try:
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        if hasattr(module, 'unregister'):
                            print(f"Unregistering single-file addon: {module_name}")
                            module.unregister()
                        del sys.modules[module_name]

                    if module_name in bpy.context.preferences.addons:
                        print(f"Disabling single-file addon: {module_name}")
                        bpy.ops.preferences.addon_disable(module=module_name)

                    if os.path.isfile(installed_path):
                        os.remove(installed_path)

                    print(f"Copying single-file addon: {expanded_path}")
                    shutil.copy(expanded_path, installed_path)
                    print(f"Enabling single-file addon: {module_name}")
                    bpy.ops.preferences.addon_enable(module=module_name)
                    updated_addons.append(module_name)

                except Exception as e:
                    errors.append(f"Error updating single-file addon {module_name}: {e}")

        if updated_addons:
            self.report({'INFO'}, f"Updated addons: {', '.join(updated_addons)}")
        if errors:
            self.report({'WARNING'}, "\n".join(errors))
        elif not updated_addons:
            self.report({'INFO'}, "No addons updated")
        return {'FINISHED'}

class ADDONUPDATER_Preferences(AddonPreferences):
    bl_idname = __name__

    folder_paths: CollectionProperty(type=AddonFolderPath)
    file_paths: CollectionProperty(type=AddonFilePath)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Addon Folder Paths:")
        try:
            # Load config and sync with UI
            config = load_config()
            self.folder_paths.clear()
            for folder in config["folders"]:
                item = self.folder_paths.add()
                item.path = folder
            self.file_paths.clear()
            for file in config["files"]:
                item = self.file_paths.add()
                item.path = file.get("path", "")
                item.module_name = file.get("module_name", "")
        except Exception as e:
            print(f"Error syncing config with UI: {e}")
            layout.label(text="Error loading configuration", icon="ERROR")

        for i, addon_path in enumerate(self.folder_paths):
            row = layout.row()
            row.label(text=os.path.basename(os.path.expanduser(addon_path.path)) or "Unnamed Addon")
            row.prop(addon_path, "path", text="")
            row.operator("addonupdater.remove_folder_path", text="", icon="X").index = i

        layout.label(text="Single-File Addon Paths:")
        for i, item in enumerate(self.file_paths):
            row = layout.row()
            row.label(text=item.module_name or "Unnamed Addon")
            row.prop(item, "path", text="")
            row.operator("addonupdater.remove_file_path", text="", icon="X").index = i

        row = layout.row()
        row.operator("addonupdater.add_folder_path", text="Project", icon="ADD")
        row.operator("addonupdater.add_file", text="Script", icon="ADD")
        row.operator("addonupdater.update_addons", text="Update", icon="FILE_REFRESH")

addon_keymaps = []

def register():
    register_class(AddonFolderPath)
    register_class(AddonFilePath)
    register_class(ADDONUPDATER_OT_select_folder)
    register_class(ADDONUPDATER_OT_add_file)
    register_class(ADDONUPDATER_OT_add_folder_path)
    register_class(ADDONUPDATER_OT_remove_folder_path)
    register_class(ADDONUPDATER_OT_remove_file_path)
    register_class(ADDONUPDATER_OT_update_addons)
    register_class(ADDONUPDATER_Preferences)

    if not os.path.exists(get_config_path()):
        save_config([], [])

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km.keymap_items.new("addonupdater.update_addons", 'U', 'PRESS', ctrl=True, alt=True, shift=True)
    addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    unregister_class(ADDONUPDATER_Preferences)
    unregister_class(ADDONUPDATER_OT_update_addons)
    unregister_class(ADDONUPDATER_OT_remove_file_path)
    unregister_class(ADDONUPDATER_OT_remove_folder_path)
    unregister_class(ADDONUPDATER_OT_add_folder_path)
    unregister_class(ADDONUPDATER_OT_add_file)
    unregister_class(ADDONUPDATER_OT_select_folder)
    unregister_class(AddonFilePath)
    unregister_class(AddonFolderPath)

if __name__ == "__main__":
    register()