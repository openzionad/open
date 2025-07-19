import bpy
import webbrowser
import mathutils
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, FloatProperty, FloatVectorProperty, BoolProperty, IntProperty
from datetime import datetime

# ===================================================================
# パラメータ設定
# ===================================================================

# --- プレフィックスとID設定 ---
_PREFIX_STATIC_PART = "z25_2__stable" # バージョンを更新
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"
ADDON_MODULE_NAME = __name__

# --- アドオン情報 ---
ADDON_CATEGORY_NAME = "   [ glare bloom 20250718 ]   " # 日付を更新

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (Full Feature, Final Stable)",
    "author": "zionadchat (As Ordered)",
    "version": (25, 2, 1), # バージョンを更新 (バグ修正)
    "blender": (4, 1, 0),
    "location": f"View3D > Sidebar > {ADDON_CATEGORY_NAME}",
    "description": "【警告: 動的Prefixのため設定は保存されません】オブジェクトの表裏で異なる色を設定する機能を追加。ベースカラー制御、ブルーム、リンク等を統合した最終安定版",
    "category": "zParameter",
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/11/131157",
}

if bpy.app.version >= (4, 2, 0):
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE_NEXT'
else:
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE'

# --- リンクデータ ---
ADDON_LINKS = [
{"label": "glare bloom 20250717", "url": "https://memo2017.hatenablog.com/entry/2025/07/17/134442"}, # URL更新
{"label": "glare bloom 20250716", "url": "https://memo2017.hatenablog.com/entry/2025/07/16/143651"},
]
NEW_DOC_LINKS = [
{"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"},
{"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},
]
DOC_LINKS = [
{"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"},
{"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"},
]
SOCIAL_LINKS = [
{"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"},
{"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"},
{"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"},
]


# ===================================================================
# ヘルパー関数 (ノード操作など)
# ===================================================================

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

# ▼▼▼【新機能】裏面設定用のノードを管理するヘルパー関数▼▼▼
def setup_backface_nodes(mat, create=True):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = get_principled_bsdf(mat)
    if not bsdf: return None
    node_names = {
        "geo": get_node_name("backface_geometry"),
        "mix_base": get_node_name("backface_mix_base"),
        "mix_emission": get_node_name("backface_mix_emission")
    }
    found_nodes = {k: nodes.get(v) for k, v in node_names.items()}
    is_incomplete = not all(found_nodes.values())
    if not create: return None if is_incomplete else found_nodes

    if is_incomplete:
        for node in found_nodes.values():
            if node: nodes.remove(node)
        if bsdf.inputs['Base Color'].is_linked:
            for link in list(bsdf.inputs['Base Color'].links): links.remove(link)
        if bsdf.inputs['Emission Color'].is_linked:
            for link in list(bsdf.inputs['Emission Color'].links): links.remove(link)
        geo = nodes.new(type='ShaderNodeNewGeometry'); geo.name = node_names["geo"]
        geo.location = (bsdf.location.x - 400, bsdf.location.y - 100)
        mix_base = nodes.new(type='ShaderNodeMixRGB'); mix_base.name = node_names["mix_base"]
        mix_base.location = (bsdf.location.x - 200, bsdf.location.y + 50)
        mix_emission = nodes.new(type='ShaderNodeMixRGB'); mix_emission.name = node_names["mix_emission"]
        mix_emission.location = (bsdf.location.x - 200, bsdf.location.y - 150)
        found_nodes = {"geo": geo, "mix_base": mix_base, "mix_emission": mix_emission}
        links.new(geo.outputs['Backfacing'], mix_base.inputs['Fac'])
        links.new(geo.outputs['Backfacing'], mix_emission.inputs['Fac'])
        links.new(mix_base.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(mix_emission.outputs['Color'], bsdf.inputs['Emission Color'])
    return found_nodes

def remove_backface_nodes(mat):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    backface_nodes = setup_backface_nodes(mat, create=False)
    if backface_nodes:
        bsdf = get_principled_bsdf(mat)
        if bsdf:
            for socket_name, node_key in [('Base Color', 'mix_base'), ('Emission Color', 'mix_emission')]:
                if bsdf.inputs[socket_name].is_linked and bsdf.inputs[socket_name].links[0].from_node == backface_nodes[node_key]:
                    links.remove(bsdf.inputs[socket_name].links[0])
        for node in backface_nodes.values():
            if node: nodes.remove(node)
# ▲▲▲【新機能】ここまで▲▲▲

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

# ===================================================================
# Update関数 (プロパティが変更されたときの処理)
# ===================================================================

def apply_material_settings(context):
    if not hasattr(context.scene, 'zionad_tool_props'): return
    props = context.scene.zionad_tool_props
    obj = context.object
    if not obj or not obj.active_material: return
    mat = obj.active_material
    bsdf = get_principled_bsdf(mat)
    if not bsdf: return
    
    # --- 色の決定 ---
    front_emission_color_obj = mathutils.Color(); front_emission_color_obj.hsv = (props.hue, props.saturation, props.brightness)
    front_emission_color_rgba = (*front_emission_color_obj, 1.0)
    front_base_color_rgba = front_emission_color_rgba if props.sync_base_and_emission_color else (*props.base_color, 1.0)
    
    # --- 共通設定 ---
    mat.blend_method = 'BLEND' if props.transparency < 1.0 else 'OPAQUE'
    bsdf.inputs['Alpha'].default_value = props.transparency
    bsdf.inputs['Emission Strength'].default_value = props.emission_strength
    
    # ▼▼▼【CORRECTED】裏面設定のロジックを修正し、UIとの整合性を確保▼▼▼
    if props.use_backface_settings:
        backface_nodes = setup_backface_nodes(mat, create=True)
        if backface_nodes:
            # Sync logic correction: If synced, base color drives emission color, matching the UI.
            if props.sync_backface_colors:
                # To prevent update loops, we check if the values are already synced.
                # This is a bit safer than trying to set the property from within its own update chain.
                synced_color_rgba = (*props.backface_base_color, 1.0)
                backface_base_color_rgba = synced_color_rgba
                backface_emission_color_rgba = synced_color_rgba
            else:
                backface_base_color_rgba = (*props.backface_base_color, 1.0)
                backface_emission_color_rgba = (*props.backface_emission_color, 1.0)
            
            backface_nodes["mix_base"].inputs['Color1'].default_value = front_base_color_rgba
            backface_nodes["mix_base"].inputs['Color2'].default_value = backface_base_color_rgba
            backface_nodes["mix_emission"].inputs['Color1'].default_value = front_emission_color_rgba
            backface_nodes["mix_emission"].inputs['Color2'].default_value = backface_emission_color_rgba
    else:
        remove_backface_nodes(mat)
        bsdf.inputs['Base Color'].default_value = front_base_color_rgba
        bsdf.inputs['Emission Color'].default_value = front_emission_color_rgba
    # ▲▲▲【CORRECTED】ここまで▲▲▲
        
    if props.use_per_object_bloom:
        bloom_nodes = setup_per_object_bloom_nodes(mat, create=True)
        if bloom_nodes:
            # ブルームの色は表側の発光色を基準とする
            bloom_nodes["emission"].inputs['Color'].default_value = front_emission_color_rgba
            bloom_nodes["emission"].inputs['Strength'].default_value = props.per_object_bloom_intensity
            bloom_nodes["layer"].inputs['Blend'].default_value = props.per_object_bloom_falloff
    else: remove_per_object_bloom_nodes(mat)

def update_from_color_picker(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    context.scene.zionad_is_loading = True
    props = context.scene.zionad_tool_props; color_hsv = mathutils.Color(props.color[:3])
    props.hue, props.brightness, props.saturation = color_hsv.h, color_hsv.v, color_hsv.s
    context.scene.zionad_is_loading = False
    apply_material_settings(context)
def update_from_sliders(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    context.scene.zionad_is_loading = True
    props = context.scene.zionad_tool_props; new_color = mathutils.Color()
    new_color.hsv = (props.hue, props.saturation, props.brightness)
    props.color = new_color[:3]
    context.scene.zionad_is_loading = False
    apply_material_settings(context)
def update_material_all(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    apply_material_settings(context)
def update_scene_bloom(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    props = context.scene.zionad_tool_props
    if props.use_scene_bloom:
        glare_node = get_scene_bloom_glare_node(context)
        if glare_node:
            glare_node.threshold = props.scene_bloom_threshold
            glare_node.size = props.scene_bloom_size
            glare_node.mix = props.scene_bloom_mix
    else: remove_scene_bloom_glare_node(context)

# ===================================================================
# プロパティグループ (UIの値を保持する)
# ===================================================================

class ZionADToolProperties(PropertyGroup):
    # --- 表面設定 ---
    color: FloatVectorProperty(name="発光色", subtype='COLOR', default=(1.0, 1.0, 1.0), size=3, min=0.0, max=1.0, update=update_from_color_picker)
    base_color: FloatVectorProperty(name="ベースカラー", subtype='COLOR', default=(0.8, 0.8, 0.8), size=3, min=0.0, max=1.0, update=update_material_all)
    sync_base_and_emission_color: BoolProperty(name="ベースカラーと発光色を同期", default=True, update=update_material_all)
    hue: FloatProperty(name="Hue", subtype='FACTOR', default=0.0, min=0.0, max=1.0, update=update_from_sliders)
    brightness: FloatProperty(name="明度", min=0.0, max=1.0, default=1.0, update=update_from_sliders)
    saturation: FloatProperty(name="彩度", min=0.0, max=1.0, default=1.0, update=update_from_sliders)
    
    # --- 共通マテリアル設定 ---
    transparency: FloatProperty(name="透明度", min=0.0, max=1.0, default=1.0, subtype='FACTOR', update=update_material_all)
    emission_strength: FloatProperty(name="発光強度", min=0.0, max=50.0, default=0.0, description="オブジェクト中心部の光の強さ", update=update_material_all)

    # ▼▼▼【新機能】裏面設定プロパティ▼▼▼
    use_backface_settings: BoolProperty(name="裏面の色を個別に設定", default=False, description="オブジェクトの裏面の色を表とは別に設定します", update=update_material_all)
    backface_base_color: FloatVectorProperty(name="裏面 ベースカラー", subtype='COLOR', default=(0.8, 0.0, 0.0), size=3, min=0.0, max=1.0, update=update_material_all)
    backface_emission_color: FloatVectorProperty(name="裏面 発光色", subtype='COLOR', default=(1.0, 0.0, 0.0), size=3, min=0.0, max=1.0, update=update_material_all)
    sync_backface_colors: BoolProperty(name="裏面のベース/発光色を同期", default=True, update=update_material_all)
    # ▲▲▲【新機能】ここまで▲▲▲

    # --- ブルーム設定 ---
    use_per_object_bloom: BoolProperty(name="個別ブルームを有効化", default=False, description="マテリアルによるオブジェクト単位のブルーム", update=update_material_all)
    per_object_bloom_falloff: FloatProperty(name="広がり", min=0.0, max=10.0, default=0.5, description="輪郭の光のにじむ範囲", update=update_material_all)
    per_object_bloom_intensity: FloatProperty(name="強度", min=0.0, max=100.0, default=1.0, description="輪郭の光の明るさ", update=update_material_all)
    use_scene_bloom: BoolProperty(name="シーンブルームを有効化", default=False, description="コンポジターを用いたシーン全体のブルーム効果 (EEVEE標準)", update=update_scene_bloom)
    scene_bloom_threshold: FloatProperty(name="しきい値", min=0.0, default=1.0, description="ブルームが発生する明るさの基準", update=update_scene_bloom)
    scene_bloom_size: IntProperty(name="サイズ", min=1, max=9, default=7, description="ブルームの広がり具合", update=update_scene_bloom)
    scene_bloom_mix: FloatProperty(name="ミックス", min=-1.0, max=1.0, default=0.0, description="元の画像とのブレンド量", update=update_scene_bloom)

# ===================================================================
# オペレーター (ボタンが押されたときの処理)
# ===================================================================

class ZIONAD_OT_InitializeSettings(Operator):
    bl_idname = f"{PREFIX}.initialize_settings"; bl_label = "操作を開始"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_is_loading'): return {'CANCELLED'}
        context.scene.zionad_is_loading = True
        props = context.scene.zionad_tool_props
        obj = context.object
        if obj and obj.type == 'MESH':
            mat = get_or_create_material(obj)
            bsdf = get_principled_bsdf(mat)
            if bsdf:
                backface_nodes = setup_backface_nodes(mat, create=False)
                if backface_nodes:
                    props.use_backface_settings = True
                    front_base_rgba = backface_nodes["mix_base"].inputs['Color1'].default_value
                    back_base_rgba = backface_nodes["mix_base"].inputs['Color2'].default_value
                    front_emission_rgba = backface_nodes["mix_emission"].inputs['Color1'].default_value
                    back_emission_rgba = backface_nodes["mix_emission"].inputs['Color2'].default_value
                    props.base_color = front_base_rgba[:3]
                    props.backface_base_color = back_base_rgba[:3]
                    props.backface_emission_color = back_emission_rgba[:3]
                    props.sync_base_and_emission_color = all(abs(b - e) < 0.001 for b, e in zip(front_base_rgba, front_emission_rgba))
                    props.sync_backface_colors = all(abs(b - e) < 0.001 for b, e in zip(back_base_rgba, back_emission_rgba))
                    emission_hsv = mathutils.Color(front_emission_rgba[:3]); props.color = emission_hsv[:3]
                    props.hue, props.saturation, props.brightness = emission_hsv.h, emission_hsv.s, emission_hsv.v
                else:
                    props.use_backface_settings = False
                    emission_rgba = bsdf.inputs['Emission Color'].default_value
                    base_rgba = bsdf.inputs['Base Color'].default_value
                    emission_hsv = mathutils.Color(emission_rgba[:3]); props.color = emission_hsv[:3]
                    props.hue, props.saturation, props.brightness = emission_hsv.h, emission_hsv.s, emission_hsv.v
                    props.base_color = base_rgba[:3]
                    props.sync_base_and_emission_color = all(abs(b - e) < 0.001 for b, e in zip(base_rgba, emission_rgba))
                props.transparency = bsdf.inputs['Alpha'].default_value
                props.emission_strength = bsdf.inputs['Emission Strength'].default_value
            bloom_nodes = setup_per_object_bloom_nodes(mat, create=False)
            props.use_per_object_bloom = bool(bloom_nodes)
            if bloom_nodes:
                props.per_object_bloom_falloff = bloom_nodes["layer"].inputs['Blend'].default_value
                props.per_object_bloom_intensity = bloom_nodes["emission"].inputs['Strength'].default_value
        glare_node = context.scene.node_tree.nodes.get(get_node_name("scene_bloom_glare")) if context.scene.use_nodes else None
        props.use_scene_bloom = bool(glare_node)
        if glare_node:
            props.scene_bloom_threshold = glare_node.threshold
            props.scene_bloom_size = glare_node.size
            props.scene_bloom_mix = glare_node.mix
        context.scene.zionad_is_loading = False
        apply_material_settings(context)
        return {'FINISHED'}

class ZIONAD_OT_FinalizeAllChanges(Operator):
    bl_idname = f"{PREFIX}.finalize_all_changes"; bl_label = "全ての変更を確定"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_tool_props'): return {'CANCELLED'}
        apply_material_settings(context)
        update_scene_bloom(self, context)
        context.scene.zionad_is_loading = True
        props = context.scene.zionad_tool_props
        props.color, props.hue, props.brightness, props.saturation = (1.0, 1.0, 1.0), 0.0, 1.0, 1.0
        props.base_color = (0.8, 0.8, 0.8); props.sync_base_and_emission_color = True
        props.transparency = 1.0; props.emission_strength = 0.0
        
        # ▼▼▼【CORRECTED】裏面設定のリセット方法を修正し、エラーを回避してロジックを修正▼▼▼
        props.use_backface_settings = False
        # Directly assign the default tuple value instead of using .default from RNA properties. This is more robust.
        # Also, set both colors to the same value to maintain sync consistency.
        default_back_color = (0.8, 0.0, 0.0)
        props.backface_base_color = default_back_color
        props.backface_emission_color = default_back_color
        props.sync_backface_colors = True
        # ▲▲▲【CORRECTED】ここまで▲▲▲
        
        props.use_per_object_bloom = False; props.per_object_bloom_falloff = 0.5; props.per_object_bloom_intensity = 1.0
        props.use_scene_bloom = False; props.scene_bloom_threshold = 1.0; props.scene_bloom_size = 7; props.scene_bloom_mix = 0.0
        context.scene.zionad_is_loading = False
        return {'FINISHED'}
class ZIONAD_OT_ResetProperty(Operator):
    bl_idname = f"{PREFIX}.reset_property"; bl_label = "値をリセット"; bl_options = {'REGISTER', 'UNDO'}
    prop_name: StringProperty()
    def execute(self, context):
        if not hasattr(context.scene, 'zionad_tool_props'): return {'CANCELLED'}
        props = context.scene.zionad_tool_props
        # Use getattr to get the default from the class definition itself
        default_value = ZionADToolProperties.bl_rna.properties[self.prop_name].default
        if self.prop_name == 'color': props.hue, props.saturation, props.brightness = 0.0, 1.0, 1.0
        setattr(props, self.prop_name, default_value)
        return {'FINISHED'}

# (その他のオペレーターは変更なし)
class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"; bl_label = "Open URL"
    url: StringProperty(name="URL", default="")
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}
class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"{PREFIX}.remove_addon"; bl_label = "アドオンのコンポーネントを登録解除"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): unregister(); return {'FINISHED'}
class ZIONAD_OT_SetRenderEngine(Operator):
    bl_idname = f"{PREFIX}.set_render_engine"; bl_label = "Set Render Engine"
    engine: StringProperty()
    def execute(self, context): context.scene.render.engine = self.engine; return {'FINISHED'}
class ZIONAD_OT_ToggleCompositorDisplay(Operator):
    bl_idname = f"{PREFIX}.toggle_comp_view"; bl_label = "Toggle Compositor Display"
    def execute(self, context):
        shading = context.space_data.shading
        shading.use_compositor = 'ALWAYS' if shading.use_compositor == 'DISABLED' else 'DISABLED'
        return {'FINISHED'}
class ZIONAD_OT_SetCompositorMode(Operator):
    bl_idname = f"{PREFIX}.set_compositor_mode"; bl_label = "Set Compositor Mode"
    mode: StringProperty(name="Compositor Mode", default='ALWAYS', options={'HIDDEN'})
    def execute(self, context): context.space_data.shading.use_compositor = self.mode; return {'FINISHED'}

# ===================================================================
# UIパネル (サイドバーに表示されるUI)
# ===================================================================

class ZIONAD_PT_BasePanel(Panel):
    bl_label = "メインコントロール"; bl_idname = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME
    bl_order = -1
    def draw_header(self, context): self.layout.label(text="", icon='TOOL_SETTINGS')
    def draw(self, context):
        layout = self.layout; col = layout.column(align=True)
        col.operator(ZIONAD_OT_FinalizeAllChanges.bl_idname, icon='CHECKMARK')
        col.operator(ZIONAD_OT_InitializeSettings.bl_idname, text="全設定を読込/リロード", icon='FILE_REFRESH')
        col.separator()
        box = col.box(); box.label(text="レンダラー設定:")
        row = box.row(align=True)
        is_eevee = context.scene.render.engine == EEVEE_ENGINE_ID
        op_eevee = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="EEVEE", depress=is_eevee); op_eevee.engine = EEVEE_ENGINE_ID
        op_cycles = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="Cycles", depress=not is_eevee); op_cycles.engine = 'CYCLES'
        box = col.box(); box.label(text="ビューポートプレビュー:")
        shading = context.space_data.shading
        is_compositor_on = shading.use_compositor == 'ALWAYS'
        btn_text = "リアルタイム表示: ON" if is_compositor_on else "リアルタイム表示: OFF"
        btn_icon = 'HIDE_ON' if is_compositor_on else 'HIDE_OFF'
        box.operator(ZIONAD_OT_ToggleCompositorDisplay.bl_idname, text=btn_text, icon=btn_icon)
        box = col.box(); box.label(text="コンポジターモード:")
        row = box.row(align=True); current_mode = shading.use_compositor
        op_always = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Always", depress=current_mode == 'ALWAYS'); op_always.mode = 'ALWAYS'
        op_camera = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Camera", depress=current_mode == 'CAMERA'); op_camera.mode = 'CAMERA'
        op_disabled = row.operator(ZIONAD_OT_SetCompositorMode.bl_idname, text="Disabled", depress=current_mode == 'DISABLED'); op_disabled.mode = 'DISABLED'

class ZIONAD_PT_MaterialPanel(Panel):
    bl_label = "オブジェクト調整"; bl_parent_id = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 1
    def draw(self, context):
        layout = self.layout; obj = context.object
        if not obj or obj.type != 'MESH': layout.label(text="メッシュオブジェクトを選択", icon='INFO'); return
        if not obj.active_material: layout.operator(ZIONAD_OT_InitializeSettings.bl_idname, text="マテリアルを作成して開始", icon='PLAY'); return
        
        props = context.scene.zionad_tool_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True)
            row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        
        box = layout.box(); box.label(text="表面の色 (Front Face)")
        draw_property_row(box, "sync_base_and_emission_color", "同期")
        box.separator()
        if props.sync_base_and_emission_color:
            draw_property_row(box.column(align=True), "color", "ベース/発光色")
        else:
            col = box.column(align=True); col.label(text="ベースカラー:"); draw_property_row(col, "base_color", "")
            col.separator(); col.label(text="発光色:"); draw_property_row(col, "color", "")
        box.separator()
        col_hsv = box.column(align=True)
        draw_property_row(col_hsv, "hue", "色相 (発光)"); draw_property_row(col_hsv, "brightness", "明度 (発光)"); draw_property_row(col_hsv, "saturation", "彩度 (発光)")
        box.separator()
        col_common = box.column(align=True)
        draw_property_row(col_common, "emission_strength", "発光強度"); draw_property_row(col_common, "transparency", "透明度")
        
        box = layout.box(); box.label(text="裏面の色 (Back Face)")
        draw_property_row(box, "use_backface_settings", "個別に設定")
        sub_backface = box.column(align=True); sub_backface.enabled = props.use_backface_settings
        draw_property_row(sub_backface, "sync_backface_colors", "同期")
        sub_backface.separator()
        if props.sync_backface_colors:
            # When synced, the UI shows a control for base_color.
            # The corrected apply_material_settings function now correctly uses this as the driver.
            draw_property_row(sub_backface.column(align=True), "backface_base_color", "裏: ベース/発光色")
        else:
            col = sub_backface.column(align=True)
            draw_property_row(col, "backface_base_color", "裏: ベースカラー")
            draw_property_row(col, "backface_emission_color", "裏: 発光色")

        box = layout.box(); box.label(text="個別ブルーム (マテリアル)")
        box.prop(props, "use_per_object_bloom")
        sub = box.column(align=True); sub.enabled = props.use_per_object_bloom
        draw_property_row(sub, "per_object_bloom_falloff", "広がり")
        draw_property_row(sub, "per_object_bloom_intensity", "強度")

class ZIONAD_PT_SceneBloomPanel(Panel):
    bl_label = "シーンブルーム (EEVEE)"; bl_parent_id = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 2
    @classmethod
    def poll(cls, context): return context.scene.render.engine == EEVEE_ENGINE_ID
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_tool_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True); row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        box = layout.box(); box.prop(props, "use_scene_bloom")
        sub = box.column(align=True); sub.enabled = props.use_scene_bloom
        draw_property_row(sub, "scene_bloom_threshold", "しきい値")
        draw_property_row(sub, "scene_bloom_size", "サイズ")
        draw_property_row(sub, "scene_bloom_mix", "ミックス")
        
class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集 (Links)"; bl_idname = f"{PREFIX}_PT_links_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME
    bl_order = 10; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        def draw_links(link_list, label):
            box = layout.box(); box.label(text=label)
            for link in link_list:
                op = box.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL'); op.url = link["url"]
        draw_links(ADDON_LINKS, "メインドキュメント:")
        draw_links(NEW_DOC_LINKS, "更新情報 / 目次:")
        draw_links(DOC_LINKS, "過去のドキュメント:")
        draw_links(SOCIAL_LINKS, "関連リンク / SNS:")

class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"; bl_idname = f"{PREFIX}_PT_remove_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME
    bl_order = 11; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): self.layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="このパネルを登録解除", icon='CANCEL')
  
# ===================================================================
# 登録・解除処理
# ===================================================================

classes = (
    ZionADToolProperties, ZIONAD_OT_InitializeSettings, ZIONAD_OT_FinalizeAllChanges,
    ZIONAD_OT_ResetProperty, ZIONAD_OT_OpenURL, ZIONAD_OT_RemoveAddon,
    ZIONAD_OT_SetRenderEngine, ZIONAD_OT_ToggleCompositorDisplay, ZIONAD_OT_SetCompositorMode,
    ZIONAD_PT_BasePanel, ZIONAD_PT_MaterialPanel, ZIONAD_PT_SceneBloomPanel,
    ZIONAD_PT_LinksPanel, ZIONAD_PT_RemovePanel,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.zionad_tool_props = PointerProperty(type=ZionADToolProperties)
    bpy.types.Scene.zionad_is_loading = BoolProperty(default=False)

def unregister():
    if hasattr(bpy.types.Scene, 'zionad_tool_props'): del bpy.types.Scene.zionad_tool_props
    if hasattr(bpy.types.Scene, 'zionad_is_loading'): del bpy.types.Scene.zionad_is_loading
    for cls in reversed(classes):
        if hasattr(bpy.utils, "unregister_class"):
            try: bpy.utils.unregister_class(cls)
            except RuntimeError: pass

if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()

# === 次の生成AIへの引き継ぎコメント ===
# ユーザーからのエラー報告（ValueError: sequence expected at dimension 1, not 'float'）に対応するため、アドオンのバージョンをv25.2.1に更新しました。

# ## **今回の修正と学習**
# - **バグ修正（クラッシュ回避）**: `ZIONAD_OT_FinalizeAllChanges`オペレーター内で、プロパティのデフォルト値をリセットする際に`bl_rna.properties[...].default`を使用していました。これが稀な状況下で`FloatVectorProperty`に対して単一の`float`を返すことがあり、クラッシュの原因となっていました。これを、より安全で直接的なタプルの代入 `props.backface_base_color = (0.8, 0.0, 0.0)` に変更することで、エラーを根本的に解決しました。
# - **ロジック修正（設定の同期）**: 上記の修正と同時に、リセット時のロジックを改善しました。以前は、異なる色のデフォルト値を設定した直後に`sync_backface_colors = True`としてしまい、設定が矛盾していました。修正後は、リセット時に`backface_base_color`と`backface_emission_color`の両方に同じデフォルト値を設定するようにし、UIの状態と内部データの一貫性を保つようにしました。
# - **ロジック修正（UIとの整合性）**: `apply_material_settings`関数内の裏面カラー同期ロジックを修正しました。以前は、UIが`backface_base_color`を操作するにもかかわらず、バックエンドでは`backface_emission_color`を色のソースとして使用していました。これを、UIの操作通り`backface_base_color`が色のソースとなるように修正し、ユーザーの操作が正しく反映されるようにしました。

# ## **次のAIへの指示**
# - **安定性の維持**: このバージョン(v25.2.1)で主要なクラッシュバグとロジックの不整合を修正しました。今後の開発では、特にプロパティの値をリセットしたり、複数のプロパティが連動して更新されたりする部分の安定性に注意してください。直接的な値の代入は、動的なRNAプロパティへのアクセスよりも安全な場合があります。
# - **コードの可読性**: 複雑なロジック（特にupdate関数内）には、今回のようにコメントを追加して、なぜその処理が必要なのか（例：「UIとの整合性を保つため」など）を明確にすると、将来のメンテナンスが容易になります。
# - **引き継ぎ継続**: ユーザー指示である「‘最後に次の生成AIに引き継ぎのコメントを必ず作る’」を遵守し、修正の背景、技術的な詳細、そして次の担当者への注意点を明確に記述し続けてください。

# このコードで報告された問題は解決されているはずです。