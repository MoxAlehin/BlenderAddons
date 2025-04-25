bl_info = {
    "name": "Fix UV Plugin",
    "author": "Your Name",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Tools > Fix UV, Object Context Menu",
    "description": "Fixes UV channels for selected mesh objects, keeping Unwrap and Gradients at the top",
    "category": "UV"
}

import bpy
import bmesh
from bpy.types import Operator, Panel
from math import radians

class OBJECT_OT_FixUV(Operator):
    bl_idname = "object.fix_uv"
    bl_label = "Fix UV"
    bl_description = "Fix UV channels for selected objects, keeping Unwrap and Gradients at the top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        for obj in selected_objects:
            # Снимаем выделение со всех объектов                
            for o in selected_objects:
                o.select_set(False)
            # Выделяем только текущий объект
            obj.select_set(True)
            context.view_layer.objects.active = obj

            bpy.ops.object.mode_set(mode='OBJECT')
            uv_layers = obj.data.uv_layers

            # Проверяем наличие Unwrap и Gradients
            unwrap_exists = any(layer.name == "Unwrap" for layer in uv_layers)
            gradients_exists = any(layer.name == "Gradients" for layer in uv_layers)
            gradients_is_render = any(layer.name == "Gradients" and layer.active_render for layer in uv_layers)

            # Если Unwrap и Gradients существуют, в правильном порядке и Gradients активен для рендера
            if unwrap_exists and gradients_exists and gradients_is_render and \
               uv_layers[0].name == "Unwrap" and uv_layers[1].name == "Gradients":
                uv_layers.active_index = 1  # Устанавливаем Gradients для отображения
                continue

            # Сохраняем данные первого UV-канала, если он есть
            first_uv_data = None
            if len(uv_layers) > 0:
                first_uv_data = [(uv.uv[0], uv.uv[1]) for uv in uv_layers[0].data]

            # Создаем или настраиваем каналы
            if len(uv_layers) == 0:
                # Нет UV-каналов: создаем Unwrap и Gradients
                unwrap_layer = uv_layers.new(name="Unwrap")
                gradients_layer = uv_layers.new(name="Gradients")
            else:
                # Есть UV-каналы
                if not unwrap_exists:
                    # Создаем Unwrap в начале
                    unwrap_layer = uv_layers.new(name="Unwrap")
                    if first_uv_data:
                        for i, uv_coord in enumerate(first_uv_data):
                            unwrap_layer.data[i].uv = uv_coord
                else:
                    unwrap_layer = next(layer for layer in uv_layers if layer.name == "Unwrap")

                if not gradients_exists:
                    # Переименовываем первый канал в Gradients
                    uv_layers[0].name = "Gradients"
                    gradients_layer = uv_layers[0]
                else:
                    gradients_layer = next(layer for layer in uv_layers if layer.name == "Gradients")

            # Перестраиваем порядок: Unwrap первый, Gradients второй
            temp_uv_data = {layer.name: [(uv.uv[0], uv.uv[1]) for uv in layer.data] for layer in uv_layers}
            temp_names = [layer.name for layer in uv_layers]
            # Очищаем UV-каналы
            while len(uv_layers) > 0:
                uv_layers.remove(uv_layers[0])

            # Создаем каналы в нужном порядке
            unwrap_layer = uv_layers.new(name="Unwrap")
            if "Unwrap" in temp_uv_data:
                for i, uv_coord in enumerate(temp_uv_data["Unwrap"]):
                    unwrap_layer.data[i].uv = uv_coord
            elif first_uv_data:
                for i, uv_coord in enumerate(first_uv_data):
                    unwrap_layer.data[i].uv = uv_coord

            gradients_layer = uv_layers.new(name="Gradients")
            if "Gradients" in temp_uv_data:
                for i, uv_coord in enumerate(temp_uv_data["Gradients"]):
                    gradients_layer.data[i].uv = uv_coord
            elif first_uv_data:
                for i, uv_coord in enumerate(first_uv_data):
                    gradients_layer.data[i].uv = uv_coord

            # Восстанавливаем остальные каналы
            for name in temp_names:
                if name not in ["Unwrap", "Gradients"]:
                    new_layer = uv_layers.new(name=name)
                    if name in temp_uv_data:
                        for i, uv_coord in enumerate(temp_uv_data[name]):
                            new_layer.data[i].uv = uv_coord

            # Устанавливаем active_render: отключаем для всех, кроме Gradients
            for layer in uv_layers:
                layer.active_render = (layer.name == "Gradients")

            # Переключаемся в режим редактирования
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Smart UV Project для Unwrap
            bpy.context.scene.tool_settings.use_uv_select_sync = False
            uv_layers.active_index = 0  # Unwrap (первый)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=radians(66))
            
            # Возвращаемся в режим объекта
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Устанавливаем активный UV канал на Gradients для отображения
            uv_layers.active_index = 1  # Gradients (второй)

        # Восстанавливаем исходное выделение
        for o in selected_objects:
            o.select_set(True)

        self.report({'INFO'}, f"Processed {len(selected_objects)} objects")
        return {'FINISHED'}

class VIEW3D_PT_FixUVPanel(Panel):
    bl_label = "Fix UV"
    bl_idname = "VIEW3D_PT_fix_uv"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.fix_uv")

def context_menu_func(self, context):
    self.layout.operator("object.fix_uv")
    self.layout.separator()

def register():
    bpy.utils.register_class(OBJECT_OT_FixUV)
    bpy.utils.register_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(context_menu_func)
    bpy.types.VIEW3D_MT_object.append(context_menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_FixUV)
    bpy.utils.unregister_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object_context_menu.remove(context_menu_func)
    bpy.types.VIEW3D_MT_object.remove(context_menu_func)

if __name__ == "__main__":
    register()