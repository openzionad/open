import bpy
from bpy.props import FloatVectorProperty, FloatProperty, EnumProperty, StringProperty, BoolProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy.app.handlers import persistent

# Add-on metadata
bl_info = {
    "name": "zionad 520 [ 3D Viewport Color] ",
    "author": "zionadchat",
    "version": (3, 5), # バージョンを更新
    "blender": (4, 1, 0),
    "category": "   520  [  3D Viewport  ]   ",
    "description": "Control 3D Viewport colors with master presets and individual adjustments.",
    "location": "View3D > Sidebar",
}

# Constants
ADDON_CATEGORY_NAME = bl_info["category"]
PREFIX = "view20250320f"

# Panel definitions
BG_PANEL_IDNAME_1 = f"{PREFIX}_VIEW3D_PT_solid_background_panel"
OBJECT_COLORS_PANEL_IDNAME = f"{PREFIX}_VIEW3D_PT_object_colors_panel"
INTERFACE_COLORS_PANEL_IDNAME = f"{PREFIX}_VIEW3D_PT_interface_colors_panel"
REMOVE_PANEL_IDNAME = f"{PREFIX}_VIEW3D_PT_remove"

# Panel labels
PANEL_LABELS = {
    "BACKGROUND": "Viewport Color Themes",
    "OBJECT_COLORS": "Object Colors",
    "INTERFACE_COLORS": "Interface Colors",
    "REMOVE": "アドオン削除",
}

# --- Master Theme Presets ---
MASTER_PRESETS = [
    # --- ご指示の新しいテーマを追加し、デフォルトとして設定 ---
    (
        "ZIONAD_CYAN", "Zionad Cyan (Default)", "A new dark theme with cyan accents, loaded by default.",
        {
            "header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "custom_gradient_high": (0.0804, 0.1062, 0.1080), # ご指定の値
            "custom_gradient_low": (0.0026, 0.0026, 0.0026),   # ご指定の値
            "background_type": 'LINEAR',                        # ご指定の値
            "grid_color": (0.3011, 0.8439, 1.0000, 0.25),
            "wire_color": (0.6000, 1.0000, 0.5000),              # ご指定の値
            "camera_color": (0.3011, 0.8439, 1.0000),            # ご指定の値
            "light_color": (0.85, 0.95, 1.0, 1.0),
            "top_bar_header_color": (0.0026, 0.0026, 0.0026, 1.0),
            "ui_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "ui_frame_color": (0.3011, 0.8439, 1.0000, 0.5),
            "render_color": (0.0026, 0.0026, 0.0026, 1.0),
            "render_environment_strength": 1.0,                 # ご指定の値
            "outliner_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "outliner_background_color": (0.040, 0.053, 0.054, 1.0),
            "text_editor_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "text_editor_background_color": (0.040, 0.053, 0.054, 1.0),
        }
    ),
    # --- 既存のテーマはここから下に残してあります ---
    (
        "USER_DARK_THEME", "My Dark Theme", "A user-defined dark theme.",
        {
            "header_color": (0.0804, 0.1062, 0.1080, 1.0), "custom_gradient_high": (0.0804, 0.1062, 0.1080),
            "custom_gradient_low": (0.0026, 0.0026, 0.0026), "background_type": 'LINEAR',
            "grid_color": (0.6000, 1.0000, 0.5000, 0.25), "wire_color": (0.6000, 1.0000, 0.5000),
            "camera_color": (0.6000, 1.0000, 0.5000), "light_color": (0.9, 1.0, 0.85, 1.0),
            "top_bar_header_color": (0.0026, 0.0026, 0.0026, 1.0), "ui_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "ui_frame_color": (0.6000, 1.0000, 0.5000, 0.5), "render_color": (0.0026, 0.0026, 0.0026, 1.0),
            "render_environment_strength": 1.0, "outliner_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "outliner_background_color": (0.040, 0.053, 0.054, 1.0), "text_editor_header_color": (0.0804, 0.1062, 0.1080, 1.0),
            "text_editor_background_color": (0.040, 0.053, 0.054, 1.0),
        }
    ),
    (
        "ZIONAD_GREEN", "Zionad Green", "A custom green theme.",
        {
            "header_color": (0.05, 0.1, 0.05, 1.0), "custom_gradient_high": (0.162, 0.242, 0.082),
            "custom_gradient_low": (0.0, 0.004, 0.0), "background_type": 'LINEAR',
            "grid_color": (0.6, 1.0, 0.5, 0.4), "wire_color": (0.6, 1.0, 0.5),
            "camera_color": (0.6, 1.0, 0.5), "light_color": (0.8, 1.0, 0.8, 1.0),
            "top_bar_header_color": (0.02, 0.03, 0.02, 1.0), "ui_header_color": (0.05, 0.1, 0.05, 1.0),
            "ui_frame_color": (0.6, 1.0, 0.5, 0.4), "render_color": (0.0, 0.004, 0.0, 1.0),
            "render_environment_strength": 1.0, "outliner_header_color": (0.05, 0.1, 0.05, 1.0),
            "outliner_background_color": (0.03, 0.05, 0.03, 1.0), "text_editor_header_color": (0.05, 0.1, 0.05, 1.0),
            "text_editor_background_color": (0.03, 0.05, 0.03, 1.0),
        }
    ),
    (
        "BLENDER_STANDARD_DARK", "Blender Standard Dark", "Revert to the standard Blender colors.",
        {
            "header_color": (0.188, 0.188, 0.188, 1.0), "custom_gradient_high": (0.239, 0.239, 0.239),
            "custom_gradient_low": (0.188, 0.188, 0.188), "background_type": 'LINEAR',
            "grid_color": (0.329, 0.329, 0.329, 0.502), "wire_color": (0.2, 0.7, 0.2),
            "camera_color": (0.1, 0.5, 0.8), "light_color": (1.0, 1.0, 1.0, 1.0),
            "top_bar_header_color": (0.09, 0.09, 0.09, 1.0), "ui_header_color": (0.188, 0.188, 0.188, 1.0),
            "ui_frame_color": (0.0, 0.0, 0.0, 0.4), "render_color": (0.051, 0.051, 0.051, 1.0),
            "render_environment_strength": 1.0, "outliner_header_color": (0.188, 0.188, 0.188, 1.0),
            "outliner_background_color": (0.141, 0.141, 0.141, 1.0), "text_editor_header_color": (0.188, 0.188, 0.188, 1.0),
            "text_editor_background_color": (0.141, 0.141, 0.141, 1.0),
        }
    ),
]

BACKGROUND_TYPES = [('SINGLE_COLOR', "Single", ""), ('LINEAR', "Linear", ""), ('RADIAL', "Vignette", "")]
DECIMAL_PLACES = [('2', "2", ""), ('3', "3", "")]

def format_tuple(t, decimal_places):
    fmt = f".{decimal_places}f"
    return '(' + ', '.join(f"{x:{fmt}}" for x in t) + ')'

# --- Update Functions ---
def _redraw_areas(context, area_types):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in area_types: area.tag_redraw()
            if area.type == 'PROPERTIES': area.tag_redraw()

def update_background(self, context):
    theme = bpy.context.preferences.themes[0]
    space = theme.view_3d.space
    space.header = self.header_color
    if self.background_type == 'SINGLE_COLOR':
        space.gradients.background_type = 'LINEAR'
        space.gradients.high_gradient = self.custom_gradient_low
        space.gradients.gradient = self.custom_gradient_low
    else:
        space.gradients.background_type = self.background_type
        space.gradients.high_gradient = self.custom_gradient_high
        space.gradients.gradient = self.custom_gradient_low
    _redraw_areas(context, {'VIEW_3D'})

def update_grid(self, context): bpy.context.preferences.themes[0].view_3d.grid = self.grid_color; _redraw_areas(context, {'VIEW_3D'})
def update_wire(self, context): theme = bpy.context.preferences.themes[0]; theme.view_3d.wire = self.wire_color; theme.view_3d.object_active = self.wire_color; _redraw_areas(context, {'VIEW_3D'})
def update_camera(self, context): bpy.context.preferences.themes[0].view_3d.camera = self.camera_color; _redraw_areas(context, {'VIEW_3D'})
def update_light(self, context): bpy.context.preferences.themes[0].view_3d.light = self.light_color; _redraw_areas(context, {'VIEW_3D'})
def update_top_bar(self, context): bpy.context.preferences.themes[0].topbar.space.header = self.top_bar_header_color; _redraw_areas(context, {'TOPBAR'})
def update_ui_header(self, context): bpy.context.preferences.themes[0].user_interface.header = self.ui_header_color; _redraw_areas(context, {'VIEW_3D', 'PROPERTIES', 'OUTLINER', 'INFO'})
def update_ui_frame(self, context): bpy.context.preferences.themes[0].user_interface.wcol_regular.outline = self.ui_frame_color; _redraw_areas(context, {'VIEW_3D', 'PROPERTIES', 'OUTLINER', 'INFO'})
def update_render(self, context):
    theme = bpy.context.preferences.themes[0]; render_space = theme.image_editor.space; render_space.back = self.render_color[:3]; render_space.header = self.render_color
    world = context.scene.world
    if not world: world = bpy.data.worlds.new('MyWorld'); context.scene.world = world
    world.use_nodes = True; bg_node = world.node_tree.nodes.get('Background')
    if not bg_node:
        bg_node = world.node_tree.nodes.new(type='ShaderNodeBackground'); output_node = world.node_tree.nodes.get('World Output')
        if not output_node: output_node = world.node_tree.nodes.new(type='ShaderNodeOutputWorld')
        if output_node: world.node_tree.links.new(bg_node.outputs[0], output_node.inputs['Surface'])
    if bg_node: bg_node.inputs[0].default_value = self.render_color; bg_node.inputs[1].default_value = self.render_environment_strength
    _redraw_areas(context, {'IMAGE_EDITOR', 'VIEW_3D'})
def update_outliner(self, context): theme = bpy.context.preferences.themes[0]; outliner_space = theme.outliner.space; outliner_space.header = self.outliner_header_color; outliner_space.back = self.outliner_background_color[:3]; _redraw_areas(context, {'OUTLINER'})
def update_text_editor(self, context): theme = bpy.context.preferences.themes[0]; text_space = theme.text_editor.space; text_space.header = self.text_editor_header_color; text_space.back = self.text_editor_background_color[:3]; _redraw_areas(context, {'TEXT_EDITOR'})

def update_master_preset(self, context):
    selected_preset = next((p[3] for p in MASTER_PRESETS if p[0] == self.master_preset), None)
    if selected_preset:
        for key, value in selected_preset.items():
            setattr(self, key, value)

# Property Group
class ViewportColorProperties(PropertyGroup):
    master_preset: EnumProperty(name="Theme Preset", description="Select a complete color theme", items=[(p[0], p[1], p[2]) for p in MASTER_PRESETS], update=update_master_preset)
    header_color: FloatVectorProperty(name="Header", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_background)
    custom_gradient_high: FloatVectorProperty(name="Gradient High", subtype='COLOR', size=3, min=0.0, max=1.0, update=update_background)
    custom_gradient_low: FloatVectorProperty(name="Gradient Low", subtype='COLOR', size=3, min=0.0, max=1.0, update=update_background)
    background_type: EnumProperty(name="Type", items=BACKGROUND_TYPES, default='LINEAR', update=update_background)
    grid_color: FloatVectorProperty(name="Grid", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_grid)
    wire_color: FloatVectorProperty(name="Wireframe", subtype='COLOR', size=3, min=0.0, max=1.0, update=update_wire)
    camera_color: FloatVectorProperty(name="Camera", subtype='COLOR', size=3, min=0.0, max=1.0, update=update_camera)
    light_color: FloatVectorProperty(name="Light", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_light)
    top_bar_header_color: FloatVectorProperty(name="Top Bar", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_top_bar)
    ui_header_color: FloatVectorProperty(name="Menu Bar (Header)", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_ui_header)
    ui_frame_color: FloatVectorProperty(name="UI Frame", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_ui_frame)
    render_color: FloatVectorProperty(name="Render BG", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_render)
    render_environment_strength: FloatProperty(name="Strength", default=1.0, min=0.0, max=1900.0, update=update_render)
    outliner_header_color: FloatVectorProperty(name="Outliner Header", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_outliner)
    outliner_background_color: FloatVectorProperty(name="Outliner BG", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_outliner)
    text_editor_header_color: FloatVectorProperty(name="Text Header", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_text_editor)
    text_editor_background_color: FloatVectorProperty(name="Text BG", subtype='COLOR', size=4, min=0.0, max=1.0, update=update_text_editor)
    decimal_places: EnumProperty(name="Precision", items=DECIMAL_PLACES, default='3')

class THEME_OT_copy_current_settings(Operator):
    bl_idname = f"{PREFIX}_theme.copy_settings"
    bl_label = "Copy Current Settings as Preset"
    bl_description = "Copy all current color settings to the clipboard as a new master preset code"

    def execute(self, context):
        props = context.scene.viewport_color_props
        dp = int(props.decimal_places)
        def format_value(value):
            if hasattr(value, 'to_tuple'): return format_tuple(value[:], dp)
            elif isinstance(value, str): return f"'{value}'"
            return str(value)
        settings_dict = {k: getattr(props, k) for k in props.bl_rna.properties.keys() if k not in ('rna_type', 'name', 'master_preset', 'decimal_places')}
        dict_items_str = ",\n".join(f'            "{key}": {format_value(value)}' for key, value in settings_dict.items())
        preset_string = f"(\n    \"NEW_THEME\", \"New Theme Name\", \"Description\",\n    {{\n{dict_items_str}\n    }}\n),"
        context.window_manager.clipboard = preset_string
        self.report({'INFO'}, "Theme preset code copied to clipboard.")
        return {'FINISHED'}

class RemoveAllPanels(Operator):
    bl_idname = f"{PREFIX}_wm.remove_all_panels"
    bl_label = PANEL_LABELS["REMOVE"]
    def execute(self, context):
        unregister()
        return {'FINISHED'}

# --- Panels ---
class VIEW3D_PT_solid_background_panel(Panel):
    bl_label = PANEL_LABELS["BACKGROUND"]; bl_idname = BG_PANEL_IDNAME_1
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 0
    def draw(self, context):
        layout = self.layout; props = context.scene.viewport_color_props
        layout.prop(props, "master_preset", text=""); layout.operator(THEME_OT_copy_current_settings.bl_idname); layout.separator()
        box = layout.box(); row = box.row(); row.alignment = 'LEFT'; row.label(text="Viewport Background"); row.prop(props, "background_type", text="")
        box.prop(props, "header_color"); box.prop(props, "custom_gradient_high"); box.prop(props, "custom_gradient_low"); box.prop(props, "grid_color")
        box = layout.box(); box.label(text="Other Editors")
        row = box.row(align=True); row.prop(props, "render_color"); row.prop(props, "render_environment_strength", text="", slider=True)
        box.prop(props, "outliner_header_color"); box.prop(props, "outliner_background_color")
        box.prop(props, "text_editor_header_color"); box.prop(props, "text_editor_background_color"); layout.separator(); layout.prop(props, "decimal_places")

class VIEW3D_PT_ObjectColorsPanel(Panel):
    bl_label = PANEL_LABELS["OBJECT_COLORS"]; bl_idname = OBJECT_COLORS_PANEL_IDNAME
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_parent_id = BG_PANEL_IDNAME_1; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout; props = context.scene.viewport_color_props
        box = layout.box(); box.prop(props, "wire_color"); box.prop(props, "camera_color"); box.prop(props, "light_color")

class VIEW3D_PT_InterfaceColorsPanel(Panel):
    bl_label = PANEL_LABELS["INTERFACE_COLORS"]; bl_idname = INTERFACE_COLORS_PANEL_IDNAME
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_parent_id = BG_PANEL_IDNAME_1; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout; props = context.scene.viewport_color_props
        box = layout.box(); box.prop(props, "top_bar_header_color"); box.prop(props, "ui_header_color"); box.prop(props, "ui_frame_color")

class VIEW3D_PT_RemovePanel(Panel):
    bl_label = PANEL_LABELS["REMOVE"]; bl_idname = REMOVE_PANEL_IDNAME
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 99
    def draw(self, context): self.layout.operator(RemoveAllPanels.bl_idname, text=PANEL_LABELS["REMOVE"])

# Registration
classes = [
    ViewportColorProperties, THEME_OT_copy_current_settings, RemoveAllPanels,
    VIEW3D_PT_solid_background_panel, VIEW3D_PT_ObjectColorsPanel,
    VIEW3D_PT_InterfaceColorsPanel, VIEW3D_PT_RemovePanel,
]

initial_preset_applied = False

def apply_initial_preset(context):
    global initial_preset_applied
    if not context.scene or initial_preset_applied: return
    props = context.scene.viewport_color_props
    # --- デフォルトで読み込むプリセットを新しいテーマIDに設定 ---
    props.master_preset = 'ZIONAD_CYAN'
    initial_preset_applied = True

@persistent
def load_handler(dummy):
    global initial_preset_applied; initial_preset_applied = False
    bpy.app.timers.register(lambda: apply_initial_preset(bpy.context), first_interval=0.1)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.viewport_color_props = PointerProperty(type=ViewportColorProperties)
    if load_handler not in bpy.app.handlers.load_post: bpy.app.handlers.load_post.append(load_handler)
    apply_initial_preset(bpy.context)

def unregister():
    if hasattr(bpy.types.Scene, 'viewport_color_props'): del bpy.types.Scene.viewport_color_props
    if load_handler in bpy.app.handlers.load_post: bpy.app.handlers.load_post.remove(load_handler)
    for cls in reversed(classes):
        if hasattr(bpy.utils, "unregister_class") and hasattr(cls, "bl_rna"):
            try: bpy.utils.unregister_class(cls)
            except RuntimeError: pass

if __name__ == "__main__":
    try: unregister()
    except Exception as e: print(f"Error on unregister: {e}")
    register()