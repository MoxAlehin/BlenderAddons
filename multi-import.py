bl_info = {
    "name": "Multi Importer",
    "description": "Imports multiple 3D file formats with customizable post-processing",
    "author": "Mox Alehin",
    "blender": (2, 80, 0),
    "version": (1, 2),
    "category": "Import-Export",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons/tree/master?tab=readme-ov-file#multi-import",
    "location": "File > Import",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, BoolProperty
import zipfile
import os
import tempfile
import shutil
from mathutils import Vector
import re

class MultiImporterPreferences(AddonPreferences):
    bl_idname = __name__

    clear_parent: BoolProperty(
        name="Clear Parent Relationships",
        description="Clear parent relationships while keeping transforms",
        default=True,
    )
    remove_non_mesh: BoolProperty(
        name="Remove Non-Mesh Objects",
        description="Remove all non-mesh objects after import",
        default=True,
    )
    join_meshes: BoolProperty(
        name="Join Mesh Objects",
        description="Join all mesh objects into a single object",
        default=True,
    )
    rename_object: BoolProperty(
        name="Rename Object",
        description="Rename the imported object to Upper Camel Case",
        default=True,
    )
    remove_materials: BoolProperty(
        name="Remove Materials",
        description="Remove all materials from the imported object",
        default=True,
    )
    center_origin: BoolProperty(
        name="Center Origin",
        description="Set object origin to center X/Y, bottom Z",
        default=True,
    )
    scale_to_unit: BoolProperty(
        name="Scale to 1-Meter Cube",
        description="Scale the model to fit within a 1-meter cube",
        default=True,
    )
    shade_flat: BoolProperty(
        name="Apply Shade Flat",
        description="Apply flat shading to the model",
        default=True,
    )
    clean_geometry: BoolProperty(
        name="Clean Geometry",
        description="Remove doubles and convert triangles to quads",
        default=True,
    )
    clear_seams_sharps: BoolProperty(
        name="Clear Seams and Sharps",
        description="Remove all seams and sharp edges",
        default=True,
    )
    clear_split_normals: BoolProperty(
        name="Clear Split Normals",
        description="Clear custom split normals data",
        default=True,
    )
    manage_uv_maps: BoolProperty(
        name="Manage UV Maps",
        description="Keep only the first UV map and rename it to 'UVMap'",
        default=True,
    )
    purge_orphans: BoolProperty(
        name="Purge Unused Data",
        description="Purge unused data blocks after import",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Post-Processing Options:")
        layout.prop(self, "clear_parent")
        layout.prop(self, "remove_non_mesh")
        layout.prop(self, "join_meshes")
        layout.prop(self, "rename_object")
        layout.prop(self, "remove_materials")
        layout.prop(self, "center_origin")
        layout.prop(self, "scale_to_unit")
        layout.prop(self, "shade_flat")
        layout.prop(self, "clean_geometry")
        layout.prop(self, "clear_seams_sharps")
        layout.prop(self, "clear_split_normals")
        layout.prop(self, "manage_uv_maps")
        layout.prop(self, "purge_orphans")

class ImportAllOperator(Operator, ImportHelper):
    bl_idname = "import_scene.multi_importer"
    bl_label = "Import Multi Format"

    filter_glob: StringProperty(
        default="*.fbx;*.obj;*.stl;*.abc;*.usd;*.usdz;*.blend;*.zip;*.dae;*.glb;*.gltf",
        options={'HIDDEN'},
    )

    def execute(self, context):
        # Get addon preferences
        addon_prefs = context.preferences.addons[__name__].preferences

        # Save existing objects before import
        existing_objects = set(bpy.data.objects.keys())

        # Determine file extension and call appropriate import function
        filepath = self.filepath
        file_extension = filepath.split('.')[-1].lower()

        # Get filename without extension
        filename = os.path.basename(self.filepath)
        object_name_raw = os.path.splitext(filename)[0]

        # Convert name to Upper Camel Case
        object_name = self.to_upper_camel_case(object_name_raw)

        self.import_file(filepath, file_extension)

        # Get list of imported objects
        imported_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]

        # Perform post-processing based on preferences
        self.post_process(imported_objects, object_name, addon_prefs)

        return {'FINISHED'}

    def to_upper_camel_case(self, name):
        # Replace any non-alphanumeric characters with spaces
        name = re.sub(r'[^A-Za-z0-9]+', ' ', name)
        # Split the string into words
        words = name.strip().split()
        # Capitalize each word and join them
        return ''.join(word.capitalize() for word in words)

    def import_file(self, filepath, file_extension):
        if file_extension == 'fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif file_extension == 'obj':
            bpy.ops.wm.obj_import(filepath=filepath)
        elif file_extension == 'stl':
            bpy.ops.import_mesh.stl(filepath=filepath)
        elif file_extension == 'abc':
            bpy.ops.wm.alembic_import(filepath=filepath)
        elif file_extension == 'usd' or file_extension == 'usdz':
            bpy.ops.wm.usd_import(filepath=filepath)
        elif file_extension in ['glb', 'gltf']:
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif file_extension == 'blend':
            # Using append to add data from the .blend file
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)
        elif file_extension == 'dae':
            bpy.ops.wm.collada_import(filepath=filepath)
        elif file_extension == 'zip':
            self.import_from_zip(filepath)
        elif file_extension in ['png', 'jpg', 'jpeg', 'tga', 'bmp']:
            self.import_texture(filepath)
        else:
            self.report({'ERROR'}, f"Unsupported file format: {file_extension}")
            return {'CANCELLED'}

    def import_from_zip(self, filepath, temp_dir=None):
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()

        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        for root, _, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                file_extension = file.split('.')[-1].lower()
                self.import_file(full_path, file_extension)

        if temp_dir:
            # Clean up the temporary directory only if it was created in this function call
            shutil.rmtree(temp_dir)

    def import_texture(self, filepath):
        texture_name = os.path.basename(filepath)
        if texture_name in bpy.data.images:
            img = bpy.data.images[texture_name]
            img.filepath = filepath
            img.reload()
        else:
            img = bpy.data.images.load(filepath)
        img.pack()  # Pack the image into the .blend file

    def post_process(self, imported_objects, object_name, addon_prefs):
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Separate objects into meshes and non-meshes
        mesh_objects = []
        non_mesh_objects = []
        for obj in imported_objects:
            if obj.type == 'MESH':
                mesh_objects.append(obj)
                obj.select_set(True)
            else:
                non_mesh_objects.append(obj)

        # Clear parent while keeping transforms
        if addon_prefs.clear_parent:
            for obj in mesh_objects:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # Remove all non-mesh objects
        if addon_prefs.remove_non_mesh:
            for obj in non_mesh_objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        if not mesh_objects:
            # No imported mesh objects
            return

        # Set the active object
        bpy.context.view_layer.objects.active = mesh_objects[0]

        # Join selected objects into one
        if addon_prefs.join_meshes and len(mesh_objects) > 1:
            bpy.ops.object.join()
            active_obj = bpy.context.view_layer.objects.active
        else:
            active_obj = mesh_objects[0]

        # Rename object and its mesh
        if addon_prefs.rename_object:
            active_obj.name = object_name
            active_obj.data.name = object_name

        # Remove all materials from the object
        if addon_prefs.remove_materials:
            active_obj.data.materials.clear()

        # Calculate bounding box world coordinates
        if addon_prefs.center_origin or addon_prefs.scale_to_unit:
            bbox = [active_obj.matrix_world @ Vector(corner) for corner in active_obj.bound_box]

        # Move origin to center X/Y, bottom Z
        if addon_prefs.center_origin:
            center_x = sum([v.x for v in bbox]) / 8.0
            center_y = sum([v.y for v in bbox]) / 8.0
            min_z = min(v.z for v in bbox)
            pivot = Vector((center_x, center_y, min_z))
            active_obj.location -= pivot
            bpy.context.view_layer.update()
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
            active_obj.location += pivot
            bpy.ops.object.location_clear()

        # Scale the model to fit inside a 1-meter cube
        if addon_prefs.scale_to_unit:
            bbox = [active_obj.matrix_world @ Vector(corner) for corner in active_obj.bound_box]
            min_coord = Vector((min([v[i] for v in bbox]) for i in range(3)))
            max_coord = Vector((max([v[i] for v in bbox]) for i in range(3)))
            size = max_coord - min_coord
            max_dimension = max(size)
            scene_unit_scale = bpy.context.scene.unit_settings.scale_length
            target_size = 1.0 / scene_unit_scale
            scale_factor = target_size / max_dimension
            active_obj.scale *= scale_factor
            bpy.ops.object.transform_apply(scale=True)

        # Apply Shade Flat
        if addon_prefs.shade_flat:
            bpy.ops.object.shade_flat()

        # Geometry cleanup operations
        if addon_prefs.clean_geometry or addon_prefs.clear_seams_sharps or addon_prefs.clear_split_normals:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            if addon_prefs.clean_geometry:
                bpy.ops.mesh.remove_doubles(threshold=0.0001)
                bpy.ops.mesh.tris_convert_to_quads(face_threshold=60, shape_threshold=60)
            if addon_prefs.clear_seams_sharps:
                bpy.ops.mesh.mark_seam(clear=True)
                bpy.ops.mesh.mark_sharp(clear=True)
            if addon_prefs.clear_split_normals:
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
            bpy.ops.object.mode_set(mode='OBJECT')

        # Keep only the first UV map and rename it to "UVMap"
        if addon_prefs.manage_uv_maps:
            mesh = active_obj.data
            if hasattr(mesh, "uv_layers") and len(mesh.uv_layers) > 0:
                mesh.uv_layers[0].name = "UVMap"
                while len(mesh.uv_layers) > 1:
                    mesh.uv_layers.remove(mesh.uv_layers[-1])

        # Purge unused data
        if addon_prefs.purge_orphans:
            bpy.ops.outliner.orphans_purge(do_recursive=True)

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(ImportAllOperator.bl_idname, text="Import Multi Format")

def register():
    bpy.utils.register_class(MultiImporterPreferences)
    bpy.utils.register_class(ImportAllOperator)
    bpy.types.TOPBAR_MT_file_import.append(ImportAllOperator.menu_func_import)

    # Keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new(ImportAllOperator.bl_idname, 'I', 'PRESS', ctrl=True, shift=True, alt=True)

def unregister():
    bpy.utils.unregister_class(ImportAllOperator)
    bpy.utils.unregister_class(MultiImporterPreferences)
    bpy.types.TOPBAR_MT_file_import.remove(ImportAllOperator.menu_func_import)

    # Remove keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Window']
        for kmi in km.keymap_items:
            if kmi.idname == ImportAllOperator.bl_idname:
                km.keymap_items.remove(kmi)
                break

if __name__ == "__main__":
    register()