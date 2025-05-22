import bpy


def update_stab_options(self, context):
    preferences = context.preferences.addons[__package__].preferences
    scene = bpy.context.scene

    if not preferences.enable_vertex_stab:
        if scene.is_stab_active:
            scene.is_stab_active = not scene.is_stab_active
        scene.stabilize_on_prop = '3D_CURSOR'


class STAB_OT_SaveHotkey(bpy.types.Operator):
    bl_idname = "stab.save_hotkey"
    bl_label = "Save Hotkey"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences

        event_rna = bpy.types.Event.bl_rna.properties["type"]
        enum_items = event_rna.enum_items.keys()
        if preferences.stab_toggle_hotkey_key not in enum_items:
            self.report({'ERROR'}, "Please enter appropriate Key name")
            return {'CANCELLED'}

        keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
        keymap = keyconfigs_addon.keymaps["3D View"] 

        keymap_item = keymap.keymap_items["stab.stabilize_toggle"]
        keymap.keymap_items.remove(keymap_item)

        keymap_item = keymap.keymap_items.new(
            idname="stab.stabilize_toggle", value='PRESS',
            type=preferences.stab_toggle_hotkey_key,
            shift=preferences.stab_toggle_hotkey_shift,
            ctrl=preferences.stab_toggle_hotkey_ctrl,
            alt=preferences.stab_toggle_hotkey_alt,
        )
        self.report({'INFO'}, "Hotkey saved!")
        return {'FINISHED'}


class STAB_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    stab_toggle_hotkey_key: bpy.props.StringProperty(
        default='C')
    stab_toggle_hotkey_shift: bpy.props.BoolProperty(
        default=False)
    stab_toggle_hotkey_ctrl: bpy.props.BoolProperty(
        default=False)
    stab_toggle_hotkey_alt: bpy.props.BoolProperty(
        default=True)

    enable_vertex_stab: bpy.props.BoolProperty(
        name="Enable option of stabilization on multiple selected vertices "
             "(potentially bad for performance)",
        default=False,
        update=update_stab_options,
    )
    vertices_limit: bpy.props.IntProperty(
        name="Limit of mesh total vertices (for vertex stabilization)",
        default=1000,
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Assign Hotkey:")
        box = layout.box()
        row = box.row()
        row.prop(self, 'stab_toggle_hotkey_key', text='Key')
        column = row.column()
        column.prop(self, 'stab_toggle_hotkey_shift', text='Shift')
        column.prop(self, 'stab_toggle_hotkey_ctrl', text='Ctrl')
        column.prop(self, 'stab_toggle_hotkey_alt', text='Alt')
        row.operator("stab.save_hotkey")
        layout.separator()

        layout.prop(self, "enable_vertex_stab")
        layout.prop(self, "vertices_limit")


def register():
    bpy.utils.register_class(STAB_OT_SaveHotkey)
    bpy.utils.register_class(STAB_Preferences)

    preferences = bpy.context.preferences.addons[__package__].preferences
    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    keymap = keyconfigs_addon.keymaps.new(
        name="3D View", space_type='VIEW_3D')
    event_rna = bpy.types.Event.bl_rna.properties["type"]
    enum_items = event_rna.enum_items.keys()
    if preferences.stab_toggle_hotkey_key in enum_items:
        keymap.keymap_items.new(
            idname="stab.stabilize_toggle", value='PRESS',
            type=preferences.stab_toggle_hotkey_key,
            shift=preferences.stab_toggle_hotkey_shift,
            ctrl=preferences.stab_toggle_hotkey_ctrl,
            alt=preferences.stab_toggle_hotkey_alt,
        )


def unregister():
    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    keymap = keyconfigs_addon.keymaps["3D View"]
    keymap_item = keymap.keymap_items["stab.stabilize_toggle"]
    keymap.keymap_items.remove(keymap_item)

    bpy.utils.unregister_class(STAB_Preferences)
    bpy.utils.unregister_class(STAB_OT_SaveHotkey)
