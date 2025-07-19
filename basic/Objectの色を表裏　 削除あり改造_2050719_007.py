# blender-cod: utf-8
import bpy
import webbrowser
from datetime import datetime
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatVectorProperty, FloatProperty

# ===================================================================
# アドオン情報 & グローバル設定
# ===================================================================

# --- 統合後のアドオン情報 ---
# UIに表示されるタブ（カテゴリ）名を定義
ADDON_CATEGORY_NAME = "claude 表裏色変更"

bl_info = {
    "name": "表裏色変更 & リンク/削除パネル",
    "author": "Your Name & Claude",
    "version": (1, 6, 0),
    "blender": (4, 2, 0),
    "location": f"View3D > Sidebar > {ADDON_CATEGORY_NAME}",
    "description": "オブジェクトの表裏に別々の材質を設定し、便利なリンクとアドオン削除機能を提供します。",
    "category": ADDON_CATEGORY_NAME,
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/11/131157",
}

# --- プレフィックスとID設定 (各機能の競合を避けるため) ---

# [1] 表裏色変更機能のプレフィックス
PREFIX_C_LOWER = "claude_c_20250719"
PREFIX_C_UPPER = "CLAUDE_C_20250719"
PROP_GROUP_NAME = f"{PREFIX_C_LOWER}_props"

# [2] リンク/削除機能のプレフィックス
_PREFIX_STATIC_PART = "z_rev16_remover"
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX_Z = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"


# ===================================================================
# 機能 [1]: 表裏色変更 (ここから)
# ===================================================================

# --- プロパティグループ ---
class CLAUDE_C_20250719_PG_Properties(PropertyGroup):
    """アドオンのプロパティを保持するグループ"""
    # 表面設定
    front_color: FloatVectorProperty(name="表面色", description="表面の色", subtype='COLOR', default=(0.8, 0.8, 0.8, 1.0), size=4)
    front_alpha: FloatProperty(name="表面透明度", description="表面の透明度", default=1.0, min=0.0, max=1.0)
    front_metallic: FloatProperty(name="表面金属", description="表面の金属値", default=0.0, min=0.0, max=1.0)
    front_roughness: FloatProperty(name="表面ラフネス", description="表面のラフネス", default=0.5, min=0.0, max=1.0)
    
    # 裏面設定
    back_color: FloatVectorProperty(name="裏面色", description="裏面の色", subtype='COLOR', default=(0.2, 0.2, 0.8, 1.0), size=4)
    back_alpha: FloatProperty(name="裏面透明度", description="裏面の透明度", default=1.0, min=0.0, max=1.0)
    back_metallic: FloatProperty(name="裏面金属", description="裏面の金属値", default=0.0, min=0.0, max=1.0)
    back_roughness: FloatProperty(name="裏面ラフネス", description="裏面のラフネス", default=0.5, min=0.0, max=1.0)

# --- オペレーター ---
class CLAUDE_C_20250719_OT_ApplySettings(Operator):
    """選択オブジェクトに表裏の色と材質設定を適用するオペレーター"""
    bl_idname = f"{PREFIX_C_LOWER}.apply_settings"
    bl_label = "設定を適用"
    bl_description = "選択オブジェクトに表裏の色と材質設定を適用"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = getattr(context.scene, PROP_GROUP_NAME)
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "メッシュオブジェクトを選択してください")
            return {'CANCELLED'}
        
        for obj in selected_objects:
            self.apply_front_back_material(obj, props)
        
        self.report({'INFO'}, f"{len(selected_objects)}個のオブジェクトに設定を適用しました")
        return {'FINISHED'}
    
    def apply_front_back_material(self, obj, props):
        mat_name = f"{obj.name}_{PREFIX_C_UPPER}_FrontBack"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        
        mat.node_tree.nodes.clear()
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.location = (400, 0)
        geometry = nodes.new('ShaderNodeNewGeometry')
        geometry.location = (-400, 200)
        
        front_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        front_bsdf.location = (0, 100)
        front_bsdf.inputs['Base Color'].default_value = props.front_color
        front_bsdf.inputs['Alpha'].default_value = props.front_alpha
        front_bsdf.inputs['Metallic'].default_value = props.front_metallic
        front_bsdf.inputs['Roughness'].default_value = props.front_roughness
        
        back_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        back_bsdf.location = (0, -100)
        back_bsdf.inputs['Base Color'].default_value = props.back_color
        back_bsdf.inputs['Alpha'].default_value = props.back_alpha
        back_bsdf.inputs['Metallic'].default_value = props.back_metallic
        back_bsdf.inputs['Roughness'].default_value = props.back_roughness
        
        links.new(geometry.outputs['Backfacing'], mix_shader.inputs['Fac'])
        links.new(front_bsdf.outputs['BSDF'], mix_shader.inputs[1])
        links.new(back_bsdf.outputs['BSDF'], mix_shader.inputs[2])
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
        
        if props.front_alpha < 1.0 or props.back_alpha < 1.0:
            mat.blend_method = 'BLEND'
            mat.show_transparent_back = False
        else:
            mat.blend_method = 'OPAQUE'

class CLAUDE_C_20250719_OT_InitializeObject(Operator):
    """選択オブジェクトのマテリアル設定を初期化するオペレーター"""
    bl_idname = f"{PREFIX_C_LOWER}.initialize_object"
    bl_label = "選択オブジェクト初期化"
    bl_description = "選択オブジェクトのマテリアル設定を初期化"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "メッシュオブジェクトを選択してください")
            return {'CANCELLED'}
        for obj in selected_objects:
            obj.data.materials.clear()
        self.report({'INFO'}, f"{len(selected_objects)}個のオブジェクトを初期化しました")
        return {'FINISHED'}

class CLAUDE_C_20250719_OT_GetObjectInfo(Operator):
    """選択オブジェクトのマテリアル情報をUIに反映するオペレーター"""
    bl_idname = f"{PREFIX_C_LOWER}.get_object_info"
    bl_label = "選択オブジェクト情報取得"
    bl_description = "選択オブジェクトのマテリアル情報をUIに反映"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = getattr(context.scene, PROP_GROUP_NAME)
        active_obj = context.active_object
        
        if not (active_obj and active_obj.type == 'MESH' and active_obj.data.materials):
            self.report({'WARNING'}, "マテリアルを持つメッシュオブジェクトを選択してください")
            return {'CANCELLED'}
        
        mat = active_obj.data.materials[0]
        if not (mat and mat.use_nodes):
            self.report({'WARNING'}, "マテリアルがノードを使用していません")
            return {'CANCELLED'}
        
        nodes = mat.node_tree.nodes
        mix_shader = next((n for n in nodes if n.type == 'MIX_SHADER'), None)
        
        if not mix_shader:
            self.report({'WARNING'}, "表裏設定用のMix Shaderノードが見つかりません。")
            return {'CANCELLED'}

        # シェーダー入力からノードをたどる
        front_bsdf_node = mix_shader.inputs[1].links[0].from_node if mix_shader.inputs[1].is_linked else None
        back_bsdf_node = mix_shader.inputs[2].links[0].from_node if mix_shader.inputs[2].is_linked else None

        if front_bsdf_node and front_bsdf_node.type == 'BSDF_PRINCIPLED':
            props.front_color = front_bsdf_node.inputs['Base Color'].default_value
            props.front_alpha = front_bsdf_node.inputs['Alpha'].default_value
            props.front_metallic = front_bsdf_node.inputs['Metallic'].default_value
            props.front_roughness = front_bsdf_node.inputs['Roughness'].default_value
        
        if back_bsdf_node and back_bsdf_node.type == 'BSDF_PRINCIPLED':
            props.back_color = back_bsdf_node.inputs['Base Color'].default_value
            props.back_alpha = back_bsdf_node.inputs['Alpha'].default_value
            props.back_metallic = back_bsdf_node.inputs['Metallic'].default_value
            props.back_roughness = back_bsdf_node.inputs['Roughness'].default_value

        self.report({'INFO'}, "オブジェクト情報を取得しました")
        return {'FINISHED'}

# --- UIパネル ---
class CLAUDE_C_20250719_PT_MainPanel(Panel):
    """アドオンのメインUIパネル"""
    bl_label = "表裏 色/材質 設定"
    bl_idname = f"{PREFIX_C_UPPER}_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0  # このパネルを最初に表示
    
    def draw(self, context):
        layout = self.layout
        props = getattr(context.scene, PROP_GROUP_NAME)
        
        row = layout.row()
        row.scale_y = 2.0
        row.operator(f"{PREFIX_C_LOWER}.apply_settings", icon='CHECKMARK')
        
        col = layout.column(align=True)
        col.operator(f"{PREFIX_C_LOWER}.initialize_object", icon='TRASH')
        col.operator(f"{PREFIX_C_LOWER}.get_object_info", icon='EYEDROPPER')
        
        layout.separator()
        
        box = layout.box()
        box.label(text="表面設定", icon='MOD_NORMALEDIT')
        col = box.column(align=True)
        col.prop(props, "front_color", text="色")
        col.prop(props, "front_alpha", text="透明度")
        col.prop(props, "front_metallic", text="金属")
        col.prop(props, "front_roughness", text="ラフネス")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="裏面設定", icon='MOD_NORMALEDIT')
        sub = box.column(align=True)
        sub.prop(props, "back_color", text="色")
        sub.prop(props, "back_alpha", text="透明度")
        sub.prop(props, "back_metallic", text="金属")
        sub.prop(props, "back_roughness", text="ラフネス")


# ===================================================================
# 機能 [2]: リンク & 削除機能 (ここから)
# ===================================================================

# --- リンクデータ ---
ADDON_LINKS = ({"label": "カメラ 固定 Git 管理 20250711", "url":"https://memo2017.hatenablog.com/entry/2025/07/11/131157"},)
NEW_DOC_LINKS = [{"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"},]
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

# --- オペレーター ---
class ZIONAD_OT_OpenURL(Operator):
    """指定されたURLをウェブブラウザで開くオペレーター"""
    bl_idname = f"{PREFIX_Z}.open_url"
    bl_label = "Open URL"
    bl_description = "Opens the specified URL in a web browser"
    url: StringProperty(default="")

    def execute(self, context):
        try:
            webbrowser.open(self.url)
            self.report({'INFO'}, f"Opened: {self.url}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open URL: {e}")
        return {'FINISHED'}

class ZIONAD_OT_RemoveAddon(Operator):
    """このアドオンのコンポーネントを登録解除するオペレーター"""
    bl_idname = f"{PREFIX_Z}.remove_addon"
    bl_label = "アドオンのコンポーネントを登録解除"
    bl_description = "このアドオンの全コンポーネントを登録解除します。プリファレンスから手動で無効化/削除が必要な場合があります。"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            unregister()
            self.report({'INFO'}, "アドオンのコンポーネントを登録解除しました。")
        except Exception as e:
            self.report({'ERROR'}, f"アドオンの削除中にエラーが発生しました: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

# --- UIパネル ---
class ZIONAD_PT_LinksPanel(Panel):
    """ドキュメントやSNSへのリンクを表示するパネル"""
    bl_label = "リンク集 (Links)"
    bl_idname = f"{PREFIX_Z}_PT_links_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 1  # 2番目に表示
    bl_options = {'DEFAULT_CLOSED'} # デフォルトで閉じておく

    def draw(self, context):
        layout = self.layout
        def draw_links(link_list):
            for link in link_list:
                op = layout.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL')
                op.url = link["url"]
        
        box = layout.box()
        box.label(text="メインドキュメント:")
        draw_links(ADDON_LINKS)
        box = layout.box()
        box.label(text="更新情報 / 目次:")
        draw_links(NEW_DOC_LINKS)
        box = layout.box()
        box.label(text="過去のドキュメント:")
        draw_links(DOC_LINKS)
        box = layout.box()
        box.label(text="関連リンク / SNS:")
        draw_links(SOCIAL_LINKS)

class ZIONAD_PT_RemovePanel(Panel):
    """アドオンを削除するためのパネル"""
    bl_label = "アドオン管理"
    bl_idname = f"{PREFIX_Z}_PT_remove_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 2  # 3番目に表示
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="このアドオンをUIから削除します:")
        layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="登録解除", icon='CANCEL')
        layout.label(text="（再度有効にするにはプリファレンスから）", icon='INFO')


# ===================================================================
# 登録・解除処理
# ===================================================================

# 登録対象の全クラスをタプルにまとめる
classes = (
    # 機能[1]のクラス
    CLAUDE_C_20250719_PG_Properties,
    CLAUDE_C_20250719_OT_ApplySettings,
    CLAUDE_C_20250719_OT_InitializeObject,
    CLAUDE_C_20250719_OT_GetObjectInfo,
    CLAUDE_C_20250719_PT_MainPanel,
    # 機能[2]のクラス
    ZIONAD_OT_OpenURL,
    ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_LinksPanel,
    ZIONAD_PT_RemovePanel,
)

def register():
    """アドオン有効化時の処理"""
    for cls in classes:
        bpy.utils.register_class(cls)
    # PropertyGroupをSceneに追加
    bpy.types.Scene.claude_c_20250719_props = bpy.props.PointerProperty(type=CLAUDE_C_20250719_PG_Properties)

def unregister():
    """アドオン無効化時の処理"""
    # 登録したクラスを逆順で解除
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # PropertyGroupをSceneから削除
    del bpy.types.Scene.claude_c_20250719_props

# スクリプトとして直接実行された場合の処理（テスト用）
if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()