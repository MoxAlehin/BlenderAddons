bl_info = {
    "name": "Unlink Asset",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Right-Click Context Menu",
    "description": "Adds Library Override option to context menu for linked objects",
    "warning": "",
    "category": "Object",
}

import bpy
from bpy.types import Operator, Menu

class OBJECT_OT_ApplyLibraryOverride(Operator):
    """Apply Library Override to linked objects"""
    bl_idname = "object.apply_library_override"
    bl_label = "Unlink Asset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Проверяем, есть ли выделенные объекты и хотя бы один из них связан
        if not context.selected_objects:
            return False
        return any(obj.library and not obj.override_library for obj in context.selected_objects)

    def ensure_object_in_view_layer(self, context, obj):
        """Ensure the object is in the active view layer and collection"""
        view_layer = context.view_layer
        # Проверяем, находится ли объект в текущем View Layer
        if obj.name not in view_layer.objects:
            try:
                # Добавляем объект в активную коллекцию сцены
                context.collection.objects.link(obj)
                # Обновляем depsgraph, чтобы убедиться, что объект доступен
                context.view_layer.depsgraph.update()
                return True
            except Exception as e:
                self.report({'ERROR'}, f"Failed to link {obj.name} to View Layer: {e}")
                return False
        return True

    def execute(self, context):
        # Синхронизируем цвета материалов
        try:
            bpy.ops.object.sync_material_colors()
            self.report({'INFO'}, "Material colors synchronized")
        except Exception as e:
            self.report({'WARNING'}, f"Failed to sync material colors: {e}")

        linked_objects = [obj for obj in context.selected_objects if obj.library and not obj.override_library]
        
        if not linked_objects:
            self.report({'WARNING'}, "No linked objects selected or all already have overrides")
            return {'CANCELLED'}

        # Сохраняем текущий активный объект и выделение
        original_active = context.view_layer.objects.active
        original_selected = context.selected_objects[:]

        success_count = 0
        for obj in linked_objects:
            try:
                # Убедимся, что объект находится в текущем View Layer
                if not self.ensure_object_in_view_layer(context, obj):
                    continue

                # Проверяем, можно ли выделить объект
                if obj.name not in context.view_layer.objects:
                    self.report({'ERROR'}, f"Cannot select {obj.name}: not in View Layer")
                    continue

                # Устанавливаем объект как активный
                context.view_layer.objects.active = obj
                # Устанавливаем выделение только для текущего объекта
                for other_obj in context.selected_objects:
                    other_obj.select_set(False)
                try:
                    obj.select_set(True)
                except Exception as e:
                    self.report({'ERROR'}, f"Cannot select {obj.name}: {e}")
                    continue

                # Применяем Library Override
                bpy.ops.object.make_override_library()
                success_count += 1
                self.report({'INFO'}, f"Applied Library Override to {obj.name}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to apply Library Override to {obj.name}: {e}")

        # Восстанавливаем исходное выделение и активный объект
        for obj in original_selected:
            if obj.name in context.view_layer.objects:
                obj.select_set(True)
        context.view_layer.objects.active = original_active

        if success_count > 0:
            self.report({'INFO'}, f"Successfully applied Library Override to {success_count} object(s)")
        else:
            self.report({'ERROR'}, "No Library Overrides were applied")

        return {'FINISHED'}

def library_override_menu_func(self, context):
    """Add Library Override option to the top of the context menu"""
    if OBJECT_OT_ApplyLibraryOverride.poll(context):
        self.layout.operator(OBJECT_OT_ApplyLibraryOverride.bl_idname, icon='LIBRARY_DATA_OVERRIDE')
        self.layout.separator()

def register():
    bpy.utils.register_class(OBJECT_OT_ApplyLibraryOverride)
    # Добавляем опцию в контекстное меню 3D Viewport
    bpy.types.VIEW3D_MT_object_context_menu.prepend(library_override_menu_func)

def unregister():
    # Удаляем опцию из контекстного меню
    bpy.types.VIEW3D_MT_object_context_menu.remove(library_override_menu_func)
    bpy.utils.unregister_class(OBJECT_OT_ApplyLibraryOverride)

if __name__ == "__main__":
    register()