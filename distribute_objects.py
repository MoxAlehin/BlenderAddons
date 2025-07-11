import bpy
import math
from mathutils import Vector
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty
from operator import itemgetter
from collections import defaultdict

bl_info = {
    "name": "Distribute Objects",
    "author": "Your Name",
    "version": (2, 20),
    "blender": (4, 4, 0),
    "location": "Object > Distribute Objects or Search > Distribute Objects",
    "description": "Distributes selected objects in rows, optionally centering active object at origin",
    "category": "Object",
}

def get_child_objects(obj, objects=None):
    """Recursively collects all child objects."""
    if objects is None:
        objects = []
    if obj not in objects:
        objects.append(obj)
    for child in obj.children:
        get_child_objects(child, objects)
    return objects

def get_object_size(obj):
    """Calculate the size and bounding box center of an object, including its children and modifiers."""
    mesh_objects = [o for o in get_child_objects(obj) if o.type == 'MESH']
    
    if not mesh_objects:
        dims = [max(obj.dimensions)] * 3
        center_x = center_y = center_z = 0.0
        min_z = -dims[2] / 2
        max_z = dims[2] / 2
        return dims[0], dims[1], dims[2], center_x, center_y, min_z, max_z, center_z
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    min_coords = Vector((float('inf'), float('inf'), float('inf')))
    max_coords = Vector((-float('inf'), -float('inf'), -float('inf')))
    
    for mesh_obj in mesh_objects:
        eval_obj = mesh_obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
        matrix = mesh_obj.matrix_world
        for vert in mesh.vertices:
            world_vert = matrix @ vert.co
            min_coords.x = min(min_coords.x, world_vert.x)
            min_coords.y = min(min_coords.y, world_vert.y)
            min_coords.z = min(min_coords.z, world_vert.z)
            max_coords.x = max(max_coords.x, world_vert.x)
            max_coords.y = max(max_coords.y, world_vert.y)
            max_coords.z = max(max_coords.z, world_vert.z)
        eval_obj.to_mesh_clear()
    
    width = max_coords.x - min_coords.x
    depth = max_coords.y - min_coords.y
    height = max_coords.z - min_coords.z
    center_world = (max_coords + min_coords) / 2
    matrix_inv = obj.matrix_world.inverted()
    center_local = matrix_inv @ center_world
    center_x = center_local.x
    center_y = center_local.y
    center_z = center_local.z
    min_z_world = min_coords.z
    max_z_world = max_coords.z
    min_z = (matrix_inv @ Vector((0, 0, min_z_world))).z
    max_z = (matrix_inv @ Vector((0, 0, max_z_world))).z
    
    return width, depth, height, center_x, center_y, min_z, max_z, center_z

def sort_objects(objects_with_sizes, sort_method, center_active, active_object, group_by_name, name_prefix_length):
    """Sort objects based on specified method, optionally grouping by name prefix."""
    if center_active and active_object:
        active_item = next((obj, size) for obj, size in objects_with_sizes if obj == active_object)
        objects_with_sizes = [item for item in objects_with_sizes if item[0] != active_object]
    else:
        active_item = None
    
    if sort_method == 'WIDTH':
        key_func = lambda x: x[1][0]
    elif sort_method == 'X_PLUS_Y':
        key_func = lambda x: x[1][0] + x[1][1]
    elif sort_method == 'X_PLUS_Y_PLUS_Z':
        key_func = lambda x: x[1][0] + x[1][1] + x[1][2]
    elif sort_method == 'AVG':
        key_func = lambda x: sum(x[1][:3]) / 3
    elif sort_method == 'MAX':
        key_func = lambda x: max(x[1][:3])
    
    if group_by_name:
        groups = defaultdict(list)
        for obj, size in objects_with_sizes:
            prefix = obj.name[:min(len(obj.name), name_prefix_length)]
            groups[prefix].append((obj, size))
        group_sizes = []
        for prefix, group in groups.items():
            avg_size = sum(key_func(item) for item in group) / len(group)
            group_sizes.append((prefix, avg_size, group))
        sorted_groups = sorted(group_sizes, key=lambda x: x[1], reverse=True)
        sorted_objects = []
        for prefix, _, group in sorted_groups:
            sorted_group = sorted(group, key=key_func, reverse=True)
            sorted_objects.extend(sorted_group)
    else:
        sorted_objects = sorted(objects_with_sizes, key=key_func, reverse=True)
    
    if active_item:
        sorted_objects.insert(0, active_item)
    
    return sorted_objects

def distribute_objects(spacing, center_active, sort_method, z_alignment, group_by_name, name_prefix_length):
    """Distribute objects in rows, centering active object or entire matrix at origin."""
    for obj in bpy.context.selected_objects:
        if obj.parent:
            obj.select_set(False)
    
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type in ('MESH', 'ARMATURE')]
    if not selected_objects:
        return
    
    active_object = bpy.context.active_object if center_active and bpy.context.active_object in selected_objects else None
    objects_with_sizes = [(obj, get_object_size(obj)) for obj in selected_objects]
    sorted_objects = sort_objects(objects_with_sizes, sort_method, center_active, active_object, group_by_name, name_prefix_length)
    
    num_objects = len(selected_objects)
    num_rows = max(1, round(math.sqrt(num_objects)))
    central_row_idx = num_rows // 2
    
    total_width = sum(size[0] for _, size in sorted_objects) + max(spacing, 0.1) * (num_objects - 1)
    target_row_width = total_width / num_rows if num_rows > 0 else total_width
    
    rows = [[] for _ in range(num_rows)]
    if center_active and active_object:
        active_item = next((obj, size) for obj, size in sorted_objects if obj == active_object)
        sorted_objects = [item for item in sorted_objects if item[0] != active_object]
        rows[central_row_idx].append(active_item)
    
    if group_by_name:
        groups = defaultdict(list)
        for obj, size in sorted_objects:
            prefix = obj.name[:min(len(obj.name), name_prefix_length)]
            groups[prefix].append((obj, size))
        sorted_groups = []
        for obj, size in sorted_objects:
            prefix = obj.name[:min(len(obj.name), name_prefix_length)]
            if prefix in groups:
                sorted_groups.append((prefix, groups[prefix]))
                del groups[prefix]
        current_row_idx = 0
        current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
        for prefix, group in sorted_groups:
            group_width = sum(size[0] for _, size in group) + max(spacing, 0.1) * (len(group) - 1)
            if current_width + group_width <= target_row_width * 1.1 or not rows[current_row_idx]:
                rows[current_row_idx].extend(group)
                current_width += group_width
            else:
                current_row_idx = (current_row_idx + 1) % num_rows
                current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
                rows[current_row_idx].extend(group)
                current_width += group_width
    else:
        current_row_idx = 0
        current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
        for obj, size in sorted_objects:
            obj_width = size[0]
            if current_width + obj_width + (len(rows[current_row_idx]) * max(spacing, 0.1)) <= target_row_width * 1.1 or not rows[current_row_idx]:
                rows[current_row_idx].append((obj, size))
                current_width += obj_width
            else:
                current_row_idx = (current_row_idx + 1) % num_rows
                current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
                rows[current_row_idx].append((obj, size))
                current_width += obj_width
    
    rows = rows[::-1]
    central_row = rows[central_row_idx]
    
    if center_active and central_row and active_object:
        try:
            active_item = next((obj, size) for obj, size in central_row if obj == active_object)
            central_row.remove(active_item)
            mid_idx = len(central_row) // 2
            central_row.insert(mid_idx, active_item)
        except StopIteration:
            pass
    elif central_row and not center_active:
        max_obj = max(central_row, key=lambda x: x[1][0])
        central_row.remove(max_obj)
        mid_idx = len(central_row) // 2
        central_row.insert(mid_idx, max_obj)
    
    row_y_positions = [0] * num_rows
    max_row_width = 0
    row_widths = []
    row_depths = []
    
    for row_idx in range(num_rows):
        row = rows[row_idx]
        row_depth = max(size[1] for _, size in row) if row else 0
        row_width = sum(size[0] for _, size in row) + max(spacing, 0.1) * (len(row) - 1) if row else 0
        row_widths.append(row_width)
        row_depths.append(row_depth)
        max_row_width = max(max_row_width, row_width)
    
    for row_idx in range(num_rows):
        if row_idx == central_row_idx:
            row_y_positions[row_idx] = 0
        elif row_idx < central_row_idx:
            y = 0
            for j in range(row_idx + 1, central_row_idx + 1):
                if rows[j]:
                    prev_depth = max(size[1] for _, size in rows[j]) if j == central_row_idx else row_depths[j]
                    curr_depth = row_depths[row_idx] if j == row_idx + 1 else row_depths[j - 1]
                    y -= (prev_depth / 2 + curr_depth / 2 + max(spacing, 0.1))
            row_y_positions[row_idx] = y
        else:
            y = 0
            for j in range(central_row_idx, row_idx):
                if rows[j]:
                    prev_depth = row_depths[j]
                    curr_depth = row_depths[row_idx] if j == row_idx - 1 else row_depths[j + 1]
                    y += (prev_depth / 2 + curr_depth / 2 + max(spacing, 0.1))
            row_y_positions[row_idx] = y
    
    positions = []
    for row_idx, row in enumerate(rows):
        if not row:
            positions.extend([(0, row_y_positions[row_idx])] if row_idx == central_row_idx else [])
            continue
        num_objects_in_row = len(row)
        total_object_width = sum(size[0] for _, size in row)
        spacing_adjusted = (max_row_width - total_object_width) / (num_objects_in_row - 1) if num_objects_in_row > 1 else max(spacing, 0.1)
        start_x = -max_row_width / 2
        row_positions = [None] * num_objects_in_row
        for i in range(num_objects_in_row):
            obj, (width, depth, height, center_x, center_y, min_z, max_z, center_z) = row[i]
            x = start_x + width / 2
            row_positions[i] = (x, row_y_positions[row_idx])
            start_x += width + spacing_adjusted
        positions.extend([p for p in row_positions if p is not None])
    
    # Center the entire matrix when center_active is False
    if not center_active:
        # Calculate bounding box of all positions
        min_x = min(x for x, _ in positions) if positions else 0
        max_x = max(x for x, _ in positions) if positions else 0
        min_y = min(y for _, y in positions) if positions else 0
        max_y = max(y for _, y in positions) if positions else 0
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        # Shift positions to center the matrix at (0, 0)
        positions = [(x - center_x, y - center_y) for x, y in positions]
    else:
        # Center on active object
        ref_center_x = None
        ref_pos_idx = sum(len(r) for r in rows[:central_row_idx]) + next(i for i, (obj, _) in enumerate(central_row) if obj == active_object) if active_object and central_row else 0
        if positions and ref_pos_idx < len(positions):
            ref_center_x = positions[ref_pos_idx][0]
            positions = [(x - ref_center_x, y) for x, y in positions]
    
    final_row_widths = []
    for row_idx, row in enumerate(rows):
        if row:
            x_positions = [positions[i][0] for i in range(sum(len(r) for r in rows[:row_idx]), sum(len(r) for r in rows[:row_idx + 1]))]
            row_width = max(x_positions) - min(x_positions) + max(size[0] for _, size in row)
            final_row_widths.append(row_width)
        else:
            final_row_widths.append(0)
    
    print(f"Final row widths: {final_row_widths}")
    
    assigned_positions = []
    pos_idx = 0
    for row_idx, row in enumerate(rows):
        for obj, size in row:
            x, y = positions[pos_idx]
            center_x, center_y, min_z, max_z, center_z = size[3], size[4], size[5], size[6], size[7]
            if z_alignment == 'PIVOT':
                z = 0
            elif z_alignment == 'CENTER':
                z = -center_z
            elif z_alignment == 'BOTTOM':
                z = -min_z
            elif z_alignment == 'TOP':
                z = -max_z
            loc_x = x - center_x
            loc_y = y - center_y
            loc_z = z
            assigned_positions.append((obj, loc_x, loc_y, loc_z))
            pos_idx += 1
    
    for obj, loc_x, loc_y, loc_z in assigned_positions:
        obj.location.x = loc_x
        obj.location.y = loc_y
        obj.location.z = loc_z
        center_x = loc_x + obj.get('center_x', 0)
        center_y = loc_y + obj.get('center_y', 0)
        print(f"Object {obj.name}: x={loc_x}, y={loc_y}, z={loc_z}, center_x={center_x}, center_y={center_y}")

class OBJECT_OT_DistributeObjects(Operator):
    """Distribute selected objects in rows, optionally centering active object at origin"""
    bl_idname = "object.distribute_objects"
    bl_label = "Distribute Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    spacing: FloatProperty(
        name="Spacing",
        description="Minimum distance between object bounding boxes",
        default=5.0,
        min=0.0
    )
    
    center_active: BoolProperty(
        name="Center Active Object",
        description="Use active object as the reference object at the origin",
        default=False
    )
    
    sort_method: EnumProperty(
        name="Sort Method",
        description="Method to sort objects",
        items=[
            ('WIDTH', "Width (X)", "Sort by width along X"),
            ('X_PLUS_Y', "X + Y", "Sort by sum of width and depth"),
            ('X_PLUS_Y_PLUS_Z', "X + Y + Z", "Sort by sum of all dimensions"),
            ('AVG', "Average (X, Y, Z)", "Sort by average of dimensions"),
            ('MAX', "Max (X, Y, Z)", "Sort by maximum dimension"),
        ],
        default='AVG'
    )
    
    z_alignment: EnumProperty(
        name="Z Alignment",
        description="How to align objects along Z axis",
        items=[
            ('PIVOT', "Pivot at Z=0", "Place object's pivot point at Z=0"),
            ('CENTER', "Center at Z=0", "Place object's bounding box center at Z=0"),
            ('BOTTOM', "Bottom at Z=0", "Place object's bounding box bottom at Z=0"),
            ('TOP', "Top at Z=0", "Place object's bounding box top at Z=0"),
        ],
        default='BOTTOM'
    )
    
    group_by_name: BoolProperty(
        name="Group by Name",
        description="Group objects by the prefix of their names",
        default=True
    )
    
    name_prefix_length: IntProperty(
        name="Name Prefix Length",
        description="Number of characters to consider for grouping by name",
        default=5,
        min=1
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "spacing")
        if context.active_object and context.active_object in context.selected_objects:
            layout.prop(self, "center_active")
        layout.prop(self, "sort_method")
        layout.prop(self, "z_alignment")
        layout.prop(self, "group_by_name")
        if self.group_by_name:
            layout.prop(self, "name_prefix_length")
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len([obj for obj in context.selected_objects if obj.type in ('MESH', 'ARMATURE')]) > 0
    
    def execute(self, context):
        distribute_objects(
            self.spacing,
            self.center_active and context.active_object and context.active_object in context.selected_objects,
            self.sort_method,
            self.z_alignment,
            self.group_by_name,
            self.name_prefix_length
        )
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_DistributeObjects.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_DistributeObjects)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_DistributeObjects)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()