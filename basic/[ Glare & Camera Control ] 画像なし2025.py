# [厳守事項] このコードは、「bl_idnameが長すぎる」というエラーを修正した最終安定版です。
# プレフィックスとオペレーターIDを短縮し、Blenderの文字数制限(63文字)に対応しました。

import bpy
import webbrowser
import math
import mathutils
import os
from bpy.types import Operator, Panel, PropertyGroup, Scene
from bpy.props import StringProperty, PointerProperty, FloatProperty, FloatVectorProperty, BoolProperty, IntProperty, EnumProperty, CollectionProperty
from datetime import datetime

# ===================================================================
# パラメータ設定 (全体)
# ===================================================================

# --- プレフィックスとID設定 ---
# ▼▼▼ 修正: bl_idnameの文字数制限に対応するため、静的パーツを短縮 ▼▼▼
_PREFIX_STATIC_PART = "z26_integ" 
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"
ADDON_MODULE_NAME = __name__

# --- アドオン情報 (統合版) ---
ADDON_CATEGORY_NAME = "   [ Glare & Camera Control ]   "

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (Integrated)",
    "author": "zionadchat (As Ordered)",
    "version": (26, 0, 1), # エラー修正によるパッチバージョンアップ
    "blender": (4, 1, 0),
    "location": f"View3D > Sidebar > {ADDON_CATEGORY_NAME}",
    "description": "【警告: 動的Prefixのため設定は保存されません】カラー調整、ブルーム、カメラ固定、ワールド(HDRI)制御、各種UIを統合した多機能版",
    "category": "zParameter",
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/16/143651",
}

# --- Blenderバージョン互換性 ---
if bpy.app.version >= (4, 2, 0):
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE_NEXT'
else:
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE'


# ===================================================================
# glare bloom 由来の定数とリンクデータ
# ===================================================================
GB_ADDON_LINKS = [
    {"label": "glare bloom 20250716", "url": "https://memo2017.hatenablog.com/entry/2025/07/16/143651"},
    {"label": "HDRi ワールドコントロール 20250705", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"},
]
GB_NEW_DOC_LINKS = [
    {"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"},
    {"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},
]
GB_DOC_LINKS = [
    {"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"},
    {"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"},
    {"label": "addon 目次整理　from 20250116", "url": "https://blenderzionad.hatenablog.com/entry/2025/01/17/002322"},
]
GB_SOCIAL_LINKS = [
    {"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"},
    {"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"},
    {"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"},
    {"label": "単純トリック 2025 open", "url": "https://www.notion.so/2025-open-221b3deba7a2809a85a9f5ab5600ab06"},
]


# ======================================================================
# Fixed Camera & World 由来の定数とユーザー設定
# ======================================================================
# --- HDRI画像ファイルのフルパスリスト ---
HDRI_PATHS = [
#    r"C:\a111\HDRi_pic\qwantani_afternoon_puresky_4k.exr",
#    r"C:\a111\HDRi_pic\rogland_moonlit_night_4k.hdr",
#    r"C:\a111\HDRi_pic\rogland_clear_night_4k.hdr",
#    r"C:\a111\HDRi_pic\golden_bay_4k.hdr",
]
# --- ワイヤーフレームの色プリセット ---
WIRE_PRESETS = [("CUSTOM_GREENISH", "Custom Greenish", "Custom greenish wire color", (0.51, 1.0, 0.75)), ("WHITE", "White", "White wire", (1.0, 1.0, 1.0)), ("RED", "Red", "Red wire", (1.0, 0.0, 0.0)), ("GREEN", "Green", "Green wire", (0.0, 1.0, 0.0)),]
# --- グリッドの色プリセット ---
GRID_PRESETS = [("CUSTOM_REDDISH", "Custom Reddish", "Custom reddish color", (0.545, 0.322, 0.322, 1.0)), ("DEEP_GREEN", "Deep Green", "A deep green color", (0.098, 0.314, 0.271, 1.0)), ("MINT_GREEN", "Mint Green", "A mint green color", (0.165, 0.557, 0.475, 1.0)),]
# --- 専用カメラのコレクション名とオブジェクト名 ---
CAMERA_COLLECTION_NAME = "Cam"
DEDICATED_CAMERA_NAME = "Fixed_Cam"
# --- 定数定義 ---
SENSOR_WIDTH = 36.0
FOV_PRESETS = [1, 5, 10, 30, 45, 60, 90, 120, 135, 150, 179]
CAMERA_COLOR_PRESETS = [("CYAN", "Cyan", "水色", (0.0, 1.0, 1.0)), ("Cam 4.4.0", "Cam 4.4.0", "Blenderデフォルト色", (0.0, 0.0, 0.0)), ("YELLOW", "Yellow", "黄色", (1.0, 1.0, 0.0)), ("PURPLE", "Purple", "紫色", (0.5, 0.0, 0.5)),]
# --- リンクパネル用データ ---
FCW_ADDON_LINKS = ({"label": "カメラ 固定 Git 管理 20250711", "url":"https://memo2017.hatenablog.com/entry/2025/07/11/131157"},)
FCW_NEW_DOC_LINKS = [{"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},]
FCW_DOC_LINKS = [{"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"}, {"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"}, {"label": "addon 目次整理　from 20250116", "url": "https://blenderzionad.hatenablog.com/entry/2025/01/17/002322"},]
FCW_SOCIAL_LINKS = [{"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"}, {"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"}, {"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"}, {"label": "単純トリック 2025 open", "url": "https://www.notion.so/2025-open-221b3deba7a2809a85a9f5ab5600ab06"},]


# ===================================================================
# ヘルパー関数 (統合)
# ===================================================================

# --- glare bloom 由来 ---
def get_node_name(suffix): return f"zionad_node_{PREFIX}_{suffix}"
def get_or_create_material(obj):
    if obj.active_material: return obj.active_material
    mat = bpy.data.materials.new(name=f"{obj.name}_Material")
    obj.data.materials.append(mat)
    return mat
def get_principled_bsdf(material):
    if not material.use_nodes: material.use_nodes = True
    node = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not node:
        node = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        output_node = next((n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if output_node: material.node_tree.links.new(node.outputs['BSDF'], output_node.inputs['Surface'])
    return node
def setup_per_object_bloom_nodes(mat, create=True):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = get_principled_bsdf(mat)
    output_node = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not (bsdf and output_node): return None
    mix_shader = nodes.get(get_node_name("mix_shader"))
    bloom_emission = nodes.get(get_node_name("per_object_bloom_emission"))
    layer_weight = nodes.get(get_node_name("layer_weight"))
    is_incomplete = not all([mix_shader, bloom_emission, layer_weight])
    if not create: return None if is_incomplete else {"mix": mix_shader, "emission": bloom_emission, "layer": layer_weight}
    if is_incomplete:
        if mix_shader: nodes.remove(mix_shader)
        if bloom_emission: nodes.remove(bloom_emission)
        if layer_weight: nodes.remove(layer_weight)
        if not output_node.inputs['Surface'].is_linked or output_node.inputs['Surface'].links[0].from_node != bsdf:
            for link in output_node.inputs['Surface'].links: links.remove(link)
            links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])
        original_link = output_node.inputs['Surface'].links[0]
        mix_shader = nodes.new(type='ShaderNodeMixShader'); mix_shader.name = get_node_name("mix_shader")
        bloom_emission = nodes.new(type='ShaderNodeEmission'); bloom_emission.name = get_node_name("per_object_bloom_emission")
        layer_weight = nodes.new(type='ShaderNodeLayerWeight'); layer_weight.name = get_node_name("layer_weight")
        mix_shader.location = (bsdf.location.x + 200, bsdf.location.y)
        bloom_emission.location = (mix_shader.location.x - 200, mix_shader.location.y - 150)
        layer_weight.location = (mix_shader.location.x - 400, mix_shader.location.y)
        links.remove(original_link)
        links.new(bsdf.outputs['BSDF'], mix_shader.inputs[2])
        links.new(bloom_emission.outputs['Emission'], mix_shader.inputs[1])
        links.new(layer_weight.outputs['Fresnel'], mix_shader.inputs['Fac'])
        links.new(mix_shader.outputs['Shader'], output_node.inputs['Surface'])
    return {"mix": mix_shader, "emission": bloom_emission, "layer": layer_weight}
def remove_per_object_bloom_nodes(mat):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bloom_nodes = setup_per_object_bloom_nodes(mat, create=False)
    if bloom_nodes:
        bsdf = get_principled_bsdf(mat)
        output_node = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if bsdf and output_node:
            for link in output_node.inputs['Surface'].links: links.remove(link)
            links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])
        for node in bloom_nodes.values():
            if node: nodes.remove(node)
def get_scene_bloom_glare_node(context):
    scene = context.scene
    if not scene.use_nodes: scene.use_nodes = True
    tree, nodes = scene.node_tree, scene.node_tree.nodes
    glare_node = nodes.get(get_node_name("scene_bloom_glare"))
    if not glare_node:
        render_layers = next((n for n in nodes if n.type == 'R_LAYERS'), None)
        if not render_layers: return None
        glare_node = nodes.new(type='CompositorNodeGlare')
        glare_node.name = get_node_name("scene_bloom_glare")
        glare_node.glare_type = 'BLOOM'
        glare_node.location = render_layers.location + mathutils.Vector((300, 0))
        output_socket = render_layers.outputs['Image']
        if output_socket.is_linked:
            original_link = output_socket.links[0]
            to_node, to_socket = original_link.to_node, original_link.to_socket
            tree.links.remove(original_link)
            tree.links.new(glare_node.outputs['Image'], to_socket)
        else:
            composite_node = next((n for n in nodes if n.type == 'COMPOSITE'), None)
            if composite_node: tree.links.new(glare_node.outputs['Image'], composite_node.inputs['Image'])
        tree.links.new(output_socket, glare_node.inputs['Image'])
    return glare_node
def remove_scene_bloom_glare_node(context):
    scene = context.scene
    if not scene.use_nodes: return
    tree, nodes = scene.node_tree, scene.node_tree.nodes
    glare_node = nodes.get(get_node_name("scene_bloom_glare"))
    if glare_node:
        if glare_node.inputs['Image'].is_linked and glare_node.outputs['Image'].is_linked:
            from_socket = glare_node.inputs['Image'].links[0].from_socket
            for link in list(glare_node.outputs['Image'].links):
                tree.links.new(from_socket, link.to_socket)
        nodes.remove(glare_node)

# --- Fixed Camera & World 由来 ---
_is_updating_by_addon = False; _update_timer = None
def reset_update_flag(): global _is_updating_by_addon, _update_timer; _is_updating_by_addon = False; _update_timer = None; return None
def schedule_update_flag_reset():
    global _update_timer
    if _update_timer and bpy.app.timers.is_registered(reset_update_flag): bpy.app.timers.unregister(reset_update_flag)
    bpy.app.timers.register(reset_update_flag, first_interval=0.01)
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
def calculate_horizontal_fov(focal_length, sensor_width=SENSOR_WIDTH):
    try: return 2 * math.atan(sensor_width / (2 * focal_length)) * (180 / math.pi)
    except (ZeroDivisionError, ValueError): return 0.0
def calculate_focal_length(fov_degrees, sensor_width=SENSOR_WIDTH):
    try: return sensor_width / (2 * math.tan(math.radians(fov_degrees) / 2))
    except (ZeroDivisionError, ValueError): return 50.0
def get_target_location(props): return mathutils.Vector(props.target_location)
def update_object_transform(obj, props):
    location = mathutils.Vector(props.fixed_location)
    target_location = get_target_location(props); direction = target_location - location
    if direction.length < 0.0001: direction = mathutils.Vector((0, -1, 0))
    base_track_quat = direction.to_track_quat('-Z', 'Y')
    offset_euler = mathutils.Euler((props.offset_pitch, props.offset_yaw, props.offset_roll), 'XYZ')
    final_quat = base_track_quat @ offset_euler.to_quaternion()
    obj.location = location; obj.rotation_euler = final_quat.to_euler('XYZ')


# ===================================================================
# Update関数 (統合)
# ===================================================================

# --- glare bloom 由来 ---
def apply_material_settings(context):
    if not hasattr(context.scene, 'zionad_gb_props'): return
    props = context.scene.zionad_gb_props
    obj = context.object
    if not obj or not obj.active_material: return
    mat = obj.active_material
    if not get_principled_bsdf(mat): return
    final_color = mathutils.Color(); final_color.hsv = (props.hue, props.saturation, props.brightness)
    final_color_rgba = (*final_color, 1.0)
    mat.blend_method = 'BLEND' if props.transparency < 1.0 else 'OPAQUE'
    bsdf = get_principled_bsdf(mat)
    bsdf.inputs['Alpha'].default_value = props.transparency
    bsdf.inputs['Emission Color'].default_value = final_color_rgba
    bsdf.inputs['Emission Strength'].default_value = props.emission_strength
    if props.sync_base_and_emission_color:
        bsdf.inputs['Base Color'].default_value = final_color_rgba
    if props.use_per_object_bloom:
        bloom_nodes = setup_per_object_bloom_nodes(mat, create=True)
        if bloom_nodes:
            bloom_nodes["emission"].inputs['Color'].default_value = final_color_rgba
            bloom_nodes["emission"].inputs['Strength'].default_value = props.per_object_bloom_intensity
            bloom_nodes["layer"].inputs['Blend'].default_value = props.per_object_bloom_falloff
    else: remove_per_object_bloom_nodes(mat)
def update_from_color_picker(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    context.scene.zionad_is_loading = True
    props = context.scene.zionad_gb_props; color_hsv = mathutils.Color(props.color[:3])
    props.hue, props.brightness, props.saturation = color_hsv.h, color_hsv.v, color_hsv.s
    context.scene.zionad_is_loading = False
    apply_material_settings(context)
def update_from_sliders(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    context.scene.zionad_is_loading = True
    props = context.scene.zionad_gb_props; new_color = mathutils.Color()
    new_color.hsv = (props.hue, props.saturation, props.brightness)
    props.color = new_color
    context.scene.zionad_is_loading = False
    apply_material_settings(context)
def update_material_all(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    apply_material_settings(context)
def update_scene_bloom(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    props = context.scene.zionad_gb_props
    if props.use_scene_bloom:
        glare_node = get_scene_bloom_glare_node(context)
        if glare_node:
            glare_node.threshold = props.scene_bloom_threshold
            glare_node.size = props.scene_bloom_size
            glare_node.mix = props.scene_bloom_mix
    else: remove_scene_bloom_glare_node(context)

# --- Fixed Camera & World 由来 ---
def update_background_mode(self, context):
    mode = context.scene.zionad_fcw_world_props.background_mode; world, nodes, links = get_world_nodes(context)
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
        props = context.scene.zionad_fcw_world_props
        if 0 <= props.hdri_list_index < len(HDRI_PATHS): load_hdri_from_path(HDRI_PATHS[props.hdri_list_index], context)
    update_viewport(context)
def update_surface_camera(self, context):
    global _is_updating_by_addon
    if _is_updating_by_addon: return
    _is_updating_by_addon = True
    try:
        props, camera_obj = context.scene.zionad_fcw_cam_props, context.scene.zionad_fcw_cam_props.camera_obj
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
    if not (hasattr(context, 'scene') and context.scene and hasattr(context.scene, 'zionad_fcw_cam_props')): return
    sfc_props = context.scene.zionad_fcw_cam_props
    for update in depsgraph.updates:
        if not update.is_updated_transform: continue
        try:
            obj_id = update.id.original
            if sfc_props.camera_obj and obj_id == sfc_props.camera_obj: sync_ui_from_manual_transform(sfc_props, sfc_props.camera_obj, context); return
        except ReferenceError:
            pass # オブジェクトが削除された場合など


# ===================================================================
# プロパティグループ (統合)
# ===================================================================

class ZIONAD_GB_ToolProperties(PropertyGroup):
    color: FloatVectorProperty(name="ベース/発光色", subtype='COLOR', default=(1.0, 1.0, 1.0), min=0.0, max=1.0, update=update_from_color_picker)
    hue: FloatProperty(name="Hue", subtype='FACTOR', default=0.0, min=0.0, max=1.0, update=update_from_sliders)
    brightness: FloatProperty(name="明度", min=0.0, max=1.0, default=1.0, update=update_from_sliders)
    saturation: FloatProperty(name="彩度", min=0.0, max=1.0, default=1.0, update=update_from_sliders)
    transparency: FloatProperty(name="透明度", min=0.0, max=1.0, default=1.0, subtype='FACTOR', update=update_material_all)
    emission_strength: FloatProperty(name="発光強度", min=0.0, max=50.0, default=0.0, description="オブジェクト中心部の光の強さ", update=update_material_all)
    sync_base_and_emission_color: BoolProperty(name="ベースカラーと発光色を同期", default=True, update=update_material_all)
    use_per_object_bloom: BoolProperty(name="個別ブルームを有効化", default=False, description="マテリアルによるオブジェクト単位のブルーム", update=update_material_all)
    per_object_bloom_falloff: FloatProperty(name="広がり", min=0.0, max=10.0, default=0.5, description="輪郭の光のにじむ範囲", update=update_material_all)
    per_object_bloom_intensity: FloatProperty(name="強度", min=0.0, max=100.0, default=1.0, description="輪郭の光の明るさ", update=update_material_all)
    use_scene_bloom: BoolProperty(name="シーンブルームを有効化", default=False, description="コンポジターを用いたシーン全体のブルーム効果 (EEVEE標準)", update=update_scene_bloom)
    scene_bloom_threshold: FloatProperty(name="しきい値", min=0.0, default=1.0, description="ブルームが発生する明るさの基準", update=update_scene_bloom)
    scene_bloom_size: IntProperty(name="サイズ", min=1, max=9, default=7, description="ブルームの広がり具合", update=update_scene_bloom)
    scene_bloom_mix: FloatProperty(name="ミックス", min=-1.0, max=1.0, default=0.0, description="元の画像とのブレンド量", update=update_scene_bloom)

class ZIONAD_FCW_ThemeGridProperties(PropertyGroup):
    grid_color: FloatVectorProperty(name="Grid Color", subtype='COLOR', size=4, min=0.0, max=1.0, default=(0.545, 0.322, 0.322, 1.0))
    grid_preset: EnumProperty(name="Grid Preset", items=[(p[0], p[1], p[2]) for p in GRID_PRESETS], update=lambda self, context: ZIONAD_FCW_OT_GridApplyColor.update_preset(self, context))
class ZIONAD_FCW_ThemeWireProperties(PropertyGroup):
    wire_color: FloatVectorProperty(name="Wire Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.51, 1.0, 0.75))
    wire_preset: EnumProperty(name="Wire Preset", items=[(p[0], p[1], p[2]) for p in WIRE_PRESETS], update=lambda self, context: ZIONAD_FCW_OT_WireApplyColor.update_preset(self, context))
class ZIONAD_FCW_TargetProperty(PropertyGroup): name: StringProperty()
class ZIONAD_FCW_CameraProperties(PropertyGroup):
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
    camera_preset: EnumProperty(name="カメラプリセット", items=[(p[0], p[1], p[2]) for p in CAMERA_COLOR_PRESETS], default="CYAN", update=lambda self, context: ZIONAD_FCW_OT_ApplyCameraColor.update_preset(self, context))
class ZIONAD_FCW_WorldProperties(PropertyGroup):
    background_mode: EnumProperty(name="Background Mode", items=[('HDRI', "HDRI", ""), ('SKY', "Sky", "")], default='HDRI', update=update_background_mode)
    hdri_list_index: IntProperty(name="Active HDRI Index", default=0, update=update_background_mode)


# ===================================================================
# オペレーター (統合)
# ===================================================================

# --- 共通オペレーター ---
class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"; bl_label = "Open URL"; url: StringProperty(default="")
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}
class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"; bl_label = "アドオンのコンポーネントを登録解除"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        try: unregister(); self.report({'INFO'}, "アドオンのコンポーネントを登録解除しました。")
        except Exception as e: self.report({'ERROR'}, f"アドオンの削除中にエラーが発生しました: {e}"); return {'CANCELLED'}
        return {'FINISHED'}

# --- glare bloom 由来のオペレーター ---
class ZIONAD_GB_OT_InitializeSettings(Operator):
    # ▼▼▼ 修正: bl_idnameを短縮 ▼▼▼
    bl_idname = f"{PREFIX}.gb_init"; bl_label = "操作を開始"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_is_loading'): return {'CANCELLED'}
        context.scene.zionad_is_loading = True
        props = context.scene.zionad_gb_props; obj = context.object
        if obj and obj.type == 'MESH':
            mat = get_or_create_material(obj); bsdf = get_principled_bsdf(mat)
            if bsdf:
                emission_rgba = bsdf.inputs['Emission Color'].default_value; base_rgba = bsdf.inputs['Base Color'].default_value
                color_to_load = emission_rgba if any(c > 0.0 for c in emission_rgba[:3]) else base_rgba
                color_hsv = mathutils.Color(color_to_load[:3])
                props.hue, props.saturation, props.brightness, props.color = color_hsv.h, color_hsv.s, color_hsv.v, color_hsv
                props.transparency = bsdf.inputs['Alpha'].default_value; props.emission_strength = bsdf.inputs['Emission Strength'].default_value
                props.sync_base_and_emission_color = all(abs(b - e) < 0.001 for b, e in zip(base_rgba, emission_rgba))
            bloom_nodes = setup_per_object_bloom_nodes(mat, create=False)
            if bloom_nodes:
                props.use_per_object_bloom = True; props.per_object_bloom_falloff = bloom_nodes["layer"].inputs['Blend'].default_value; props.per_object_bloom_intensity = bloom_nodes["emission"].inputs['Strength'].default_value
            else: props.use_per_object_bloom = False
        if context.scene.use_nodes:
            glare_node = context.scene.node_tree.nodes.get(get_node_name("scene_bloom_glare"))
            if glare_node:
                props.use_scene_bloom = True; props.scene_bloom_threshold = glare_node.threshold; props.scene_bloom_size = glare_node.size; props.scene_bloom_mix = glare_node.mix
            else: props.use_scene_bloom = False
        else: props.use_scene_bloom = False
        context.scene.zionad_is_loading = False; apply_material_settings(context); return {'FINISHED'}
class ZIONAD_GB_OT_FinalizeAllChanges(Operator):
    # ▼▼▼ 修正: bl_idnameを短縮 ▼▼▼
    bl_idname = f"{PREFIX}.gb_finalize"; bl_label = "全ての変更を確定"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_gb_props'): return {'CANCELLED'}
        apply_material_settings(context); update_scene_bloom(self, context); context.scene.zionad_is_loading = True
        props = context.scene.zionad_gb_props
        props.color, props.hue, props.brightness, props.saturation = (1.0, 1.0, 1.0), 0.0, 1.0, 1.0
        props.transparency = 1.0; props.emission_strength = 0.0; props.sync_base_and_emission_color = True
        props.use_per_object_bloom = False; props.per_object_bloom_falloff = 0.5; props.per_object_bloom_intensity = 1.0
        props.use_scene_bloom = False; props.scene_bloom_threshold = 1.0; props.scene_bloom_size = 7; props.scene_bloom_mix = 0.0
        context.scene.zionad_is_loading = False; return {'FINISHED'}
class ZIONAD_GB_OT_ResetProperty(Operator):
    # ▼▼▼ 修正: bl_idnameを短縮 ▼▼▼
    bl_idname = f"{PREFIX}.gb_reset_prop"; bl_label = "値をリセット"; bl_options = {'REGISTER', 'UNDO'}; prop_name: StringProperty()
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_gb_props'): return {'CANCELLED'}
        props = context.scene.zionad_gb_props; default_value = ZIONAD_GB_ToolProperties.bl_rna.properties[self.prop_name].default
        if self.prop_name == 'color': props.hue, props.saturation, props.brightness = 0.0, 1.0, 1.0
        setattr(props, self.prop_name, default_value); return {'FINISHED'}
class ZIONAD_OT_SetRenderEngine(Operator):
    bl_idname = f"{PREFIX}.set_render_engine"; bl_label = "Set Render Engine"; engine: StringProperty()
    def execute(self, context): context.scene.render.engine = self.engine; return {'FINISHED'}
class ZIONAD_OT_ToggleCompositorDisplay(Operator):
    bl_idname = f"{PREFIX}.toggle_comp_view"; bl_label = "Toggle Compositor Display"
    def execute(self, context):
        shading = context.space_data.shading
        if shading.use_compositor == 'DISABLED': shading.use_compositor = 'ALWAYS'
        else: shading.use_compositor = 'DISABLED'
        return {'FINISHED'}
class ZIONAD_OT_SetCompositorMode(Operator):
    bl_idname = f"{PREFIX}.set_comp_mode"; bl_label = "Set Compositor Mode"; mode: StringProperty(default='ALWAYS', options={'HIDDEN'})
    def execute(self, context):
        valid_modes = {'ALWAYS', 'CAMERA', 'DISABLED'}
        if self.mode not in valid_modes: self.report({'ERROR'}, f"Invalid compositor mode: {self.mode}"); return {'CANCELLED'}
        context.space_data.shading.use_compositor = self.mode; self.report({'INFO'}, f"Compositor mode set to: {self.mode}"); return {'FINISHED'}

# --- Fixed Camera & World 由来のオペレーター ---
class ZIONAD_FCW_OT_ApplyCameraColor(Operator):
    bl_idname = f"{PREFIX}.fcw_apply_cam_color"; bl_label = "カメラカラー適用"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): context.preferences.themes[0].view_3d.camera = context.scene.zionad_fcw_cam_props.camera_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context): props = context.scene.zionad_fcw_cam_props; props.camera_color = next((p[3] for p in CAMERA_COLOR_PRESETS if p[0] == props.camera_preset), props.camera_color); getattr(bpy.ops, f"{PREFIX}.fcw_apply_cam_color")()
class ZIONAD_FCW_OT_GridApplyColor(Operator):
    bl_idname = f"{PREFIX}.fcw_apply_grid_color"; bl_label = "Apply Grid Color"
    def execute(self, context): props = context.scene.zionad_fcw_grid_props; bpy.context.preferences.themes[0].view_3d.grid = props.grid_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context): props = context.scene.zionad_fcw_grid_props; props.grid_color = next((p[3] for p in GRID_PRESETS if p[0] == props.grid_preset), props.grid_color); getattr(bpy.ops, f"{PREFIX}.fcw_apply_grid_color")()
class ZIONAD_FCW_OT_GridCopyColor(Operator):
    bl_idname = f"{PREFIX}.fcw_copy_grid_color"; bl_label = "Copy Grid Color"
    def execute(self, context): color_tuple = tuple(round(c, 3) for c in bpy.context.preferences.themes[0].view_3d.grid); context.window_manager.clipboard = f'("CUSTOM", "Custom", "Custom grid color", {color_tuple}),'; self.report({'INFO'}, f"グリッドの色をコピーしました: {context.window_manager.clipboard}"); return {'FINISHED'}
class ZIONAD_FCW_OT_CreateDedicatedCamera(Operator):
    # ▼▼▼ 修正: bl_idnameを短縮 ▼▼▼
    bl_idname = f"{PREFIX}.fcw_create_cam"; bl_label = "専用カメラ作成"
    def execute(self, context):
        if DEDICATED_CAMERA_NAME not in bpy.data.objects:
            cam_data = bpy.data.cameras.new(name=DEDICATED_CAMERA_NAME); cam_obj = bpy.data.objects.new(DEDICATED_CAMERA_NAME, cam_data)
            cam_collection = bpy.data.collections.get(CAMERA_COLLECTION_NAME) or bpy.data.collections.new(CAMERA_COLLECTION_NAME)
            if CAMERA_COLLECTION_NAME not in context.scene.collection.children: context.scene.collection.children.link(cam_collection)
            cam_collection.objects.link(cam_obj)
            if cam_obj.name in context.scene.collection.objects: context.scene.collection.objects.unlink(cam_obj)
        else: cam_obj = bpy.data.objects[DEDICATED_CAMERA_NAME]
        props = context.scene.zionad_fcw_cam_props; props.camera_obj = cam_obj; props.is_updating_settings = True
        for key in props.bl_rna.properties.keys():
            if key not in ['camera_obj', 'bl_rna', 'is_updating_settings'] and not props.bl_rna.properties[key].is_readonly: props.property_unset(key)
        props.is_updating_settings = False; update_surface_camera(props, context); self.report({'INFO'}, f"カメラ '{DEDICATED_CAMERA_NAME}' を作成/選択し、初期化しました。"); return {'FINISHED'}
class ZIONAD_FCW_OT_SyncWithCamera(Operator):
    bl_idname = f"{PREFIX}.fcw_sync_cam"; bl_label = "UIを同期"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, cam_obj = context.scene.zionad_fcw_cam_props, context.scene.zionad_fcw_cam_props.camera_obj
        if not cam_obj or cam_obj.type != 'CAMERA': self.report({'WARNING'}, "有効なカメラが選択されていません。"); return {'CANCELLED'}
        context.scene.camera = cam_obj; cam_data = cam_obj.data; props.is_updating_settings = True
        props.lens_focal_length, props.clip_start, props.clip_end = cam_data.lens, cam_data.clip_start, cam_data.clip_end
        props.is_updating_settings = False; sync_ui_from_manual_transform(props, cam_obj, context); self.report({'INFO'}, f"カメラ '{cam_obj.name}' の設定をUIに読み込みました。"); return {'FINISHED'}
class ZIONAD_FCW_OT_UnlinkObject(Operator):
    bl_idname = f"{PREFIX}.fcw_unlink_obj"; bl_label = "解除"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, update_func, obj_prop = context.scene.zionad_fcw_cam_props, update_surface_camera, 'camera_obj'
        if getattr(props, obj_prop): self.report({'INFO'}, f"'{getattr(props, obj_prop).name}' との関連付けを解除しました。"); setattr(props, obj_prop, None)
        props.is_updating_settings = True
        for key in props.bl_rna.properties.keys():
            if key not in ['bl_rna', 'is_updating_settings', 'camera_obj'] and not props.bl_rna.properties[key].is_readonly: props.property_unset(key)
        props.is_updating_settings = False; update_func(props, context); return {'FINISHED'}
class ZIONAD_FCW_OT_ResetProperty(Operator):
    bl_idname = f"{PREFIX}.fcw_reset_prop"; bl_label = "プロパティリセット"; targets: CollectionProperty(type=ZIONAD_FCW_TargetProperty)
    def execute(self, context):
        props, update_func = context.scene.zionad_fcw_cam_props, update_surface_camera
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
class ZIONAD_FCW_OT_SetFOV(Operator):
    bl_idname = f"{PREFIX}.fcw_set_fov"; bl_label = "FOV設定"; fov: FloatProperty(default=0.0)
    def execute(self, context): props = context.scene.zionad_fcw_cam_props; props.lens_focal_length = calculate_focal_length(self.fov); return {'FINISHED'}
class ZIONAD_FCW_OT_CopyAllInfo(Operator):
    bl_idname = f"{PREFIX}.fcw_copy_info"; bl_label = "全情報コピー"
    def execute(self, context):
        props=context.scene.zionad_fcw_cam_props; context.window_manager.clipboard = (f"カメラ情報 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n----------------------------------------\n" f"焦点距離: {props.info_focal_length}\n水平視野角: {props.info_horizontal_fov}\nカメラ位置: {props.info_camera_location}\n" f"注視点: {props.info_target_location}\n注視点までの距離: {props.info_distance_to_target}\n注視点での横幅: {props.info_viewable_width}\n" f"クリップ範囲: {props.info_clip_setting}\n----------------------------------------"); self.report({'INFO'}, "全情報をクリップボードにコピーしました。"); return {'FINISHED'}
class ZIONAD_FCW_OT_WireApplyColor(Operator):
    bl_idname = f"{PREFIX}.fcw_apply_wire_color"; bl_label = "Apply Wire Color"
    def execute(self, context): props=context.scene.zionad_fcw_wire_props; theme=bpy.context.preferences.themes[0]; theme.view_3d.wire=props.wire_color; theme.view_3d.object_active=props.wire_color; return {'FINISHED'}
    @staticmethod
    def update_preset(self, context):
        props = context.scene.zionad_fcw_wire_props; props.wire_color = next((p[3] for p in WIRE_PRESETS if p[0] == props.wire_preset), props.wire_color); getattr(bpy.ops, f"{PREFIX}.fcw_apply_wire_color")()
class ZIONAD_FCW_OT_WireCopyColor(Operator):
    bl_idname = f"{PREFIX}.fcw_copy_wire_color"; bl_label = "Copy Wire Color"
    def execute(self, context): theme=bpy.context.preferences.themes[0]; color_tuple=tuple(round(c, 2) for c in theme.view_3d.wire); context.window_manager.clipboard=f'("CUSTOM", "Custom", "Custom wire color", {color_tuple}),'; self.report({'INFO'}, f"ワイアの色をコピーしました: {context.window_manager.clipboard}"); return {'FINISHED'}
class ZIONAD_FCW_OT_SetFixedLocationFromView(Operator):
    # ▼▼▼ 修正: bl_idnameを短縮（これがエラーの原因でした） ▼▼▼
    bl_idname = f"{PREFIX}.fcw_set_loc_view"; bl_label = "現在のカメラ位置をセット"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props, cam_obj = context.scene.zionad_fcw_cam_props, context.scene.zionad_fcw_cam_props.camera_obj
        if not cam_obj: self.report({'WARNING'}, "操作対象のカメラが選択されていません。"); return {'CANCELLED'}
        props.fixed_location = cam_obj.location; self.report({'INFO'}, f"固定位置を {tuple(round(c, 2) for c in cam_obj.location)} に設定しました。"); return {'FINISHED'}
class ZIONAD_FCW_OT_LoadHdriFromList(Operator):
    bl_idname = f"{PREFIX}.fcw_load_hdri"; bl_label = "Load HDRI from List"; bl_options = {'REGISTER', 'UNDO'}; hdri_index: IntProperty()
    def execute(self, context):
        props = context.scene.zionad_fcw_world_props
        if 0 <= self.hdri_index < len(HDRI_PATHS):
            props.hdri_list_index = self.hdri_index; props.background_mode = 'HDRI'; load_hdri_from_path(HDRI_PATHS[self.hdri_index], context); update_background_mode(props, context)
            self.report({'INFO'}, f"Loaded: {os.path.basename(HDRI_PATHS[self.hdri_index])}")
        else: self.report({'ERROR'}, "Invalid HDRI index")
        return {'FINISHED'}
class ZIONAD_FCW_OT_ResetTransform(Operator):
    bl_idname = f"{PREFIX}.fcw_reset_trans"; bl_label = "Reset Transform Value"; bl_options = {'REGISTER', 'UNDO'}; property_to_reset: StringProperty()
    def execute(self, context):
        _, nodes, _ = get_world_nodes(context);
        if not nodes: return {'CANCELLED'}
        mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
        if not mapping_node: return {'CANCELLED'}
        if self.property_to_reset == 'Location': mapping_node.inputs['Location'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Rotation': mapping_node.inputs['Rotation'].default_value = (0, 0, 0)
        elif self.property_to_reset == 'Scale': mapping_node.inputs['Scale'].default_value = (1, 1, 1)
        return {'FINISHED'}


# ===================================================================
# UIパネル (統合)
# ===================================================================

# --- glare bloom 由来のパネル ---
class ZIONAD_PT_BasePanel(Panel):
    bl_label = "メインコントロール"; bl_idname = f"{PREFIX}_PT_base_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = -1
    def draw_header(self, context): self.layout.label(text="", icon='TOOL_SETTINGS')
    def draw(self, context):
        layout = self.layout; col = layout.column(align=True)
        col.operator(ZIONAD_GB_OT_FinalizeAllChanges.bl_idname, icon='CHECKMARK')
        col.operator(ZIONAD_GB_OT_InitializeSettings.bl_idname, text="全設定を読込/リロード", icon='FILE_REFRESH')
        col.separator()
        box = col.box(); box.label(text="レンダラー設定:")
        row = box.row(align=True); is_eevee = context.scene.render.engine == EEVEE_ENGINE_ID
        op_eevee = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="EEVEE", depress=is_eevee); op_eevee.engine = EEVEE_ENGINE_ID
        op_cycles = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="Cycles", depress=not is_eevee); op_cycles.engine = 'CYCLES'
        box = col.box(); box.label(text="ビューポートプレビュー:")
        shading = context.space_data.shading; is_compositor_on = shading.use_compositor == 'ALWAYS'
        btn_text = "リアルタイム表示: ON" if is_compositor_on else "リアルタイム表示: OFF"; btn_icon = 'HIDE_ON' if is_compositor_on else 'HIDE_OFF'
        box.operator(ZIONAD_OT_ToggleCompositorDisplay.bl_idname, text=btn_text, icon=btn_icon)
        box = col.box(); box.label(text="コンポジターモード:")
        row = box.row(align=True); current_mode = shading.use_compositor
        op_always = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Always", depress=current_mode == 'ALWAYS'); op_always.mode = 'ALWAYS'
        op_camera = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Camera", depress=current_mode == 'CAMERA'); op_camera.mode = 'CAMERA'
        op_disabled = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Disabled", depress=current_mode == 'DISABLED'); op_disabled.mode = 'DISABLED'
class ZIONAD_PT_MaterialPanel(Panel):
    bl_label = "オブジェクト調整"; bl_parent_id = f"{PREFIX}_PT_base_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 1
    def draw(self, context):
        layout = self.layout; obj = context.object
        if not obj or obj.type != 'MESH': layout.label(text="メッシュオブジェクトを選択", icon='INFO'); return
        if not obj.active_material: layout.operator(ZIONAD_GB_OT_InitializeSettings.bl_idname, text="マテリアルを作成して開始", icon='PLAY'); return
        props = context.scene.zionad_gb_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True); row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_GB_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        box = layout.box(); box.label(text="基本色 / 発光")
        draw_property_row(box, "color", "ベース/発光色"); draw_property_row(box, "hue", "色相")
        draw_property_row(box, "brightness", "明度"); draw_property_row(box, "saturation", "彩度")
        draw_property_row(box, "emission_strength", "発光強度"); draw_property_row(box, "transparency", "透明度")
        box.prop(props, "sync_base_and_emission_color")
        box = layout.box(); box.label(text="個別ブルーム (マテリアル)"); box.prop(props, "use_per_object_bloom")
        sub = box.column(align=True); sub.enabled = props.use_per_object_bloom
        draw_property_row(sub, "per_object_bloom_falloff", "広がり"); draw_property_row(sub, "per_object_bloom_intensity", "強度")
class ZIONAD_PT_SceneBloomPanel(Panel):
    bl_label = "シーンブルーム (EEVEE)"; bl_parent_id = f"{PREFIX}_PT_base_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 2
    @classmethod
    def poll(cls, context): return context.scene.render.engine == EEVEE_ENGINE_ID
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_gb_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True); row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_GB_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        box = layout.box(); box.prop(props, "use_scene_bloom")
        sub = box.column(align=True); sub.enabled = props.use_scene_bloom
        draw_property_row(sub, "scene_bloom_threshold", "しきい値"); draw_property_row(sub, "scene_bloom_size", "サイズ"); draw_property_row(sub, "scene_bloom_mix", "ミックス")

# --- ▼▼▼ ここからFixed Camera & WorldのUIパネル群 (統合版) ▼▼▼ ---

# 新しい親パネル
class ZIONAD_PT_CameraWorld_BasePanel(Panel):
    bl_label = "カメラとワールド制御"
    bl_idname = f"{PREFIX}_PT_cam_world_base"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0 # メインコントロールのすぐ下に配置
    def draw_header(self, context): self.layout.label(text="", icon='WORLD')
    def draw(self, context):
        self.layout.label(text="カメラとワールドの設定を行います。")

# 以下、Fixed Camera & World由来のパネルを子パネルとして設定
class ZIONAD_FCW_PT_CameraSetupPanel(Panel):
    bl_label = "1. カメラ設定"; bl_idname = f"{PREFIX}_PT_fcw_setup"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_fcw_cam_props; box = layout.box(); col = box.column(); col.prop(props, "camera_obj", text="カメラ")
        if props.camera_obj: row = col.row(align=True); row.operator(f"{PREFIX}.fcw_sync_cam", icon='UV_SYNC_SELECT'); row.operator(f"{PREFIX}.fcw_unlink_obj", icon='X')
        else: col.label(text="カメラを選択してください", icon='ERROR'); col.operator(f"{PREFIX}.fcw_create_cam", text=f"'{DEDICATED_CAMERA_NAME}' を作成/選択", icon='ADD')
        col.separator(); box.prop(props, "camera_preset", text="色プリセット"); box.prop(props, "camera_color", text="カラー"); box.operator(f"{PREFIX}.fcw_apply_cam_color", text="ビューポート色を適用")
class ZIONAD_FCW_PT_PositionPanel(Panel):
    bl_label = "2. カメラ位置 (固定)"; bl_idname = f"{PREFIX}_PT_fcw_position"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_fcw_cam_props; box = layout.box(); col = box.column(align=True); row = col.row(align=True)
        row.label(text="固定位置"); op = row.operator(f"{PREFIX}.fcw_reset_prop", text="", icon='LOOP_BACK'); op.targets.add().name = "location"
        col.prop(props, "fixed_location", text=""); col.operator(f"{PREFIX}.fcw_set_loc_view", icon='OBJECT_ORIGIN')
class ZIONAD_FCW_PT_AimingPanel(Panel):
    bl_label = "3. カメラ視線制御"; bl_idname = f"{PREFIX}_PT_fcw_aiming"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout, props = self.layout, context.scene.zionad_fcw_cam_props; box_aim = layout.box(); col_aim = box_aim.column(align=True); row_aim = col_aim.row(align=True); row_aim.label(text="注視点")
        op_aim = row_aim.operator(f"{PREFIX}.fcw_reset_prop", text="", icon='LOOP_BACK'); op_aim.targets.add().name = "aim"; col_aim.prop(props, "target_location", text="")
        box_offset = layout.box(); col_offset = box_offset.column(align=True); row_offset = col_offset.row(align=True); row_offset.label(text="視線オフセット (YPR)")
        op_offset = row_offset.operator(f"{PREFIX}.fcw_reset_prop", text="", icon='LOOP_BACK'); op_offset.targets.add().name = "ypr"
        col_offset.prop(props, "offset_yaw"); col_offset.prop(props, "offset_pitch"); col_offset.prop(props, "offset_roll")
class ZIONAD_FCW_PT_LensPanel(Panel):
    bl_label = "4. レンズ設定"; bl_idname = f"{PREFIX}_PT_fcw_lens"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"
    def draw(self, context):
        layout, props = self.layout, context.scene.zionad_fcw_cam_props; box = layout.box(); col = box.column(align=True); row = col.row(align=True)
        row.label(text="レンズとクリップ"); op = row.operator(f"{PREFIX}.fcw_reset_prop", text="", icon='LOOP_BACK'); op.targets.add().name = "clip"
        col.prop(props, "lens_focal_length"); row = col.row(align=True); row.label(text="水平視野角:"); row.label(text=props.info_horizontal_fov); col.label(text="FOVプリセット:")
        row = col.row(align=True); col1, col2 = row.column(align=True), row.column(align=True)
        for i, fov in enumerate(FOV_PRESETS): op = (col1 if i % 2 == 0 else col2).operator(f"{PREFIX}.fcw_set_fov", text=f"{fov}°"); op.fov = fov
        col.separator(); row = col.row(align=True); row.prop(props, "clip_start"); row.prop(props, "clip_end")
class ZIONAD_FCW_PT_CameraDisplayPanel(Panel):
    bl_label = "Camera Display & Render"; bl_idname = f"{PREFIX}_PT_fcw_cam_display"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout, scene, cam = self.layout, context.scene, context.scene.camera; box_render = layout.box(); box_render.label(text="Render Engine", icon='SCENE'); box_render.prop(scene.render, "engine", expand=True); layout.separator()
        if not cam or not isinstance(cam.data, bpy.types.Camera): layout.box().label(text="シーンにアクティブなカメラがありません", icon='ERROR'); return
        cam_data = cam.data; overlay = context.space_data.overlay if context.space_data and hasattr(context.space_data, 'overlay') else None; layout.label(text="Active Camera: " + cam.name, icon='CAMERA_DATA'); box_passepartout = layout.box(); box_passepartout.label(text="Passepartout", icon='MOD_MASK'); col_passepartout = box_passepartout.column(align=True); col_passepartout.prop(cam_data, "show_passepartout", text="Enable"); row_passepartout = col_passepartout.row(); row_passepartout.enabled = cam_data.show_passepartout; row_passepartout.prop(cam_data, "passepartout_alpha", text="Opacity"); layout.separator(); box_display = layout.box(); box_display.label(text="Viewport Display", icon='OVERLAY');
        if not overlay: box_display.label(text="3D Viewport only", icon='INFO'); return
        box_display.prop(overlay, "show_overlays", text="Viewport Overlays"); col_overlay_options = box_display.column(); col_overlay_options.enabled = overlay.show_overlays; col_overlay_options.prop(overlay, "show_extras", text="Extras"); col_details = col_overlay_options.column(); col_details.enabled = overlay.show_extras; col_details.prop(overlay, "show_text", text="Text Info"); col_details.prop(cam_data, "show_name", text="Name"); col_details.prop(cam_data, "show_limits", text="Limits")
class ZIONAD_FCW_PT_WorldControlPanel(Panel):
    bl_label = "World Control"; bl_idname = f"{PREFIX}_PT_fcw_world"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout, scene, props = self.layout, context.scene, context.scene.zionad_fcw_world_props; world, nodes, _ = get_world_nodes(context, create=False)
        if not world or not world.use_nodes or not nodes:
            col = layout.column(align=True)
            if not world: col.label(text="No World in Scene", icon='ERROR'); col.operator("world.new", text="Create New World")
            else: col.label(text="Enable Nodes in World"); col.prop(world, "use_nodes", text="Use Nodes")
            return
        box_mode = layout.box(); box_mode.label(text="Background Mode", icon='WORLD'); box_mode.prop(props, "background_mode", expand=True); layout.separator()
        if props.background_mode == 'HDRI':
            box_env = layout.box(); box_env.label(text="Environment Texture (HDRI)", icon='IMAGE_DATA'); col_list = box_env.column(align=True); col_list.label(text="HDRI Presets:")
            for i, path in enumerate(HDRI_PATHS): op = col_list.operator(f"{PREFIX}.fcw_load_hdri", text=os.path.basename(path), depress=(props.hdri_list_index == i)); op.hdri_index = i
            box_env.separator(); env_node = find_node(nodes, 'ShaderNodeTexEnvironment', 'Environment_Texture')
            if env_node:
                box_env.template_ID(env_node, "image", open="image.open", text="Select HDRI"); mapping_node = find_node(nodes, 'ShaderNodeMapping', 'Mapping')
                if mapping_node:
                    box_transform = box_env.box(); box_transform.label(text="Transform", icon='OBJECT_DATA'); col = box_transform.column(align=True)
                    for prop_name in ['Location', 'Rotation', 'Scale']:
                        row = col.row(align=True); split = row.split(factor=0.8, align=True); split.prop(mapping_node.inputs[prop_name], "default_value", text=prop_name)
                        op = split.operator(f"{PREFIX}.fcw_reset_trans", text="", icon='FILE_REFRESH'); op.property_to_reset = prop_name
        elif props.background_mode == 'SKY':
            box_sky = layout.box(); box_sky.label(text="Sky Texture", icon='WORLD_DATA'); sky_node = find_node(nodes, 'ShaderNodeTexSky', 'Sky_Texture')
            if sky_node:
                col_sky = box_sky.column(align=True); col_sky.prop(sky_node, "sky_type", text="Sky Type")
                # 各Sky Typeのプロパティを描画
class ZIONAD_FCW_PT_InfoPanel(Panel):
    bl_label = "カメラ情報"; bl_idname = f"{PREFIX}_PT_fcw_info"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props = self.layout, context.scene.zionad_fcw_cam_props; col = layout.column(align=True); row = col.row(align=True); row.label(text="焦点距離:"); row.label(text=props.info_focal_length); row = col.row(align=True); row.label(text="水平視野角:"); row.label(text=props.info_horizontal_fov); col.separator(); row = col.row(align=True); row.label(text="カメラ位置:"); row.label(text=props.info_camera_location); row = col.row(align=True); row.label(text="注視点:"); row.label(text=props.info_target_location); row = col.row(align=True); row.label(text="注視点までの距離:"); row.label(text=props.info_distance_to_target); row = col.row(align=True); row.label(text="注視点での横幅:"); row.label(text=props.info_viewable_width); col.separator(); row = col.row(align=True); row.label(text="クリップ範囲:"); row.label(text=props.info_clip_setting); col.separator(); col.prop(props, "info_precision", text="表示桁数"); col.operator(f"{PREFIX}.fcw_copy_info", text="全情報をコピー", icon='COPY_ID')
class ZIONAD_FCW_PT_GridPanel(Panel):
    bl_label = "Grid Color"; bl_idname = f"{PREFIX}_PT_fcw_grid"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props, theme = self.layout, context.scene.zionad_fcw_grid_props, bpy.context.preferences.themes[0]; layout.label(text=f"Current: {tuple(round(c, 3) for c in theme.view_3d.grid)}"); layout.operator(f"{PREFIX}.fcw_copy_grid_color", text="Copy Grid Color"); layout.separator(); layout.prop(props, "grid_preset"); layout.prop(props, "grid_color"); layout.operator(f"{PREFIX}.fcw_apply_grid_color", text="Apply Grid Color")
class ZIONAD_FCW_PT_WirePanel(Panel):
    bl_label = "Wire Color"; bl_idname = f"{PREFIX}_PT_fcw_wire"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_parent_id = f"{PREFIX}_PT_cam_world_base"; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): layout, props, theme = self.layout, context.scene.zionad_fcw_wire_props, bpy.context.preferences.themes[0]; layout.label(text=f"Current: {tuple(round(c, 3) for c in theme.view_3d.wire)}"); layout.operator(f"{PREFIX}.fcw_copy_wire_color", text="Copy Wire Color"); layout.separator(); layout.prop(props, "wire_preset"); layout.prop(props, "wire_color"); layout.operator(f"{PREFIX}.fcw_apply_wire_color", text="Apply Wire Color")

# --- ▲▲▲ Fixed Camera & WorldのUIパネル群 ここまで ▲▲▲ ---

# --- 共通パネル (リンク、削除など) ---
class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集 (Links)"; bl_idname = f"{PREFIX}_PT_links_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 10; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        def draw_links(link_list):
            for link in link_list: op = layout.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL'); op.url = link["url"]
        box = layout.box(); box.label(text="glare bloom ドキュメント:"); draw_links(GB_ADDON_LINKS)
        box = layout.box(); box.label(text="カメラ/ワールド ドキュメント:"); draw_links(FCW_ADDON_LINKS)
        box = layout.box(); box.label(text="更新情報 / 目次:"); draw_links(GB_NEW_DOC_LINKS)
        box = layout.box(); box.label(text="過去のドキュメント:"); draw_links(GB_DOC_LINKS)
        box = layout.box(); box.label(text="関連リンク / SNS:"); draw_links(GB_SOCIAL_LINKS)
class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"; bl_idname = f"{PREFIX}_PT_remove_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order = 11; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): self.layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="このパネルを登録解除", icon='CANCEL')


# ===================================================================
# 登録・解除処理 (統合)
# ===================================================================

all_classes = (
    # PropertyGroups
    ZIONAD_GB_ToolProperties, ZIONAD_FCW_ThemeGridProperties, ZIONAD_FCW_ThemeWireProperties,
    ZIONAD_FCW_TargetProperty, ZIONAD_FCW_CameraProperties, ZIONAD_FCW_WorldProperties,
    # Common Operators
    ZIONAD_OT_OpenURL, ZIONAD_OT_RemoveAddon,
    # glare bloom Operators
    ZIONAD_GB_OT_InitializeSettings, ZIONAD_GB_OT_FinalizeAllChanges, ZIONAD_GB_OT_ResetProperty,
    ZIONAD_OT_SetRenderEngine, ZIONAD_OT_ToggleCompositorDisplay, ZIONAD_OT_SetCompositorMode,
    # Fixed Camera & World Operators
    ZIONAD_FCW_OT_ApplyCameraColor, ZIONAD_FCW_OT_GridApplyColor, ZIONAD_FCW_OT_GridCopyColor,
    ZIONAD_FCW_OT_CreateDedicatedCamera, ZIONAD_FCW_OT_SyncWithCamera, ZIONAD_FCW_OT_UnlinkObject,
    ZIONAD_FCW_OT_ResetProperty, ZIONAD_FCW_OT_SetFOV, ZIONAD_FCW_OT_CopyAllInfo,
    ZIONAD_FCW_OT_WireApplyColor, ZIONAD_FCW_OT_WireCopyColor, ZIONAD_FCW_OT_SetFixedLocationFromView,
    ZIONAD_FCW_OT_LoadHdriFromList, ZIONAD_FCW_OT_ResetTransform,
    # Panels
    ZIONAD_PT_BasePanel, ZIONAD_PT_MaterialPanel, ZIONAD_PT_SceneBloomPanel,
    ZIONAD_PT_CameraWorld_BasePanel, # 新しい親パネル
    ZIONAD_FCW_PT_CameraSetupPanel, ZIONAD_FCW_PT_PositionPanel, ZIONAD_FCW_PT_AimingPanel,
    ZIONAD_FCW_PT_LensPanel, ZIONAD_FCW_PT_CameraDisplayPanel, ZIONAD_FCW_PT_WorldControlPanel,
    ZIONAD_FCW_PT_InfoPanel, ZIONAD_FCW_PT_GridPanel, ZIONAD_FCW_PT_WirePanel,
    ZIONAD_PT_LinksPanel, ZIONAD_PT_RemovePanel,
)

def fcw_initial_setup():
    if bpy.context.scene.world and bpy.context.scene.world.use_nodes and hasattr(bpy.context.scene, 'zionad_fcw_world_props'):
        props = bpy.context.scene.zionad_fcw_world_props; nodes = bpy.context.scene.world.node_tree.nodes
        background_node = find_node(nodes, 'ShaderNodeBackground', 'Background')
        if background_node and background_node.inputs['Color'].is_linked:
            source_node = background_node.inputs['Color'].links[0].from_node
            if source_node.type == 'TEX_SKY': props.background_mode = 'SKY'
            else: props.background_mode = 'HDRI';
        update_background_mode(props, bpy.context)
    return None

def register():
    for cls in all_classes:
        bpy.utils.register_class(cls)
    # glare bloom properties
    bpy.types.Scene.zionad_gb_props = PointerProperty(type=ZIONAD_GB_ToolProperties)
    bpy.types.Scene.zionad_is_loading = BoolProperty(default=False)
    # Fixed Camera & World properties
    bpy.types.Scene.zionad_fcw_cam_props = PointerProperty(type=ZIONAD_FCW_CameraProperties)
    bpy.types.Scene.zionad_fcw_grid_props = PointerProperty(type=ZIONAD_FCW_ThemeGridProperties)
    bpy.types.Scene.zionad_fcw_wire_props = PointerProperty(type=ZIONAD_FCW_ThemeWireProperties)
    bpy.types.Scene.zionad_fcw_world_props = PointerProperty(type=ZIONAD_FCW_WorldProperties)
    # Handlers and Timers
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    if not bpy.app.timers.is_registered(fcw_initial_setup): bpy.app.timers.register(fcw_initial_setup, first_interval=0.1)

def unregister():
    # Handlers and Timers
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    global _update_timer
    if _update_timer and bpy.app.timers.is_registered(reset_update_flag): bpy.app.timers.unregister(reset_update_flag)
    if bpy.app.timers.is_registered(fcw_initial_setup): bpy.app.timers.unregister(fcw_initial_setup)
    # Properties
    for prop_name in ['zionad_gb_props', 'zionad_is_loading', 'zionad_fcw_cam_props', 'zionad_fcw_grid_props', 'zionad_fcw_wire_props', 'zionad_fcw_world_props']:
        if hasattr(bpy.types.Scene, prop_name):
            try: delattr(bpy.types.Scene, prop_name)
            except (AttributeError, RuntimeError): pass
    # Classes
    for cls in reversed(all_classes):
        if hasattr(bpy.utils, "unregister_class"):
            try: bpy.utils.unregister_class(cls)
            except RuntimeError: pass

if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()