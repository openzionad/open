import bpy
from bpy.props import FloatVectorProperty, EnumProperty, BoolProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

# Add-on metadata
bl_info = {
    "name": "zionad 520 [ 3D Viewport Color] (Simplified)",
    "author": "zionadchat",
    "version": (2, 1),
    "blender": (4, 4, 0),
    "category": " small  520  [  3D Viewport  ]   ",
    "description": "Control 3D Viewport header and background colors with presets and gradients",
    "location": "View3D > Sidebar",
}

# Constants
ADDON_CATEGORY_NAME = bl_info["category"]
PREFIX = "view20250718s"

# Panel definitions
BG_PANEL_IDNAME_1 = f"{PREFIX}_VIEW3D_PT_solid_background_panel"
REMOVE_PANEL_IDNAME = f"{PREFIX}_VIEW3D_PT_remove"

# Panel labels
PANEL_LABELS = {
    "BACKGROUND": "3D Viewport Color",
    "REMOVE": "アドオン削除",
}

# Presets for the 3D Viewport Background
BASE_PRESETS = [
    ("Viewport 4.4.0", "Viewport 4.4.0", "Viewport 4.4.0 theme", (0.188, 0.188, 0.188, 0.702), (0.239, 0.239, 0.239), (0.188, 0.188, 0.188)),
    ("DARK_BLUE", "Dark Blue", "Dark Blue theme", (0.1, 0.1, 0.3, 1.0), (0.0706, 0.1294, 0.3137), (0.05, 0.05, 0.15)),
    ("CUSTOM", "Custom", "Custom theme", (0.090, 0.137, 0.047, 1.000), (0.502, 0.702, 0.502), (0.102, 0.149, 0.051)),
    ("FOREST_GREEN", "Forest Green", "Forest Green theme", (0.2, 0.3, 0.1, 1.0), (0.5, 0.7, 0.5), (0.1, 0.15, 0.05)),
    ("DARK_GREEN", "Dark Green", "Dark Green theme", (0.00, 0.03, 0.00, 1.00), (0.00, 0.278, 0.016), (0.10, 0.15, 0.05)),
    ("DEEP_PURPLE", "Deep Purple", "Deep Purple theme", (0.3, 0.1, 0.3, 1.0), (0.9, 0.8, 1.0), (0.15, 0.05, 0.15)),
    ("DEEP_CRIMSON", "Deep Crimson", "Deep Crimson theme", (0.251, 0.039, 0.161, 1.0), (0.251, 0.039, 0.161), (0.000, 0.031, 0.102)),
    ("CUSTOM2", "Custom2", "Custom2 theme", (0.15, 0.04, 0.16, 1.00), (0.15, 0.04, 0.16), (0.00, 0.03, 0.10)),
    ("CUSTOM3", "Custom3", "Custom3 theme", (0.25, 0.44, 0.16, 1.00), (0.25, 0.44, 0.16), (0.00, 0.03, 0.10)),
]

# Background type options and Decimal places options
BACKGROUND_TYPES = [
    ('SINGLE_COLOR', "Single Color", "Uniform background color"),
    ('LINEAR', "Linear Gradient", "Linear gradient background"),
    ('RADIAL', "Vignette", "Radial gradient simulating a vignette effect"),
]

DECIMAL_PLACES = [
    ('2', "2 Decimal Places", "Display colors with 2 decimal places"),
    ('3', "3 Decimal Places", "Display colors with 3 decimal places"),
]

# Utility function to format tuples
def format_tuple(t, decimal_places):
    fmt = f".{decimal_places}f"
    return '(' + ', '.join(f"{x:{fmt}}" for x in t) + ')'

# Property Group for all color settings
class ViewportColorProperties(PropertyGroup):
    # Background Properties
    background_type: EnumProperty(
        name="Background Type", description="Choose the background type",
        items=BACKGROUND_TYPES, default='LINEAR'
    )
    header_color: FloatVectorProperty(name="Header Color", subtype='COLOR', size=4, min=0.0, max=1.0, default=(0.188, 0.188, 0.188, 0.702))
    custom_gradient_high: FloatVectorProperty(name="Gradient High Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.239, 0.239, 0.239))
    custom_gradient_low: FloatVectorProperty(name="Gradient Low Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.188, 0.188, 0.188))
    reverse_gradient: BoolProperty(name="Reverse Gradient", default=False, description="Reverse the gradient colors")
    preset: EnumProperty(
        name="Color Preset", description="Choose a color preset",
        items=[(p[0], p[1], p[2]) for p in BASE_PRESETS], default="Viewport 4.4.0",
        update=lambda self, context: ViewportColorProperties.update_preset(self, context)
    )
    decimal_places: EnumProperty(
        name="Decimal Places", description="Choose the number of decimal places for display",
        items=DECIMAL_PLACES, default='3'
    )

    @staticmethod
    def update_preset(self, context):
        props = context.scene.viewport_color_props
        preset_id = props.preset
        for preset in BASE_PRESETS:
            if preset[0] == preset_id:
                props.header_color = preset[3]
                props.custom_gradient_high = preset[4]
                props.custom_gradient_low = preset[5]
                break
        bpy.ops.view20250320f_background.apply_color()

# Operators
class BACKGROUND_OT_apply_color(Operator):
    bl_idname = f"{PREFIX}_background.apply_color"
    bl_label = "Apply Background Color"
    bl_description = "Apply the selected background color for Solid Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.viewport_color_props
        theme = bpy.context.preferences.themes[0]
        space = theme.view_3d.space
        space.header = props.header_color
        if props.background_type == 'SINGLE_COLOR':
            space.gradients.background_type = 'LINEAR'
            color = props.custom_gradient_low if props.reverse_gradient else props.custom_gradient_high
            space.gradients.high_gradient = color
            space.gradients.gradient = color
        else:
            high_color = props.custom_gradient_low if props.reverse_gradient else props.custom_gradient_high
            low_color = props.custom_gradient_high if props.reverse_gradient else props.custom_gradient_low
            space.gradients.background_type = props.background_type
            space.gradients.high_gradient = high_color
            space.gradients.gradient = low_color
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        self.report({'INFO'}, f"Viewport colors updated - Header: {format_tuple(props.header_color, int(props.decimal_places))}, High: {format_tuple(props.custom_gradient_high, int(props.decimal_places))}, Low: {format_tuple(props.custom_gradient_low, int(props.decimal_places))}")
        return {'FINISHED'}

class BACKGROUND_OT_copy_color(Operator):
    bl_idname = f"{PREFIX}_background.copy_color"
    bl_label = "Copy Background Colors"
    bl_description = "Copy current 3D Viewport colors to clipboard in preset format"

    def execute(self, context):
        props = context.scene.viewport_color_props
        theme = bpy.context.preferences.themes[0]
        space = theme.view_3d.space
        decimal_places = int(props.decimal_places)
        header_str = format_tuple(space.header, decimal_places)
        high_str = format_tuple(space.gradients.high_gradient, decimal_places)
        low_str = format_tuple(space.gradients.gradient, decimal_places)
        color_str = f'("CUSTOM", "Custom", "Custom theme", {header_str}, {high_str}, {low_str}),'
        context.window_manager.clipboard = color_str
        self.report({'INFO'}, "Preset format copied to clipboard")
        return {'FINISHED'}

class RemoveAllPanels(Operator):
    bl_idname = f"{PREFIX}_wm.remove_all_panels"
    bl_label = PANEL_LABELS["REMOVE"]

    def execute(self, context):
        unregister()
        self.report({'INFO'}, f"Add-on '{bl_info['name']}' has been unregistered.")
        return {'FINISHED'}

# Panels
class VIEW3D_PT_solid_background_panel(Panel):
    bl_label = PANEL_LABELS["BACKGROUND"]
    bl_idname = BG_PANEL_IDNAME_1
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        props = context.scene.viewport_color_props
        theme = bpy.context.preferences.themes[0]
        space = theme.view_3d.space
        decimal_places = int(props.decimal_places)
        layout.label(text="Current Colors:")
        layout.label(text=f"Header: {format_tuple(space.header, decimal_places)}")
        layout.label(text=f"High: {format_tuple(space.gradients.high_gradient, decimal_places)}")
        layout.label(text=f"Low: {format_tuple(space.gradients.gradient, decimal_places)}")
        layout.operator(f"{PREFIX}_background.copy_color", text="Copy Colors")
        layout.separator()
        layout.prop(props, "preset")
        layout.prop(props, "header_color")
        layout.prop(props, "background_type")
        if props.background_type != 'SINGLE_COLOR':
            layout.prop(props, "custom_gradient_high")
            layout.prop(props, "custom_gradient_low")
        layout.prop(props, "reverse_gradient")
        layout.prop(props, "decimal_places", text="Display Precision")
        layout.operator(f"{PREFIX}_background.apply_color")

class VIEW3D_PT_RemovePanel(Panel):
    bl_label = PANEL_LABELS["REMOVE"]
    bl_idname = REMOVE_PANEL_IDNAME
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 1  # Displayed after the main panel

    def draw(self, context):
        layout = self.layout
        layout.operator(f"{PREFIX}_wm.remove_all_panels", text=PANEL_LABELS["REMOVE"])

# Helper function to initialize properties from current theme
def initialize_properties(context):
    if not hasattr(context, 'scene') or context.scene is None:
        return  # Skip if no valid scene context
    props = context.scene.viewport_color_props
    theme = bpy.context.preferences.themes[0]
    space = theme.view_3d.space
    
    # Only update if not already initialized to avoid overwriting user changes
    if props.header_color == (0.188, 0.188, 0.188, 0.702):
        props.header_color = space.header[:]
    if props.custom_gradient_high == (0.239, 0.239, 0.239):
        props.custom_gradient_high = space.gradients.high_gradient[:]
    if props.custom_gradient_low == (0.188, 0.188, 0.188):
        props.custom_gradient_low = space.gradients.gradient[:]
    props.background_type = space.gradients.background_type

# List of classes to register/unregister
classes = (
    ViewportColorProperties,
    BACKGROUND_OT_apply_color,
    BACKGROUND_OT_copy_color,
    RemoveAllPanels,
    VIEW3D_PT_solid_background_panel,
    VIEW3D_PT_RemovePanel,
)

# Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.viewport_color_props = PointerProperty(type=ViewportColorProperties)

# Unregistration
def unregister():
    # Unregister in reverse order to avoid errors
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, 'viewport_color_props'):
        del bpy.types.Scene.viewport_color_props

# Add a persistent handler to initialize properties when a scene is loaded
from bpy.app.handlers import persistent

@persistent
def load_handler(dummy):
    # This handler ensures properties are initialized with the current theme
    # when Blender starts or a new file is loaded.
    if bpy.context.scene is not None:
        initialize_properties(bpy.context)

# Main execution block
if __name__ == "__main__":
    try:
        # A clean unregister before registering can prevent issues during development
        unregister()
    except Exception as e:
        print(f"Error during unregister on script reload: {e}")
    
    register()
    
    # Register the load handler
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    
    # Manually initialize for the first run
    load_handler(None)