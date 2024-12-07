bl_info = {
    "name": "Seasonal Leaves",
    "author": "Mox Alehin",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "Search Menu (Edit Mode)",
    "description": "Prepares leaves for seasons by creating UV and optionally making Two Sided geometry",
    "category": "Mesh",
}

import bpy
import bmesh
import random

class MESH_OT_seasonal_leaves(bpy.types.Operator):
    """Seasonal Leaves"""
    bl_idname = "mesh.seasonal_leaves"
    bl_label = "Seasonal Leaves"
    bl_options = {'REGISTER', 'UNDO'}

    clean_leaves: bpy.props.BoolProperty(
        name="Clean Leaves",
        description="Merge by distance and recalculate normals outside before processing",
        default=True,
    )

    make_two_sided: bpy.props.BoolProperty(
        name="Make Two Sided",
        description="Duplicate faces and flip normals to make leaves Two Sided",
        default=True,
    )

    def execute(self, context):
        # Get the active object
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}
        
        # Use BMesh to work with geometry
        bm = bmesh.from_edit_mesh(obj.data)

        if self.clean_leaves:
            # Remove duplicate vertices
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            # Recalculate normals to point outside
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        uv_name = "LeavesSeasons"

        # Create or use the UV map LeavesSeasons
        if uv_name not in obj.data.uv_layers:
            obj.data.uv_layers.new(name=uv_name)
        uv_layer = bm.loops.layers.uv.get(uv_name)

        # List of selected faces
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'ERROR'}, "No faces selected.")
            return {'CANCELLED'}

        # Function to find connected components
        def find_connected_faces(face, visited_faces):
            stack = [face]
            connected_faces = set()
            while stack:
                current_face = stack.pop()
                if current_face in visited_faces:
                    continue
                visited_faces.add(current_face)
                connected_faces.add(current_face)
                for edge in current_face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face not in visited_faces:
                            stack.append(linked_face)
            return connected_faces

        # Find connected components
        islands = []
        visited_faces = set()

        for face in selected_faces:
            if face not in visited_faces:
                island = find_connected_faces(face, visited_faces)
                islands.append(island)

        # Set UV coordinates for each group
        u_step = 1.0 / len(islands) if len(islands) > 0 else 1.0
        u_pos = 0.0

        random.shuffle(islands)

        for island in islands:
            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer]
                    uv.uv = (u_pos, 0.5)  # All vertices of the island are moved to one point on the UV
            u_pos += u_step  # Move along the U axis

        # Duplicate selected faces and flip normals only for new ones
        if self.make_two_sided:
            duplicate_result = bmesh.ops.duplicate(bm, geom=selected_faces)
            new_faces = [geom for geom in duplicate_result["geom"] if isinstance(geom, bmesh.types.BMFace)]
            for face in new_faces:
                face.normal_flip()

        # Apply changes and update the mesh
        bmesh.update_edit_mesh(obj.data, loop_triangles=True)
        self.report({'INFO'}, "Leaves prepared for seasonal use.")
        return {'FINISHED'}

# Add the operator to the menu
def menu_func(self, context):
    self.layout.operator(MESH_OT_seasonal_leaves.bl_idname, icon='UV')

def register():
    bpy.utils.register_class(MESH_OT_seasonal_leaves)
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)
    bpy.utils.unregister_class(MESH_OT_seasonal_leaves)

if __name__ == "__main__":
    register()
