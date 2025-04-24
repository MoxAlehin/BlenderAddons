bl_info = {
    "name": "Mox Low Poly",
    "description": "Automatically adds custom linear color properties to selected new mesh objects",
    "author": "Mox Alehin",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "category": "Object",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons",
}

import bpy
from bpy.app.handlers import persistent

# Определяем custom properties для цветов (float array, linear color)
CUSTOM_PROPERTIES = {
    "Color 1": {
        "type": "FLOAT",
        "subtype": "COLOR",
        "default": [0.5, 0.5, 0.5, 1.0],  # RGBA, серый цвет
        "min": 0.0,
        "max": 1.0,
        "description": "First linear color for low poly material",
        "size": 4  # Размер массива для RGBA
    },
    "Color 2": {
        "type": "FLOAT",
        "subtype": "COLOR",
        "default": [1.0, 0.0, 0.0, 1.0],  # RGBA, красный цвет
        "min": 0.0,
        "max": 1.0,
        "description": "Second linear color for low poly material",
        "size": 4
    },
    "Color 3": {
        "type": "FLOAT",
        "subtype": "COLOR",
        "default": [0.0, 1.0, 0.0, 1.0],  # RGBA, зелёный цвет
        "min": 0.0,
        "max": 1.0,
        "description": "Third linear color for low poly material",
        "size": 4
    },
    "Color 4": {
        "type": "FLOAT",
        "subtype": "COLOR",
        "default": [0.0, 0.0, 1.0, 1.0],  # RGBA, синий цвет
        "min": 0.0,
        "max": 1.0,
        "description": "Fourth linear color for low poly material",
        "size": 4
    }
}

@persistent
def add_custom_properties_to_new_object(scene):
    # Проверяем только выделенные объекты
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':  # Применяем только к мешам
            continue
        # Проверяем и добавляем custom properties
        for prop_name, prop_settings in CUSTOM_PROPERTIES.items():
            if prop_name not in obj:
                # Добавляем custom property как массив
                obj[prop_name] = prop_settings["default"]
                # Настраиваем параметры свойства
                prop = obj.id_properties_ui(prop_name)
                prop.update(
                    subtype="COLOR",
                    min=prop_settings["min"],
                    max=prop_settings["max"],
                    soft_min=prop_settings["min"],
                    soft_max=prop_settings["max"],
                    default=prop_settings["default"],
                    description=prop_settings["description"]
                )

class MoxLowPolyPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="This addon adds custom linear color properties (Color 1-4) to selected new mesh objects.")

def register():
    bpy.utils.register_class(MoxLowPolyPreferences)
    if add_custom_properties_to_new_object not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(add_custom_properties_to_new_object)

def unregister():
    if add_custom_properties_to_new_object in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(add_custom_properties_to_new_object)
    bpy.utils.unregister_class(MoxLowPolyPreferences)

if __name__ == "__main__":
    register()