import bpy
from bpy.types import Operator, Panel
from bpy.props import FloatProperty, EnumProperty
from mathutils import Vector

class OBJECT_OT_Rescale(Operator):
    bl_idname = "object.rescale"
    bl_label = "Rescale Object"
    bl_description = "Rescale selected objects' mesh data to a specified size"
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
        unit_scale = context.scene.unit_settings.scale_length  # Учитываем масштаб сцены
        target_size_scaled = self.target_size / unit_scale    # Корректируем целевой размер

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Получаем меш
            mesh = obj.data

            # Вычисляем bounding box меша для определения его базовых размеров
            if not mesh.vertices:
                self.report({'WARNING'}, f"Object {obj.name} has no vertices")
                continue

            # Собираем координаты вершин
            coords = [vert.co for vert in mesh.vertices]
            if not coords:
                self.report({'WARNING'}, f"Object {obj.name} has no valid vertices")
                continue

            # Вычисляем границы (min/max) по каждой оси
            min_x = min(co.x for co in coords)
            max_x = max(co.x for co in coords)
            min_y = min(co.y for co in coords)
            max_y = max(co.y for co in coords)
            min_z = min(co.z for co in coords)
            max_z = max(co.z for co in coords)

            # Размеры меша (без учёта obj.scale)
            dims_base = Vector((max_x - min_x, max_y - min_y, max_z - min_z))
            dims_scaled = dims_base / unit_scale  # Учитываем unit_scale

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

            # Масштабируем вершины меша
            for vert in mesh.vertices:
                vert.co *= scale_factor

            # Сбрасываем масштаб объекта к (1, 1, 1)
            obj.scale = (1.0, 1.0, 1.0)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_size")
        layout.prop(self, "axis")

class VIEW3D_PT_Rescale(Panel):
    bl_label = "Rescale Tool"
    bl_idname = "VIEW3D_PT_rescale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.rescale", text="Rescale Selected Objects")

bl_info = {
    "name": "Rescale Object",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Tool > Rescale Tool, Search (F3)",
    "description": "Rescale objects' mesh data to a specified size along a chosen axis",
    "category": "Object",
}

classes = (
    OBJECT_OT_Rescale,
    VIEW3D_PT_Rescale,
)

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_Rescale.bl_idname, text="Rescale")

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"Registered class: {cls.__name__}")
        except Exception as e:
            print(f"Failed to register class {cls.__name__}: {e}")
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