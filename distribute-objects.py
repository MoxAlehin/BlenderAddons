import bpy
import math
from mathutils import Vector
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from operator import itemgetter

bl_info = {
    "name": "Distribute Objects",
    "author": "Your Name",
    "version": (2, 9),
    "blender": (4, 4, 0),
    "location": "Object > Distribute Objects or Search > Distribute Objects",
    "description": "Distributes selected objects in rows to minimize bounding box",
    "category": "Object",
}

def get_object_size(obj):
    """Calculate the size of an object, including its children, based on combined bounding box."""
    # Collect all mesh objects (parent and children)
    mesh_objects = [obj] if obj.type == 'MESH' else []
    for child in obj.children_recursive:
        if child.type == 'MESH':
            mesh_objects.append(child)
    
    if not mesh_objects:
        # Fallback for non-mesh objects without mesh children
        dims = max(obj.dimensions), max(obj.dimensions), max(obj.dimensions)
        return dims[0], dims[1], dims[2], 0.0, dims[2], dims[2] / 2
    
    # Compute combined bounding box in world space
    all_bbox = []
    for mesh_obj in mesh_objects:
        bbox = [mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box]
        all_bbox.extend(bbox)
    
    # Calculate dimensions and Z bounds
    width = max(v.x for v in all_bbox) - min(v.x for v in all_bbox)
    depth = max(v.y for v in all_bbox) - min(v.y for v in all_bbox)
    height = max(v.z for v in all_bbox) - min(v.z for v in all_bbox)
    min_z = min(v.z for v in all_bbox)
    max_z = max(v.z for v in all_bbox)
    center_z = (min_z + max_z) / 2
    
    return width, depth, height, min_z, max_z, center_z

def sort_objects(objects_with_sizes, sort_method, center_active, active_object):
    """Sort objects based on specified method."""
    if center_active and active_object:
        # Remove active object to place it in the center later
        active_item = next((obj, size) for obj, size in objects_with_sizes if obj == active_object)
        objects_with_sizes = [item for item in objects_with_sizes if item[0] != active_object]
    else:
        active_item = None
    
    # Define sorting key
    if sort_method == 'WIDTH':
        key_func = lambda x: x[1][0]  # Width (X)
    elif sort_method == 'X_PLUS_Y':
        key_func = lambda x: x[1][0] + x[1][1]  # X + Y
    elif sort_method == 'X_PLUS_Y_PLUS_Z':
        key_func = lambda x: x[1][0] + x[1][1] + x[1][2]  # X + Y + Z
    elif sort_method == 'AVG':
        key_func = lambda x: sum(x[1][:3]) / 3  # Average of X, Y, Z
    elif sort_method == 'MAX':
        key_func = lambda x: max(x[1][:3])  # Max of X, Y, Z
    
    # Sort objects (descending, largest first)
    sorted_objects = sorted(objects_with_sizes, key=key_func, reverse=True)
    
    if active_item:
        sorted_objects.insert(0, active_item)  # Place active object first for central placement
    
    return sorted_objects

def distribute_objects(spacing, center_active, sort_method, align_method, z_alignment):
    """Distribute objects in rows to minimize bounding box with equal row widths."""
    # Deselect all parented objects
    for obj in bpy.context.selected_objects:
        if obj.parent:
            obj.select_set(False)
    
    # Get remaining selected objects
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type in ('MESH', 'ARMATURE')]
    if not selected_objects:
        return
    
    active_object = bpy.context.active_object if center_active and bpy.context.active_object in selected_objects else None
    
    # Calculate sizes
    objects_with_sizes = [(obj, get_object_size(obj)) for obj in selected_objects]
    
    # Sort objects
    sorted_objects = sort_objects(objects_with_sizes, sort_method, center_active, active_object)
    
    # Determine number of rows for square layout (~sqrt(N))
    num_objects = len(selected_objects)
    num_rows = max(1, round(math.sqrt(num_objects)))
    central_row_idx = num_rows // 2
    
    # Calculate target row width, adjust for small spacing
    total_width = sum(size[0] for _, size in sorted_objects) + max(spacing, 0.1) * (num_objects - 1)
    target_row_width = total_width / num_rows if num_rows > 0 else total_width
    
    # Distribute objects into rows to match target row width
    rows = [[] for _ in range(num_rows)]
    if center_active and active_object:
        # Reserve active object for central row
        active_item = next((obj, size) for obj, size in sorted_objects if obj == active_object)
        sorted_objects = [item for item in sorted_objects if item[0] != active_object]
        rows[central_row_idx].append(active_item)
    
    # Distribute remaining objects
    current_row_idx = 0
    current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
    
    for obj, size in sorted_objects:
        obj_width = size[0]
        # Try to add to current row
        if current_width + obj_width + (len(rows[current_row_idx]) * max(spacing, 0.1)) <= target_row_width * 1.1 or not rows[current_row_idx]:
            rows[current_row_idx].append((obj, size))
            current_width += obj_width
        else:
            current_row_idx += 1
            if current_row_idx >= num_rows:
                # Distribute remaining objects to existing rows
                current_row_idx = 0
                current_width = sum(size[0] for _, size in rows[current_row_idx]) if rows[current_row_idx] else 0
                rows[current_row_idx].append((obj, size))
                current_width += obj_width
            else:
                rows[current_row_idx].append((obj, size))
                current_width = obj_width
    
    # Reverse rows to place largest objects in back (-Y)
    rows = rows[::-1]
    
    # Adjust central row
    central_row = rows[central_row_idx]
    
    if central_row and center_active and active_object:
        # Ensure active object is in the middle
        try:
            active_item = next((obj, size) for obj, size in central_row if obj == active_object)
            central_row.remove(active_item)
            mid_idx = len(central_row) // 2
            central_row.insert(mid_idx, active_item)
        except StopIteration:
            pass  # Active object already handled
    elif central_row and not center_active:
        # Place largest object in the middle
        max_obj = max(central_row, key=lambda x: x[1][0])
        central_row.remove(max_obj)
        mid_idx = len(central_row) // 2
        central_row.insert(mid_idx, max_obj)
    
    # Select reference object
    reference_obj = next((obj, size) for obj, size in central_row if obj == active_object) if center_active and active_object else central_row[len(central_row) // 2] if central_row else sorted_objects[0]
    reference_idx = next(i for i, (obj, _) in enumerate(central_row) if obj == reference_obj[0]) if central_row else 0
    print(f"Central row: {len(central_row)} objects, reference_idx: {reference_idx}")
    
    # Calculate Y positions for rows (central row at Y=0, largest in back)
    row_y_positions = []
    max_row_width = 0
    row_widths = []
    
    for row_idx in range(num_rows):
        row = rows[row_idx]
        row_depth = max(size[1] for _, size in row) if row else 0
        # Calculate row width for alignment
        row_width = sum(size[0] for _, size in row) + max(spacing, 0.1) * (len(row) - 1) if row else 0
        row_widths.append(row_width)
        max_row_width = max(max_row_width, row_width)
        
        # Place largest objects in back (-Y), smallest in front (+Y)
        if row_idx < central_row_idx:
            # Rows behind central row (more negative Y)
            y = -sum(max(size[1] for _, size in rows[j]) + max(spacing, 0.1) for j in range(row_idx + 1, central_row_idx + 1))
        elif row_idx == central_row_idx:
            y = 0
        else:
            # Rows in front of central row (positive Y)
            y = sum(max(size[1] for _, size in rows[j]) + max(spacing, 0.1) for j in range(central_row_idx, row_idx))
        row_y_positions.append(y)
    
    print(f"Row widths: {row_widths}")
    
    # Calculate X positions for each row
    positions = []
    
    # First, calculate positions for central row
    central_row_positions = [None] * len(central_row) if central_row else [None]
    ref_width = reference_obj[1][0]
    central_row_positions[reference_idx] = (0, 0) if central_row else (0, 0)
    
    if central_row:
        left_x = -(ref_width / 2 + max(spacing, 0.1))
        right_x = ref_width / 2 + max(spacing, 0.1)
        left_idx = reference_idx - 1
        right_idx = reference_idx + 1
        
        for i in range(len(central_row)):
            if i != reference_idx:
                obj, (width, depth, height, min_z, max_z, center_z) = central_row[i]
                if i < reference_idx:
                    x = left_x - width / 2
                    central_row_positions[left_idx] = (x, 0)
                    left_x -= (width / 2 + max(spacing, 0.1))
                    left_idx -= 1
                else:
                    x = right_x + width / 2
                    central_row_positions[right_idx] = (x, 0)
                    right_x += (width / 2 + max(spacing, 0.1))
                    right_idx += 1
    else:
        central_row_positions[0] = (0, 0)
    
    central_x_positions = [p[0] for p in central_row_positions if p is not None]
    print(f"Central row X positions: {central_x_positions}")
    
    # Process all rows
    for row_idx, row in enumerate(rows):
        num_objects_in_row = len(row)
        row_positions = [None] * num_objects_in_row if row else [None]
        
        if row_idx == central_row_idx:
            row_positions = central_row_positions
        else:
            if num_objects_in_row == len(central_row) and row:
                # Align with central row
                for i in range(num_objects_in_row):
                    obj, (width, depth, height, min_z, max_z, center_z) = row[i]
                    x = central_x_positions[i]
                    row_positions[i] = (x, row_y_positions[row_idx])
            else:
                # Calculate positions based on row width and alignment
                row_width = row_widths[row_idx] if row_idx < len(row_widths) else 0
                if align_method == 'LEFT':
                    start_x = -max_row_width / 2
                elif align_method == 'RIGHT':
                    start_x = max_row_width / 2 - row_width
                elif align_method == 'CENTER':
                    start_x = (max_row_width - row_width) / 2 - max_row_width / 2
                elif align_method == 'JUSTIFY' and num_objects_in_row > 1:
                    # Distribute objects evenly across max_row_width
                    spacing_adjusted = (max_row_width - sum(size[0] for _, size in row)) / (num_objects_in_row - 1) if row else max(spacing, 0.1)
                    start_x = -max_row_width / 2
                    for i in range(num_objects_in_row):
                        obj, (width, depth, height, min_z, max_z, center_z) = row[i]
                        x = start_x + width / 2
                        row_positions[i] = (x, row_y_positions[row_idx])
                        start_x += width + spacing_adjusted
                    positions.extend([p for p in row_positions if p is not None])
                    continue
                else:  # JUSTIFY with 1 object or fallback
                    start_x = (max_row_width - row_width) / 2 - max_row_width / 2
                
                for i in range(num_objects_in_row):
                    obj, (width, depth, height, min_z, max_z, center_z) = row[i]
                    x = start_x + width / 2
                    row_positions[i] = (x, row_y_positions[row_idx])
                    start_x += width + max(spacing, 0.1)
        
        positions.extend([p for p in row_positions if p is not None])
    
    # Apply positions (move only selected objects)
    assigned_positions = []
    pos_idx = 0
    for row_idx, row in enumerate(rows):
        for obj, size in row:
            x, y = positions[pos_idx]
            # Adjust Z based on z_alignment
            min_z, max_z, center_z = size[3], size[4], size[5]
            if z_alignment == 'PIVOT':
                z = 0  # Pivot (origin) at Z=0
            elif z_alignment == 'CENTER':
                z = -center_z  # Center of bounding box at Z=0
            elif z_alignment == 'BOTTOM':
                z = -min_z  # Bottom of bounding box at Z=0
            elif z_alignment == 'TOP':
                z = -max_z  # Top of bounding box at Z=0
            assigned_positions.append((obj, x, y, z))
            pos_idx += 1
    
    for obj, x, y, z in assigned_positions:
        if obj == reference_obj[0]:
            obj.location.x = 0
            obj.location.y = 0
            obj.location.z = z
        else:
            obj.location.x = x
            obj.location.y = y
            obj.location.z = z
        print(f"Object {obj.name}: x={x}, y={y}, z={z}")

class OBJECT_OT_DistributeObjects(Operator):
    """Distribute selected objects in rows to minimize bounding box"""
    bl_idname = "object.distribute_objects"
    bl_label = "Distribute Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    spacing: FloatProperty(
        name="Spacing",
        description="Minimum distance between object bounding boxes",
        default=0.0,
        min=0.0
    )
    
    center_active: BoolProperty(
        name="Center Active Object",
        description="Use active object as the reference object at the center",
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
    
    align_method: EnumProperty(
        name="Alignment",
        description="Alignment of objects in rows",
        items=[
            ('LEFT', "Left", "Align objects to the left"),
            ('CENTER', "Center", "Center objects in the row"),
            ('RIGHT', "Right", "Align objects to the right"),
            ('JUSTIFY', "Justify", "Distribute objects evenly across the row"),
        ],
        default='JUSTIFY'
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
    
    @classmethod
    def poll(cls, context):
        return len([obj for obj in context.selected_objects if obj.type in ('MESH', 'ARMATURE')]) > 0
    
    def execute(self, context):
        distribute_objects(self.spacing, self.center_active, self.sort_method, self.align_method, self.z_alignment)
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