bl_info = {
    "name": "Object Material Properties",
    "author": "Your Name",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "location": "Properties > Mesh > Object Materials",
    "description": "Adds four Enum properties to objects and meshes for selecting materials, with panel in Mesh Properties",
    "category": "Object",
}

import bpy
from bpy.props import EnumProperty

# Simplified material options as a list of strings
MATERIAL_OPTIONS = [
    "Light Wood",
    "Dark Wood",
    "Steel",
    "Stone",
    "Earth",
]

# Convert MATERIAL_OPTIONS to EnumProperty items format
ENUM_ITEMS = [(str(i), name, "") for i, name in enumerate(MATERIAL_OPTIONS)]

# Update function to sync Mesh properties to Object properties
def update_material(self, context):
    # Get the mesh (self is the Mesh)
    mesh = self
    # Get the active object from context
    obj = context.active_object
    if not obj or obj.data != mesh:
        print(f"Warning: No valid object found for mesh {mesh.name}")
        return
    
    # List of properties to sync
    properties = ['material_1', 'material_2', 'material_3', 'material_4']
    
    # Sync all properties
    for prop_name in properties:
        if prop_name in mesh:
            # Ensure the object has the property, initialize if missing
            if prop_name not in obj:
                obj[prop_name] = mesh[prop_name]
                print(f"Initialized {prop_name} on object {obj.name} to {mesh[prop_name]}")
            else:
                # Update the object property
                obj[prop_name] = mesh[prop_name]
                print(f"Synced {prop_name}: Mesh={mesh[prop_name]} ({MATERIAL_OPTIONS[int(mesh[prop_name])]}), Object={obj[prop_name]} ({MATERIAL_OPTIONS[int(obj[prop_name])]})")

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
            layout.prop(mesh, "material_1")
            layout.prop(mesh, "material_2")
            layout.prop(mesh, "material_3")
            layout.prop(mesh, "material_4")

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
    # Remove Object properties
    del bpy.types.Object.material_1
    del bpy.types.Object.material_2
    del bpy.types.Object.material_3
    del bpy.types.Object.material_4

if __name__ == "__main__":
    register()