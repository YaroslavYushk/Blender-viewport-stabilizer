import bpy
import bmesh
from mathutils import Vector
from . import viewport_stabilizer as vp_stab
from . import preferences


class STAB_PT_stabilization_main_panel(bpy.types.Panel):
    bl_label = "Stabilize viewport"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator(
            "view3d.stabilize_toggle",
            text="Enable viewport stabilization" if not scene.stab_props.is_stab_active
            else "Disable viewport stabilization",
            icon='CON_TRACKTO')

        layout.label(text="Stabilise on:")
        layout.prop(scene.stab_props, "stabilize_on_prop", text="")
        if context.scene.stab_props.stabilize_on_prop == 'OBJ_SPECIFIED':
            layout.operator("view3d.apply_selection")
        layout.separator()
        layout.operator("view3d.create_object_center")
        layout.operator("view3d.create_vertices_center")


class STAB_OT_create_object_center(bpy.types.Operator):
    bl_idname = "view3d.create_object_center"
    bl_label = "Find Object center"
    bl_description = ("Creates an Empty in the center of mass and "
                      "parents it to the active Object")

    def execute(self, context):
        if ((not context.active_object)
                or (context.active_object.type != 'MESH')):
            self.report({'ERROR'},
                        message=("Active object should be Mesh type"))
            return {'CANCELLED'}

        mesh = context.active_object.data
        center_of_mass = Vector((0.0, 0.0, 0.0))
        for vertex in mesh.vertices:
            center_of_mass += vertex.co
        center_of_mass = center_of_mass / len(mesh.vertices)

        new = bpy.data.objects.new(f"{context.active_object.name}_center", None)
        new.empty_display_size = 25
        bpy.context.scene.collection.objects.link(new)
        new.location = center_of_mass
        new.parent = context.active_object
        return {'FINISHED'}


class STAB_OT_create_vertices_center(bpy.types.Operator):
    bl_idname = "view3d.create_vertices_center"
    bl_label = "Find Vertices center"
    bl_description = ("Creates an Empty in the middle of selected "
                      "vertices and parents it to the Object")

    def execute(self, context):
        if ((not context.active_object)
                or (context.active_object.type != 'MESH')):
            self.report({'ERROR'},
                        message=("Active object should be Mesh type"))
            return {'CANCELLED'}
        if bpy.context.object.mode != 'EDIT':
            self.report({'ERROR'},
                        message=("You should be in Edit mode and select vertices"))
            return {'CANCELLED'}

        mesh = context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        selected = []
        center_of_mass = Vector((0.0, 0.0, 0.0))
        for vertex in bm.verts:
            if vertex.select:
                selected.append(vertex)
                center_of_mass += vertex.co
        if len(selected) == 0:
            self.report({'ERROR'},
                        message=("You should select some vertices"))
            return {'CANCELLED'}
        center_of_mass = center_of_mass / len(selected)

        new = bpy.data.objects.new(f"{context.active_object.name}_stab_point", None)
        new.empty_display_size = 25
        bpy.context.scene.collection.objects.link(new)
        new.location = center_of_mass
        new.parent = context.active_object

        return {'FINISHED'}


def register():
    vp_stab.register()
    bpy.utils.register_class(STAB_OT_create_object_center)
    bpy.utils.register_class(STAB_OT_create_vertices_center)
    bpy.utils.register_class(STAB_PT_stabilization_main_panel)
    preferences.register()


def unregister():
    preferences.unregister()
    bpy.utils.unregister_class(STAB_PT_stabilization_main_panel)
    bpy.utils.unregister_class(STAB_OT_create_vertices_center)
    bpy.utils.unregister_class(STAB_OT_create_object_center)
    vp_stab.unregister()


if __name__ == "__main__":
    register()
