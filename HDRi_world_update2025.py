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

# --- プレフィックスとID設定 ---
_PREFIX_STATIC_PART = "world" 
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"

# --- アドオン情報 ---
ADDON_CATEGORY_NAME = "[aaa   world  20250714 ]"

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (World & Links)",
    "author": "zionadchat & Your Name",
    "version": (5, 9, 1), # ★バージョンを更新
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "ワールド設定(HDRI/Sky)、折りたたみ可能な便利リンク、アドオン解除機能を提供します。",
    "category": ADDON_CATEGORY_NAME,
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343",
}

# ★★★ MODIFICATION: Skyプリセットのリスト（元のプロパティ名を使用） ★★★
SKY_PRESETS = [
    {
        "name": "Default Sunset (from image)",
        "sky_type": 'NISHITA',
        "sun_elevation": 2.1,
        "sun_rotation": 0.0,
        "altitude": 0.0,
        "air_density": 1.344,
        "dust_density": 3.908,
        "ozone_density": 6.000,
    },
    {
        "name": "Clear Day",
        "sky_type": 'NISHITA',
        "sun_elevation": 45.0,
        "sun_rotation": 180.0,
        "altitude": 1000.0,
        "air_density": 1.0,
        "dust_density": 0.5,
        "ozone_density": 3.0,
    }
]

# --- HDRIプリセットのリスト（パスとデフォルト回転） ---
HDRI_PRESETS = [
    {
        "path": r"C:\a111\HDRi_pic\qwantani_afternoon_puresky_4k.exr",
        "name": "qwantani_afternoon_puresky_4k.exr",
        "rotation": (math.radians(30), 0, math.radians(220))
    },
    {
        "path": r"C:\a111\HDRi_pic\rogland_clear_night_4k.hdr",
        "name": "rogland_clear_night_4k.hdr",
        "rotation": None
    },
    {
        "path": r"C:\a111\HDRi_pic\golden_bay_4k.hdr",
        "name": "golden_bay_4k.hdr",
        "rotation": None
    },
]

# --- リンクパネル用データ ---
ADDON_LINKS = [
    {"label": "ワールドコントロール", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"}
]
NEW_DOC_LINKS = [
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
# ヘルパー関数 (World Tools用)
# ===================================================================
def find_node(nodes, node_type, name):
    if node_type == 'OUTPUT_WORLD':
        return next((n for n in nodes if n.type == 'OUTPUT_WORLD'), None)
    return nodes.get(name)

def find_or_create_node(nodes, node_type, name, location_offset=(0, 0)):
    node = find_node(nodes, node_type, name)
    if node:
        return node
        
    new_node = nodes.new(type=node_type)
    new_node.name = name
    new_node.label = name.replace("_", " ")

    if node_type == 'ShaderNodeTexSky' and SKY_PRESETS:
        preset = SKY_PRESETS[0]
        new_node.sky_type = preset.get("sky_type", 'NISHITA')
        
        if new_node.sky_type == 'NISHITA':
            if hasattr(new_node, 'sun_elevation'):
                new_node.sun_elevation = math.radians(preset.get("sun_elevation", 45.0))
            if hasattr(new_node, 'sun_rotation'):
                new_node.sun_rotation = math.radians(preset.get("sun_rotation", 0.0))
            if hasattr(new_node, 'altitude'):
                new_node.altitude = preset.get("altitude", 0.0)
            # ★★★ MODIFICATION: 元のプロパティ名を使用 ★★★
            if hasattr(new_node, 'air_density'):
                new_node.air_density = preset.get("air_density", 1.0)
            if hasattr(new_node, 'dust_density'):
                new_node.dust_density = preset.get("dust_density", 0.5)
            if hasattr(new_node, 'ozone_density'):
                new_node.ozone_density = preset.get("ozone_density", 3.0)

    output_node = find_node(nodes, 'OUTPUT_WORLD', '')
    if output_node:
        new_node.location = output_node.location + mathutils.Vector(location_offset)
    return new_node

def get_world_nodes(context, create=True):
    world = context.scene.world
    if not world and create:
        world = bpy.data.worlds.new("World")
        context.scene.world = world
    if not world:
        return None, None, None
    if create:
        world.use_nodes = True
    if not world.use_nodes:
        return world, None, None
    return world, world.node_tree.nodes, world.node_tree.links

def load_hdri_from_path(filepath, context):
    _, nodes, _ = get_world_nodes(context)
    if not nodes:
        return False
    env_node = find_or_create_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture')
    if os.path.exists(filepath):
        try:
            env_node.image = bpy.data.images.load(filepath, check_existing=True)
            return True
        except RuntimeError as e:
            print(f"Error loading image: {e}")
            return False
    print(f"File not found: {filepath}")
    return False

def update_viewport(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    return

# --- プロパティ更新関数 ---
def update_background_mode(self, context):
    mode = context.scene.zionad_world_props.background_mode
    world, nodes, links = get_world_nodes(context)
    if not nodes:
        return

    output_node = find_or_create_node(nodes, 'OUTPUT_WORLD', 'World_Output')
    background_node = find_or_create_node(nodes, 'ShaderNodeBackground', 'Background', (-250, 0))
    sky_node = find_or_create_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture', (-550, 0))
    env_node = find_or_create_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture', (-550, 0))
    mapping_node = find_or_create_node(nodes, 'ShaderNodeMapping', 'Mapping', (-800, 0))
    tex_coord_node = find_or_create_node(nodes, 'ShaderNodeTexCoord', 'Texture_Coordinate', (-1050, 0))

    if background_node.inputs['Color'].is_linked:
        links.remove(background_node.inputs['Color'].links[0])
    if output_node.inputs['Surface'].is_linked:
        links.remove(output_node.inputs['Surface'].links[0])

    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

    if mode == 'SKY':
        links.new(sky_node.outputs['Color'], background_node.inputs['Color'])
    elif mode == 'HDRI':
        if not mapping_node.inputs['Vector'].is_linked:
            links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
        if not env_node.inputs['Vector'].is_linked:
            links.new(mapping_node.outputs['Vector'], env_node.inputs['Vector'])
        links.new(env_node.outputs['Color'], background_node.inputs['Color'])
        props = context.scene.zionad_world_props
        if 0 <= props.hdri_list_index < len(HDRI_PRESETS):
            hdri_path = HDRI_PRESETS[props.hdri_list_index]["path"]
            load_hdri_from_path(hdri_path, context)

    update_viewport(context)
    
# ===================================================================
# プロパティグループ
# ===================================================================
class ZIONAD_WorldProperties(PropertyGroup):
    background_mode: EnumProperty(
        name="Background Mode",
        items=[('HDRI', "HDRI", ""), ('SKY', "Sky", "")],
        default='HDRI',
        update=update_background_mode
    )
    hdri_list_index: IntProperty(
        name="Active HDRI Index",
        default=0,
        update=update_background_mode
    )

class ZIONAD_LinkPanelProperties(PropertyGroup):
    show_main_docs: BoolProperty(name="メインドキュメント", default=True)
    show_new_docs: BoolProperty(name="更新情報 / 目次", default=True)
    show_old_docs: BoolProperty(name="過去のドキュメント", default=False)
    show_social: BoolProperty(name="関連リンク / SNS", default=False)

# ===================================================================
# オペレーター (ボタンが押されたときの処理)
# ===================================================================

class ZIONAD_OT_LoadSkyPreset(Operator):
    bl_idname = f"{PREFIX}.load_sky_preset"
    bl_label = "Load Sky Preset"
    bl_options = {'REGISTER', 'UNDO'}
    preset_index: IntProperty()

    def execute(self, context):
        if not (0 <= self.preset_index < len(SKY_PRESETS)):
            self.report({'ERROR'}, "Invalid Sky preset index")
            return {'CANCELLED'}

        preset = SKY_PRESETS[self.preset_index]
        context.scene.zionad_world_props.background_mode = 'SKY'
        _, nodes, _ = get_world_nodes(context)
        if not nodes:
            return {'CANCELLED'}
        sky_node = find_or_create_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture')

        sky_node.sky_type = preset["sky_type"]
        if sky_node.sky_type == 'NISHITA':
            if hasattr(sky_node, 'sun_elevation'):
                sky_node.sun_elevation = math.radians(preset.get("sun_elevation", 45.0))
            if hasattr(sky_node, 'sun_rotation'):
                sky_node.sun_rotation = math.radians(preset.get("sun_rotation", 0.0))
            if hasattr(sky_node, 'altitude'):
                sky_node.altitude = preset.get("altitude", 0.0)
            # ★★★ MODIFICATION: 元のプロパティ名を使用 ★★★
            if hasattr(sky_node, 'air_density'):
                sky_node.air_density = preset.get("air_density", 1.0)
            if hasattr(sky_node, 'dust_density'):
                sky_node.dust_density = preset.get("dust_density", 0.5)
            if hasattr(sky_node, 'ozone_density'):
                sky_node.ozone_density = preset.get("ozone_density", 3.0)
        
        self.report({'INFO'}, f"Loaded Sky Preset: {preset['name']}")
        return {'FINISHED'}

class ZIONAD_OT_LoadHdriFromList(Operator):
    bl_idname = f"{PREFIX}.load_hdri_from_list"
    bl_label = "Load HDRI from List"
    bl_options = {'REGISTER', 'UNDO'}
    hdri_index: IntProperty()

    def execute(self, context):
        props = context.scene.zionad_world_props
        if 0 <= self.hdri_index < len(HDRI_PRESETS):
            preset = HDRI_PRESETS[self.hdri_index]
            props.background_mode = 'HDRI'
            props.hdri_list_index = self.hdri_index
            
            _, nodes, _ = get_world_nodes(context)
            if nodes:
                mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
                if mapping_node:
                    mapping_node.inputs['Location'].default_value = (0, 0, 0)
                    mapping_node.inputs['Scale'].default_value = (1, 1, 1)
                    if preset.get("rotation"):
                        mapping_node.inputs['Rotation'].default_value = preset["rotation"]
                    else:
                        mapping_node.inputs['Rotation'].default_value = (0, 0, 0)
            self.report({'INFO'}, f"Loaded: {preset['name']}")
        else:
            self.report({'ERROR'}, "Invalid HDRI index")
        return {'FINISHED'}

class ZIONAD_OT_ResetTransform(Operator):
    bl_idname = f"{PREFIX}.reset_transform"
    bl_label = "Reset Transform Value"
    bl_options = {'REGISTER', 'UNDO'}
    property_to_reset: StringProperty()

    def execute(self, context):
        _, nodes, _ = get_world_nodes(context)
        if not nodes: return {'CANCELLED'}
        mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
        if not mapping_node: return {'CANCELLED'}
        
        if self.property_to_reset == 'Location':
            mapping_node.inputs['Location'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Rotation':
            mapping_node.inputs['Rotation'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Scale':
            mapping_node.inputs['Scale'].default_value = (1, 1, 1)
        return {'FINISHED'}

class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"
    bl_label = "Open URL"
    bl_description = "Opens the specified URL in a web browser"
    url: StringProperty(name="URL", description="The URL to open", default="")

    def execute(self, context):
        if not self.url:
            self.report({'WARNING'}, "URLが設定されていません。")
            return {'CANCELLED'}
        try:
            webbrowser.open(self.url)
            self.report({'INFO'}, f"開きました: {self.url}")
        except Exception as e:
            self.report({'ERROR'}, f"URLを開けませんでした: {e}")
        return {'FINISHED'}

class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"
    bl_label = "アドオンのコンポーネントを登録解除"
    bl_description = "このアドオンの全コンポーネントを登録解除します。"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            unregister()
            self.report({'INFO'}, "アドオンのコンポーネントを登録解除しました。")
        except Exception as e:
            self.report({'ERROR'}, f"アドオンの削除中にエラーが発生しました: {e}")
        return {'CANCELLED'}
        return {'FINISHED'}

# ===================================================================
# UIパネル (サイドバーに表示されるUI)
# ===================================================================

class ZIONAD_PT_WorldControlPanel(Panel):
    bl_label = "World Control"
    bl_idname = f"{PREFIX}_PT_world_control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.zionad_world_props
        world, nodes, _ = get_world_nodes(context, create=False)

        if not world or not world.use_nodes or not nodes:
            col = layout.column(align=True)
            if not world:
                col.label(text="No World in Scene", icon='ERROR')
                col.operator("world.new", text="Create New World")
            else:
                col.label(text="Enable Nodes in World")
                col.prop(world, "use_nodes", text="Use Nodes")
            return

        box_render = layout.box()
        box_render.label(text="Render Engine", icon='SCENE_DATA')
        box_render.prop(scene.render, "engine", expand=True)
        layout.separator()

        box_mode = layout.box()
        box_mode.label(text="Background Mode", icon='WORLD')
        box_mode.prop(props, "background_mode", expand=True)
        layout.separator()

        if props.background_mode == 'HDRI':
            box_env = layout.box()
            box_env.label(text="Environment Texture (HDRI)", icon='IMAGE_DATA')
            col_list = box_env.column(align=True)
            col_list.label(text="HDRI Presets:")
            for i, preset in enumerate(HDRI_PRESETS):
                op = col_list.operator(ZIONAD_OT_LoadHdriFromList.bl_idname, text=preset["name"], depress=(props.hdri_list_index == i))
                op.hdri_index = i

            box_env.separator()
            env_node = find_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture')
            if env_node:
                box_env.template_ID(env_node, "image", open="image.open", text="Select HDRI")
                mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
                if mapping_node:
                    box_transform = box_env.box()
                    box_transform.label(text="Transform", icon='OBJECT_DATA')
                    col = box_transform.column(align=True)
                    for prop_name in ['Location', 'Rotation', 'Scale']:
                        row = col.row(align=True)
                        split = row.split(factor=0.8, align=True)
                        split.prop(mapping_node.inputs[prop_name], "default_value", text=prop_name)
                        op = split.operator(ZIONAD_OT_ResetTransform.bl_idname, text="", icon='FILE_REFRESH')
                        op.property_to_reset = prop_name

        elif props.background_mode == 'SKY':
            box_sky = layout.box()
            box_sky.label(text="Sky Texture", icon='WORLD_DATA')
            
            col_presets = box_sky.column(align=True)
            col_presets.label(text="Sky Presets:")
            for i, preset in enumerate(SKY_PRESETS):
                op = col_presets.operator(ZIONAD_OT_LoadSkyPreset.bl_idname, text=preset["name"])
                op.preset_index = i
            box_sky.separator()

            sky_node = find_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture')
            if sky_node:
                col_sky = box_sky.column(align=True)
                col_sky.prop(sky_node, "sky_type", text="Sky Type")
                if sky_node.sky_type == 'NISHITA':
                    # ★★★ MODIFICATION: 元のプロパティ名でUIを表示 ★★★
                    if hasattr(sky_node, 'sun_elevation'): col_sky.prop(sky_node, "sun_elevation")
                    if hasattr(sky_node, 'sun_rotation'): col_sky.prop(sky_node, "sun_rotation")
                    if hasattr(sky_node, 'altitude'): col_sky.prop(sky_node, "altitude")
                    if hasattr(sky_node, 'air_density'): col_sky.prop(sky_node, "air_density")
                    if hasattr(sky_node, 'dust_density'): col_sky.prop(sky_node, "dust_density")
                    if hasattr(sky_node, 'ozone_density'): col_sky.prop(sky_node, "ozone_density")
                elif sky_node.sky_type in {'PREETHAM', 'HOSEK_WILKIE'}:
                    if hasattr(sky_node, 'turbidity'): col_sky.prop(sky_node, "turbidity")
                    if hasattr(sky_node, 'ground_albedo'): col_sky.prop(sky_node, "ground_albedo")

class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集 (Links)"
    bl_idname = f"{PREFIX}_PT_links_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        link_props = context.scene.zionad_link_panel_props

        def draw_collapsible_section(prop_name, link_list):
            box = layout.box()
            is_expanded = getattr(link_props, prop_name)
            row = box.row()
            row.prop(link_props, prop_name, icon="TRIA_DOWN" if is_expanded else "TRIA_RIGHT", emboss=False)
            if is_expanded:
                col = box.column(align=True)
                for link in link_list:
                    op = col.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL')
                    op.url = link["url"]

        draw_collapsible_section("show_main_docs", ADDON_LINKS)
        draw_collapsible_section("show_new_docs", NEW_DOC_LINKS)
        draw_collapsible_section("show_old_docs", DOC_LINKS)
        draw_collapsible_section("show_social", SOCIAL_LINKS)

class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"
    bl_idname = f"{PREFIX}_PT_remove_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="登録解除", icon='CANCEL')
  
# ===================================================================
# タイマーを使った初期化 (World Tools用)
# ===================================================================
def initial_setup():
    context = bpy.context
    if not context.scene: return None
    props = context.scene.zionad_world_props
    
    if not context.scene.world:
        context.scene.world = bpy.data.worlds.new("World")
    if not context.scene.world.use_nodes:
        context.scene.world.use_nodes = True
        
    nodes = context.scene.world.node_tree.nodes
    background_node = find_node(nodes, 'ShaderNodeBackground', 'Background')

    if background_node and background_node.inputs['Color'].is_linked:
        source_node = background_node.inputs['Color'].links[0].from_node
        if source_node.type == 'TEX_SKY':
            props.background_mode = 'SKY'
        else:
            props.background_mode = 'HDRI'
    else:
        props.background_mode = 'HDRI'
        props.hdri_list_index = 0
        update_background_mode(props, context)
        
        if len(HDRI_PRESETS) > 0:
            preset = HDRI_PRESETS[0]
            _, nodes, _ = get_world_nodes(context)
            if nodes:
                mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
                if mapping_node:
                    mapping_node.inputs['Location'].default_value = (0, 0, 0)
                    mapping_node.inputs['Scale'].default_value = (1, 1, 1)
                    if preset.get("rotation"):
                        mapping_node.inputs['Rotation'].default_value = preset["rotation"]
                    else:
                        mapping_node.inputs['Rotation'].default_value = (0, 0, 0)

    update_background_mode(props, context)
    return None

# ===================================================================
# 登録・解除処理
# ===================================================================
classes = (
    # World Tools
    ZIONAD_WorldProperties,
    ZIONAD_OT_LoadSkyPreset,
    ZIONAD_OT_LoadHdriFromList,
    ZIONAD_OT_ResetTransform,
    ZIONAD_PT_WorldControlPanel,
    # Links & Remover
    ZIONAD_LinkPanelProperties,
    ZIONAD_OT_OpenURL,
    ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_LinksPanel,
    ZIONAD_PT_RemovePanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    Scene.zionad_world_props = PointerProperty(type=ZIONAD_WorldProperties)
    Scene.zionad_link_panel_props = PointerProperty(type=ZIONAD_LinkPanelProperties)

    if not bpy.app.timers.is_registered(initial_setup):
        bpy.app.timers.register(initial_setup, first_interval=0.1)

def unregister():
    if bpy.app.timers.is_registered(initial_setup):
        bpy.app.timers.unregister(initial_setup)
        
    if hasattr(Scene, "zionad_world_props"):
        del Scene.zionad_world_props
    if hasattr(Scene, "zionad_link_panel_props"):
        del Scene.zionad_link_panel_props
        
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass 

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()