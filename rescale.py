import bpy
from bpy.types import Operator, Panel
from bpy.props import FloatProperty, EnumProperty
from mathutils import Vector

# Оператор для функции Rescale
class OBJECT_OT_Rescale(Operator):
    bl_idname = "object.rescale"
    bl_label = "Rescale Object"
    bl_description = "Rescale selected objects to a specified size"
    bl_options = {'REGISTER', 'UNDO'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    target_size: FloatProperty(
        name="Target Size",
        description="Desired size",
        default=10.0,
        min=0.001,
        unit='LENGTH'
    )

    axis: EnumProperty(
        name="Axis",
        description="Axis to base the scaling on",
        items=[
            ('X', "X", "Use X axis"),
            ('Y', "Y", "Use Y axis"),
            ('Z', "Z", "Use Z axis"),
            ('MAX', "Maximum", "Use the longest axis"),
            ('MIN', "Minimum", "Use the shortest axis"),
        ],
        default='MAX'
    )

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == 'OBJECT'

    def execute(self, context):
        unit_scale = context.scene.unit_settings.scale_length  # Учитываем unit_scale сцены
        target_size_scaled = self.target_size / unit_scale  # Делим target_size на unit_scale

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Получаем габариты объекта, учитывая текущий масштаб
            dims = obj.dimensions
            scale = obj.scale
            # Поэлементное деление размеров на масштаб для получения базовых размеров
            dims_base = Vector((dims.x / scale.x, dims.y / scale.y, dims.z / scale.z))
            # Учитываем unit_scale для получения размеров в единицах сцены
            dims_scaled = dims_base / unit_scale

            # Определяем текущий размер в зависимости от выбранной оси
            if self.axis == 'X':
                current_size = dims_scaled.x
            elif self.axis == 'Y':
                current_size = dims_scaled.y
            elif self.axis == 'Z':
                current_size = dims_scaled.z
            elif self.axis == 'MAX':
                current_size = max(dims_scaled.x, dims_scaled.y, dims_scaled.z)
            else:  # MIN
                current_size = min(dims_scaled.x, dims_scaled.y, dims_scaled.z)

            if current_size == 0:
                self.report({'WARNING'}, f"Object {obj.name} has zero dimension on selected axis")
                continue

            # Вычисляем коэффициент масштабирования
            scale_factor = target_size_scaled / current_size

            # Применяем равномерный масштаб
            obj.scale *= scale_factor

            # Применяем масштаб (Apply Scale)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_size")
        layout.prop(self, "axis")

# Панель для интерфейса
class VIEW3D_PT_Rescale(Panel):
    bl_label = "Rescale Tool"
    bl_idname = "VIEW3D_PT_rescale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.rescale", text="Rescale Selected Objects")

# Информация об аддоне
bl_info = {
    "name": "Rescale Object",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Tool > Rescale Tool, Search (F3)",
    "description": "Rescale objects to a specified size along a chosen axis",
    "category": "Object",
}

# Регистрация классов
classes = (
    OBJECT_OT_Rescale,
    VIEW3D_PT_Rescale,
)

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_Rescale.bl_idname, text="Rescale Object")

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"Registered class: {cls.__name__}")
        except Exception as e:
            print(f"Failed to register class {cls.__name__}: {e}")
    # Добавляем в меню поиска (F3)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    print("Rescale plugin registered successfully")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"Unregistered class: {cls.__name__}")
        except Exception as e:
            print(f"Failed to unregister class {cls.__name__}: {e}")
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    print("Rescale plugin unregistered")

if __name__ == "__main__":
    register()