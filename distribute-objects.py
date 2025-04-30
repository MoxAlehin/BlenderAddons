import bpy
import math
from mathutils import Vector
import numpy as np
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty

bl_info = {
    "name": "Distribute Objects",
    "author": "Your Name",
    "version": (1, 18),
    "blender": (4, 4, 0),
    "location": "Object > Distribute Objects or Search > Distribute Objects",
    "description": "Distributes selected objects in rows with a fixed reference object in center",
    "category": "Object",
}

def get_object_size(obj):
    """Calculate the size of an object based on its dimensions."""
    return obj.dimensions.x, obj.dimensions.y

def distribute_objects(min_distance, center_active):
    """Main function to distribute objects."""
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not selected_objects:
        return
    
    active_object = bpy.context.active_object if center_active and bpy.context.active_object and bpy.context.active_object in selected_objects else None
    
    # Calculate sizes and store initial order
    objects_with_sizes = [(obj, get_object_size(obj)) for obj in selected_objects]
    
    # Sort by depth only once to maintain consistent order
    objects_with_sizes.sort(key=lambda x: x[1][1], reverse=True)
    
    # If active object exists, ensure it's included correctly
    if active_object:
        active_item = next((obj, size) for obj, size in objects_with_sizes if obj == active_object)
        objects_with_sizes.remove(active_item)
    
    # Determine number of rows for square layout (~sqrt(N))
    num_objects = len(selected_objects)
    num_rows = max(1, round(math.sqrt(num_objects)))
    
    # Split objects into rows
    rows = []
    objects_per_row = num_objects // num_rows if num_rows > 0 else num_objects
    remainder = num_objects % num_rows if num_rows > 0 else 0
    
    start_idx = 0
    central_row_idx = num_rows // 2
    
    for i in range(num_rows):
        row_size = objects_per_row + (1 if i < remainder else 0)
        if i == central_row_idx:
            # Form central row with reference object in the middle
            row_objects = objects_with_sizes[start_idx:start_idx + row_size - (1 if active_object else 0)]
            if active_object:
                # Place active object in the middle
                central_row = row_objects.copy()
                mid_idx = len(central_row) // 2
                central_row.insert(mid_idx, active_item)
            else:
                # Place object with max depth in the middle
                central_row = row_objects.copy()
                if central_row:
                    max_depth_obj = max(central_row, key=lambda x: x[1][1])
                    central_row.remove(max_depth_obj)
                    mid_idx = len(central_row) // 2
                    central_row.insert(mid_idx, max_depth_obj)
            rows.append(central_row)
            start_idx += row_size - (1 if active_object else 0)
        else:
            rows.append(objects_with_sizes[start_idx:start_idx + row_size])
            start_idx += row_size
    
    # Select reference object
    central_row = rows[central_row_idx]
    if active_object:
        reference_obj = next((obj, size) for obj, size in central_row if obj == active_object)
    else:
        reference_obj = max(central_row, key=lambda x: x[1][1]) if central_row else objects_with_sizes[0]
    
    reference_idx = next(i for i, (obj, _) in enumerate(central_row) if obj == reference_obj[0])
    print(f"Central row: {len(central_row)} objects, reference_idx: {reference_idx}")
    
    # Calculate Y positions for rows (central row at Y=0)
    row_y_positions = []
    row_heights = [max(size[1] for _, size in row) if row else 0 for row in rows]
    
    for row_idx in range(num_rows):
        current_height = row_heights[row_idx]
        if row_idx < central_row_idx:
            # Rows before central: stack upwards
            if row_idx == 0:
                y = -(row_heights[central_row_idx] / 2 + current_height / 2 + min_distance)
            else:
                y = row_y_positions[row_idx - 1] - (row_heights[row_idx - 1] / 2 + current_height / 2 + min_distance)
            row_y_positions.append(y)
        elif row_idx == central_row_idx:
            # Central row at Y=0
            row_y_positions.append(0)
        else:
            # Rows after central: stack downwards
            if row_idx == central_row_idx + 1:
                y = row_heights[central_row_idx] / 2 + current_height / 2 + min_distance
            else:
                y = row_y_positions[row_idx - 1] + (row_heights[row_idx - 1] / 2 + current_height / 2 + min_distance)
            row_y_positions.append(y)
        print(f"Row {row_idx}: y={row_y_positions[row_idx]}, height={current_height}")
    
    # Calculate X positions for each row, aligning objects with same count
    positions = []
    max_row_width = 0
    
    # First, calculate positions for central row to use for alignment
    central_row_positions = [None] * len(central_row)
    ref_width = reference_obj[1][0]
    central_row_positions[reference_idx] = (0, 0)
    
    # Place other objects symmetrically around reference in central row
    left_x = -(ref_width / 2 + min_distance)
    right_x = ref_width / 2 + min_distance
    left_idx = reference_idx - 1
    right_idx = reference_idx + 1
    
    for i in range(len(central_row)):
        if i != reference_idx:
            obj, (width, _) = central_row[i]
            if i < reference_idx:
                x = left_x - width / 2
                central_row_positions[left_idx] = (x, 0)
                left_x -= (width / 2 + min_distance)
                left_idx -= 1
            else:
                x = right_x + width / 2
                central_row_positions[right_idx] = (x, 0)
                right_x += (width / 2 + min_distance)
                right_idx += 1
    
    central_x_positions = [p[0] for p in central_row_positions if p is not None]
    print(f"Central row X positions: {central_x_positions}")
    
    # Calculate total width of central row
    central_row_width = sum(size[0] for _, size in central_row) + min_distance * (len(central_row) - 1) if central_row else 0
    
    # Now process all rows
    for row_idx, row in enumerate(rows):
        num_objects_in_row = len(row)
        row_height = max(size[1] for _, size in row) if row else 0
        
        # Calculate total width of the row
        total_width = sum(size[0] for _, size in row) + min_distance * (num_objects_in_row - 1) if row else 0
        max_row_width = max(max_row_width, total_width)
        print(f"Row {row_idx}: {num_objects_in_row} objects, total_width: {total_width}")
        
        # Calculate positions
        row_positions = [None] * num_objects_in_row
        
        if row_idx == central_row_idx:
            # Use pre-calculated central row positions
            row_positions = central_row_positions
        else:
            # Non-central row: align with central row if same number of objects
            if num_objects_in_row == len(central_row):
                for i in range(num_objects_in_row):
                    obj, (width, _) = row[i]
                    x = central_x_positions[i]
                    row_positions[i] = (x, row_y_positions[row_idx])
            else:
                # Place objects based on own row width
                start_x = -total_width / 2 if num_objects_in_row > 0 else 0
                for i in range(num_objects_in_row):
                    obj, (width, _) = row[i]
                    x = start_x + width / 2
                    row_positions[i] = (x, row_y_positions[row_idx])
                    start_x += width + min_distance
        
        positions.extend([p for p in row_positions if p is not None])
    
    # Apply positions, ensuring reference object stays at (0, 0)
    assigned_positions = []
    pos_idx = 0
    for row_idx, row in enumerate(rows):
        for obj, _ in row:
            x, y = positions[pos_idx]
            assigned_positions.append((obj, x, y))
            pos_idx += 1
    
    for obj, x, y in assigned_positions:
        if obj == reference_obj[0]:
            obj.location.x = 0
            obj.location.y = 0
            obj.location.z = 0
        else:
            obj.location.x = x
            obj.location.y = y
            obj.location.z = 0
        print(f"Object {obj.name}: x={x}, y={y}")

class OBJECT_OT_DistributeObjects(Operator):
    """Distribute selected objects in rows with a fixed reference object in center"""
    bl_idname = "object.distribute_objects"
    bl_label = "Distribute Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    min_distance: FloatProperty(
        name="Additional Distance",
        description="Additional distance between objects and rows",
        default=0.0,
        min=0.0
    )
    
    center_active: BoolProperty(
        name="Center Active Object",
        description="Use active object as the reference object at the center",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return len([obj for obj in context.selected_objects if obj.type == 'MESH']) > 0
    
    def execute(self, context):
        distribute_objects(self.min_distance, self.center_active)
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