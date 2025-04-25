bl_info = {
    "name": "Fix UV Plugin",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Tools > Fix UV",
    "description": "Fixes UV channels for selected mesh objects",
    "category": "UV"
}

import bpy
import bmesh
from bpy.types import Operator, Panel
from math import radians

class OBJECT_OT_FixUV(Operator):
    bl_idname = "object.fix_uv"
    bl_label = "Fix UV"
    bl_description = "Fix UV channels for selected objects"
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
            bpy.ops.object.mode_set(mode='OBJECT')
            uv_layers = obj.data.uv_layers

            # Проверяем UV каналы
            if len(uv_layers) == 2 and \
               uv_layers[0].name == "Unwrap" and \
               uv_layers[1].name == "Gradients" and \
               uv_layers[1].active_render:
                # Если всё уже настроено, просто устанавливаем Gradients активным для отображения
                uv_layers.active_index = 1
                continue

            # Очищаем UV каналы и создаем новые
            if len(uv_layers) > 0:
                first_uv = uv_layers[0]
                first_uv_data = [(uv.uv[0], uv.uv[1]) for uv in first_uv.data]
                
                while len(uv_layers) > 0:
                    uv_layers.remove(uv_layers[0])
                
                unwrap_layer = uv_layers.new(name="Unwrap")
                for i, uv_data in enumerate(first_uv_data):
                    unwrap_layer.data[i].uv = uv_data
                
                gradients_layer = uv_layers.new(name="Gradients")
                for i, uv_data in enumerate(first_uv_data):
                    gradients_layer.data[i].uv = uv_data
            else:
                unwrap_layer = uv_layers.new(name="Unwrap")
                gradients_layer = uv_layers.new(name="Gradients")

            # Явно отключаем active_render для Unwrap и включаем для Gradients
            unwrap_layer.active_render = False
            gradients_layer.active_render = True

            # Переключаемся в режим редактирования
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Smart UV Project для Unwrap
            bpy.context.scene.tool_settings.use_uv_select_sync = False
            uv_layers.active_index = 0  # Unwrap
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=radians(66))
            
            # Возвращаемся в режим объекта
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Устанавливаем активный UV канал на Gradients для отображения
            uv_layers.active_index = 1  # Gradients

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

def menu_func(self, context):
    self.layout.operator("object.fix_uv")

def register():
    bpy.utils.register_class(OBJECT_OT_FixUV)
    bpy.utils.register_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_FixUV)
    bpy.utils.unregister_class(VIEW3D_PT_FixUVPanel)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()