import bpy
import webbrowser
import mathutils
import os
import math
from bpy.types import Operator, Panel, Scene, PropertyGroup
from bpy.props import StringProperty, EnumProperty, IntProperty, PointerProperty, BoolProperty, FloatProperty
from datetime import datetime

# ===================================================================
# パラメータ設定
# ===================================================================
_PREFIX_STATIC_PART = "world" 
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"
ADDON_CATEGORY_NAME = "[aaa   world  20250714 ]"

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (World & Links)",
    "author": "zionadchat & Your Name",
    "version": (9, 0, 7), # ★バージョンアップ
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "ワールド設定、エンジン連動、パネル展開、初期視点設定などを含む統合アドオン",
    "category": ADDON_CATEGORY_NAME,
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343",
}

# ===================================================================
# プリセットとリンクデータ
# ===================================================================
SKY_PRESETS = [
    {"name": "Default Sunset", "sky_type": 'NISHITA', "sun_elevation": 2.1, "sun_rotation": 0.0, "altitude": 0.0, "air_density": 1.344, "dust_density": 3.908, "ozone_density": 6.000,},
    {"name": "Clear Day", "sky_type": 'NISHITA', "sun_elevation": 45.0, "sun_rotation": 180.0, "altitude": 1000.0, "air_density": 1.0, "dust_density": 0.5, "ozone_density": 3.0,},
]

HDRI_PRESETS = [
    {"path": r"C:\a111\HDRi_pic\qwantani_afternoon_puresky_4k.exr", "name": "qwantani_afternoon_puresky_4k.exr", "rotation": (math.radians(30), 0, math.radians(220))},
    {"path": r"C:\a111\HDRi_pic\rogland_clear_night_4k.hdr", "name": "rogland_clear_night_4k.hdr", "rotation": None},
    {"path": r"C:\a111\HDRi_pic\rogland_moonlit_night_4k.hdr", "name": "rogland_moonlit_night_4k.hdr", "rotation": None},
    {"path": r"C:\a111\HDRi_pic\golden_bay_4k.hdr", "name": "golden_bay_4k.hdr", "rotation": None},
    {"path": r"C:\a111\HDRi_pic\hangar_interior_4k.hdr", "name": "hangar_interior_4k.hdr", "rotation": None},
]

ADDON_LINKS = [
    {"label": "HDRi ワールドコントロール 20250705", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"},
]

NEW_DOC_LINKS = [
    {"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"},
    {"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},
]

DOC_LINKS = [
    {"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"},
    {"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"},
    {"label": "addon 目次整理　from 20250116", "url": "https://blenderzionad.hatenablog.com/entry/2025/01/17/002322"},
]

SOCIAL_LINKS = [
    {"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"},
    {"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"},
    {"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"},
    {"label": "単純トリック 2025 open", "url": "https://www.notion.so/2025-open-221b3deba7a2809a85a9f5ab5600ab06"},
]

# ===================================================================
# ヘルパー関数
# ===================================================================
def get_world_nodes(context, create=True):
    world = context.scene.world
    if not world and create:
        world = bpy.data.worlds.new("World")
        context.scene.world = world
    if not world: return None, None
    if create: world.use_nodes = True
    if not world.use_nodes: return world, None
    return world, world.node_tree

def find_or_create_node(nodes, node_type, name, location_offset=(0, 0)):
    node = nodes.get(name)
    if node: return node
    
    new_node = nodes.new(type=node_type)
    new_node.name = name
    new_node.label = name.replace("_", " ")
    
    output_node = nodes.get('World Output')
    if output_node:
        new_node.location = output_node.location + mathutils.Vector(location_offset)
    return new_node
    
def update_viewport(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D': space.shading.type = 'RENDERED'; return

def update_background_mode(self, context):
    mode = context.scene.zionad_world_props.background_mode
    world, tree = get_world_nodes(context)
    if not tree: return
    
    nodes, links = tree.nodes, tree.links
    
    output_node = find_or_create_node(nodes, 'ShaderNodeOutputWorld', 'World Output')
    background_node = find_or_create_node(nodes, 'ShaderNodeBackground', 'Background', (-200, 0))
    sky_node = find_or_create_node(nodes, 'ShaderNodeTexSky', 'Sky Texture', (-450, 100))
    env_node = find_or_create_node(nodes, 'ShaderNodeTexEnvironment', 'Environment Texture', (-450, -100))
    
    if background_node.inputs['Color'].is_linked:
        links.remove(background_node.inputs['Color'].links[0])
    if output_node.inputs['Surface'].is_linked:
        links.remove(output_node.inputs['Surface'].links[0])
        
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    
    if mode == 'SKY':
        links.new(sky_node.outputs['Color'], background_node.inputs['Color'])
    elif mode == 'HDRI':
        mapping_node = find_or_create_node(nodes, 'ShaderNodeMapping', 'Mapping', (-700, -100))
        tex_coord_node = find_or_create_node(nodes, 'ShaderNodeTexCoord', 'Texture Coordinate', (-950, -100))
        
        if not mapping_node.inputs['Vector'].is_linked:
            links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
        if not env_node.inputs['Vector'].is_linked:
            links.new(mapping_node.outputs['Vector'], env_node.inputs['Vector'])
        links.new(env_node.outputs['Color'], background_node.inputs['Color'])
        
        props = context.scene.zionad_world_props
        if 0 <= props.hdri_list_index < len(HDRI_PRESETS):
             bpy.ops.world_20240715120000.load_hdri_from_list(hdri_index=props.hdri_list_index)

    update_viewport(context)

def update_sun_size_from_percent(self, context):
    world, tree = get_world_nodes(context, create=False)
    if not tree: return
    sky_node = tree.nodes.get('Sky Texture')
    if sky_node:
        max_angle_rad = math.pi
        sky_node.sun_size = (self.sun_size_percent / 100.0) * max_angle_rad

# ===================================================================
# プロパティグループ
# ===================================================================
class ZIONAD_WorldProperties(PropertyGroup):
    background_mode: EnumProperty(name="Background Mode", items=[('HDRI', "HDRI", ""), ('SKY', "Sky", "")], default='SKY', update=update_background_mode)
    sun_size_percent: FloatProperty(name="Sun Size", description="太陽のサイズをパーセンテージで設定 (0% = 0°, 100% = 180°)", subtype='PERCENTAGE', min=0.0, max=100.0, default=(30.0 / 180.0) * 100.0, update=update_sun_size_from_percent)
    hdri_list_index: IntProperty(name="Active HDRI Index", default=0)

class ZIONAD_LinkPanelProperties(PropertyGroup):
    show_main_docs: BoolProperty(name="HDRi ワールドコントロール 20250705", default=True)
    show_new_docs: BoolProperty(name="更新情報 / 目次", default=True)
    show_old_docs: BoolProperty(name="過去のドキュメント", default=False)
    show_social: BoolProperty(name="関連リンク / SNS", default=False)

# ===================================================================
# オペレーター
# ===================================================================
class ZIONAD_OT_ResetSkyProperty(Operator):
    bl_idname = f"{PREFIX}.reset_sky_property"; bl_label = "Reset Sky Property"; bl_options = {'REGISTER', 'UNDO'}; property_to_reset: StringProperty()
    def execute(self, context):
        props = context.scene.zionad_world_props; world, tree = get_world_nodes(context, create=False)
        if not tree: return {'CANCELLED'}
        sky_node = tree.nodes.get('Sky Texture'); background_node = tree.nodes.get('Background'); mapping_node = tree.nodes.get('Mapping')
        prop = self.property_to_reset; default_sun_size_rad = math.radians(0.545); max_angle_rad = math.pi; default_sun_size_percent = (default_sun_size_rad / max_angle_rad) * 100.0
        defaults = {"sun_size_percent": default_sun_size_percent, "sun_intensity": 1.0, "sun_elevation": math.radians(45.0), "sun_rotation": math.radians(0.0), "altitude": 0.0, "air_density": 1.0, "dust_density": 0.0, "ozone_density": 3.0, "strength": 1.0,}
        if prop in ['Location', 'Rotation', 'Scale'] and mapping_node:
            if prop == 'Location': mapping_node.inputs['Location'].default_value = (0, 0, 0)
            elif prop == 'Rotation': mapping_node.inputs['Rotation'].default_value = (0, 0, 0)
            elif prop == 'Scale': mapping_node.inputs['Scale'].default_value = (1, 1, 1)
            self.report({'INFO'}, f"Reset '{prop}' to default."); return {'FINISHED'}

        if prop in defaults:
            if prop == "strength" and background_node: background_node.inputs['Strength'].default_value = defaults[prop]
            elif prop == "sun_size_percent": setattr(props, prop, defaults[prop])
            elif sky_node and hasattr(sky_node, prop): setattr(sky_node, prop, defaults[prop])
            self.report({'INFO'}, f"Reset '{prop}' to default.")
        else: self.report({'WARNING'}, f"Unknown property to reset: {prop}")
        return {'FINISHED'}

class ZIONAD_OT_ShowWorldProperties(Operator):
    bl_idname = f"{PREFIX}.show_world_properties"; bl_label = "右下をワールド設定にする"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        text_editor_area = next((area for area in context.screen.areas if area.type == 'TEXT_EDITOR'), None)
        if text_editor_area:
            text_editor_area.type = 'PROPERTIES'; text_editor_area.spaces.active.context = 'WORLD'
            self.report({'INFO'}, "テキストエディタをワールド設定に切り替えました。"); return {'FINISHED'}
        else:
            self.report({'WARNING'}, "切り替え対象のテキストエディタが見つかりません。"); return {'CANCELLED'}

class ZIONAD_OT_ShowTextEditor(Operator):
    bl_idname = f"{PREFIX}.show_text_editor"; bl_label = "右下をテキストエディタにする"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        properties_area = next((area for area in context.screen.areas if area.type == 'PROPERTIES'), None)
        if properties_area:
            properties_area.type = 'TEXT_EDITOR'; self.report({'INFO'}, "プロパティエディタをテキストエディタに切り替えました。"); return {'FINISHED'}
        else:
            self.report({'WARNING'}, "切り替え対象のプロパティエディタが見つかりません。"); return {'CANCELLED'}

class ZIONAD_OT_ToggleSunDisc(Operator):
    bl_idname = f"{PREFIX}.toggle_sun_disc_and_engine"; bl_label = "Toggle Sun Disc"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        world, tree = get_world_nodes(context, create=False);
        if not tree: self.report({'WARNING'}, "World nodes not found."); return {'CANCELLED'}
        sky_node = tree.nodes.get('Sky Texture');
        if not sky_node or sky_node.sky_type != 'NISHITA': self.report({'WARNING'}, "Nishita Sky Texture not found."); return {'CANCELLED'}
        sky_node.sun_disc = not sky_node.sun_disc
        if sky_node.sun_disc:
            context.scene.render.engine = 'CYCLES'; props = context.scene.zionad_world_props
            props.sun_size_percent = (30.0 / 180.0) * 100.0
            self.report({'INFO'}, "Sun Disc ON (Sun Size set to 30°). Switched to Cycles.")
        else:
            context.scene.render.engine = 'EEVEE'; self.report({'INFO'}, "Sun Disc OFF. Switched to Eevee.")
        return {'FINISHED'}

class ZIONAD_OT_LoadSkyPreset(Operator):
    bl_idname = f"{PREFIX}.load_sky_preset"; bl_label = "Load Sky Preset"; bl_options = {'REGISTER', 'UNDO'}; preset_index: IntProperty()
    def execute(self, context):
        if not (0 <= self.preset_index < len(SKY_PRESETS)): self.report({'ERROR'}, "Invalid Sky preset index"); return {'CANCELLED'}
        preset = SKY_PRESETS[self.preset_index]; context.scene.zionad_world_props.background_mode = 'SKY'
        world, tree = get_world_nodes(context, create=False);
        if not tree: return {'CANCELLED'}
        sky_node = tree.nodes.get('Sky Texture')
        if sky_node:
            sky_node.sky_type = preset.get("sky_type", 'NISHITA')
            sky_node.sun_elevation = math.radians(preset.get("sun_elevation", 45.0))
        self.report({'INFO'}, f"Loaded preset: {preset['name']}"); return {'FINISHED'}

class ZIONAD_OT_LoadHdriFromList(Operator):
    bl_idname = f"{PREFIX}.load_hdri_from_list"; bl_label = "Load HDRI from List"; bl_options = {'REGISTER', 'UNDO'}
    hdri_index: IntProperty()
    def execute(self, context):
        props = context.scene.zionad_world_props
        if not (0 <= self.hdri_index < len(HDRI_PRESETS)): self.report({'ERROR'}, "Invalid HDRI index"); return {'CANCELLED'}
        
        props.hdri_list_index = self.hdri_index
        if props.background_mode != 'HDRI': props.background_mode = 'HDRI'
        
        preset = HDRI_PRESETS[self.hdri_index]; filepath = preset["path"]
        world, tree = get_world_nodes(context)
        if not tree: return {'CANCELLED'}
        
        env_node = tree.nodes.get('Environment Texture')
        if not env_node: self.report({'ERROR'}, "Environment Texture node not found."); return {'CANCELLED'}

        if os.path.exists(filepath):
            try: env_node.image = bpy.data.images.load(filepath, check_existing=True)
            except RuntimeError as e: self.report({'ERROR'}, f"Failed to load image: {e}"); return {'CANCELLED'}
        else: self.report({'WARNING'}, f"File not found: {filepath}"); return {'CANCELLED'}
        
        mapping_node = tree.nodes.get('Mapping')
        if mapping_node:
            mapping_node.inputs['Location'].default_value = (0, 0, 0)
            mapping_node.inputs['Scale'].default_value = (1, 1, 1)
            # ★★★ 変更点: rotationがNoneの場合に (0, 0, 0) を使うように修正 ★★★
            rotation_value = preset.get("rotation")
            mapping_node.inputs['Rotation'].default_value = rotation_value if rotation_value is not None else (0, 0, 0)

        update_viewport(context)
        self.report({'INFO'}, f"Loaded: {preset['name']}"); return {'FINISHED'}

class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"; bl_label = "Open URL"; url: StringProperty(); 
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}

class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"; bl_label = "登録解除"; bl_options = {'REGISTER', 'UNDO'}; 
    def execute(self, context):
        unregister()
        self.report({'INFO'}, "アドオンを登録解除しました。"); return {'CANCELLED'}

# ===================================================================
# UIパネル
# ===================================================================
class ZIONAD_PT_WorldControlPanel(Panel):
    bl_label = "World Control"; bl_idname = f"{PREFIX}_PT_world_control"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 0
    def _draw_prop_with_reset(self, layout, obj, prop_name, text=None):
        row = layout.row(align=True); split = row.split(factor=0.85, align=True)
        split.prop(obj, prop_name, text=text if text else prop_name.replace("_", " ").title())
        op = split.operator(ZIONAD_OT_ResetSkyProperty.bl_idname, text="", icon='FILE_REFRESH'); op.property_to_reset = prop_name
    def _draw_input_with_reset(self, layout, node_input, prop_name, text=None):
        row = layout.row(align=True); split = row.split(factor=0.85, align=True)
        split.prop(node_input, "default_value", text=text if text else prop_name.replace("_", " ").title())
        op = split.operator(ZIONAD_OT_ResetSkyProperty.bl_idname, text="", icon='FILE_REFRESH'); op.property_to_reset = prop_name
    def draw(self, context):
        layout = self.layout; scene = context.scene; props = scene.zionad_world_props; world, tree = get_world_nodes(context, create=False)
        if not tree: layout.label(text="ワールドノードを有効にしてください", icon='ERROR'); return
        nodes = tree.nodes
        box_render = layout.box(); box_render.prop(scene.render, "engine", expand=True); layout.separator()
        box_mode = layout.box(); box_mode.prop(props, "background_mode", expand=True); layout.separator()
        
        if props.background_mode == 'SKY':
            box_sky = layout.box(); box_sky.label(text="Sky Texture", icon='WORLD_DATA')
            col = box_sky.column(align=True)
            col.operator(ZIONAD_OT_ShowWorldProperties.bl_idname, icon='PROPERTIES')
            col.operator(ZIONAD_OT_ShowTextEditor.bl_idname, icon='TEXT')
            box_sky.separator()
            sky_node = nodes.get('Sky Texture'); background_node = nodes.get('Background')
            if sky_node:
                col_sky = box_sky.column(align=True); self._draw_prop_with_reset(col_sky, sky_node, "sky_type", text="Type")
                if sky_node.sky_type == 'NISHITA':
                    op_text = f"Sun Disc ON ({'Cycles'})" if sky_node.sun_disc else f"Sun Disc OFF ({'Eevee'})"
                    col_sky.operator(ZIONAD_OT_ToggleSunDisc.bl_idname, text=op_text, depress=sky_node.sun_disc); col_sky.separator()
                    self._draw_prop_with_reset(col_sky, props, "sun_size_percent", text="Sun Size")
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_intensity")
                    if background_node: self._draw_input_with_reset(col_sky, background_node.inputs['Strength'], "strength", text="Strength")
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_elevation"); self._draw_prop_with_reset(col_sky, sky_node, "sun_rotation")
                    self._draw_prop_with_reset(col_sky, sky_node, "altitude"); self._draw_prop_with_reset(col_sky, sky_node, "air_density", text="Air")
                    self._draw_prop_with_reset(col_sky, sky_node, "dust_density", text="Dust"); self._draw_prop_with_reset(col_sky, sky_node, "ozone_density", text="Ozone")
        
        elif props.background_mode == 'HDRI':
            box_env = layout.box(); box_env.label(text="Environment Texture (HDRI)", icon='IMAGE_DATA')
            col_list = box_env.column(align=True); col_list.label(text="HDRI Presets:")
            for i, preset in enumerate(HDRI_PRESETS):
                op = col_list.operator(ZIONAD_OT_LoadHdriFromList.bl_idname, text=preset["name"], depress=(props.hdri_list_index == i))
                op.hdri_index = i
            
            box_env.separator()
            env_node = nodes.get('Environment Texture')
            if env_node: box_env.template_ID(env_node, "image", open="image.open", text="Select HDRI")
            
            mapping_node = nodes.get('Mapping')
            if mapping_node:
                box_transform = box_env.box(); box_transform.label(text="Transform", icon='OBJECT_DATA')
                col_transform = box_transform.column(align=True)
                self._draw_input_with_reset(col_transform, mapping_node.inputs['Location'], 'Location')
                self._draw_input_with_reset(col_transform, mapping_node.inputs['Rotation'], 'Rotation')
                self._draw_input_with_reset(col_transform, mapping_node.inputs['Scale'], 'Scale')

class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集"; bl_idname = f"{PREFIX}_PT_links_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 1; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_link_panel_props
        def draw_collapsible_section(prop_name, link_list):
            box = layout.box(); row = box.row(); is_expanded = getattr(props, prop_name)
            row.prop(props, prop_name, icon="TRIA_DOWN" if is_expanded else "TRIA_RIGHT", emboss=False)
            if is_expanded:
                col = box.column(align=True)
                for link in link_list:
                    op = col.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL'); op.url = link["url"]
        draw_collapsible_section("show_main_docs", ADDON_LINKS)
        draw_collapsible_section("show_new_docs", NEW_DOC_LINKS)
        draw_collapsible_section("show_old_docs", DOC_LINKS)
        draw_collapsible_section("show_social", SOCIAL_LINKS)

class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"; bl_idname = f"{PREFIX}_PT_remove_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 2; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): self.layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, icon='CANCEL')

# ===================================================================
# 初期化と登録処理
# ===================================================================
def apply_initial_sky_settings(context):
    world, tree = get_world_nodes(context);
    if not tree: return
    nodes = tree.nodes; sky_node = find_or_create_node(nodes, 'ShaderNodeTexSky', 'Sky Texture'); background_node = find_or_create_node(nodes, 'ShaderNodeBackground', 'Background')
    sky_node.sky_type = 'NISHITA'; sky_node.sun_disc = True
    props = context.scene.zionad_world_props; props.sun_size_percent = (30.0 / 180.0) * 100.0
    sky_node.sun_intensity = 0.01; sky_node.sun_elevation = math.radians(3.0); sky_node.sun_rotation = math.radians(0.0)
    sky_node.altitude = 0.0; sky_node.air_density = 1.0; sky_node.dust_density = 1.0; sky_node.ozone_density = 10.0
    background_node.inputs['Strength'].default_value = 0.3
def initial_setup():
    context = bpy.context;
    if not context.scene: return None
    context.scene.render.engine = 'CYCLES'; get_world_nodes(context, create=True)
    props = context.scene.zionad_world_props; props.background_mode = 'SKY'
    apply_initial_sky_settings(context); update_viewport(context)
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_rotation = mathutils.Quaternion((1.0, 0.0, 0.0, 0.0), 0.0)
                    space.region_3d.view_perspective = 'PERSP'
    return None

classes = (
    ZIONAD_WorldProperties, ZIONAD_LinkPanelProperties,
    ZIONAD_OT_ShowWorldProperties, ZIONAD_OT_ShowTextEditor,
    ZIONAD_OT_ToggleSunDisc, ZIONAD_OT_ResetSkyProperty,
    ZIONAD_OT_LoadSkyPreset, ZIONAD_OT_LoadHdriFromList,
    ZIONAD_OT_OpenURL, ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_WorldControlPanel, ZIONAD_PT_LinksPanel, ZIONAD_PT_RemovePanel
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    Scene.zionad_world_props = PointerProperty(type=ZIONAD_WorldProperties); Scene.zionad_link_panel_props = PointerProperty(type=ZIONAD_LinkPanelProperties)
    if not bpy.app.timers.is_registered(initial_setup): bpy.app.timers.register(initial_setup, first_interval=0.1)
def unregister():
    if bpy.app.timers.is_registered(initial_setup): bpy.app.timers.unregister(initial_setup)
    if hasattr(Scene, "zionad_world_props"): del Scene.zionad_world_props
    if hasattr(Scene, "zionad_link_panel_props"): del Scene.zionad_link_panel_props
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except RuntimeError: pass 
if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()