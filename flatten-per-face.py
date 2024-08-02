import bpy
import bmesh

bl_info = {
	"name": "Flatten Per Face",
	"description": "Sequentially flatten selected faces in Edit Mode",
    "author": "Mox Alehin",
	"blender": (2, 80, 0),
	"version": (1, 0),
	"category": "Mesh",
    "doc-url": "https://github.com/MoxAlehin/Blender-Addons",
	"location": "View3D > Mesh",
}

class FlattenPerFace(bpy.types.Operator):
	bl_idname = "mesh.flatten_per_face"
	bl_label = "Flatten Per Face"
	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):

		looptools_name = "mesh_looptools"

		if not looptools_name in bpy.context.preferences.addons:
			self.report({'ERROR'}, "LoopTools is NOT active")
			return {'CANCELLED'}

		obj = bpy.context.edit_object
		me = obj.data
		bm = bmesh.from_edit_mesh(me)

		selected_faces = []

		for face in bm.faces:
			if face.select:
				selected_faces.append(face)
				face.select = False

		for face in selected_faces:
			face.select = True
			bpy.ops.mesh.looptools_flatten(influence=100, lock_x=False, lock_y=False, lock_z=False, plane='best_fit', restriction='none')
			face.select = False
			
		for face in selected_faces:
			face.select = True

		bmesh.update_edit_mesh(me)

		self.report({'INFO'}, "Selected faces flattened separately")
		return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(FlattenPerFace.bl_idname, text="Flatten Per Face")
    
def register():
    bpy.utils.register_class(FlattenPerFace)
    bpy.types.VIEW3D_MT_edit_mesh_looptools.append(menu_func)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new(FlattenPerFace.bl_idname, 'F', 'PRESS', ctrl=True, shift=True, alt=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(FlattenPerFace)
    bpy.types.VIEW3D_MT_edit_mesh_looptools.remove(menu_func)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
	register()
