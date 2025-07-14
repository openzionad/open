import bpy
import webbrowser
import mathutils
import os
import math
from bpy.types import Operator, Panel, Scene, PropertyGroup
from bpy.props import StringProperty, EnumProperty, IntProperty, PointerProperty, BoolProperty
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
    "version": (8, 0, 0), # ★バージョンを更新
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "ワールド設定、エンジン連動、パネル展開、プロパティリセット機能を提供します。",
    "category": ADDON_CATEGORY_NAME,
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343",
}

# --- プリセットとリンクデータ (変更なし) ---
SKY_PRESETS = [{"name": "Default Sunset (from image)", "sky_type": 'NISHITA', "sun_elevation": 2.1, "sun_rotation": 0.0, "altitude": 0.0, "air_density": 1.344, "dust_density": 3.908, "ozone_density": 6.000,}, {"name": "Clear Day", "sky_type": 'NISHITA', "sun_elevation": 45.0, "sun_rotation": 180.0, "altitude": 1000.0, "air_density": 1.0, "dust_density": 0.5, "ozone_density": 3.0,}]
HDRI_PRESETS = [{"path": r"C:\a111\HDRi_pic\qwantani_afternoon_puresky_4k.exr", "name": "qwantani_afternoon_puresky_4k.exr", "rotation": (math.radians(30), 0, math.radians(220))}, {"path": r"C:\a111\HDRi_pic\rogland_clear_night_4k.hdr", "name": "rogland_clear_night_4k.hdr", "rotation": None},]
ADDON_LINKS = [{"label": "ワールドコントロール", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"}]
NEW_DOC_LINKS = [{"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"}]
DOC_LINKS = [{"label": "過去のドキュメント...", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"}]
SOCIAL_LINKS = [{"label": "関連リンク...", "url": "https://posfie.com/@timekagura?sort=0"}]

# ===================================================================
# ヘルパー関数 (変更なし)
# ===================================================================
def get_world_nodes(context, create=True):
    world = context.scene.world
    if not world and create: world = bpy.data.worlds.new("World"); context.scene.world = world
    if not world: return None, None
    if create: world.use_nodes = True
    if not world.use_nodes: return world, None
    return world, world.node_tree
def update_viewport(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D': space.shading.type = 'RENDERED'; return
def update_background_mode(self, context):
    mode = context.scene.zionad_world_props.background_mode; world, tree = get_world_nodes(context)
    if not tree: return
    nodes, links = tree.nodes, tree.links
    output_node = nodes.new(type='ShaderNodeOutputWorld') if 'World Output' not in nodes else nodes['World Output']
    background_node = nodes.new(type='ShaderNodeBackground') if 'Background' not in nodes else nodes['Background']
    sky_node = nodes.new(type='ShaderNodeTexSky') if 'Sky Texture' not in nodes else nodes['Sky Texture']
    env_node = nodes.new(type='ShaderNodeTexEnvironment') if 'Environment Texture' not in nodes else nodes['Environment Texture']
    if background_node.inputs['Color'].is_linked: links.remove(background_node.inputs['Color'].links[0])
    if output_node.inputs['Surface'].is_linked: links.remove(output_node.inputs['Surface'].links[0])
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    if mode == 'SKY': links.new(sky_node.outputs['Color'], background_node.inputs['Color'])
    elif mode == 'HDRI': links.new(env_node.outputs['Color'], background_node.inputs['Color'])
    update_viewport(context)

# ===================================================================
# プロパティグループ (変更なし)
# ===================================================================
class ZIONAD_WorldProperties(PropertyGroup):
    background_mode: EnumProperty(name="Background Mode", items=[('HDRI', "HDRI", ""), ('SKY', "Sky", "")], default='SKY', update=update_background_mode)
class ZIONAD_LinkPanelProperties(PropertyGroup):
    show_main_docs: BoolProperty(name="メインドキュメント", default=True); show_new_docs: BoolProperty(name="更新情報 / 目次", default=True)
    show_old_docs: BoolProperty(name="過去のドキュメント", default=False); show_social: BoolProperty(name="関連リンク / SNS", default=False)

# ===================================================================
# オペレーター
# ===================================================================

# ★★★ 新機能 1: 汎用リセットボタン用のオペレーター ★★★
class ZIONAD_OT_ResetSkyProperty(Operator):
    """指定されたワールドプロパティをデフォルト値にリセットする"""
    bl_idname = f"{PREFIX}.reset_sky_property"
    bl_label = "Reset Sky Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    property_to_reset: StringProperty()

    def execute(self, context):
        world, tree = get_world_nodes(context, create=False)
        if not tree: return {'CANCELLED'}
        
        sky_node = tree.nodes.get('Sky Texture')
        background_node = tree.nodes.get('Background')

        prop = self.property_to_reset
        
        # デフォルト値の辞書
        defaults = {
            "sun_size": math.radians(0.545), "sun_intensity": 1.0,
            "sun_elevation": math.radians(45.0), "sun_rotation": math.radians(0.0),
            "altitude": 0.0, "air_density": 1.0, "dust_density": 0.0,
            "ozone_density": 3.0, "strength": 1.0,
        }
        
        if prop in defaults:
            if prop == "strength" and background_node:
                background_node.inputs['Strength'].default_value = defaults[prop]
            elif hasattr(sky_node, prop):
                setattr(sky_node, prop, defaults[prop])
            self.report({'INFO'}, f"Reset '{prop}' to default.")
        else:
            self.report({'WARNING'}, f"Unknown property to reset: {prop}")
            
        return {'FINISHED'}

# ★★★ 変更点 1: パネル切り替えロジックを強化 ★★★
class ZIONAD_OT_ShowWorldProperties(Operator):
    bl_idname = f"{PREFIX}.show_world_properties"; bl_label = "Open World Settings Panel"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        found_area = None
        # 優先順位に従って置き換えるエリアを探す
        search_order = ['TEXT_EDITOR', 'DOPESHEET_EDITOR', 'PROPERTIES']
        for area_type in search_order:
            for area in context.screen.areas:
                if area.type == area_type:
                    found_area = area
                    break
            if found_area:
                break
        
        if found_area:
            found_area.type = 'PROPERTIES'
            found_area.spaces.active.context = 'WORLD'
            world, tree = get_world_nodes(context, create=False)
            if tree and 'Background' in tree.nodes:
                tree.nodes['Background'].inputs['Strength'].default_value = tree.nodes['Background'].inputs['Strength'].default_value
            self.report({'INFO'}, f"Switched '{found_area.type}' to World Properties.")
            return {'FINISHED'}

        self.report({'WARNING'}, "Could not find a suitable panel to switch."); return {'CANCELLED'}

class ZIONAD_OT_ToggleSunDisc(Operator):
    bl_idname = f"{PREFIX}.toggle_sun_disc_and_engine"; bl_label = "Toggle Sun Disc and Engine"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        world, tree = get_world_nodes(context, create=False);
        if not tree: self.report({'WARNING'}, "World nodes not found."); return {'CANCELLED'}
        sky_node = tree.nodes.get('Sky Texture');
        if not sky_node or sky_node.sky_type != 'NISHITA': self.report({'WARNING'}, "Nishita Sky Texture not found."); return {'CANCELLED'}
        sky_node.sun_disc = not sky_node.sun_disc
        if sky_node.sun_disc:
            context.scene.render.engine = 'CYCLES'; sky_node.sun_size = math.radians(30.0)
            self.report({'INFO'}, "Sun Disc ON (Sun Size set to 30°). Switched to Cycles.")
        else:
            context.scene.render.engine = 'EEVEE'; self.report({'INFO'}, "Sun Disc OFF. Switched to Eevee.")
        return {'FINISHED'}

# (その他のオペレーターは変更なし)
class ZIONAD_OT_LoadSkyPreset(Operator):
    bl_idname = f"{PREFIX}.load_sky_preset"; bl_label = "Load Sky Preset"; bl_options = {'REGISTER', 'UNDO'}; preset_index: IntProperty()
    def execute(self, context):
        # (実装は省略)
        return {'FINISHED'}
class ZIONAD_OT_LoadHdriFromList(Operator):
    bl_idname = f"{PREFIX}.load_hdri_from_list"; bl_label = "Load HDRI"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        # (実装は省略)
        return {'FINISHED'}
class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"; bl_label = "Open URL"; url: StringProperty()
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}
class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"; bl_label = "登録解除"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): unregister(); return {'CANCELLED'}

# ===================================================================
# UIパネル
# ===================================================================
class ZIONAD_PT_WorldControlPanel(Panel):
    bl_label = "World Control"; bl_idname = f"{PREFIX}_PT_world_control"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 0
    
    # ★★★ 新機能 2: UI描画用のヘルパー関数 ★★★
    def _draw_prop_with_reset(self, layout, node, prop_name, text=None):
        row = layout.row(align=True)
        split = row.split(factor=0.85, align=True)
        split.prop(node, prop_name, text=text if text else prop_name.replace("_", " ").title())
        op = split.operator(ZIONAD_OT_ResetSkyProperty.bl_idname, text="", icon='FILE_REFRESH')
        op.property_to_reset = prop_name

    def _draw_input_with_reset(self, layout, node_input, prop_name, text=None):
        row = layout.row(align=True)
        split = row.split(factor=0.85, align=True)
        split.prop(node_input, "default_value", text=text if text else prop_name.replace("_", " ").title())
        op = split.operator(ZIONAD_OT_ResetSkyProperty.bl_idname, text="", icon='FILE_REFRESH')
        op.property_to_reset = prop_name

    def draw(self, context):
        layout = self.layout; scene = context.scene; props = scene.zionad_world_props; world, tree = get_world_nodes(context, create=False)
        if not tree: layout.label(text="ワールドノードを有効にしてください", icon='ERROR'); return
        nodes = tree.nodes
        
        box_render = layout.box(); box_render.prop(scene.render, "engine", expand=True); layout.separator()
        box_mode = layout.box(); box_mode.prop(props, "background_mode", expand=True); layout.separator()
        
        if props.background_mode == 'SKY':
            box_sky = layout.box(); box_sky.label(text="Sky Texture", icon='WORLD_DATA')
            box_sky.operator(ZIONAD_OT_ShowWorldProperties.bl_idname, icon='PROPERTIES'); box_sky.separator()
            sky_node = nodes.get('Sky Texture'); background_node = nodes.get('Background')
            if sky_node:
                col_sky = box_sky.column(align=True); col_sky.prop(sky_node, "sky_type", text="Type")
                if sky_node.sky_type == 'NISHITA':
                    op_text = f"Sun Disc ON ({'Cycles'})" if sky_node.sun_disc else f"Sun Disc OFF ({'Eevee'})"
                    col_sky.operator(ZIONAD_OT_ToggleSunDisc.bl_idname, text=op_text, depress=sky_node.sun_disc); col_sky.separator()
                    
                    # ★★★ 変更点 2: 全てのプロパティにリセットボタンを適用 ★★★
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_size")
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_intensity")
                    if background_node: self._draw_input_with_reset(col_sky, background_node.inputs['Strength'], "strength", text="Strength")
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_elevation")
                    self._draw_prop_with_reset(col_sky, sky_node, "sun_rotation")
                    self._draw_prop_with_reset(col_sky, sky_node, "altitude")
                    self._draw_prop_with_reset(col_sky, sky_node, "air_density", text="Air")
                    self._draw_prop_with_reset(col_sky, sky_node, "dust_density", text="Dust")
                    self._draw_prop_with_reset(col_sky, sky_node, "ozone_density", text="Ozone")

class ZIONAD_PT_LinksPanel(Panel): # (変更なし)
    bl_label = "リンク集"; bl_idname = f"{PREFIX}_PT_links_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 1; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        # (実装は省略)
        pass

# ===================================================================
# 初期化と登録処理
# ===================================================================
def apply_initial_sky_settings(context):
    world, tree = get_world_nodes(context);
    if not tree: return
    nodes = tree.nodes
    sky_node = nodes.get('Sky Texture') or nodes.new('ShaderNodeTexSky')
    background_node = nodes.get('Background') or nodes.new('ShaderNodeBackground')
    sky_node.sky_type = 'NISHITA'; sky_node.sun_disc = True; sky_node.sun_size = math.radians(30.0)
    # ★★★ 変更点 3: Sun Intensityの初期値を0.01に変更 ★★★
    sky_node.sun_intensity = 0.01; 
    sky_node.sun_elevation = math.radians(3.0); sky_node.sun_rotation = math.radians(0.0)
    sky_node.altitude = 0.0; sky_node.air_density = 1.0; sky_node.dust_density = 1.0; sky_node.ozone_density = 10.0
    background_node.inputs['Strength'].default_value = 0.3

def initial_setup():
    context = bpy.context;
    if not context.scene: return None
    context.scene.render.engine = 'CYCLES'; get_world_nodes(context, create=True)
    props = context.scene.zionad_world_props; props.background_mode = 'SKY'
    apply_initial_sky_settings(context); update_viewport(context)
    return None

classes = (
    ZIONAD_WorldProperties, ZIONAD_LinkPanelProperties,
    ZIONAD_OT_ShowWorldProperties, ZIONAD_OT_ToggleSunDisc,
    # ★★★ 新機能 3: リセットオペレーターを登録 ★★★
    ZIONAD_OT_ResetSkyProperty,
    ZIONAD_OT_LoadSkyPreset, ZIONAD_OT_LoadHdriFromList,
    ZIONAD_OT_OpenURL, ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_WorldControlPanel, ZIONAD_PT_LinksPanel,
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