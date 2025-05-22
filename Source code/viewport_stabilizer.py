import bpy
import bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def update_3d_stab_point():
    scene = bpy.context.scene

    if scene.stabilize_on_prop == '3D_CURSOR':
        scene.stab_point_3d = scene.cursor.location

    if scene.stabilize_on_prop == 'OBJ_ACTIVE':
        if ((bpy.context.active_object is None)
                or (bpy.context.active_object.type == 'CAMERA')):
            scene.is_stab_active = not scene.is_stab_active
            return
        scene.stab_point_3d = (
            bpy.context.active_object.matrix_world.translation)

    if scene.stabilize_on_prop == 'OBJ_SPECIFIED':
        if ((scene.stabilize_on_obj is None)
                or (scene.stabilize_on_obj.name not in scene.collection.all_objects)):
            scene.is_stab_active = not scene.is_stab_active
            return
        scene.stab_point_3d = (
            scene.stabilize_on_obj.matrix_world.translation)

    if scene.stabilize_on_prop == 'VERT_GROUP':
        if ((not bpy.context.active_object)
                or (bpy.context.active_object.type != 'MESH')):
            scene.is_stab_active = not scene.is_stab_active
            return
        preferences = bpy.context.preferences.addons[__package__].preferences
        vertices = bpy.context.active_object.data.vertices
        if len(vertices) > preferences.vertices_limit:
            scene.is_stab_active = not scene.is_stab_active
            return
        if bpy.context.object.mode != 'EDIT':
            return
        mesh = bpy.context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        selected = []
        center_of_mass = Vector((0.0, 0.0, 0.0))
        for vertex in bm.verts:
            if vertex.select:
                selected.append(vertex)
                center_of_mass += vertex.co
        if len(selected) == 0:
            return
        center_of_mass = center_of_mass / len(selected)
        scene.stab_point_3d = (
            bpy.context.active_object.matrix_world @ center_of_mass)


def update_2d_stab_point(scene):
    if not bpy.context.scene.is_stab_active:
        return
    if not scene.camera:
        print("Vewport stabilizer: There's no active camera in scene")
        return

    update_3d_stab_point()
    if bpy.types.Scene.is_stab_active is False: return

    bpy.context.scene.stab_point_2d = world_to_camera_view(
        scene=scene,
        obj=scene.camera,
        coord=Vector(scene.stab_point_3d))


def stabilize_view(scene):
    if not bpy.context.scene.is_stab_active:
        return
    if not scene.camera:
        print("Vewport stabilizer: There's no active camera in scene")
        return

    update_3d_stab_point()
    new_stab_point_2d = world_to_camera_view(
        scene=bpy.context.scene,
        obj=bpy.context.scene.camera,
        coord=Vector(bpy.context.scene.stab_point_3d))

    offset = (new_stab_point_2d - Vector(bpy.context.scene.stab_point_2d))

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        rv3d = region.data
                        old_viewport_pos = rv3d.view_camera_offset
                        res_x = bpy.context.scene.render.resolution_x
                        res_y = bpy.context.scene.render.resolution_y
                        width = area.width
                        heigth = area.height

                        new_viewport_pos = [
                            old_viewport_pos[0]
                            + offset.x / 2
                            * heigth / min(width, heigth)
                            * res_x / max(res_x, res_y),

                            old_viewport_pos[1]
                            + offset.y / 2
                            * width / min(width, heigth)
                            * res_y / max(res_x, res_y)]

                        rv3d.view_camera_offset = (new_viewport_pos)
    return


class STAB_OT_toggle(bpy.types.Operator):
    bl_idname = "stab.stabilize_toggle"
    bl_label = "Toggle Viewport Stabilization"
    bl_description = "Turn on/off 2d stabilization on the selected point"

    def execute(self, context):
        context.scene.is_stab_active = not context.scene.is_stab_active

        if context.scene.is_stab_active:
            if update_2d_stab_point not in bpy.app.handlers.frame_change_pre:
                bpy.app.handlers.frame_change_pre.append(update_2d_stab_point)
            if stabilize_view not in bpy.app.handlers.frame_change_post:
                bpy.app.handlers.frame_change_post.append(stabilize_view)

        if not context.scene.is_stab_active:
            if update_2d_stab_point in bpy.app.handlers.frame_change_pre:
                bpy.app.handlers.frame_change_pre.remove(update_2d_stab_point)
            if stabilize_view in bpy.app.handlers.frame_change_post:
                bpy.app.handlers.frame_change_post.remove(stabilize_view)

        return {'FINISHED'}


class STAB_OT_apply_selection(bpy.types.Operator):
    bl_idname = "stab.apply_selection"
    bl_label = "Select object"

    def execute(self, context):
        if ((bpy.context.active_object.type != 'MESH')
                and (bpy.context.active_object.type != 'EMPTY')):
            self.report({'ERROR'},
                        message=("Select an Object or an Empty"))

        bpy.context.scene.stabilize_on_obj = bpy.context.active_object
        self.report(
            {'INFO'},
            f"Object selected: {bpy.context.scene.stabilize_on_obj.name}")
        return {'FINISHED'}


def get_stabilize_options(self, context):
    preferences = context.preferences.addons[__package__].preferences
    items = [
        ('3D_CURSOR', "3D Cursor",
            "Stabilise on position of 3D Cursor"),
        ('OBJ_ACTIVE', "Active object (pivot)",
            "Stabilise on the pivot of Active object"),
        ('OBJ_SPECIFIED', "Specified object (pivot)",
            "Stabilize on the pivot of specified object"),
    ]
    if preferences.enable_vertex_stab:
        items.append(('VERT_GROUP', "Selected Vertices",
                      "Stabilise on group of selected vertices"))
    return items


def update_toggle_operator(self, context):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'UI':
                    region.tag_redraw()


def register():
    bpy.types.Scene.stabilize_on_prop = bpy.props.EnumProperty(
        items=get_stabilize_options,
        name="Stabilize on",
        description="Pick what to stabilize on",
        default=0,
    )
    bpy.types.Scene.stabilize_on_obj = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.is_stab_active = bpy.props.BoolProperty(
        default=False, update=update_toggle_operator)
    bpy.types.Scene.stab_point_3d = bpy.props.FloatVectorProperty()
    bpy.types.Scene.stab_point_2d = bpy.props.FloatVectorProperty()

    bpy.utils.register_class(STAB_OT_toggle)
    bpy.utils.register_class(STAB_OT_apply_selection)


def unregister():
    if bpy.context.scene.is_stab_active:
        bpy.context.scene.is_stab_active = False

    if update_2d_stab_point in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(update_2d_stab_point)
    if stabilize_view in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(stabilize_view)

    bpy.utils.unregister_class(STAB_OT_toggle)
    bpy.utils.unregister_class(STAB_OT_apply_selection)

    del bpy.types.Scene.is_stab_active
    del bpy.types.Scene.stab_point_3d
    del bpy.types.Scene.stab_point_2d
    del bpy.types.Scene.stabilize_on_obj
    del bpy.types.Scene.stabilize_on_prop
