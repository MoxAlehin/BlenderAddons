bl_info = {
    "name": "Color Palette",
    "author": "Mox Alehin",
    "version": (1, 36),
    "blender": (3, 0, 0),
    "location": "Properties > Mesh > Object Materials",
    "description": "Adds four Enum and four Color properties to objects and meshes, with panel in Mesh Properties",
    "category": "Object",
}

import bpy
from bpy.props import EnumProperty, FloatVectorProperty, StringProperty, IntProperty
from bpy.app.handlers import persistent
import json
import os

# Custom path to material_options.json (relative to user home directory)
CUSTOM_JSON_PATH = "Brain/Activities/App/Blender/Add-ons/MoxAddons/material_options.json"

# Global material options and enum items
MATERIAL_OPTIONS = {}
ENUM_ITEMS = []

# Load MATERIAL_OPTIONS from JSON file
def load_material_options():
    home_dir = os.path.expanduser("~")
    json_path = os.path.join(home_dir, CUSTOM_JSON_PATH)
    
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading material_options.json from {json_path}: {e}")
        return {"None": "#000000"}

# Save MATERIAL_OPTIONS to JSON file
def save_material_options():
    home_dir = os.path.expanduser("~")
    json_path = os.path.join(home_dir, CUSTOM_JSON_PATH)
    
    try:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(MATERIAL_OPTIONS, f, indent=4)
        print(f"Saved material_options.json to {json_path}")
    except Exception as e:
        print(f"Error saving material_options.json to {json_path}: {e}")

# Update ENUM_ITEMS based on MATERIAL_OPTIONS
def update_enum_items():
    global ENUM_ITEMS
    ENUM_ITEMS = [(str(i), name, "") for i, name in enumerate(MATERIAL_OPTIONS.keys())]
    # Update EnumProperty items for all material properties
    for i in range(1, 5):
        prop_name = f"material_{i}"
        for target in (bpy.types.Mesh, bpy.types.Object):
            if hasattr(target, '__annotations__') and prop_name in target.__annotations__:
                prop = target.__annotations__[prop_name]
                prop.keywords['items'] = ENUM_ITEMS
                # Reset to default if current value is invalid
                for obj in bpy.data.objects:
                    if obj.type == 'MESH' and obj.data:
                        mesh = obj.data
                        if prop_name in mesh and int(mesh[prop_name]) >= len(ENUM_ITEMS):
                            mesh[prop_name] = '0'
                        if prop_name in obj and int(obj[prop_name]) >= len(ENUM_ITEMS):
                            obj[prop_name] = '0'

# Initialize MATERIAL_OPTIONS and ENUM_ITEMS
MATERIAL_OPTIONS = load_material_options()
update_enum_items()

# Convert hex color to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

# Update function to sync Mesh material properties to Object and update colors
def update_material(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        print(f"Warning: No valid object found for mesh {mesh.name}")
        return
    
    properties = ['material_1', 'material_2', 'material_3', 'material_4']
    for prop_name in properties:
        if prop_name not in mesh:
            mesh[prop_name] = '0'
            print(f"Initialized {prop_name} on mesh {mesh.name} to '0'")
        if prop_name not in obj:
            obj[prop_name] = '0'
            print(f"Initialized {prop_name} on object {obj.name} to '0'")
        
        obj[prop_name] = mesh[prop_name]
        print(f"Synced {prop_name}: Mesh={mesh[prop_name]} ({list(MATERIAL_OPTIONS.keys())[int(mesh[prop_name])]}), Object={obj[prop_name]} ({list(MATERIAL_OPTIONS.keys())[int(obj[prop_name])]})")
        
        material_name = list(MATERIAL_OPTIONS.keys())[int(mesh[prop_name])]
        color_prop = f"color_{prop_name.split('_')[1]}"
        if material_name != "None":
            if color_prop not in mesh:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                print(f"Initialized {color_prop} on mesh {mesh.name} to (0.0, 0.0, 0.0)")
            if color_prop not in obj:
                obj[color_prop] = (0.0, 0.0, 0.0)
                print(f"Initialized {color_prop} on object {obj.name} to (0.0, 0.0, 0.0)")
            
            hex_color = MATERIAL_OPTIONS[material_name]
            rgb_color = hex_to_rgb(hex_color)
            mesh[color_prop] = rgb_color
            obj[color_prop] = rgb_color
            print(f"Updated {color_prop}: Set to {rgb_color} from {material_name} ({hex_color})")

# Update function to sync Mesh color properties to Object and enforce read-only
def update_color(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        print(f"Warning: No valid object found for mesh {mesh.name}")
        return
    
    properties = ['color_1', 'color_2', 'color_3', 'color_4']
    for prop_name in properties:
        if prop_name not in mesh:
            mesh[prop_name] = (0.0, 0.0, 0.0)
            print(f"Initialized {prop_name} on mesh {mesh.name} to (0.0, 0.0, 0.0)")
        if prop_name not in obj:
            obj[prop_name] = (0.0, 0.0, 0.0)
            print(f"Initialized {prop_name} on object {obj.name} to (0.0, 0.0, 0.0)")
        
        material_prop = f"material_{prop_name.split('_')[1]}"
        if material_prop not in mesh:
            mesh[material_prop] = '0'
            print(f"Initialized {material_prop} on mesh {mesh.name} to '0'")
        if material_prop not in obj:
            obj[material_prop] = '0'
            print(f"Initialized {prop_name} on object {obj.name} to '0'")
        
        material_name = list(MATERIAL_OPTIONS.keys())[int(mesh[material_prop])]
        if material_name != "None":
            hex_color = MATERIAL_OPTIONS[material_name]
            rgb_color = hex_to_rgb(hex_color)
            if tuple(mesh[prop_name]) != rgb_color:
                mesh[prop_name] = rgb_color
                obj[prop_name] = rgb_color
                print(f"Reverted {prop_name}: Set to {rgb_color} from {material_name} ({hex_color})")
        else:
            obj[prop_name] = mesh[prop_name]
            print(f"Synced {prop_name}: Mesh={mesh[prop_name][:3]}, Object={obj[prop_name][:3]}")

# Operator to sync material colors for all mesh objects in the scene
class SyncMaterialColorsOperator(bpy.types.Operator):
    bl_idname = "object.sync_material_colors"
    bl_label = "Sync Material Colors"
    bl_description = "Synchronize colors for all mesh objects in the scene based on their material properties"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True  # Button is always active

    def execute(self, context):
        print("Executing SyncMaterialColorsOperator")
        original_active = context.active_object
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data:
                context.view_layer.objects.active = obj
                mesh = obj.data
                update_material(mesh, context)
                update_color(mesh, context)
                # Update mesh to apply custom properties
                mesh.update()
                print(f"Processed {obj.name} for material and color sync")
        context.view_layer.objects.active = original_active
        # Update dependency graph
        context.view_layer.depsgraph.update()
        # Force redraw
        bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
        return {'FINISHED'}

# UI List for displaying materials
class MATERIAL_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False)
        # Use a sub-row to control color picker appearance
        color_row = row.row()
        color_row.ui_units_x = 4  # Fixed width for consistency
        color_row.prop(item, "color", text="")
        # Remove rounded corners by setting a style
        color_row.emboss = 'NONE_OR_STATUS'

# Operator to edit materials
class EditMaterialsOperator(bpy.types.Operator):
    bl_idname = "object.edit_materials"
    bl_label = "Edit Materials"
    bl_description = "Edit material options for the addon"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        # Initialize temporary material list, excluding "None"
        context.scene.material_items.clear()
        for name, hex_color in MATERIAL_OPTIONS.items():
            if name != "None":
                item = context.scene.material_items.add()
                item.name = name
                item.color = hex_to_rgb(hex_color)
        
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        # Button row at the top
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("material.add_material", text="+")
        row.operator("material.delete_material", text="−")
        row.operator("material.move_material_up", text="↑")
        row.operator("material.move_material_down", text="↓")
        
        # Material list with dynamic height
        num_items = len(context.scene.material_items)
        rows = min(num_items if num_items > 0 else 1, 30)  # At least 1 row, max 30
        layout.template_list(
            "MATERIAL_UL_materials",
            "",
            context.scene,
            "material_items",
            context.scene,
            "material_index",
            rows=rows
        )

    def execute(self, context):
        global MATERIAL_OPTIONS
        # Start with "None" as the first entry
        MATERIAL_OPTIONS = {"None": "#000000"}
        # Add other materials from material_items
        for item in context.scene.material_items:
            if item.name and item.name != "None":
                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(item.color[0] * 255),
                    int(item.color[1] * 255),
                    int(item.color[2] * 255)
                )
                MATERIAL_OPTIONS[item.name] = hex_color
        
        # Save to JSON
        save_material_options()
        
        # Update ENUM_ITEMS
        update_enum_items()
        
        # Sync all objects
        original_active = context.active_object
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data:
                context.view_layer.objects.active = obj
                mesh = obj.data
                update_material(mesh, context)
                update_color(mesh, context)
                # Update mesh to apply custom properties
                mesh.update()
        context.view_layer.objects.active = original_active
        # Update dependency graph
        context.view_layer.depsgraph.update()
        # Force redraw
        bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
        return {'FINISHED'}

# Operator to add a new material
class AddMaterialOperator(bpy.types.Operator):
    bl_idname = "material.add_material"
    bl_label = "Add Material"
    bl_description = "Add a new material to the list"

    def execute(self, context):
        item = context.scene.material_items.add()
        item.name = "New Material"
        item.color = (1.0, 1.0, 1.0)  # Default to white
        context.scene.material_index = len(context.scene.material_items) - 1
        return {'FINISHED'}

# Operator to delete a material
class DeleteMaterialOperator(bpy.types.Operator):
    bl_idname = "material.delete_material"
    bl_label = "Delete Material"
    bl_description = "Delete the selected material"

    def execute(self, context):
        if context.scene.material_index < len(context.scene.material_items):
            context.scene.material_items.remove(context.scene.material_index)
            context.scene.material_index = min(context.scene.material_index, len(context.scene.material_items) - 1)
        return {'FINISHED'}

# Operator to move material up
class MoveMaterialUpOperator(bpy.types.Operator):
    bl_idname = "material.move_material_up"
    bl_label = "Move Material Up"
    bl_description = "Move the selected material up in the list"

    def execute(self, context):
        index = context.scene.material_index
        if index > 0:
            context.scene.material_items.move(index, index - 1)
            context.scene.material_index -= 1
        return {'FINISHED'}

# Operator to move material down
class MoveMaterialDownOperator(bpy.types.Operator):
    bl_idname = "material.move_material_down"
    bl_label = "Move Material Down"
    bl_description = "Move the selected material down in the list"

    def execute(self, context):
        index = context.scene.material_index
        if index < len(context.scene.material_items) - 1:
            context.scene.material_items.move(index, index + 1)
            context.scene.material_index += 1
        return {'FINISHED'}

# Custom property group for material items
class MaterialItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Material")
    color: FloatVectorProperty(name="Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0))

# Function to register material EnumProperty
def register_material_property(prop_name, target):
    setattr(target, prop_name, EnumProperty(
        name=prop_name.replace('_', ' ').title(),
        items=ENUM_ITEMS,
        default='0',
        update=update_material if target == bpy.types.Mesh else None
    ))

# Function to register color FloatVectorProperty
def register_color_property(prop_name, target):
    setattr(target, prop_name, FloatVectorProperty(
        name=prop_name.replace('_', ' ').title(),
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.0, 0.0, 0.0),
        update=update_color if target == bpy.types.Mesh else None
    ))

# Register properties
for i in range(1, 5):
    material_prop = f"material_{i}"
    color_prop = f"color_{i}"
    register_material_property(material_prop, bpy.types.Mesh)
    register_color_property(color_prop, bpy.types.Mesh)
    register_material_property(material_prop, bpy.types.Object)
    register_color_property(color_prop, bpy.types.Object)

# Register custom properties for material editing
bpy.utils.register_class(MaterialItem)
bpy.types.Scene.material_items = bpy.props.CollectionProperty(type=MaterialItem)
bpy.types.Scene.material_index = IntProperty(name="Material Index", default=0)

# Custom panel in Mesh Properties
class MATERIAL_PT_panel(bpy.types.Panel):
    bl_label = "Object Materials"
    bl_idname = "PT_ObjectMaterials"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"  # Mesh Properties

    def draw(self, context):
        layout = self.layout
        mesh = context.mesh
        if mesh:
            row = layout.row()

            column = row.column()
            column.prop(mesh, "material_1", text="")
            column.prop(mesh, "material_3", text="")

            column = row.column()
            column.scale_x = 0.35
            column.prop(mesh, "color_1", text="")
            column.prop(mesh, "color_3", text="")

            column = row.column()
            column.prop(mesh, "material_2", text="")
            column.prop(mesh, "material_4", text="")

            column = row.column()
            column.scale_x = 0.35
            column.prop(mesh, "color_2", text="")
            column.prop(mesh, "color_4", text="")

            # Buttons
            row = layout.row()
            row.operator("object.sync_material_colors", text="Sync Colors")
            row.operator("object.edit_materials", text="Edit Materials")

# Handler for auto-sync after loading a .blend file
@persistent
def auto_sync_post_load(dummy):
    try:
        bpy.ops.object.sync_material_colors()
        print("Auto-sync triggered after file load")
        return
    except Exception as e:
        print(f"Error during auto-sync after file load: {e}")

# Register the addon
def register():
    bpy.utils.register_class(MATERIAL_PT_panel)
    bpy.utils.register_class(SyncMaterialColorsOperator)
    bpy.utils.register_class(EditMaterialsOperator)
    bpy.utils.register_class(MATERIAL_UL_materials)
    bpy.utils.register_class(AddMaterialOperator)
    bpy.utils.register_class(DeleteMaterialOperator)
    bpy.utils.register_class(MoveMaterialUpOperator)
    bpy.utils.register_class(MoveMaterialDownOperator)
    # Register load_post handler
    bpy.app.handlers.load_post.append(auto_sync_post_load)
    print("Registered SyncMaterialColorsOperator, EditMaterialsOperator, and auto-sync handler")

# Unregister the addon
def unregister():
    bpy.utils.unregister_class(MATERIAL_PT_panel)
    bpy.utils.unregister_class(SyncMaterialColorsOperator)
    bpy.utils.unregister_class(EditMaterialsOperator)
    bpy.utils.unregister_class(MATERIAL_UL_materials)
    bpy.utils.unregister_class(AddMaterialOperator)
    bpy.utils.unregister_class(DeleteMaterialOperator)
    bpy.utils.unregister_class(MoveMaterialUpOperator)
    bpy.utils.unregister_class(MoveMaterialDownOperator)
    # Remove load_post handler
    if auto_sync_post_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(auto_sync_post_load)
    del bpy.types.Scene.material_items
    del bpy.types.Scene.material_index
    print("Unregistered SyncMaterialColorsOperator, EditMaterialsOperator, and auto-sync handler")
    for i in range(1, 5):
        for target in (bpy.types.Mesh, bpy.types.Object):
            for prop in (f"material_{i}", f"color_{i}"):
                if hasattr(target, prop):
                    delattr(target, prop)

if __name__ == "__main__":
    register()