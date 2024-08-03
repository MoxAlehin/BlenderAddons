bl_info = {
    "name": "Multi Importer",
    "description": "",
    "author": "Mox Alehin",
    "blender": (2, 80, 0),
    "version": (1, 0),
    "category": "Import-Export",
    "doc_url": "https://github.com/MoxAlehin/Blender-Addons/tree/master?tab=readme-ov-file#multi-import",
    "location": "File > Import",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty
import zipfile
import os
import tempfile
import shutil

class ImportAllOperator(Operator, ImportHelper):
    bl_idname = "import_scene.multi_importer"
    bl_label = "Import Multi Format"

    filter_glob: StringProperty(
        default="*.fbx;*.obj;*.stl;*.abc;*.usd;*.usdz;*.blend;*.zip;*.dae",
        options={'HIDDEN'},
    )

    def execute(self, context):
        # Here we will check the file extension and call the appropriate import function
        filepath = self.filepath
        file_extension = filepath.split('.')[-1].lower()

        self.import_file(filepath, file_extension)

        return {'FINISHED'}

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

def menu_func_import(self, context):
    self.layout.operator(ImportAllOperator.bl_idname, text="Import Multi Format")

def register():
    bpy.utils.register_class(ImportAllOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    # Keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new(ImportAllOperator.bl_idname, 'I', 'PRESS', ctrl=True, shift=True, alt=True)

def unregister():
    bpy.utils.unregister_class(ImportAllOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

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
