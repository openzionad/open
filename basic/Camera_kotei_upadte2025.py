import bpy
import math
import mathutils
import webbrowser
import os
from bpy.types import Operator, Panel, Scene, PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty, FloatVectorProperty, FloatProperty, CollectionProperty, BoolProperty, IntProperty
from datetime import datetime

# --- ユニークID生成 ---
START_TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
PREFIX = f"cam_kotei{START_TIMESTAMP}"

# --- bl_info ---
bl_info = {
    "name": "zionad v100 [Fixed Camera & World]",
    "author": "zionadchat",
    "version": (35, 0, 5), # バージョンアップ
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > zionad Control",
    "description": "カメラの位置固定、向き(YPR)、レンズ制御に加え、ワールド(HDRI/背景)設定機能を提供します。",
    "category": "   v100[ 固定　Camera ]   ",
}

# ======================================================================
# --- ユーザー設定 / Parameters to Customize ---
# ======================================================================

ADDON_CATEGORY_NAME = bl_info["category"]

# --- HDRI画像ファイルのフルパスリスト ---
# ▼▼▼【変更点】ご指定のHDRIパスをリストの2番目に追加しました ▼▼▼
HDRI_PATHS = [
    r"C:\a111\HDRi_pic\qwantani_afternoon_puresky_4k.exr",
    r"C:\a111\HDRi_pic\rogland_moonlit_night_4k.hdr",
    r"C:\a111\HDRi_pic\rogland_clear_night_4k.hdr",
    r"C:\a111\HDRi_pic\golden_bay_4k.hdr",
]

# --- ワイヤーフレームの色プリセット ---
# 形式: ("ID", "ラベル", "説明", (R, G, B))
WIRE_PRESETS = [
    ("CUSTOM_GREENISH", "Custom Greenish", "Custom greenish wire color", (0.51, 1.0, 0.75)),
    ("WHITE", "White", "White wire", (1.0, 1.0, 1.0)),
    ("RED", "Red", "Red wire", (1.0, 0.0, 0.0)),
    ("GREEN", "Green", "Green wire", (0.0, 1.0, 0.0)),
]

# --- グリッドの色プリセット ---
# 形式: ("ID", "ラベル", "説明", (R, G, B, A))
GRID_PRESETS = [
    ("CUSTOM_REDDISH", "Custom Reddish", "Custom reddish color", (0.545, 0.322, 0.322, 1.0)),
    ("DEEP_GREEN", "Deep Green", "A deep green color", (0.098, 0.314, 0.271, 1.0)),
    ("MINT_GREEN", "Mint Green", "A mint green color", (0.165, 0.557, 0.475, 1.0)),
]

# --- 専用カメラのコレクション名とオブジェクト名 ---
CAMERA_COLLECTION_NAME = "Cam"
DEDICATED_CAMERA_NAME = "Fixed_Cam"

# ======================================================================
# --- 定数定義 / Constants ---
# ======================================================================

SENSOR_WIDTH = 36.0
FOV_PRESETS = [1, 5, 10, 30, 45, 60, 90, 120, 135, 150, 179]
CAMERA_COLOR_PRESETS = [("CYAN", "Cyan", "水色", (0.0, 1.0, 1.0)), ("Cam 4.4.0", "Cam 4.4.0", "Blenderデフォルト色", (0.0, 0.0, 0.0)), ("YELLOW", "Yellow", "黄色", (1.0, 1.0, 0.0)), ("PURPLE", "Purple", "紫色", (0.5, 0.0, 0.5)),]

# --- リンクパネル用データ ---
ADDON_LINKS = ({"label": "カメラ 固定 Git 管理 20250711", "url":"https://memo2017.hatenablog.com/entry/2025/07/11/131157"},)

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

# --- パネルIDと順序 ---
PANEL_IDS = {
    "SETUP": f"{PREFIX}_PT_setup", "POSITION": f"{PREFIX}_PT_position", "AIMING": f"{PREFIX}_PT_aiming",
    "LENS": f"{PREFIX}_PT_lens", "CAMERA_DISPLAY": f"{PREFIX}_PT_camera_display", "WORLD_CONTROL": f"{PREFIX}_PT_world_control",
    "INFO": f"{PREFIX}_PT_info", "GRID": f"{PREFIX}_PT_grid_panel", "WIRE": f"{PREFIX}_PT_wire_panel",
    "LINKS": f"{PREFIX}_PT_links",
    "LINKS_NEWDOC": f"{PREFIX}_PT_links_newdoc", "LINKS_DOC": f"{PREFIX}_PT_links_doc", "LINKS_SOCIAL": f"{PREFIX}_PT_links_social",
    "REMOVE": f"{PREFIX}_PT_remove",
}
PANEL_ORDER = {PANEL_IDS["SETUP"]: 0, PANEL_IDS["POSITION"]: 1, PANEL_IDS["AIMING"]: 2, PANEL_IDS["LENS"]: 3, PANEL_IDS["CAMERA_DISPLAY"]: 4, PANEL_IDS["WORLD_CONTROL"]: 5, PANEL_IDS["INFO"]: 6, PANEL_IDS["GRID"]: 89, PANEL_IDS["WIRE"]: 90, PANEL_IDS["LINKS"]: 100, PANEL_IDS["REMOVE"]: 200,}

# --- グローバル状態管理 ---
_is_updating_by_addon = False; _update_timer = None
def reset_update_flag(): global _is_updating_by_addon, _update_timer; _is_updating_by_addon = False; _update_timer = None; return None
def schedule_update_flag_reset():
    global _update_timer
    if _update_timer and bpy.app.timers.is_registered(reset_update_flag): bpy.app.timers.unregister(reset_update_flag)
    bpy.app.timers.register(reset_update_flag, first_interval=0.01)

# --- World Tools ヘルパー関数 ---
def find_node(nodes, node_type, name):
    if node_type == 'OUTPUT_WORLD': return next((n for n in nodes if n.type == 'OUTPUT_WORLD'), None)
    return nodes.get(name)
def find_or_create_node(nodes, node_type, name, location_offset=(0, 0)):
    node = find_node(nodes, node_type, name)
    if node: return node
    new_node = nodes.new(type=node_type); new_node.name = name; new_node.label = name.replace("_", " ")
    output_node = find_node(nodes, 'OUTPUT_WORLD', '');
    if output_node: new_node.location = output_node.location + mathutils.Vector(location_offset)
    return new_node
def get_world_nodes(context, create=True):
    world = context.scene.world
    if not world and create: world = bpy.data.worlds.new("World"); context.scene.world = world
    if not world: return None, None, None
    if create: world.use_nodes = True
    if not world.use_nodes: return world, None, None
    return world, world.node_tree.nodes, world.node_tree.links
def load_hdri_from_path(filepath, context):
    _, nodes, _ = get_world_nodes(context)
    if not nodes: return False
    env_node = find_or_create_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture')
    if os.path.exists(filepath):
        try: env_node.image = bpy.data.images.load(filepath, check_existing=True); return True
        except RuntimeError as e: print(f"Error loading image: {e}"); return False
    print(f"File not found: {filepath}"); return False
def update_viewport(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D': space.shading.type = 'RENDERED'; return
def update_background_mode(self, context):
    mode = context.scene.zionad_swt_props.background_mode; world, nodes, links = get_world_nodes(context)
    if not nodes: return
    output_node = find_or_create_node(nodes, 'OUTPUT_WORLD', 'World_Output')
    background_node = find_or_create_node(nodes, 'ShaderNodeBackground', 'Background', (-250, 0))
    sky_node = find_or_create_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture', (-550, 0))
    env_node = find_or_create_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture', (-550, 0))
    mapping_node = find_or_create_node(nodes, 'ShaderNodeMapping', 'Mapping', (-800, 0))
    tex_coord_node = find_or_create_node(nodes, 'ShaderNodeTexCoord', 'Texture_Coordinate', (-1050, 0))
    if background_node.inputs['Color'].is_linked: links.remove(background_node.inputs['Color'].links[0])
    if output_node.inputs['Surface'].is_linked: links.remove(output_node.inputs['Surface'].links[0])
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    if mode == 'SKY': links.new(sky_node.outputs['Color'], background_node.inputs['Color'])
    elif mode == 'HDRI':
        if not mapping_node.inputs['Vector'].is_linked: links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
        if not env_node.inputs['Vector'].is_linked: links.new(mapping_node.outputs['Vector'], env_node.inputs['Vector'])
        links.new(env_node.outputs['Color'], background_node.inputs['Color'])
        props = context.scene.zionad_swt_props
        if 0 <= props.hdri_list_index < len(HDRI_PATHS): load_hdri_from_path(HDRI_PATHS[props.hdri_list_index], context)
    update_viewport(context)

# --- プロパティグループ ---
class ThemeGridProperties(PropertyGroup):
    grid_color: FloatVectorProperty(name="Grid Color", subtype='COLOR', size=4, min=0.0, max=1.0, default=(0.545, 0.322, 0.322, 1.0))
    grid_preset: EnumProperty(name="Grid Preset", items=[(p[0], p[1], p[2]) for p in GRID_PRESETS], update=lambda self, context: SFC_OT_GridApplyColor.update_preset(self, context))
class ThemeWireProperties(PropertyGroup):
    wire_color: FloatVectorProperty(name="Wire Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.51, 1.0, 0.75))
    wire_preset: EnumProperty(name="Wire Preset", items=[(p[0], p[1], p[2]) for p in WIRE_PRESETS], update=lambda self, context: SFC_OT_WireApplyColor.update_preset(self, context))
class TargetProperty(PropertyGroup): name: StringProperty()
class SurfaceCameraProperties(PropertyGroup):
    camera_obj: PointerProperty(name="操作カメラ", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'CAMERA', update=lambda s,c: update_surface_camera(s,c))
    fixed_location: FloatVectorProperty(name="固定位置", default=(0.0, -10.0, 0.0), subtype='XYZ', update=lambda s,c: update_surface_camera(s,c))
    target_location: FloatVectorProperty(name="固定注視点", default=(0, 0, 0), subtype='XYZ', update=lambda s,c: update_surface_camera(s,c))
    offset_yaw: FloatProperty(name="Yaw", subtype='ANGLE', default=0, update=lambda s,c: update_surface_camera(s,c)); offset_pitch: FloatProperty(name="Pitch", subtype='ANGLE', default=0, update=lambda s,c: update_surface_camera(s,c)); offset_roll: FloatProperty(name="Roll", subtype='ANGLE', default=0, update=lambda s,c: update_surface_camera(s,c))
    is_updating_settings: BoolProperty(default=False, options={'HIDDEN'})
    lens_focal_length: FloatProperty(name="焦点距離 (mm)", default=50.0, min=1.0, max=1000.0, unit='LENGTH', update=lambda s,c: update_surface_camera(s,c))
    clip_start: FloatProperty(name="クリップ開始", default=0.1, min=0.001, update=lambda s,c: update_surface_camera(s,c)); clip_end: FloatProperty(name="クリップ終了", default=1000.0, min=1.0, update=lambda s,c: update_surface_camera(s,c))
    info_precision: EnumProperty(name="桁数", items=[('1', '1', ''), ('2', '2', ''), ('3', '3', '')], default='1', update=lambda s,c: update_info_panel_text(s,c))
    info_focal_length: StringProperty(name="焦点距離"); info_horizontal_fov: StringProperty(name="水平視野角"); info_camera_location: StringProperty(name="カメラ位置"); info_target_location: StringProperty(name="注視点位置"); info_distance_to_target: StringProperty(name="注視点までの距離"); info_clip_setting: StringProperty(name="クリップ範囲"); info_viewable_width: StringProperty(name="注視点での横幅")
    camera_color: FloatVectorProperty(name="カメラカラー", subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.0, 1.0, 1.0))
    camera_preset: EnumProperty(name="カメラプリセット", items=[(p[0], p[1], p[2]) for p in CAMERA_COLOR_PRESETS], default="CYAN", update=lambda self, context: SFC_OT_ApplyCameraColor.update_preset(self, context))
class ZIONAD_SWT_Properties(PropertyGroup):
    background_mode: EnumProperty(name="Background Mode", items=[('HDRI', "HDRI", ""), ('SKY', "Sky", "")], default='HDRI', update=update_background_mode)
    hdri_list_index: IntProperty(name="Active HDRI Index", default=0, update=update_background_mode)

# --- カメラ コアロジック ---
def calculate_horizontal_fov(focal_length, sensor_width=SENSOR_WIDTH):
    try: return 2 * math.atan(sensor_width / (2 * focal_length)) * (180 / math.pi)
    except (ZeroDivisionError, ValueError): return 0.0
def calculate_focal_length(fov_degrees, sensor_width=SENSOR_WIDTH):
    try: return sensor_width / (2 * math.tan(math.radians(fov_degrees) / 2))
    except (ZeroDivisionError, ValueError): return 50.0
def get_target_location(props):
    return mathutils.Vector(props.target_location)
def update_object_transform(obj, props):
    location = mathutils.Vector(props.fixed_location)
    target_location = get_target_location(props); direction = target_location - location
    if direction.length < 0.0001: direction = mathutils.Vector((0, -1, 0))
    base_track_quat = direction.to_track_quat('-Z', 'Y')
    offset_euler = mathutils.Euler((props.offset_pitch, props.offset_yaw, props.offset_roll), 'XYZ')
    final_quat = base_track_quat @ offset_euler.to_quaternion()
    obj.location = location; obj.rotation_euler = final_quat.to_euler('XYZ')
def update_surface_camera(self, context):
    global _is_updating_by_addon
    if _is_updating_by_addon: return
    _is_updating_by_addon = True
    try:
        props, camera_obj = context.scene.surface_camera_properties, context.scene.surface_camera_properties.camera_obj
        if props.is_updating_settings or not camera_obj: update_info_panel_text(props, context); return
        cam_data = camera_obj.data
        if cam_data: cam_data.sensor_fit, cam_data.lens_unit, cam_data.lens, cam_data.clip_start, cam_data.clip_end = 'HORIZONTAL', 'MILLIMETERS', props.lens_focal_length, props.clip_start, props.clip_end
        update_object_transform(camera_obj, props); update_info_panel_text(props, context)
    finally: schedule_update_flag_reset()
def update_info_panel_text(props, context):
    if not hasattr(context, 'scene') or not props: return
    precision, fmt = int(props.info_precision), f".{props.info_precision}f"
    camera_location, target_location = mathutils.Vector(props.fixed_location), get_target_location(props)
    props.info_camera_location = f"({camera_location.x:{fmt}}, {camera_location.y:{fmt}}, {camera_location.z:{fmt}})"; current_fov = calculate_horizontal_fov(props.lens_focal_length); props.info_horizontal_fov = f"{current_fov:{fmt}} °"; props.info_focal_length = f"{props.lens_focal_length:{fmt}} mm"
    props.info_target_location = f"({target_location.x:{fmt}}, {target_location.y:{fmt}}, {target_location.z:{fmt}})"; distance = (target_location - camera_location).length; props.info_distance_to_target = f"{distance:{fmt}}"
    if distance > 0 and current_fov > 0: props.info_viewable_width = f"{2 * distance * math.tan(math.radians(current_fov) / 2):{fmt}}"
    else: props.info_viewable_width = "N/A"
    props.info_clip_setting = f"{props.clip_start:{fmt}} - {props.clip_end:{fmt}}"
def sync_ui_from_manual_transform(props, obj, context):
    global _is_updating_by_addon
    if _is_updating_by_addon: return
    _is_updating_by_addon = True
    try:
        props.fixed_location = obj.location
        target_location = get_target_location(props); direction = target_location - obj.location
        if direction.length < 0.0001: direction = mathutils.Vector((0, -1, 0))
        base_track_quat, final_quat = direction.to_track_quat('-Z', 'Y'), obj.matrix_world.to_quaternion()
        offset_quat, offset_euler = base_track_quat.inverted() @ final_quat, offset_quat.to_euler('XYZ')
        props.offset_pitch, props.offset_yaw, props.offset_roll = offset_euler.x, offset_euler.y, offset_euler.z
    finally: _is_updating_by_addon = False
    update_info_panel_text(props, context)
@bpy.app.handlers.persistent
def on_depsgraph_update(scene, depsgraph):
    if _is_updating_by_addon: return
    context = bpy.context
    if not (hasattr(context, 'scene') and context.scene): return
    sfc_props = context.scene.surface_camera_properties
    for update in depsgraph.updates:
        if not update.is_updated_transform: continue
        obj_id = update.id.original
        if sfc_props.camera_obj and obj_id == sfc_props.camera_obj: sync_ui_from_manual_transform(sfc_props, sfc_props.camera_obj, context); return

# --- オペレーター ---
class SFC_OT_ApplyCameraColor(Operator):
    bl_idname = f"{PREFIX}.apply_camera_color"; bl_label = "カメラカラー適用"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): context.preferences.themes[0].view_3d.camera = context.scene.surface_camera_properties.camera_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context): props = context.scene.surface_camera_properties; props.camera_color = next((p[3] for p in CAMERA_COLOR_PRESETS if p[0] == props.camera_preset), props.camera_color); getattr(bpy.ops, f"{PREFIX}.apply_camera_color")()
class SFC_OT_GridApplyColor(Operator):
    bl_idname = f"{PREFIX}.apply_grid_color"; bl_label = "Apply Grid Color"
    def execute(self, context): props = context.scene.theme_grid_properties; theme = bpy.context.preferences.themes[0]; theme.view_3d.grid = props.grid_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context):
        props = context.scene.theme_grid_properties
        props.grid_color = next((p[3] for p in GRID_PRESETS if p[0] == props.grid_preset), props.grid_color)
        getattr(bpy.ops, f"{PREFIX}.apply_grid_color")()
class SFC_OT_GridCopyColor(Operator):
    bl_idname = f"{PREFIX}.copy_grid_color"; bl_label = "Copy Grid Color"
    def execute(self, context): theme = bpy.context.preferences.themes[0]; color_tuple = tuple(round(c, 3) for c in theme.view_3d.grid); context.window_manager.clipboard = f'("CUSTOM", "Custom", "Custom grid color", {color_tuple}),'; self.report({'INFO'}, f"グリッドの色をコピーしました: {context.window_manager.clipboard}"); return {'FINISHED'}
class SFC_OT_CreateDedicatedCamera(Operator):
    bl_idname = f"{PREFIX}.create_dedicated_camera"; bl_label = "専用カメラ作成"
    def execute(self, context):
        if DEDICATED_CAMERA_NAME not in bpy.data.objects:
            cam_data = bpy.data.cameras.new(name=DEDICATED_CAMERA_NAME); cam_obj = bpy.data.objects.new(DEDICATED_CAMERA_NAME, cam_data)
            cam_collection = bpy.data.collections.get(CAMERA_COLLECTION_NAME) or bpy.data.collections.new(CAMERA_COLLECTION_NAME)
            if CAMERA_COLLECTION_NAME not in context.scene.collection.children: context.scene.collection.children.link(cam_collection)
            cam_collection.objects.link(cam_obj)
            if cam_obj.name in context.scene.collection.objects: context.scene.collection.objects.unlink(cam_obj)
        else: cam_obj = bpy.data.objects[DEDICATED_CAMERA_NAME]
        props = context.scene.surface_camera_properties; props.camera_obj = cam_obj; props.is_updating_settings = True
        for key in props.bl_rna.properties.keys():
            if key not in ['camera_obj', 'bl_rna', 'is_updating_settings'] and not props.bl_rna.properties[key].is_readonly: props.property_unset(key)
        props.is_updating_settings = False; update_surface_camera(props, context); self.report({'INFO'}, f"カメラ '{DEDICATED_CAMERA_NAME}' を作成/選択し、初期化しました。"); return {'FINISHED'}
class SFC_OT_SyncWithCamera(Operator):
    bl_idname = f"{PREFIX}.sync_with_camera"; bl_label = "UIを同期"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, cam_obj = context.scene.surface_camera_properties, context.scene.surface_camera_properties.camera_obj
        if not cam_obj or cam_obj.type != 'CAMERA': self.report({'WARNING'}, "有効なカメラが選択されていません。"); return {'CANCELLED'}
        context.scene.camera = cam_obj; cam_data = cam_obj.data; props.is_updating_settings = True
        props.lens_focal_length, props.clip_start, props.clip_end = cam_data.lens, cam_data.clip_start, cam_data.clip_end
        props.is_updating_settings = False; sync_ui_from_manual_transform(props, cam_obj, context); self.report({'INFO'}, f"カメラ '{cam_obj.name}' の設定をUIに読み込みました。"); return {'FINISHED'}
class SFC_OT_UnlinkObject(Operator):
    bl_idname = f"{PREFIX}.unlink_object"; bl_label = "解除"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, update_func, obj_prop = context.scene.surface_camera_properties, update_surface_camera, 'camera_obj'
        if getattr(props, obj_prop): self.report({'INFO'}, f"'{getattr(props, obj_prop).name}' との関連付けを解除しました。"); setattr(props, obj_prop, None)
        props.is_updating_settings = True
        for key in props.bl_rna.properties.keys():
            if key not in ['bl_rna', 'is_updating_settings', 'camera_obj'] and not props.bl_rna.properties[key].is_readonly: props.property_unset(key)
        props.is_updating_settings = False; update_func(props, context); return {'FINISHED'}
class SFC_OT_ResetProperty(Operator):
    bl_idname = f"{PREFIX}.reset_property"; bl_label = "プロパティリセット"; targets: CollectionProperty(type=TargetProperty); prop_group_name: StringProperty()
    def execute(self, context):
        props, update_func = context.scene.surface_camera_properties, update_surface_camera
        prop_groups = {"location": ["fixed_location"],"ypr": ["offset_yaw", "offset_pitch", "offset_roll"],"aim": ["target_location"],"clip": ["clip_start", "clip_end", "lens_focal_length"],}
        target_names, props_to_reset = {t.name for t in self.targets}, set()
        if "all" in target_names:
            for group_props in prop_groups.values(): props_to_reset.update(group_props)
        else:
            for name in target_names: props_to_reset.update(prop_groups.get(name, []))
        props.is_updating_settings = True
        for prop_name in props_to_reset:
            if hasattr(props, prop_name): props.property_unset(prop_name)
        props.is_updating_settings = False; update_func(props, context); return {'FINISHED'}
class SFC_OT_SetFOV(Operator):
    bl_idname = f"{PREFIX}.set_fov"; bl_label = "FOV設定"; fov: FloatProperty(default=0.0)
    def execute(self, context): props = context.scene.surface_camera_properties; props.lens_focal_length = calculate_focal_length(self.fov); return {'FINISHED'}
class SFC_OT_CopyAllInfo(Operator):
    bl_idname = f"{PREFIX}.copy_all_info"; bl_label = "全情報コピー"
    def execute(self, context):
        props=context.scene.surface_camera_properties; context.window_manager.clipboard = (f"カメラ情報 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n----------------------------------------\n" f"焦点距離: {props.info_focal_length}\n水平視野角: {props.info_horizontal_fov}\nカメラ位置: {props.info_camera_location}\n" f"注視点: {props.info_target_location}\n注視点までの距離: {props.info_distance_to_target}\n注視点での横幅: {props.info_viewable_width}\n" f"クリップ範囲: {props.info_clip_setting}\n----------------------------------------"); self.report({'INFO'}, "全情報をクリップボードにコピーしました。"); return {'FINISHED'}
class SFC_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"; bl_label = "URLを開く"; url: StringProperty(default="")
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}
class SFC_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"; bl_label = "アドオン解除"
    def execute(self, context): module_name = __name__.split('.')[0]; bpy.ops.preferences.addon_disable(module=module_name); self.report({'INFO'}, f"アドオン '{bl_info.get('name')}' を無効化・解除しました。"); unregister(); return {'FINISHED'}
class SFC_OT_WireApplyColor(Operator):
    bl_idname = f"{PREFIX}.apply_wire_color"; bl_label = "Apply Wire Color"
    def execute(self, context): props=context.scene.theme_wire_properties; theme=bpy.context.preferences.themes[0]; theme.view_3d.wire=props.wire_color; theme.view_3d.object_active=props.wire_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context):
        props = context.scene.theme_wire_properties
        props.wire_color = next((p[3] for p in WIRE_PRESETS if p[0] == props.wire_preset), props.wire_color)
        getattr(bpy.ops, f"{PREFIX}.apply_wire_color")()
class SFC_OT_WireCopyColor(Operator):
    bl_idname = f"{PREFIX}.copy_wire_color"; bl_label = "Copy Wire Color"
    def execute(self, context): theme=bpy.context.preferences.themes[0]; color_tuple=tuple(round(c, 2) for c in theme.view_3d.wire); context.window_manager.clipboard=f'("CUSTOM", "Custom", "Custom wire color", {color_tuple}),'; self.report({'INFO'}, f"ワイアの色をコピーしました: {context.window_manager.clipboard}"); return {'FINISHED'}
class SFC_OT_SetFixedLocationFromView(Operator):
    bl_idname = f"{PREFIX}.set_fixed_location_from_view"; bl_label = "現在のカメラ位置をセット"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, cam_obj = context.scene.surface_camera_properties, context.scene.surface_camera_properties.camera_obj
        if not cam_obj: self.report({'WARNING'}, "操作対象のカメラが選択されていません。"); return {'CANCELLED'}
        props.fixed_location = cam_obj.location; self.report({'INFO'}, f"固定位置を {tuple(round(c, 2) for c in cam_obj.location)} に設定しました。"); return {'FINISHED'}
class ZIONAD_SWT_OT_LoadHdriFromList(Operator):
    bl_idname = f"{PREFIX}.load_hdri_from_list"; bl_label = "Load HDRI from List"; bl_options = {'REGISTER', 'UNDO'}; hdri_index: IntProperty()
    def execute(self, context):
        props = context.scene.zionad_swt_props
        if 0 <= self.hdri_index < len(HDRI_PATHS):
            props.hdri_list_index = self.hdri_index; props.background_mode = 'HDRI'; load_hdri_from_path(HDRI_PATHS[self.hdri_index], context); update_background_mode(props, context)
            self.report({'INFO'}, f"Loaded: {os.path.basename(HDRI_PATHS[self.hdri_index])}")
        else: self.report({'ERROR'}, "Invalid HDRI index")
        return {'FINISHED'}
class ZIONAD_SWT_OT_ResetTransform(Operator):
    bl_idname = f"{PREFIX}.reset_transform"; bl_label = "Reset Transform Value"; bl_options = {'REGISTER', 'UNDO'}; property_to_reset: StringProperty()
    def execute(self, context):
        _, nodes, _ = get_world_nodes(context)
        if not nodes: return {'CANCELLED'}
        mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
        if not mapping_node: return {'CANCELLED'}
        if self.property_to_reset == 'Location': mapping_node.inputs['Location'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Rotation': mapping_node.inputs['Rotation'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Scale': mapping_node.inputs['Scale'].default_value = (1, 1, 1)
        return {'FINISHED'}

# --- UIパネル ---
class SFC_PT_CameraSetupPanel(Panel):
    bl_label = "1. カメラ設定"; bl_idname = PANEL_IDS["SETUP"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["SETUP"]]
    def draw(self, context):
        layout = self.layout; props = context.scene.surface_camera_properties; box = layout.box(); col = box.column(); col.prop(props, "camera_obj", text="カメラ")
        if props.camera_obj: row = col.row(align=True); row.operator(f"{PREFIX}.sync_with_camera", icon='UV_SYNC_SELECT'); row.operator(f"{PREFIX}.unlink_object", icon='X')
        else: col.label(text="カメラを選択してください", icon='ERROR'); col.operator(f"{PREFIX}.create_dedicated_camera", text=f"'{DEDICATED_CAMERA_NAME}' を作成/選択", icon='ADD')
        col.separator(); box.prop(props, "camera_preset", text="色プリセット"); box.prop(props, "camera_color", text="カラー"); box.operator(f"{PREFIX}.apply_camera_color", text="ビューポート色を適用")
class SFC_PT_PositionPanel(Panel):
    bl_label = "2. カメラ位置 (固定)"; bl_idname = PANEL_IDS["POSITION"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["POSITION"]]
    def draw(self, context):
        layout = self.layout; props = context.scene.surface_camera_properties; box = layout.box(); col = box.column(align=True); row = col.row(align=True)
        row.label(text="固定位置"); op = row.operator(f"{PREFIX}.reset_property", text="", icon='LOOP_BACK'); op.targets.add().name = "location"; op.prop_group_name = "camera"
        col.prop(props, "fixed_location", text=""); col.operator(f"{PREFIX}.set_fixed_location_from_view", icon='OBJECT_ORIGIN')
class SFC_PT_AimingPanel(Panel):
    bl_label = "3. カメラ視線制御"; bl_idname = PANEL_IDS["AIMING"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["AIMING"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout, props = self.layout, context.scene.surface_camera_properties
        box_aim = layout.box(); col_aim = box_aim.column(align=True)
        row_aim = col_aim.row(align=True); row_aim.label(text="注視点")
        op_aim = row_aim.operator(f"{PREFIX}.reset_property", text="", icon='LOOP_BACK'); op_aim.targets.add().name = "aim"; op_aim.prop_group_name = "camera"
        col_aim.prop(props, "target_location", text="")
        box_offset = layout.box(); col_offset = box_offset.column(align=True); row_offset = col_offset.row(align=True); row_offset.label(text="視線オフセット (YPR)")
        op_offset = row_offset.operator(f"{PREFIX}.reset_property", text="", icon='LOOP_BACK'); op_offset.targets.add().name = "ypr"; op_offset.prop_group_name = "camera"
        col_offset.prop(props, "offset_yaw"); col_offset.prop(props, "offset_pitch"); col_offset.prop(props, "offset_roll")
class SFC_PT_LensPanel(Panel):
    bl_label = "4. レンズ設定"; bl_idname = PANEL_IDS["LENS"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["LENS"]]
    def draw(self, context):
        layout, props = self.layout, context.scene.surface_camera_properties; box = layout.box(); col = box.column(align=True); row = col.row(align=True)
        row.label(text="レンズとクリップ"); op = row.operator(f"{PREFIX}.reset_property", text="", icon='LOOP_BACK'); op.targets.add().name = "clip"; op.prop_group_name = "camera"
        col.prop(props, "lens_focal_length"); row = col.row(align=True); row.label(text="水平視野角:"); row.label(text=props.info_horizontal_fov); col.label(text="FOVプリセット:")
        row = col.row(align=True); col1, col2 = row.column(align=True), row.column(align=True)
        for i, fov in enumerate(FOV_PRESETS): op = (col1 if i % 2 == 0 else col2).operator(f"{PREFIX}.set_fov", text=f"{fov}°"); op.fov = fov
        col.separator(); row = col.row(align=True); row.prop(props, "clip_start"); row.prop(props, "clip_end")
class SFC_PT_CameraDisplayPanel(Panel):
    bl_label = "Camera Display & Render"; bl_idname = PANEL_IDS["CAMERA_DISPLAY"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["CAMERA_DISPLAY"]]
    def draw(self, context):
        layout, scene, cam = self.layout, context.scene, context.scene.camera
        
        box_render = layout.box()
        box_render.label(text="Render Engine", icon='SCENE')
        box_render.prop(scene.render, "engine", expand=True)
        layout.separator()

        if not cam or not isinstance(cam.data, bpy.types.Camera):
            layout.box().label(text="シーンにアクティブなカメラがありません", icon='ERROR')
            return

        cam_data = cam.data
        overlay = context.space_data.overlay if context.space_data and hasattr(context.space_data, 'overlay') else None
        
        layout.label(text="Active Camera: " + cam.name, icon='CAMERA_DATA')
        
        box_passepartout = layout.box()
        box_passepartout.label(text="Passepartout", icon='MOD_MASK')
        col_passepartout = box_passepartout.column(align=True)
        col_passepartout.prop(cam_data, "show_passepartout", text="Enable")
        row_passepartout = col_passepartout.row()
        row_passepartout.enabled = cam_data.show_passepartout
        row_passepartout.prop(cam_data, "passepartout_alpha", text="Opacity")
        layout.separator()

        box_display = layout.box()
        box_display.label(text="Viewport Display", icon='OVERLAY')
        
        if not overlay:
            box_display.label(text="3D Viewport only", icon='INFO')
            return
            
        box_display.prop(overlay, "show_overlays", text="Viewport Overlays")
        
        col_overlay_options = box_display.column(); col_overlay_options.enabled = overlay.show_overlays
        col_overlay_options.prop(overlay, "show_extras", text="Extras")
        
        col_details = col_overlay_options.column(); col_details.enabled = overlay.show_extras
        col_details.prop(overlay, "show_text", text="Text Info")
        col_details.prop(cam_data, "show_name", text="Name")
        col_details.prop(cam_data, "show_limits", text="Limits")
class ZIONAD_SWT_PT_WorldControlPanel(Panel):
    bl_label = "World Control"; bl_idname = PANEL_IDS["WORLD_CONTROL"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["WORLD_CONTROL"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout, scene, props = self.layout, context.scene, context.scene.zionad_swt_props; world, nodes, _ = get_world_nodes(context, create=False)
        if not world or not world.use_nodes or not nodes:
            col = layout.column(align=True)
            if not world: col.label(text="No World in Scene", icon='ERROR'); col.operator("world.new", text="Create New World")
            else: col.label(text="Enable Nodes in World"); col.prop(world, "use_nodes", text="Use Nodes")
            return
        box_mode = layout.box(); box_mode.label(text="Background Mode", icon='WORLD'); box_mode.prop(props, "background_mode", expand=True); layout.separator()
        if props.background_mode == 'HDRI':
            box_env = layout.box(); box_env.label(text="Environment Texture (HDRI)", icon='IMAGE_DATA'); col_list = box_env.column(align=True); col_list.label(text="HDRI Presets:")
            for i, path in enumerate(HDRI_PATHS): op = col_list.operator(f"{PREFIX}.load_hdri_from_list", text=os.path.basename(path), depress=(props.hdri_list_index == i)); op.hdri_index = i
            box_env.separator(); env_node = find_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture')
            if env_node:
                box_env.template_ID(env_node, "image", open="image.open", text="Select HDRI"); mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
                if mapping_node:
                    box_transform = box_env.box(); box_transform.label(text="Transform", icon='OBJECT_DATA'); col = box_transform.column(align=True)
                    for prop_name in ['Location', 'Rotation', 'Scale']:
                        row = col.row(align=True); split = row.split(factor=0.8, align=True); split.prop(mapping_node.inputs[prop_name], "default_value", text=prop_name)
                        op = split.operator(f"{PREFIX}.reset_transform", text="", icon='FILE_REFRESH'); op.property_to_reset = prop_name
        elif props.background_mode == 'SKY':
            box_sky = layout.box(); box_sky.label(text="Sky Texture", icon='WORLD_DATA'); sky_node = find_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture')
            if sky_node:
                col_sky = box_sky.column(align=True); col_sky.prop(sky_node, "sky_type", text="Sky Type")
                if sky_node.sky_type == 'NISHITA':
                    if hasattr(sky_node, 'sun_elevation'): col_sky.prop(sky_node, "sun_elevation", text="Sun Elevation")
                    if hasattr(sky_node, 'sun_rotation'): col_sky.prop(sky_node, "sun_rotation", text="Sun Rotation")
                    if hasattr(sky_node, 'altitude'): col_sky.prop(sky_node, "altitude", text="Altitude")
                    if hasattr(sky_node, 'air_density'): col_sky.prop(sky_node, "air_density", text="Air Density")
                    if hasattr(sky_node, 'dust_density'): col_sky.prop(sky_node, "dust_density", text="Dust Density")
                    if hasattr(sky_node, 'ozone_density'): col_sky.prop(sky_node, "ozone_density", text="Ozone Density")
                elif sky_node.sky_type in {'PREETHAM', 'HOSEK_WILKIE'}:
                    if hasattr(sky_node, 'turbidity'): col_sky.prop(sky_node, "turbidity", text="Turbidity")
                    if hasattr(sky_node, 'ground_albedo'): col_sky.prop(sky_node, "ground_albedo", text="Ground Albedo")
class SFC_PT_InfoPanel(Panel):
    bl_label = "カメラ情報"; bl_idname = PANEL_IDS["INFO"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["INFO"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props = self.layout, context.scene.surface_camera_properties; col = layout.column(align=True); row = col.row(align=True); row.label(text="焦点距離:"); row.label(text=props.info_focal_length); row = col.row(align=True); row.label(text="水平視野角:"); row.label(text=props.info_horizontal_fov); col.separator(); row = col.row(align=True); row.label(text="カメラ位置:"); row.label(text=props.info_camera_location); row = col.row(align=True); row.label(text="注視点:"); row.label(text=props.info_target_location); row = col.row(align=True); row.label(text="注視点までの距離:"); row.label(text=props.info_distance_to_target); row = col.row(align=True); row.label(text="注視点での横幅:"); row.label(text=props.info_viewable_width); col.separator(); row = col.row(align=True); row.label(text="クリップ範囲:"); row.label(text=props.info_clip_setting); col.separator(); col.prop(props, "info_precision", text="表示桁数"); col.operator(f"{PREFIX}.copy_all_info", text="全情報をコピー", icon='COPY_ID')
class SFC_PT_GridPanel(Panel):
    bl_label = "Grid Color"; bl_idname = PANEL_IDS["GRID"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["GRID"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props, theme = self.layout, context.scene.theme_grid_properties, bpy.context.preferences.themes[0]; layout.label(text=f"Current: {tuple(round(c, 3) for c in theme.view_3d.grid)}"); layout.operator(f"{PREFIX}.copy_grid_color", text="Copy Grid Color"); layout.separator(); layout.prop(props, "grid_preset"); layout.prop(props, "grid_color"); layout.operator(f"{PREFIX}.apply_grid_color", text="Apply Grid Color")
class SFC_PT_WirePanel(Panel):
    bl_label = "Wire Color"; bl_idname = PANEL_IDS["WIRE"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["WIRE"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props, theme = self.layout, context.scene.theme_wire_properties, bpy.context.preferences.themes[0]; layout.label(text=f"Current: {tuple(round(c, 3) for c in theme.view_3d.wire)}"); layout.operator(f"{PREFIX}.copy_wire_color", text="Copy Wire Color"); layout.separator(); layout.prop(props, "wire_preset"); layout.prop(props, "wire_color"); layout.operator(f"{PREFIX}.apply_wire_color", text="Apply Wire Color")

# --- リンクパネル ---
class SFC_PT_LinksPanel(Panel):
    bl_label = "リンク"; bl_idname = PANEL_IDS["LINKS"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["LINKS"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        for link in ADDON_LINKS:
            op = layout.operator(f"{PREFIX}.open_url", text=link["label"], icon='URL')
            op.url = link["url"]
class SFC_PT_NewDocsLinksPanel(Panel):
    bl_label = "アドオン管理"; bl_idname = PANEL_IDS["LINKS_NEWDOC"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_parent_id = PANEL_IDS["LINKS"]
    def draw(self, context):
        layout = self.layout
        if not NEW_DOC_LINKS:
            layout.label(text="No links available.", icon='INFO')
        for link in NEW_DOC_LINKS:
            op = layout.operator(f"{PREFIX}.open_url", text=link["label"], icon='URL')
            op.url = link["url"]
class SFC_PT_DocsLinksPanel(Panel):
    bl_label = "関連ドキュメント"; bl_idname = PANEL_IDS["LINKS_DOC"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_parent_id = PANEL_IDS["LINKS"]
    def draw(self, context):
        layout = self.layout
        for link in DOC_LINKS:
            op = layout.operator(f"{PREFIX}.open_url", text=link["label"], icon='URL')
            op.url = link["url"]
class SFC_PT_SocialLinksPanel(Panel):
    bl_label = "ソーシャルリンク"; bl_idname = PANEL_IDS["LINKS_SOCIAL"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_parent_id = PANEL_IDS["LINKS"]
    def draw(self, context):
        layout = self.layout
        for link in SOCIAL_LINKS:
            op = layout.operator(f"{PREFIX}.open_url", text=link["label"], icon='URL')
            op.url = link["url"]

class SFC_PT_RemovePanel(Panel):
    bl_label = "アドオン削除"; bl_idname = PANEL_IDS["REMOVE"]; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = PANEL_ORDER[PANEL_IDS["REMOVE"]]; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): self.layout.operator(f"{PREFIX}.remove_addon", text="このアドオンを解除", icon='CANCEL')

# --- World Tools 初期化 ---
def initial_setup():
    if bpy.context.scene.world and bpy.context.scene.world.use_nodes:
        props = bpy.context.scene.zionad_swt_props; nodes = bpy.context.scene.world.node_tree.nodes
        background_node = find_node(nodes, 'ShaderNodeBackground', 'Background')
        if background_node and background_node.inputs['Color'].is_linked:
            source_node = background_node.inputs['Color'].links[0].from_node
            if source_node.type == 'TEX_SKY': props.background_mode = 'SKY'
            else: props.background_mode = 'HDRI';
        update_background_mode(props, bpy.context)
    return None

# --- 登録/解除 ---
classes = (
    ThemeGridProperties, ThemeWireProperties, TargetProperty, SurfaceCameraProperties, ZIONAD_SWT_Properties,
    SFC_OT_GridApplyColor, SFC_OT_GridCopyColor, SFC_OT_WireApplyColor, SFC_OT_WireCopyColor, SFC_OT_ApplyCameraColor,
    SFC_OT_CreateDedicatedCamera, SFC_OT_SyncWithCamera, SFC_OT_UnlinkObject, SFC_OT_ResetProperty, SFC_OT_SetFOV,
    SFC_OT_CopyAllInfo, SFC_OT_OpenURL, SFC_OT_RemoveAddon, SFC_OT_SetFixedLocationFromView,
    ZIONAD_SWT_OT_LoadHdriFromList, ZIONAD_SWT_OT_ResetTransform,
    SFC_PT_CameraSetupPanel, SFC_PT_PositionPanel, SFC_PT_AimingPanel, SFC_PT_LensPanel, SFC_PT_CameraDisplayPanel,
    ZIONAD_SWT_PT_WorldControlPanel, SFC_PT_InfoPanel, SFC_PT_GridPanel, SFC_PT_WirePanel,
    SFC_PT_LinksPanel, SFC_PT_NewDocsLinksPanel, SFC_PT_DocsLinksPanel, SFC_PT_SocialLinksPanel,
    SFC_PT_RemovePanel,
)
_registered_classes = []
def register():
    global _registered_classes; _registered_classes.clear()
    for cls in classes:
        try: bpy.utils.register_class(cls); _registered_classes.append(cls)
        except Exception as e: print(f"Error registering class {cls.__name__}: {e}"); unregister(); raise
    bpy.types.Scene.surface_camera_properties = PointerProperty(type=SurfaceCameraProperties)
    bpy.types.Scene.theme_grid_properties = PointerProperty(type=ThemeGridProperties)
    bpy.types.Scene.theme_wire_properties = PointerProperty(type=ThemeWireProperties)
    bpy.types.Scene.zionad_swt_props = PointerProperty(type=ZIONAD_SWT_Properties)
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    if not bpy.app.timers.is_registered(initial_setup): bpy.app.timers.register(initial_setup, first_interval=0.1)
def unregister():
    global _registered_classes
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    if _update_timer and bpy.app.timers.is_registered(reset_update_flag): bpy.app.timers.unregister(reset_update_flag)
    if bpy.app.timers.is_registered(initial_setup): bpy.app.timers.unregister(initial_setup)
    for prop_name in ['surface_camera_properties', 'theme_grid_properties', 'theme_wire_properties', 'zionad_swt_props']:
        if hasattr(bpy.types.Scene, prop_name):
            try: delattr(bpy.types.Scene, prop_name)
            except (AttributeError, RuntimeError): pass
    for cls in reversed(classes):
        if hasattr(bpy.utils, 'unregister_class') and cls in _registered_classes:
            try: bpy.utils.unregister_class(cls)
            except RuntimeError: pass
    _registered_classes.clear()

if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()