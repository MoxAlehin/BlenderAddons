bl_info = {
    "name": "Color Palette",
    "author": "Mox Alehin",
    "version": (1, 14),
    "blender": (3, 0, 0),
    "location": "Properties > Mesh > Object Materials",
    "description": "Adds four Enum and four Color properties to objects and meshes, with panel in Mesh Properties",
    "category": "Object",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons"
}

import bpy
from bpy.props import EnumProperty, FloatVectorProperty
import json
import os

# Custom path to material_options.json (relative to user home directory)
CUSTOM_JSON_PATH = "Brain/Activities/App/Blender/Add-ons/MoxAddons/material_options.json"  # Change this to your preferred path

# Load MATERIAL_OPTIONS from JSON file
def load_material_options():
    # Get the user home directory
    home_dir = os.path.expanduser("~")
    json_path = os.path.join(home_dir, CUSTOM_JSON_PATH)
    
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading material_options.json from {json_path}: {e}")
        return {}

MATERIAL_OPTIONS = load_material_options()

# Convert MATERIAL_OPTIONS to EnumProperty items format
ENUM_ITEMS = [(str(i), name, "") for i, name in enumerate(MATERIAL_OPTIONS.keys())]

# Update function to sync Mesh material properties to Object
def update_material(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        print(f"Warning: No valid object found for mesh {mesh.name}")
        return
    
    properties = ['material_1', 'material_2', 'material_3', 'material_4']
    for prop_name in properties:
        if prop_name in mesh:
            if prop_name not in obj:
                obj[prop_name] = mesh[prop_name]
                print(f"Initialized {prop_name} on object {obj.name} to {mesh[prop_name]}")
            else:
                obj[prop_name] = mesh[prop_name]
                print(f"Synced {prop_name}: Mesh={mesh[prop_name]} ({list(MATERIAL_OPTIONS.keys())[int(mesh[prop_name])]}), Object={obj[prop_name]} ({list(MATERIAL_OPTIONS.keys())[int(obj[prop_name])]})")

# Update function to sync Mesh color properties to Object
def update_color(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        print(f"Warning: No valid object found for mesh {mesh.name}")
        return
    
    properties = ['color_1', 'color_2', 'color_3', 'color_4']
    for prop_name in properties:
        if prop_name in mesh:
            if prop_name not in obj:
                obj[prop_name] = mesh[prop_name]
                print(f"Initialized {prop_name} on object {obj.name} to {mesh[prop_name]}")
            else:
                obj[prop_name] = mesh[prop_name]
                print(f"Synced {prop_name}: Mesh={mesh[prop_name][:3]}, Object={obj[prop_name][:3]}")

# Define EnumProperty for Mesh
bpy.types.Mesh.material_1 = EnumProperty(
    name="Material 1",
    description="First material slot for the mesh",
    items=ENUM_ITEMS,
    default='0',
    update=update_material
)

bpy.types.Mesh.material_2 = EnumProperty(
    name="Material 2",
    description="Second material slot for the mesh",
    items=ENUM_ITEMS,
    default='0',
    update=update_material
)

bpy.types.Mesh.material_3 = EnumProperty(
    name="Material 3",
    description="Third material slot for the mesh",
    items=ENUM_ITEMS,
    default='0',
    update=update_material
)

bpy.types.Mesh.material_4 = EnumProperty(
    name="Material 4",
    description="Fourth material slot for the mesh",
    items=ENUM_ITEMS,
    default='0',
    update=update_material
)

# Define FloatVectorProperty for Mesh (Color)
bpy.types.Mesh.color_1 = FloatVectorProperty(
    name="Color 1",
    description="First color slot for the mesh",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0),  # Black by default
    update=update_color
)

bpy.types.Mesh.color_2 = FloatVectorProperty(
    name="Color 2",
    description="Second color slot for the mesh",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0),  # Black by default
    update=update_color
)

bpy.types.Mesh.color_3 = FloatVectorProperty(
    name="Color 3",
    description="Third color slot for the mesh",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0),  # Black by default
    update=update_color
)

bpy.types.Mesh.color_4 = FloatVectorProperty(
    name="Color 4",
    description="Fourth color slot for the mesh",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0),  # Black by default
    update=update_color
)

# Define EnumProperty for Object
bpy.types.Object.material_1 = EnumProperty(
    name="Material 1",
    description="First material slot for the object",
    items=ENUM_ITEMS,
    default='0'
)

bpy.types.Object.material_2 = EnumProperty(
    name="Material 2",
    description="Second material slot for the object",
    items=ENUM_ITEMS,
    default='0'
)

bpy.types.Object.material_3 = EnumProperty(
    name="Material 3",
    description="Third material slot for the object",
    items=ENUM_ITEMS,
    default='0'
)

bpy.types.Object.material_4 = EnumProperty(
    name="Material 4",
    description="Fourth material slot for the object",
    items=ENUM_ITEMS,
    default='0'
)

# Define FloatVectorProperty for Object (Color)
bpy.types.Object.color_1 = FloatVectorProperty(
    name="Color 1",
    description="First color slot for the object",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0)  # Black by default
)

bpy.types.Object.color_2 = FloatVectorProperty(
    name="Color 2",
    description="Second color slot for the object",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0)  # Black by default
)

bpy.types.Object.color_3 = FloatVectorProperty(
    name="Color 3",
    description="Third color slot for the object",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0)  # Black by default
)

bpy.types.Object.color_4 = FloatVectorProperty(
    name="Color 4",
    description="Fourth color slot for the object",
    subtype='COLOR',
    size=3,
    min=0.0,
    max=1.0,
    default=(0.0, 0.0, 0.0)  # Black by default
)

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
            # First row: Material 1, Color 1, Material 2, Color 2
            row = layout.row()
            row.prop(mesh, "material_1", text="")
            row.prop(mesh, "color_1", text="")
            row.prop(mesh, "material_2", text="")
            row.prop(mesh, "color_2", text="")
            # Second row: Material 3, Color 3, Material 4, Color 4
            row = layout.row()
            row.prop(mesh, "material_3", text="")
            row.prop(mesh, "color_3", text="")
            row.prop(mesh, "material_4", text="")
            row.prop(mesh, "color_4", text="")

# Register the addon
def register():
    bpy.utils.register_class(MATERIAL_PT_panel)

# Unregister the addon
def unregister():
    bpy.utils.unregister_class(MATERIAL_PT_panel)
    # Remove Mesh properties
    del bpy.types.Mesh.material_1
    del bpy.types.Mesh.material_2
    del bpy.types.Mesh.material_3
    del bpy.types.Mesh.material_4
    del bpy.types.Mesh.color_1
    del bpy.types.Mesh.color_2
    del bpy.types.Mesh.color_3
    del bpy.types.Mesh.color_4
    # Remove Object properties
    del bpy.types.Object.material_1
    del bpy.types.Object.material_2
    del bpy.types.Object.material_3
    del bpy.types.Object.material_4
    del bpy.types.Object.color_1
    del bpy.types.Object.color_2
    del bpy.types.Object.color_3
    del bpy.types.Object.color_4

if __name__ == "__main__":
    register()