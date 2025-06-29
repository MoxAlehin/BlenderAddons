bl_info = {
    "name": "Dissolve Coplanar Faces",
    "blender": (4, 4, 0),
    "category": "Mesh",
    "author": "Your Name",
    "version": (1, 0),
    "description": "Select coplanar faces and dissolve them into n-gon",
}

import bpy

class OBJECT_OT_dissolve_coplanar_faces(bpy.types.Operator):
    bl_idname = "mesh.dissolve_coplanar_faces"
    bl_label = "Dissolve Coplanar Faces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object.mode != 'EDIT':
            self.report({'WARNING'}, "Switch to Edit Mode")
            return {'CANCELLED'}

        bpy.ops.mesh.select_similar(type='FACE_COPLANAR', threshold=1)
        bpy.ops.mesh.dissolve_faces(use_verts=True)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_dissolve_coplanar_faces)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new(OBJECT_OT_dissolve_coplanar_faces.bl_idname, 'X', 'PRESS', ctrl=True, shift=True)
    kmi.active = True

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_dissolve_coplanar_faces)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get("3D View")
    if km:
        for kmi in km.keymap_items:
            if kmi.idname == OBJECT_OT_dissolve_coplanar_faces.bl_idname:
                km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()