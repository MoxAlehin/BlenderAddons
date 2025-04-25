bl_info = {
    "name": "Mox Fix Object",
    "author": "Your Name",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "Object Context Menu",
    "description": "Fixes UV, scales small objects based on scene units, and applies a material from Asset Library",
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
        description="Objects smaller than this size will be scaled up by 100x (1 cm = 0.01 m)",
        default=1,
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
        # Устанавливаем Unit Scale (например, 0.01 для сантиметров в метрах)
        context.scene.unit_settings.scale_length = 0.01
        context.scene.unit_settings.length_unit = 'CENTIMETERS'

        addon_prefs = context.preferences.addons[__name__].preferences
        material_name = addon_prefs.material_name
        library_path = addon_prefs.library_path
        size_threshold = addon_prefs.size_threshold
        
        # Проверяем единицы измерения сцены
        unit_system = context.scene.unit_settings.length_unit
        # Порог всегда в метрах (0.01 м = 1 см)
        effective_threshold = size_threshold  # 0.01 м по умолчанию
        
        # Ищем материал среди всех материалов, проверяя связь с библиотекой
        material = None
        for mat in bpy.data.materials:
            if mat.name == material_name and mat.library is not None:
                material = mat
                break
        
        # Если материал не найден и указан путь к библиотеке, пробуем импортировать
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
                # Вызываем fix_uv для нормализации UV
                try:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.fix_uv()
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to fix UV for {obj.name}: {str(e)}")
                
                # Проверяем размеры объекта (obj.dimensions в метрах)
                max_dimension = max(obj.dimensions)
                # Для отладки: выводим размер объекта и порог
                print(f"Object {obj.name}: max_dimension={max_dimension} m, threshold={effective_threshold} m")

                # Сравниваем размеры в метрах
                if max_dimension < effective_threshold:
                    obj.scale *= 100
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    scaled_objects += 1
                    print(f"Scaled object {obj.name} by 100x")
                
                # Применяем материал
                obj.data.materials.clear()
                obj.data.materials.append(material)
                obj.data.materials[0].use_fake_user = True
        
        self.report({'INFO'}, f"Processed {len(context.selected_objects)} objects, scaled {scaled_objects}, applied '{material_name}'")
        return {'FINISHED'}

def menu_func(self, context):
    print("Adding Mox Fix Object to context menu")  # Отладка
    self.layout.operator(OBJECT_OT_MoxFixObject.bl_idname, text="Mox Fix Object")
    self.layout.separator()

def register():
    bpy.utils.register_class(MoxFixObjectPreferences)
    bpy.utils.register_class(OBJECT_OT_MoxFixObject)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_func)
    print("Mox Fix Object addon registered")  # Отладка

def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_MoxFixObject)
    bpy.utils.unregister_class(MoxFixObjectPreferences)
    print("Mox Fix Object addon unregistered")  # Отладка

if __name__ == "__main__":
    register()