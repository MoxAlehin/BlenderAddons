import bpy
import os
from bpy.types import AddonPreferences
from bpy.props import StringProperty

bl_info = {
    "name": "Startup Project",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Preferences > Add-ons",
    "description": "Opens a specified .blend file on Blender startup if valid",
    "category": "System",
}

class StartupProjectPreferences(AddonPreferences):
    bl_idname = __name__

    project_filepath: StringProperty(
        name="Project File Path",
        description="Path to the .blend file to open on startup",
        subtype='FILE_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "project_filepath")

def open_project_file():
    prefs = bpy.context.preferences.addons[__name__].preferences
    filepath = prefs.project_filepath

    if filepath and os.path.exists(filepath) and filepath.endswith(".blend"):
        try:
            bpy.ops.wm.open_mainfile(filepath=filepath)
        except Exception as e:
            print(f"Startup Project: Failed to open file {filepath}. Error: {e}")
    else:
        print(f"Startup Project: Invalid or missing file path: {filepath}")

def register():
    bpy.utils.register_class(StartupProjectPreferences)
    bpy.app.timers.register(open_project_file, first_interval=0.1)

def unregister():
    bpy.utils.unregister_class(StartupProjectPreferences)

if __name__ == "__main__":
    register()