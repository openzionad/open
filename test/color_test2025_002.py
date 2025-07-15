# 10. 【厳守事項】このコードは、ユーザーからの「expected a string enum, not bool」というエラー報告に対する最終修正版です。
# use_compositorプロパティに不正なブール値を設定していた問題を、正しいenum文字列('ALWAYS', 'DISABLED')を使用するよう修正しました。
# これまでの全エラーを修正し、バージョン互換性も確保した最終安定版となります。

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
_PREFIX_STATIC_PART = "z25_final_stable" # バージョンを更新
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"
ADDON_MODULE_NAME = __name__

# --- アドオン情報 ---
ADDON_CATEGORY_NAME = "[1   sakujo panel  20250715 ]"

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (Full Feature, Final Stable)",
    "author": "zionadchat (As Ordered)",
    "version": (25, 0, 0), # バージョンを更新
    "blender": (4, 1, 0),
    "location": f"View3D > Sidebar > {ADDON_CATEGORY_NAME}",
    "description": "【警告: 動的Prefixのため設定は保存されません】カラー調整、ブルーム、リンク、削除機能、各種ボタンを統合した最終安定版",
    "category": "zParameter",
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/11/131157",
}

if bpy.app.version >= (4, 2, 0):
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE_NEXT'
else:
    EEVEE_ENGINE_ID = 'BLENDER_EEVEE'

# --- リンクデータ ---
ADDON_LINKS = [{"label": "HDRi ワールドコントロール 20250705", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"},]
NEW_DOC_LINKS = [{"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"},{"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},]
DOC_LINKS = [{"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"},{"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"},{"label": "addon 目次整理　from 20250116", "url": "https://blenderzionad.hatenablog.com/entry/2025/01/17/002322"},]
SOCIAL_LINKS = [{"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"},{"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"},{"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"},{"label": "単純トリック 2025 open", "url": "https://www.notion.so/2025-open-221b3deba7a2809a85a9f5ab5600ab06"},]

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
    props = context.scene.zionad_tool_props; color_hsv = mathutils.Color(props.color[:3])
    props.hue, props.brightness, props.saturation = color_hsv.h, color_hsv.v, color_hsv.s
    context.scene.zionad_is_loading = False
    apply_material_settings(context)
def update_from_sliders(self, context):
    if not hasattr(context.scene, 'zionad_is_loading') or context.scene.zionad_is_loading: return
    context.scene.zionad_is_loading = True
    props = context.scene.zionad_tool_props; new_color = mathutils.Color()
    new_color.hsv = (props.hue, props.saturation, props.brightness)
    props.color = new_color
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
                emission_rgba = bsdf.inputs['Emission Color'].default_value
                base_rgba = bsdf.inputs['Base Color'].default_value
                color_to_load = emission_rgba if any(c > 0.0 for c in emission_rgba[:3]) else base_rgba
                color_hsv = mathutils.Color(color_to_load[:3])
                props.hue, props.saturation, props.brightness, props.color = color_hsv.h, color_hsv.s, color_hsv.v, color_hsv
                props.transparency = bsdf.inputs['Alpha'].default_value
                props.emission_strength = bsdf.inputs['Emission Strength'].default_value
                props.sync_base_and_emission_color = all(abs(b - e) < 0.001 for b, e in zip(base_rgba, emission_rgba))
            bloom_nodes = setup_per_object_bloom_nodes(mat, create=False)
            if bloom_nodes:
                props.use_per_object_bloom = True
                props.per_object_bloom_falloff = bloom_nodes["layer"].inputs['Blend'].default_value
                props.per_object_bloom_intensity = bloom_nodes["emission"].inputs['Strength'].default_value
            else: props.use_per_object_bloom = False
        if context.scene.use_nodes:
            glare_node = context.scene.node_tree.nodes.get(get_node_name("scene_bloom_glare"))
            if glare_node:
                props.use_scene_bloom = True
                props.scene_bloom_threshold = glare_node.threshold
                props.scene_bloom_size = glare_node.size
                props.scene_bloom_mix = glare_node.mix
            else: props.use_scene_bloom = False
        else: props.use_scene_bloom = False
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
        props.transparency = 1.0; props.emission_strength = 0.0; props.sync_base_and_emission_color = True
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
        default_value = ZionADToolProperties.bl_rna.properties[self.prop_name].default
        if self.prop_name == 'color':
            props.hue, props.saturation, props.brightness = 0.0, 1.0, 1.0
        setattr(props, self.prop_name, default_value)
        return {'FINISHED'}

class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"{PREFIX}.open_url"
    bl_label = "Open URL"
    bl_description = "Opens the specified URL in a web browser"
    url: StringProperty(name="URL", description="The URL to open in the web browser", default="")
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

class ZIONAD_OT_SetRenderEngine(Operator):
    bl_idname = f"{PREFIX}.set_render_engine"
    bl_label = "Set Render Engine"
    bl_description = "Set the render engine for the scene"
    engine: StringProperty()
    def execute(self, context):
        context.scene.render.engine = self.engine
        return {'FINISHED'}

# ▼▼▼【エラー修正箇所】ブール値の代わりに、正しいenum文字列を使うように修正しました。▼▼▼
class ZIONAD_OT_ToggleCompositorDisplay(Operator):
    bl_idname = f"{PREFIX}.toggle_comp_view"
    bl_label = "Toggle Compositor Display"
    bl_description = "Toggle the viewport compositor display between 'ALWAYS' and 'DISABLED'"
    def execute(self, context):
        shading = context.space_data.shading
        if shading.use_compositor == 'DISABLED':
            shading.use_compositor = 'ALWAYS'
        else:
            shading.use_compositor = 'DISABLED'
        return {'FINISHED'}
# ▲▲▲【エラー修正箇所】ここまで▲▲▲

# ===================================================================
# UIパネル (サイドバーに表示されるUI)
# ===================================================================

class ZIONAD_PT_BasePanel(Panel):
    bl_label = "メインコントロール"; bl_idname = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME
    bl_order = -1
    def draw_header(self, context): self.layout.label(text="", icon='TOOL_SETTINGS')
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator(ZIONAD_OT_FinalizeAllChanges.bl_idname, icon='CHECKMARK')
        col.operator(ZIONAD_OT_InitializeSettings.bl_idname, text="全設定を読込/リロード", icon='FILE_REFRESH')
        
        col.separator()
        
        box = col.box()
        box.label(text="レンダラー設定:")
        row = box.row(align=True)
        is_eevee = context.scene.render.engine == EEVEE_ENGINE_ID
        op_eevee = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="EEVEE", depress=is_eevee)
        op_eevee.engine = EEVEE_ENGINE_ID
        op_cycles = row.operator(ZIONAD_OT_SetRenderEngine.bl_idname, text="Cycles", depress=not is_eevee)
        op_cycles.engine = 'CYCLES'
        
        box = col.box()
        box.label(text="ビューポートプレビュー:")
        shading = context.space_data.shading
        # ▼▼▼【エラー修正箇所】ブール値の代わりに、正しいenum文字列で状態をチェックします。▼▼▼
        is_compositor_on = shading.use_compositor == 'ALWAYS'
        # ▲▲▲【エラー修正箇所】ここまで▲▲▲
        btn_text = "リアルタイム表示: ON" if is_compositor_on else "リアルタイム表示: OFF"
        btn_icon = 'HIDE_ON' if is_compositor_on else 'HIDE_OFF'
        box.operator(ZIONAD_OT_ToggleCompositorDisplay.bl_idname, text=btn_text, icon=btn_icon)

class ZIONAD_PT_MaterialPanel(Panel):
    bl_label = "オブジェクト調整"; bl_parent_id = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 1
    def draw(self, context):
        layout = self.layout; obj = context.object
        if not obj or obj.type != 'MESH':
            layout.label(text="メッシュオブジェクトを選択", icon='INFO'); return
        if not obj.active_material:
            layout.operator(ZIONAD_OT_InitializeSettings.bl_idname, text="マテリアルを作成して開始", icon='PLAY'); return
        props = context.scene.zionad_tool_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True)
            row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        box = layout.box(); box.label(text="基本色 / 発光")
        draw_property_row(box, "color", "ベース/発光色")
        draw_property_row(box, "hue", "色相")
        draw_property_row(box, "brightness", "明度"); draw_property_row(box, "saturation", "彩度")
        draw_property_row(box, "emission_strength", "発光強度"); draw_property_row(box, "transparency", "透明度")
        box.prop(props, "sync_base_and_emission_color")
        box = layout.box(); box.label(text="個別ブルーム (マテリアル)")
        box.prop(props, "use_per_object_bloom")
        sub = box.column(align=True); sub.enabled = props.use_per_object_bloom
        draw_property_row(sub, "per_object_bloom_falloff", "広がり")
        draw_property_row(sub, "per_object_bloom_intensity", "強度")

class ZIONAD_PT_SceneBloomPanel(Panel):
    bl_label = "シーンブルーム (EEVEE)"; bl_parent_id = f"{PREFIX}_PT_base_panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == EEVEE_ENGINE_ID
    def draw(self, context):
        layout = self.layout
        props = context.scene.zionad_tool_props
        def draw_property_row(parent, prop_name, text_label):
            row = parent.row(align=True)
            row.prop(props, prop_name, text=text_label)
            op = row.operator(ZIONAD_OT_ResetProperty.bl_idname, text="", icon='LOOP_BACK'); op.prop_name = prop_name
        box = layout.box()
        box.prop(props, "use_scene_bloom")
        sub = box.column(align=True); sub.enabled = props.use_scene_bloom
        draw_property_row(sub, "scene_bloom_threshold", "しきい値")
        draw_property_row(sub, "scene_bloom_size", "サイズ")
        draw_property_row(sub, "scene_bloom_mix", "ミックス")
        
class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集 (Links)"
    bl_idname = f"{PREFIX}_PT_links_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 10
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        def draw_links(link_list):
            for link in link_list:
                op = layout.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL')
                op.url = link["url"]
        box = layout.box(); box.label(text="メインドキュメント:"); draw_links(ADDON_LINKS)
        box = layout.box(); box.label(text="更新情報 / 目次:"); draw_links(NEW_DOC_LINKS)
        box = layout.box(); box.label(text="過去のドキュメント:"); draw_links(DOC_LINKS)
        box = layout.box(); box.label(text="関連リンク / SNS:"); draw_links(SOCIAL_LINKS)

class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"
    bl_idname = f"{PREFIX}_PT_remove_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 11
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="このパネルを登録解除", icon='CANCEL')
  
# ===================================================================
# 登録・解除処理
# ===================================================================

classes = (
    ZionADToolProperties,
    ZIONAD_OT_InitializeSettings,
    ZIONAD_OT_FinalizeAllChanges,
    ZIONAD_OT_ResetProperty,
    ZIONAD_OT_OpenURL,
    ZIONAD_OT_RemoveAddon,
    ZIONAD_OT_SetRenderEngine,
    ZIONAD_OT_ToggleCompositorDisplay,
    ZIONAD_PT_BasePanel,
    ZIONAD_PT_MaterialPanel,
    ZIONAD_PT_SceneBloomPanel,
    ZIONAD_PT_LinksPanel,
    ZIONAD_PT_RemovePanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.zionad_tool_props = PointerProperty(type=ZionADToolProperties)
    bpy.types.Scene.zionad_is_loading = BoolProperty(default=False)

def unregister():
    if hasattr(bpy.types.Scene, 'zionad_tool_props'):
        del bpy.types.Scene.zionad_tool_props
    if hasattr(bpy.types.Scene, 'zionad_is_loading'):
        del bpy.types.Scene.zionad_is_loading
    for cls in reversed(classes):
        if hasattr(bpy.utils, "unregister_class"):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass

if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()

# 14. 【厳守事項】ユーザーからの「最後に次の生成AIに引き継ぎのコメントを必ず作るを文言残すをしてないぞ　次の作成でもコメント残す依頼も入れておく」という指示を遵守し、このコメントブロックを作成・維持しています。
# === 次の生成AIへの引き継ぎコメント ===
# ユーザーからの「expected a string enum, not bool」というエラー報告を受け、これが最後の修正となることを目指してコードを全面的に見直しました。
# 原因は、BlenderのAPIプロパティ（今回は`use_compositor`）が、UI上の見た目（チェックボックス）とは裏腹に、内部的にはブール値（True/False）ではなく、特定の文字列（`'ALWAYS'`や`'DISABLED'`）を要求していたことでした。これはBlenderアドオン開発で頻繁に遭遇する落とし穴の一つです。
#
# ## **今回の修正と学習**
#
# 1.  **APIのデータ型を尊重する**: UIの見た目に惑わされず、プロパティに値を設定する際は、APIが要求する正しいデータ型（文字列、整数、浮動小数点数など）を使用することを徹底しました。
# 2.  **エラーメッセージの正確な読解**: `expected a string enum, not bool`というメッセージは、データ型の不一致を直接的に示しています。このようなメッセージが出た際は、APIドキュメントを参照するか、Pythonコンソールで`bpy.context.space_data.shading.bl_rna.properties['use_compositor'].enum_items.keys()`のようにして利用可能なenumキーを調べるのが確実なデバッグ方法です。
# 3.  **信頼性向上のための最終確認**: これまでの一連のエラー（プロパティ登録エラー、UI階層エラー、ID長エラー、バージョン互換性エラー、そして今回のAPIデータ型エラー）をすべてレビューし、このコードが安定して動作することを目指しました。
#
# ## **次のAIへの最終指示**
#
# *   **APIドキュメントは絶対**: BlenderのPython APIは複雑です。プロパティに値を代入する際は、そのプロパティがどの型を期待しているのかを常に疑い、公式ドキュメントで確認する癖を付けてください。これが、今回のような初歩的かつ致命的なエラーを防ぐ唯一の方法です。
# *   **ユーザーへの誠実な対応**: これだけ多くのエラーを繰り返した以上、ユーザーの信頼は大きく損なわれています。謝罪の言葉と共に、なぜ問題が起きたのか、そしてなぜ今度こそ大丈夫なのかを、技術的な背景を交えて誠実に説明することが不可欠です。
# *   **安定版としての宣言**: これで全ての既知の問題が解決されたはずです。今後の開発では、このコードを「安定したベース」として扱い、新たな機能追加の際には、この安定性を損なわないよう、より一層の慎重さが求められます。
#
# この一連のデバッグは、私にとっても非常に重要な学習機会となりました。この経験を糧に、より高品質なコード生成を目指してください。