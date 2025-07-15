import bpy
import webbrowser
from bpy.types import Operator, Panel
from bpy.props import StringProperty
from datetime import datetime

# ===================================================================
# パラメータ設定
# ===================================================================

# --- プレフィックスとID設定 ---
# プレフィックスを定義して、このアドオンの全ての要素（クラス、IDなど）を一意にする
# rev(リビジョン)を更新することで、古いバージョンとの競合を避ける
_PREFIX_STATIC_PART = "zz_rev16_remover"
_PREFIX_INSTANCE_PART = datetime.now().strftime('%Y%m%d%H%M%S')
PREFIX = f"{_PREFIX_STATIC_PART}_{_PREFIX_INSTANCE_PART}"

# --- アドオン情報 ---
# タブ（カテゴリ）名を定義
ADDON_CATEGORY_NAME = "[1   sakujo panel  20250715 ]"

bl_info = {
    "name": f"{ADDON_CATEGORY_NAME} (Links & Remover)",
    "author": "Your Name",
    "version": (1, 6, 1), # バージョンを更新
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "Displays useful documentation links and an option to remove this addon.",
    "category": ADDON_CATEGORY_NAME,
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/11/131157",
}

# --- リンクパネル用データ ---
# 他のリストと形式を合わせるため、タプルからリストに変更しました
ADDON_LINKS = [
    {"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"}, 
    {"label": "カメラ 固定 Git 管理 20250711", "url":"https://memo2017.hatenablog.com/entry/2025/07/11/131157"},
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
# オペレーター (ボタンが押されたときの処理)
# ===================================================================

class ZIONAD_OT_OpenURL(Operator):
    """指定されたURLをウェブブラウザで開くオペレーター"""
    bl_idname = f"{PREFIX}.open_url"
    bl_label = "Open URL"
    bl_description = "Opens the specified URL in a web browser"

    # ★★★★★ 修正点 ★★★★★
    # プロパティの定義方法をBlender 4.0標準のアノテーション構文に変更しました。
    # 古い `bl_property` 辞書は使わず、このようにクラス直下に定義します。
    # これにより、UIからプロパティ (op.url = ...) が正しく設定されるようになります。
    url: StringProperty(
        name="URL",
        description="The URL to open in the web browser",
        default="",
    )

    def execute(self, context):
        # URLが空でないかチェックを追加すると、より安全になります
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
    """このアドオンのコンポーネントを登録解除するオペレーター"""
    bl_idname = f"{PREFIX}.remove_addon"
    bl_label = "アドオンのコンポーネントを登録解除"
    bl_description = "このアドオンの全コンポーネントを登録解除します。プリファレンスから手動で無効化/削除が必要な場合があります。"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            # unregister関数を呼び出して全クラスを登録解除
            unregister()
            self.report({'INFO'}, "アドオンのコンポーネントを登録解除しました。")
        except Exception as e:
            self.report({'ERROR'}, f"アドオンの削除中にエラーが発生しました: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


# ===================================================================
# UIパネル (サイドバーに表示されるUI)
# ===================================================================

class ZIONAD_PT_LinksPanel(Panel):
    """ドキュメントやSNSへのリンクを表示するパネル"""
    bl_label = "リンク集 (Links)"
    bl_idname = f"{PREFIX}_PT_links_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0  # 最初に表示
    bl_options = {'DEFAULT_CLOSED'} # デフォルトで閉じておく

    def draw(self, context):
        layout = self.layout

        def draw_links(link_list):
            for link in link_list:
                # このオペレーター呼び出しは変更の必要ありません
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
    bl_idname = f"{PREFIX}_PT_remove_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 1  # 2番目に表示
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, text="登録解除", icon='CANCEL')
  

# ===================================================================
# 登録・解除処理
# ===================================================================

# 登録対象のクラスをタプルにまとめる
classes = (
    ZIONAD_OT_OpenURL,
    ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_LinksPanel,
    ZIONAD_PT_RemovePanel,
)

def register():
    """アドオン有効化時の処理"""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """アドオン無効化時の処理"""
    # 登録したクラスを逆順で解除
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# スクリプトとして直接実行された場合の処理（テスト用）
if __name__ == "__main__":
    # 既存の同名アドオンが登録されていれば一度解除してから再登録する
    try:
        # このテスト実行では、動的なPREFIXを持つ古いモジュールは直接アンロードできないため
        # 同じ名前のクラスが登録されている場合にエラーが出ることがあります。
        # Blenderを再起動するか、手動で古いアドオンを無効化するのが確実です。
        unregister()
    except Exception:
        pass
    register()
