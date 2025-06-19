import bpy
from bpy.props import IntProperty, FloatVectorProperty, StringProperty, BoolProperty, EnumProperty
from bpy.app.handlers import persistent
import json
import os
import colorsys

bl_info = {
    "name": "Color Palette",
    "author": "Mox Alehin",
    "version": (2, 24),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Header",
    "description": "Adds four Int pairs and color properties to objects and meshes, with buttons in 3D Viewport Header",
    "category": "Object",
}

# Custom path to material_options.json
CUSTOM_JSON_PATH = "Brain/Activities/App/Blender/Add-ons/MoxAddons/material_options.json"

# Global material options
MATERIAL_OPTIONS = {"materials": [], "colors": []}

# Load MATERIAL_OPTIONS from JSON file
def load_material_options():
    home_dir = os.path.expanduser("~")
    json_path = os.path.join(home_dir, CUSTOM_JSON_PATH)
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data.setdefault("materials", [{"id": 0, "name": "None", "color": "#000000"}])
            data.setdefault("colors", [{"id": 0, "name": "None", "color": "#000000"}])
            for mode in ("materials", "colors"):
                ids = set()
                for item in data[mode]:
                    # Ensure id is an integer
                    try:
                        item["id"] = int(item["id"])
                    except (ValueError, TypeError):
                        item["id"] = max(ids, default=-1) + 1
                    if item["id"] in ids:
                        item["id"] = max(ids, default=-1) + 1
                    ids.add(item["id"])
            return data
    print(f"Warning: material_options.json not found at {json_path}, using default")
    return {
        "materials": [{"id": 0, "name": "None", "color": "#000000"}],
        "colors": [{"id": 0, "name": "None", "color": "#000000"}]
    }

# Save MATERIAL_OPTIONS to JSON file
def save_material_options():
    home_dir = os.path.expanduser("~")
    json_path = os.path.join(home_dir, CUSTOM_JSON_PATH)
    
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        sorted_data = {
            "materials": sorted(MATERIAL_OPTIONS["materials"], key=lambda x: x["name"].lower()),
            "colors": sorted(MATERIAL_OPTIONS["colors"], key=lambda x: x["name"].lower())
        }
        json.dump(sorted_data, f, indent=4)

# Convert hex color to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

# Convert hex color to HSV tuple for sorting
def hex_to_hsv(hex_color):
    rgb = hex_to_rgb(hex_color)
    return colorsys.rgb_to_hsv(*rgb)

# Update material_items based on mode, sort, and search
def update_material_items(context):
    context.scene.material_items.clear()
    mode = context.scene.edit_mode
    items = MATERIAL_OPTIONS[mode]
    
    if context.scene.sort_mode == "name":
        items = sorted(items, key=lambda x: x["name"].lower())
    else:  # color
        items = sorted(items, key=lambda x: hex_to_hsv(x["color"]) if x["name"] != "None" else (0, 0, 0))
    
    for item in items:
        if item["name"] != "None" and (not context.scene.search_query or context.scene.search_query.lower() in item["name"].lower()):
            new_item = context.scene.material_items.add()
            new_item.name = item["name"]
            new_item.color = hex_to_rgb(item["color"])
            new_item.id = item["id"]
    
    if context.area:
        context.area.tag_redraw()

# Update modal options list
def update_modal_options(context):
    context.scene.modal_options.clear()
    if not context.scene.active_property:
        return
    
    # Check if active object is a mesh
    mesh = None
    if context.active_object and context.active_object.type == 'MESH' and context.active_object.data:
        mesh = context.active_object.data
    
    if not mesh:
        return
    
    mode = "materials" if context.scene.active_property.startswith("material_") else "colors"
    # Check if the active_property exists in the mesh
    active_id = mesh.get(context.scene.active_property, 0)  # Default to 0 if property doesn't exist
    items = MATERIAL_OPTIONS[mode]
    
    # Apply sorting
    if context.scene.modal_sort_mode == "name":
        items = sorted(items, key=lambda x: x["name"].lower())
    else:  # color
        items = sorted(items, key=lambda x: hex_to_hsv(x["color"]) if x["name"] != "None" else (0, 0, 0))
    
    # Add filtered items
    active_index = -1
    for index, item in enumerate(items):
        if item["name"] != "None" and (not context.scene.modal_search_query or context.scene.modal_search_query.lower() in item["name"].lower()):
            new_item = context.scene.modal_options.add()
            new_item.name = item["name"]
            new_item.color = hex_to_rgb(item["color"])
            new_item.id = item["id"]
            if item["id"] == active_id:
                active_index = context.scene.modal_options.find(new_item.name)
    
    # Set active option
    context.scene.modal_options_index = active_index if active_index >= 0 else 0
    
    if context.area:
        context.area.tag_redraw()

# Update MATERIAL_OPTIONS and re-register properties
def update_material_options_and_enums(context):
    global MATERIAL_OPTIONS
    
    saved_props = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            saved_props[obj.name] = {
                'mesh': {f"material_{i}": int(mesh.get(f"material_{i}", 0)) for i in range(1, 5)},
                'obj': {f"material_{i}": int(obj.get(f"material_{i}", 0)) for i in range(1, 5)},
                'mesh_color_ids': {f"color_id_{i}": int(mesh.get(f"color_id_{i}", 0)) for i in range(1, 5)},
                'obj_color_ids': {f"color_id_{i}": int(obj.get(f"color_id_{i}", 0)) for i in range(1, 5)},
                'mesh_colors': {f"color_{i}": mesh.get(f"color_{i}", (0.0, 0.0, 0.0)) for i in range(1, 5)},
                'obj_colors': {f"color_{i}": obj.get(f"color_{i}", (0.0, 0.0, 0.0)) for i in range(1, 5)},
            }
    
    active_mode = context.scene.edit_mode
    MATERIAL_OPTIONS[active_mode] = [{"id": 0, "name": "None", "color": "#000000"}]
    for item in context.scene.material_items:
        if item.name and item.name != "None":
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(item.color[0] * 255),
                int(item.color[1] * 255),
                int(item.color[2] * 255)
            )
            MATERIAL_OPTIONS[active_mode].append({
                "id": item.id,
                "name": item.name,
                "color": hex_color
            })
    
    save_material_options()
    
    for i in range(1, 5):
        for target in (bpy.types.Mesh, bpy.types.Object):
            for prop in (f"material_{i}", f"color_id_{i}", f"color_{i}"):
                if hasattr(target, prop):
                    delattr(target, prop)
    
    register_properties()
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data and obj.name in saved_props:
            mesh = obj.data
            props = saved_props[obj.name]
            for i in range(1, 5):
                material_prop = f"material_{i}"
                color_id_prop = f"color_id_{i}"
                color_prop = f"color_{i}"
                mesh[material_prop] = props['mesh'][material_prop]
                obj[material_prop] = props['obj'][material_prop]
                mesh[color_id_prop] = props['mesh_color_ids'][color_id_prop]
                obj[color_id_prop] = props['obj_color_ids'][color_id_prop]
                mesh[color_prop] = props['mesh_colors'][color_prop]
                obj[color_prop] = props['obj_colors'][color_prop]

# Update function for material properties
def update_material(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        return
    
    properties = [f"material_{i}" for i in range(1, 5)]
    for material_prop in properties:
        if material_prop not in mesh:
            mesh[material_prop] = 0
        if material_prop not in obj:
            obj[material_prop] = 0
        # Ensure integer value
        if not isinstance(mesh[material_prop], int):
            print(f"Warning: {material_prop} is {type(mesh[material_prop])}, resetting to 0")
            mesh[material_prop] = 0
        obj[material_prop] = mesh[material_prop]
        
        color_id_prop = f"color_id_{material_prop.split('_')[1]}"
        color_prop = f"color_{material_prop.split('_')[1]}"
        if color_id_prop not in mesh:
            mesh[color_id_prop] = 0
        if color_id_prop not in obj:
            obj[color_id_prop] = 0
        if color_prop not in mesh:
            mesh[color_prop] = (0.0, 0.0, 0.0)
        if color_prop not in obj:
            obj[color_prop] = (0.0, 0.0, 0.0)
        
        color_id = mesh[color_id_prop]
        material_id = mesh[material_prop]
        
        if color_id != 0:
            color_item = next((c for c in MATERIAL_OPTIONS["colors"] if c["id"] == color_id), None)
            if color_item and color_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(color_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)
        else:
            material_item = next((m for m in MATERIAL_OPTIONS["materials"] if m["id"] == material_id), None)
            if material_item and material_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(material_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)

# Update function for color_id properties
def update_color_id(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        return
    
    properties = [f"color_id_{i}" for i in range(1, 5)]
    for color_id_prop in properties:
        if color_id_prop not in mesh:
            mesh[color_id_prop] = 0
        if color_id_prop not in obj:
            obj[color_id_prop] = 0
        # Ensure integer value
        if not isinstance(mesh[color_id_prop], int):
            print(f"Warning: {color_id_prop} is {type(mesh[color_id_prop])}, resetting to 0")
            mesh[color_id_prop] = 0
        obj[color_id_prop] = mesh[color_id_prop]
        
        material_prop = f"material_{color_id_prop.split('_')[2]}"
        color_prop = f"color_{color_id_prop.split('_')[2]}"
        if material_prop not in mesh:
            mesh[material_prop] = 0
        if material_prop not in obj:
            obj[material_prop] = 0
        if color_prop not in mesh:
            mesh[color_prop] = (0.0, 0.0, 0.0)
        if color_prop not in obj:
            obj[color_prop] = (0.0, 0.0, 0.0)
        
        color_id = mesh[color_id_prop]
        material_id = mesh[material_prop]
        
        if color_id != 0:
            color_item = next((c for c in MATERIAL_OPTIONS["colors"] if c["id"] == color_id), None)
            if color_item and color_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(color_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)
        else:
            material_item = next((m for m in MATERIAL_OPTIONS["materials"] if m["id"] == material_id), None)
            if material_item and material_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(material_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)

# Update function to protect color_x from manual changes
def update_color_protect(self, context):
    mesh = self
    obj = context.active_object
    if not obj or obj.data != mesh:
        return
    
    for i in range(1, 5):
        color_id = mesh.get(f"color_id_{i}", 0)
        material_id = mesh.get(f"material_{i}", 0)
        color_prop = f"color_{i}"
        
        if color_id != 0:
            color_item = next((c for c in MATERIAL_OPTIONS["colors"] if c["id"] == color_id), None)
            if color_item and color_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(color_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)
        else:
            material_item = next((m for m in MATERIAL_OPTIONS["materials"] if m["id"] == material_id), None)
            if material_item and material_item["name"] != "None":
                mesh[color_prop] = hex_to_rgb(material_item["color"])
                obj[color_prop] = mesh[color_prop]
            else:
                mesh[color_prop] = (0.0, 0.0, 0.0)
                obj[color_prop] = (0.0, 0.0, 0.0)

# Function to safely open .blend file containing an asset
def open_asset_blend_file(context):
    if not hasattr(context, "asset") or not context.asset:
        print("Error: No active asset found in context")
        return False
    
    asset_file = context.asset.filepath
    if not asset_file or not os.path.exists(asset_file):
        print(f"Error: Asset file path invalid or missing: {asset_file}")
        return False
    
    if bpy.ops.asset.open_containing_blend_file.poll():
        bpy.ops.asset.open_containing_blend_file()
        return True
    else:
        print("Warning: asset.open_containing_blend_file() not available, using wm.open_mainfile")
        bpy.ops.wm.open_mainfile(filepath=asset_file)
        return True

# Operator to sync material and color properties for all mesh objects
class SyncMaterialColorsOperator(bpy.types.Operator):
    bl_idname = "object.sync_material_colors"
    bl_label = "Sync Material Colors"
    bl_description = "Synchronize material and color properties for all mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        original_active = context.active_object
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data:
                context.view_layer.objects.active = obj
                mesh = obj.data
                update_material(mesh, context)
                update_color_id(mesh, context)
                mesh.update()
        context.view_layer.objects.active = original_active
        context.view_layer.depsgraph.update()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
        return {'FINISHED'}

# Operator to reset material_x to None
class ResetMaterialOperator(bpy.types.Operator):
    bl_idname = "material.reset_material"
    bl_label = "Reset Material"
    bl_description = "Reset the material to None"
    index: IntProperty(name="Index")

    def execute(self, context):
        mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
        if mesh:
            material_prop = f"material_{self.index}"
            print(f"Resetting {material_prop} to 0")
            mesh[material_prop] = 0
            update_material(mesh, context)
            update_modal_options(context)
            bpy.ops.object.sync_material_colors()
        return {'FINISHED'}

# Operator to reset color_id to None
class ResetColorOperator(bpy.types.Operator):
    bl_idname = "material.reset_color"
    bl_label = "Reset Color"
    bl_description = "Reset the color to None"
    index: IntProperty(name="Index")

    def execute(self, context):
        mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
        if mesh:
            color_id_prop = f"color_id_{self.index}"
            print(f"Resetting {color_id_prop} to 0")
            mesh[color_id_prop] = 0
            update_color_id(mesh, context)
            update_modal_options(context)
            bpy.ops.object.sync_material_colors()
        return {'FINISHED'}

# Operator to clear modal search query
class ClearModalSearchOperator(bpy.types.Operator):
    bl_idname = "material.clear_modal_search"
    bl_label = "Clear Search"
    bl_description = "Clear the search query in the modal dialog"

    def execute(self, context):
        context.scene.modal_search_query = ""
        update_modal_options(context)
        bpy.ops.object.sync_material_colors()
        return {'FINISHED'}

# Operator to assign a material/color ID to the active property
class AssignMaterialIDOperator(bpy.types.Operator):
    bl_idname = "material.assign_id"
    bl_label = "Assign ID"
    bl_description = "Assign the selected material or color ID to the active property for all selected objects"
    item_id: IntProperty(name="Item ID")

    def execute(self, context):
        prop_name = context.scene.active_property
        if not prop_name:
            return {'CANCELLED'}
        
        # Update all selected objects
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj.data:
                mesh = obj.data
                mesh[prop_name] = self.item_id
                if prop_name.startswith("material_"):
                    update_material(mesh, context)
                elif prop_name.startswith("color_id_"):
                    update_color_id(mesh, context)
        
        update_modal_options(context)
        if context.area:
            context.area.tag_redraw()
        # Trigger sync to update material custom properties
        bpy.ops.object.sync_material_colors()
        return {'FINISHED'}

# Operator to select a toggle button
class SelectToggleOperator(bpy.types.Operator):
    bl_idname = "material.select_toggle"
    bl_label = "Select Toggle"
    bl_description = "Select a toggle and deselect all others"
    prop_name: StringProperty(name="Property Name")

    def execute(self, context):
        context.scene.active_property = self.prop_name
        # Update toggle states
        for i in range(1, 5):
            for prop in (f"material_{i}", f"color_id_{i}"):
                setattr(context.scene, f"toggle_{prop}", prop == self.prop_name)
        update_modal_options(context)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}

# Operator to set material parameters in a modal dialog
class SetMaterialParamsOperator(bpy.types.Operator):
    bl_idname = "object.set_material_params"
    bl_label = "Set Material Parameters"
    bl_description = "Set material and color properties for active and selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    cached_props = {}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.active_object.data is not None

    def invoke(self, context, event):
        global MATERIAL_OPTIONS
        MATERIAL_OPTIONS = load_material_options()
        self.cached_props = {}
        
        # Check if active object is a mesh
        if not context.active_object or context.active_object.type != 'MESH' or not context.active_object.data:
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}
        
        # Initialize properties for active mesh
        active_mesh = context.active_object.data
        active_obj = context.active_object
        for i in range(1, 5):
            material_prop = f"material_{i}"
            color_id_prop = f"color_id_{i}"
            color_prop = f"color_{i}"
            if material_prop not in active_mesh:
                active_mesh[material_prop] = 0
            if material_prop not in active_obj:
                active_obj[material_prop] = 0
            if color_id_prop not in active_mesh:
                active_mesh[color_id_prop] = 0
            if color_id_prop not in active_obj:
                active_obj[color_id_prop] = 0
            if color_prop not in active_mesh:
                active_mesh[color_prop] = (0.0, 0.0, 0.0)
            if color_prop not in active_obj:
                active_obj[color_prop] = (0.0, 0.0, 0.0)
        
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj.data:
                mesh = obj.data
                self.cached_props[obj.name] = {
                    f"material_{i}": int(mesh.get(f"material_{i}", 0)) for i in range(1, 5)
                }
                self.cached_props[obj.name].update({
                    f"color_id_{i}": int(mesh.get(f"color_id_{i}", 0)) for i in range(1, 5)
                })
                self.cached_props[obj.name].update({
                    f"color_{i}": mesh.get(f"color_{i}", (0.0, 0.0, 0.0)) for i in range(1, 5)
                })
        # Initialize with material_1 active
        if not hasattr(context.scene, "active_property") or not context.scene.active_property:
            context.scene.active_property = "material_1"
            context.scene.toggle_material_1 = True
            for i in range(1, 5):
                for prop in (f"material_{i}", f"color_id_{i}"):
                    if prop != "material_1":
                        setattr(context.scene, f"toggle_{prop}", False)
        context.scene.modal_search_query = ""  # Reset search
        context.scene.modal_sort_mode = "color"  # Default sort
        update_modal_options(context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
        if not mesh:
            return

        # Compact layout with unified blocks and minimal row spacing
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Select Property to Edit:")
        
        for i in range(1, 5):
            split = col.split(factor=0.95, align=True)  # Main split for row
            row = split.row(align=True)
            # Material toggle with reset
            mat_prop = f"material_{i}"
            mat_id = mesh.get(mat_prop, 0)
            mat_item = next((m for m in MATERIAL_OPTIONS["materials"] if m["id"] == mat_id), {"name": "None"})
            sub = row.split(factor=0.5, align=True)  # Equal split for Mat and Col
            sub_split = sub.split(factor=0.9, align=True)
            sub_split.operator("material.select_toggle", text=mat_item["name"], depress=context.scene.get(f"toggle_{mat_prop}", False)).prop_name = mat_prop
            sub_split.operator("material.reset_material", text="-").index = i
            # Color toggle with reset
            col_prop = f"color_id_{i}"
            col_id = mesh.get(col_prop, 0)
            col_item = next((c for c in MATERIAL_OPTIONS["colors"] if c["id"] == col_id), {"name": "None"})
            sub = sub.split(factor=0.9, align=True)
            sub.operator("material.select_toggle", text=col_item["name"], depress=context.scene.get(f"toggle_{col_prop}", False)).prop_name = col_prop
            sub.operator("material.reset_color", text="-").index = i
            # Small square color swatch
            sub = split.column(align=True)
            sub.scale_x = 0.3
            sub.prop(mesh, f"color_{i}", text="")
            col.separator(factor=0.2)

        # Search and sort controls
        if context.scene.active_property:
            col.label(text="Select Option:")
            row = col.row(align=True)
            row.prop(context.scene, "modal_search_query", text="", icon="VIEWZOOM")
            sub = row.column(align=True)
            sub.scale_x = 0.35  # Slightly narrower clear button
            sub.operator("material.clear_modal_search", text="-")
            row.prop(context.scene, "modal_sort_mode", expand=True)
            col.separator(factor=0.2)
            rows = min(len(context.scene.modal_options), 16)  # Extended list length
            col.template_list("MODAL_OPTIONS_UL_options", "", context.scene, "modal_options", 
                            context.scene, "modal_options_index", rows=rows)

    def execute(self, context):
        active_mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
        if active_mesh:
            for obj in context.selected_objects:
                if obj.type == 'MESH' and obj.data:
                    mesh = obj.data
                    for i in range(1, 5):
                        # Ensure integer values
                        mesh[f"material_{i}"] = int(active_mesh.get(f"material_{i}", 0))
                        mesh[f"color_id_{i}"] = int(active_mesh.get(f"color_id_{i}", 0))
                        update_material(mesh, context)
                        update_color_id(mesh, context)
                        update_color_protect(mesh, context)
                        obj[f"color_{i}"] = mesh[f"color_{i}"]
            bpy.ops.object.sync_material_colors()
        return {'FINISHED'}

    def cancel(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj.data and obj.name in self.cached_props:
                mesh = obj.data
                props = self.cached_props[obj.name]
                for i in range(1, 5):
                    mesh[f"material_{i}"] = props[f"material_{i}"]
                    mesh[f"color_id_{i}"] = props[f"color_id_{i}"]
                    mesh[f"color_{i}"] = props[f"color_{i}"]
                    update_material(mesh, context)
                    update_color_id(mesh, context)
                    update_color_protect(mesh, context)
                    obj[f"color_{i}"] = mesh[f"color_{i}"]
        bpy.ops.object.sync_material_colors()
        return {'CANCELLED'}

# UI List for modal options
class MODAL_OPTIONS_UL_options(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
        active_id = mesh.get(context.scene.active_property, 0) if mesh and context.scene.active_property else 0
        split = layout.split(factor=0.85, align=True)
        op = split.operator("material.assign_id", text=item.name, depress=(item.id == active_id), emboss=True)
        op.item_id = item.id
        col = split.column(align=True)
        col.scale_x = 0.3
        col.prop(item, "color", text="")

# UI List for displaying materials/colors in Edit Materials
class MATERIAL_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.split(factor=0.6)
        split.prop(item, "name", text="", emboss=False)
        sub_split = split.split(factor=0.75)
        sub_split.prop(item, "color", text="", emboss=True)
        button_row = sub_split.row(align=True)
        button_row.operator("material.copy_material", text="+").index = data.material_items.find(item.name)
        button_row.operator("material.delete_material", text="-").index = data.material_items.find(item.name)

# Operator to edit materials or colors
class EditMaterialsOperator(bpy.types.Operator):
    bl_idname = "object.edit_materials"
    bl_label = "Edit Materials"
    bl_description = "Edit material or color options for the addon"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global MATERIAL_OPTIONS
        MATERIAL_OPTIONS = load_material_options()
        update_material_items(context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        self.bl_label = "Edit Materials" if context.scene.edit_mode == "materials" else "Edit Colors"
        
        layout.prop(context.scene, "edit_mode", expand=True)
        layout.prop(context.scene, "sort_mode", expand=True)
        row = layout.row(align=True)
        row.prop(context.scene, "search_query", text="", icon="VIEWZOOM")
        row.scale_x = 0.5
        row.operator("material.add_material", text="+")
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.operator_cancel", text="Cancel")
        rows = min(len(context.scene.material_items), 30)
        layout.template_list("MATERIAL_UL_materials", "", context.scene, "material_items", 
                          context.scene, "material_index", rows=rows)

    def execute(self, context):
        update_material_options_and_enums(context)
        return {'FINISHED'}

    def cancel(self, context):
        context.scene.material_items.clear()
        update_material_items(context)
        return {'CANCELLED'}

# Operator to copy a material/color to the other list
class CopyMaterialOperator(bpy.types.Operator):
    bl_idname = "material.copy_material"
    bl_label = "Copy Material"
    bl_description = "Copy the selected material or color to the other list"
    index: IntProperty(name="Index", default=-1)

    @classmethod
    def poll(cls, context):
        return len(context.scene.material_items) > 0

    def execute(self, context):
        if self.index < 0 or self.index >= len(context.scene.material_items):
            return {'CANCELLED'}
        
        item = context.scene.material_items[self.index]
        source_mode = context.scene.edit_mode
        target_mode = "materials" if source_mode == "colors" else "colors"
        
        max_id = max((item["id"] for item in MATERIAL_OPTIONS[target_mode]), default=-1)
        new_id = max_id + 1
        
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(item.color[0] * 255),
            int(item.color[1] * 255),
            int(item.color[2] * 255)
        )
        MATERIAL_OPTIONS[target_mode].append({
            "id": new_id,
            "name": item.name,
            "color": hex_color
        })
        
        update_material_items(context)
        return {'FINISHED'}

# Operator to add a new material/color
class AddMaterialOperator(bpy.types.Operator):
    bl_idname = "material.add_material"
    bl_label = "Add Material"
    bl_description = "Add a new material or color to the list"

    def execute(self, context):
        mode = context.scene.edit_mode
        max_id = max((item["id"] for item in MATERIAL_OPTIONS[mode]), default=-1)
        new_name = "New Material" if mode == "materials" else "New Color"
        MATERIAL_OPTIONS[mode].append({
            "id": max_id + 1,
            "name": new_name,
            "color": "#FFFFFF"
        })
        update_material_items(context)
        context.scene.material_index = len(context.scene.material_items) - 1
        return {'FINISHED'}

# Operator to delete a material/color
class DeleteMaterialOperator(bpy.types.Operator):
    bl_idname = "material.delete_material"
    bl_label = "Delete Material"
    bl_description = "Delete the selected material or color"
    index: IntProperty(name="Index", default=-1)

    def execute(self, context):
        if self.index < 0 or self.index >= len(context.scene.material_items):
            return {'CANCELLED'}
        
        item_id = context.scene.material_items[self.index].id
        mode = context.scene.edit_mode
        MATERIAL_OPTIONS[mode] = [item for item in MATERIAL_OPTIONS[mode] if item["id"] != item_id]
        context.scene.material_index = min(context.scene.material_index, len(context.scene.material_items) - 1)
        update_material_items(context)
        return {'FINISHED'}

# Custom property group for material/color items
class MaterialItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Material")
    color: FloatVectorProperty(name="Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0))
    id: IntProperty(name="ID", default=0)

# Register material_x IntProperty
def register_material_property(prop_name, target):
    setattr(target, prop_name, IntProperty(
        name=prop_name.replace('_', ' ').title(),
        default=0,
        update=update_material if target == bpy.types.Mesh else None
    ))

# Register color_id IntProperty
def register_color_id_property(prop_name, target):
    setattr(target, prop_name, IntProperty(
        name=prop_name.replace('_', ' ').title(),
        default=0,
        update=update_color_id if target == bpy.types.Mesh else None
    ))

# Register color FloatVectorProperty
def register_color_property(prop_name, target):
    setattr(target, prop_name, FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.0, 0.0, 0.0),
        update=update_color_protect
    ))

# Register properties
def register_properties():
    for i in range(1, 5):
        material_prop = f"material_{i}"
        color_id_prop = f"color_id_{i}"
        color_prop = f"color_{i}"
        register_material_property(material_prop, bpy.types.Mesh)
        register_color_id_property(color_id_prop, bpy.types.Mesh)
        register_color_property(color_prop, bpy.types.Mesh)
        register_material_property(material_prop, bpy.types.Object)
        register_color_id_property(color_id_prop, bpy.types.Object)
        register_color_property(color_prop, bpy.types.Object)

# Register custom properties for material editing
def register_material_items():
    bpy.utils.register_class(MaterialItem)
    bpy.types.Scene.material_items = bpy.props.CollectionProperty(type=MaterialItem)
    bpy.types.Scene.modal_options = bpy.props.CollectionProperty(type=MaterialItem)
    bpy.types.Scene.material_index = bpy.props.IntProperty(name="Material Index", default=0)
    bpy.types.Scene.modal_options_index = bpy.props.IntProperty(name="Modal Options Index", default=0)
    bpy.types.Scene.search_query = bpy.props.StringProperty(
        name="Search",
        default="",
        update=lambda self, context: update_material_items(context)
    )
    bpy.types.Scene.modal_search_query = bpy.props.StringProperty(
        name="Modal Search",
        default="",
        update=lambda self, context: update_modal_options(context)
    )
    bpy.types.Scene.edit_mode = bpy.props.EnumProperty(
        name="Mode",
        items=[
            ("materials", "Materials", "Edit materials"),
            ("colors", "Colors", "Edit colors")
        ],
        default="materials",
        update=lambda self, context: update_material_items(context)
    )
    bpy.types.Scene.sort_mode = bpy.props.EnumProperty(
        name="Sort Mode",
        items=[
            ("name", "By Name", "Sort by name"),
            ("color", "By Color", "Sort by color")
        ],
        default="color",
        update=lambda self, context: update_material_items(context)
    )
    bpy.types.Scene.modal_sort_mode = bpy.props.EnumProperty(
        name="Modal Sort Mode",
        items=[
            ("name", "By Name", "Sort by name"),
            ("color", "By Color", "Sort by color")
        ],
        default="color",
        update=lambda self, context: update_modal_options(context)
    )
    bpy.types.Scene.active_property = bpy.props.StringProperty(
        name="Active Property",
        default="material_1"
    )
    for i in range(1, 5):
        for prop in (f"material_{i}", f"color_id_{i}"):
            default = (prop == "material_1")
            setattr(bpy.types.Scene, f"toggle_{prop}", BoolProperty(
                name=f"Toggle {prop}",
                default=default
            ))

# Function to draw buttons in 3D Viewport Header
def draw_buttons(self, context):
    layout = self.layout
    layout.operator("object.edit_materials", icon='SETTINGS', text="")
    layout.operator("object.set_material_params", icon='BRUSH_DATA', text="")

# Handler for auto-sync after loading a .blend file
@persistent
def auto_sync_post_load(dummy):
    if not bpy.context.scene or not bpy.data.objects or not bpy.context.view_layer:
        return
    if bpy.ops.object.sync_material_colors.poll():
        bpy.ops.object.sync_material_colors()

# Register the addon
def register():
    global MATERIAL_OPTIONS
    MATERIAL_OPTIONS = load_material_options()
    register_properties()
    register_material_items()
    bpy.utils.register_class(SyncMaterialColorsOperator)
    bpy.utils.register_class(ResetMaterialOperator)
    bpy.utils.register_class(ResetColorOperator)
    bpy.utils.register_class(ClearModalSearchOperator)
    bpy.utils.register_class(SetMaterialParamsOperator)
    bpy.utils.register_class(AssignMaterialIDOperator)
    bpy.utils.register_class(EditMaterialsOperator)
    bpy.utils.register_class(MATERIAL_UL_materials)
    bpy.utils.register_class(MODAL_OPTIONS_UL_options)
    bpy.utils.register_class(AddMaterialOperator)
    bpy.utils.register_class(DeleteMaterialOperator)
    bpy.utils.register_class(CopyMaterialOperator)
    bpy.utils.register_class(SelectToggleOperator)
    bpy.types.VIEW3D_HT_header.append(draw_buttons)
    if auto_sync_post_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(auto_sync_post_load)

# Unregister the addon
def unregister():
    if auto_sync_post_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(auto_sync_post_load)
    bpy.utils.unregister_class(SyncMaterialColorsOperator)
    bpy.utils.unregister_class(ResetMaterialOperator)
    bpy.utils.unregister_class(ResetColorOperator)
    bpy.utils.unregister_class(ClearModalSearchOperator)
    bpy.utils.unregister_class(SetMaterialParamsOperator)
    bpy.utils.unregister_class(AssignMaterialIDOperator)
    bpy.utils.unregister_class(EditMaterialsOperator)
    bpy.utils.unregister_class(MATERIAL_UL_materials)
    bpy.utils.unregister_class(MODAL_OPTIONS_UL_options)
    bpy.utils.unregister_class(AddMaterialOperator)
    bpy.utils.unregister_class(DeleteMaterialOperator)
    bpy.utils.unregister_class(CopyMaterialOperator)
    bpy.utils.unregister_class(SelectToggleOperator)
    bpy.utils.unregister_class(MaterialItem)
    bpy.types.VIEW3D_HT_header.remove(draw_buttons)
    del bpy.types.Scene.material_items
    del bpy.types.Scene.modal_options
    del bpy.types.Scene.material_index
    del bpy.types.Scene.modal_options_index
    del bpy.types.Scene.search_query
    del bpy.types.Scene.modal_search_query
    del bpy.types.Scene.edit_mode
    del bpy.types.Scene.sort_mode
    del bpy.types.Scene.modal_sort_mode
    del bpy.types.Scene.active_property
    for i in range(1, 5):
        for prop in (f"material_{i}", f"color_id_{i}"):
            if hasattr(bpy.types.Scene, f"toggle_{prop}"):
                delattr(bpy.types.Scene, f"toggle_{prop}")
    for i in range(1, 5):
        for target in (bpy.types.Mesh, bpy.types.Object):
            for prop in (f"material_{i}", f"color_id_{i}", f"color_{i}"):
                if hasattr(target, prop):
                    delattr(target, prop)

if __name__ == "__main__":
    register()