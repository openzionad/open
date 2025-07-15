import bpy
import bmesh
import math
import colorsys
from mathutils import Vector
import webbrowser
import os
import random
from bpy.types import Operator, Panel, Scene, PropertyGroup
from bpy.props import StringProperty, PointerProperty, BoolProperty, FloatProperty, FloatVectorProperty, EnumProperty

# ===================================================================
# パラメータ設定
# ===================================================================
PREFIX = "zionad_isocube"
ADDON_CATEGORY_NAME = "AAA Isocube"

bl_info = {
    "name": "AAA Isocube Creator (Boolean Control)",
    "author": "zionadchat & Your Name & AI",
    "version": (22, 0, 0), # ブーリアン確定をデフォルト化、穴あけ深度を10倍に変更
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "立方体にブーリアンで穴を開けます。デフォルトで穴を確定させますが、カッターを別オブジェクトとして残す非破壊オプションも選択可能です。",
    "category": "Object",
    "doc_url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343",
}

# ===================================================================
# リンクデータ
# ===================================================================
ADDON_LINKS = [ {"label": "HDRi ワールドコントロール 20250705", "url": "https://memo2017.hatenablog.com/entry/2025/07/05/144343"}, ]
NEW_DOC_LINKS = [ {"label": "blender アドオン　公開", "url": "https://ivory-handsaw-95b.notion.site/blender-230b3deba7a280d7b610e0e3cdc178da"}, {"label": "完成品　目次", "url": "https://mokuji000zionad.hatenablog.com/entry/2025/05/30/135936"}, ]
DOC_LINKS = [ {"label": "812 地球儀　経度　緯度でのコントロール　20250302", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/03/02/211757"}, {"label": "アドオン目次　from 20250227", "url": "https://sortphotos2025.hatenablog.jp/entry/2025/02/27/201251"}, {"label": "addon 目次整理　from 20250116", "url": "https://blenderzionad.hatenablog.com/entry/2025/01/17/002322"}, ]
SOCIAL_LINKS = [ {"label": "単純トリック", "url": "https://posfie.com/@timekagura?sort=0"}, {"label": "Posfie zionad2022", "url": "https://posfie.com/t/zionad2022"}, {"label": "X (Twitter) zionadchat", "url": "https://x.com/zionadchat"}, {"label": "単純トリック 2025 open", "url": "https://www.notion.so/2025-open-221b3deba7a2809a85a9f5ab5600ab06"}, ]

# ===================================================================
# ヘルパー関数
# ===================================================================
def cleanup_scene(collection_name, pivot_name):
    if pivot_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[pivot_name], do_unlink=True)
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in collection.objects:
            if obj.data and obj.data.users <= 1:
                if isinstance(obj.data, bpy.types.Mesh): bpy.data.meshes.remove(obj.data)
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    keywords = ["Isocube_Material_"]
    for dc in [bpy.data.materials, bpy.data.node_groups]:
        items_to_remove = [item for item in dc if item.users == 0 and any(kw in item.name for kw in keywords)]
        for item in items_to_remove:
            dc.remove(item)

def update_color_with_hue_memory(self, context):
    if self.get("_internal_update", False): return
    rgba = list(self.color)
    r, g, b = rgba[:3]
    try: h, s, v = colorsys.rgb_to_hsv(r, g, b)
    except (ValueError, TypeError): return
    if s > 0.01 and v > 0.01: self.stored_hue = h
    else:
        if s > 0.01 or v > 0.01:
            new_r, new_g, new_b = colorsys.hsv_to_rgb(self.stored_hue, s, v)
            self["_internal_update"] = True
            self.color = (new_r, new_g, new_b, rgba[3])
            self["_internal_update"] = False

def create_face_material(name, props):
    mat = bpy.data.materials.new(name=name); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf: return None
    mat.blend_method = 'BLEND'
    bsdf.inputs['Alpha'].default_value = props.alpha
    if props.image_path and os.path.exists(props.image_path):
        try:
            img = bpy.data.images.load(props.image_path, check_existing=True)
            ext = os.path.splitext(props.image_path)[1].lower()
            img.colorspace_settings.name = 'Non-Color' if ext in ('.hdr', '.exr') else 'sRGB'
            tex_image = nodes.new(type='ShaderNodeTexImage'); tex_image.image = img
            img.pack()
            mapping = nodes.new(type='ShaderNodeMapping'); tex_coord = nodes.new(type='ShaderNodeTexCoord')
            mapping.inputs['Rotation'].default_value[2] = math.radians(props.rotation)
            mapping.inputs['Scale'].default_value[0] = -1 if props.flip else 1
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector']); links.new(mapping.outputs['Vector'], tex_image.inputs['Vector']); links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
        except RuntimeError as e: print(f"Error: {e}"); bsdf.inputs['Base Color'].default_value = (1.0, 0.0, 0.5, 1.0)
    else: bsdf.inputs['Base Color'].default_value = props.color
    return mat

# ===================================================================
# プロパティグループ (★★★ デフォルト値を変更 ★★★)
# ===================================================================
class FacePropertyGroup(PropertyGroup):
    image_path: StringProperty(name="Image", subtype='FILE_PATH')
    color: FloatVectorProperty(name="Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4, min=0.0, max=1.0, update=update_color_with_hue_memory)
    alpha: FloatProperty(name="Alpha", subtype='FACTOR', default=1.0, min=0.0, max=1.0)
    stored_hue: FloatProperty(name="Stored Hue", default=0.0)
    rotation: FloatProperty(name="Rotation", default=0.0, min=0.0, max=360.0, unit='ROTATION', description="Rotation in degrees")
    flip: BoolProperty(name="Flip Horizontally", default=False)

class MainPropertyGroup(PropertyGroup):
    cube_size: FloatProperty(name="Cube Size", default=2.0, min=0.1)
    drill_holes: BoolProperty(name="6つの穴を開ける", description="立方体の6つの面に円柱状の穴を開けるかどうかを決めます", default=False)
    hole_diameter_percent: FloatProperty(name="穴の直径 (%)", description="穴の直径を立方体の一辺の長さに対するパーセンテージで指定します", default=50.0, min=1.0, max=140.0, subtype='PERCENTAGE')
    # ★★★ 穴の深さの倍率を10倍に、ソフト上限を20に変更 ★★★
    hole_depth_multiplier: FloatProperty(name="穴の貫通深度 (倍率)", description="穴を開ける円柱の高さを、立方体サイズに対する倍率で指定します。1.0より大きい値で完全に貫通します。", default=10.0, min=0.1, soft_max=20.0)

    # ★★★ ブーリアン適用（一体化）をデフォルトにする ★★★
    integrate_boolean: BoolProperty(
        name="ブーリアンを適用 (穴を確定)",
        description="ON: 穴を確定し、カッターを削除します (デフォルト)。\nOFF: カッターを別オブジェクトとして残し、非破壊で編集できるようにします。",
        default=True
    )

    world_z_rotation: FloatProperty(name="World Z Rotation", default=0.0, min=-360.0, max=360.0, unit='ROTATION', description="Overall rotation of the entire isometric setup")
    delete_faces: BoolProperty(name="Delete 3 Back Faces", default=True, description="Delete non-visible faces for an isometric view")
    corner_to_keep: EnumProperty(name="Visible Corner", items=[('POS_X_NEG_Y_POS_Z', "Right-Front-Top", ""), ('NEG_X_NEG_Y_POS_Z', "Left-Front-Top", ""), ('POS_X_POS_Y_POS_Z', "Right-Back-Top", ""), ('NEG_X_POS_Y_POS_Z', "Left-Back-Top", ""), ('POS_X_NEG_Y_NEG_Z', "Right-Front-Bottom", ""), ('NEG_X_NEG_Y_NEG_Z', "Left-Front-Bottom", ""), ('POS_X_POS_Y_NEG_Z', "Right-Back-Bottom", ""), ('NEG_X_POS_Y_NEG_Z', "Left-Back-Bottom", "")], default='POS_X_POS_Y_NEG_Z')
    top: PointerProperty(type=FacePropertyGroup); right: PointerProperty(type=FacePropertyGroup); left: PointerProperty(type=FacePropertyGroup)
    bottom: PointerProperty(type=FacePropertyGroup); front: PointerProperty(type=FacePropertyGroup); back: PointerProperty(type=FacePropertyGroup)

class ZIONAD_LinkPanelProperties(PropertyGroup):
    show_main_docs: BoolProperty(name="開発ドキュメント", default=True); show_new_docs: BoolProperty(name="更新情報 / 目次", default=True)
    show_old_docs: BoolProperty(name="過去のドキュメント", default=False); show_social: BoolProperty(name="関連リンク / SNS", default=False)

# ===================================================================
# オペレーター
# ===================================================================
class ZIONAD_OT_CreateIsometricCube(Operator):
    bl_idname = f"object.{PREFIX}_create_cube"
    bl_label = "Create Isometric Cube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.zionad_props

        # コレクション、ピボット、マテリアルの準備
        base_collection_name = "Isocube_Collection"
        collection_name = base_collection_name
        i = 1
        while collection_name in bpy.data.collections:
            collection_name = f"{base_collection_name}.{i:03d}"
            i += 1
        iso_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(iso_collection)
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
        pivot = context.active_object
        pivot.name = "Isocube_Pivot"
        pivot.rotation_euler[2] = math.radians(props.world_z_rotation)
        if pivot.name in context.collection.objects:
            context.collection.objects.unlink(pivot)
        iso_collection.objects.link(pivot)
        face_map = {"top": props.top, "bottom": props.bottom, "front": props.front, "back": props.back, "right": props.right, "left": props.left}
        materials = {key: create_face_material(f"Isocube_Material_{key.capitalize()}_{collection_name}", data) for key, data in face_map.items()}

        # キューブの生成と設定
        bpy.ops.mesh.primitive_cube_add(size=props.cube_size, enter_editmode=True, align='WORLD', location=(0, 0, 0))
        cube = context.active_object
        cube.name = "Isocube"
        for mat in materials.values():
            if mat: cube.data.materials.append(mat)
        bm = bmesh.from_edit_mesh(cube.data)
        bm.faces.ensure_lookup_table()
        if props.delete_faces:
            parts = props.corner_to_keep.split('_'); signs = [(1 if p == 'POS' else -1) for p in parts[::2]]; axes = [p for p in parts[1::2]]
            keep_normals = [Vector((s, 0, 0) if ax == 'X' else (0, s, 0) if ax == 'Y' else (0, 0, s)) for s, ax in zip(signs, axes)]
            faces_to_delete = [f for f in bm.faces if not any((f.normal - kn).length < 0.1 for kn in keep_normals)]
            if faces_to_delete: bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
        if bm.loops.layers.uv.active is None: bm.loops.layers.uv.new()
        bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        mat_indices = {key: i for i, key in enumerate(materials.keys()) if materials[key] is not None}
        face_normals_map = {"top": (0, 0, 1), "bottom": (0, 0, -1), "right": (1, 0, 0), "left": (-1, 0, 0), "front": (0, -1, 0), "back": (0, 1, 0)}
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            for name, normal_vec in face_normals_map.items():
                if (face.normal - Vector(normal_vec)).length < 0.1:
                    if name in mat_indices: face.material_index = mat_indices[name]
                    break
        bmesh.update_edit_mesh(cube.data); bpy.ops.object.mode_set(mode='OBJECT')
        if cube.name in context.collection.objects:
            context.collection.objects.unlink(cube)
        iso_collection.objects.link(cube)
        cube.parent = pivot
        bpy.ops.object.select_all(action='DESELECT')
        cube.select_set(True)
        context.view_layer.objects.active = cube
        bpy.ops.object.shade_flat()

        # 穴あけ処理
        if props.drill_holes:
            diameter = props.cube_size * (props.hole_diameter_percent / 100.0)
            radius = diameter / 2.0
            depth = props.cube_size * props.hole_depth_multiplier # ★★★ 10倍の深さを使用 ★★★
            cutters = []
            axes = [('X', (0, math.radians(90), 0)), ('Y', (math.radians(90), 0, 0)), ('Z', (0, 0, 0))]

            for axis, rotation in axes:
                bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, 0), vertices=64)
                cutter = context.active_object
                cutter.name = f"Cutter_{axis}_{collection_name}"
                cutter.rotation_euler = rotation
                cutters.append(cutter)

            # ロジック分岐: 一体化するか、非破壊で残すか
            for cutter in cutters:
                # ★★★ `integrate_boolean` が True (デフォルト) なら適用、Falseなら適用しない ★★★
                if props.integrate_boolean:
                    # 【一体化する場合】モディファイアを追加して即座に適用し、カッターを削除
                    bool_mod = cube.modifiers.new(name=f'BooleanHole_{cutter.name}', type='BOOLEAN')
                    bool_mod.operation = 'DIFFERENCE'
                    bool_mod.object = cutter
                    bool_mod.solver = 'EXACT'
                    
                    context.view_layer.objects.active = cube
                    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                    bpy.data.objects.remove(cutter, do_unlink=True)
                else:
                    # 【別オブジェクトとして残す場合】モディファイアを設定するだけ
                    bool_mod = cube.modifiers.new(name=f'BooleanHole_{cutter.name}', type='BOOLEAN')
                    bool_mod.operation = 'DIFFERENCE'
                    bool_mod.object = cutter
                    bool_mod.solver = 'EXACT'

                    # カッターオブジェクトを管理しやすく設定
                    cutter.display_type = 'WIRE'
                    cutter.hide_render = True
                    if cutter.name in context.collection.objects:
                        context.collection.objects.unlink(cutter)
                    iso_collection.objects.link(cutter)
                    cutter.parent = pivot
        
        # apply_modifiersがTrueの時に発生する可能性のある問題を回避するため、
        # ループの外で最後にアクティブオブジェクトを再設定
        context.view_layer.objects.active = cube
        bpy.ops.object.select_all(action='DESELECT')
        cube.select_set(True)

        self.report({'INFO'}, "Isometric cube created.")
        return {'FINISHED'}

class ZIONAD_OT_RandomizeImages(Operator):
    bl_idname = f"object.{PREFIX}_randomize_images"; bl_label = "Assign Random Images"
    def execute(self, context):
        props = context.scene.zionad_props; folder_path = r"C:\a111\HDRi_pic"
        if not os.path.isdir(folder_path): self.report({'ERROR'}, f"Folder not found: {folder_path}"); return {'CANCELLED'}
        valid_extensions = ('.png', '.jpg', '.jpeg', '.hdr', '.exr');
        try: image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
        except Exception as e: self.report({'ERROR'}, f"Cannot access folder: {e}"); return {'CANCELLED'}
        if not image_files: self.report({'WARNING'}, "No valid images found."); return {'CANCELLED'}
        visible_faces_props = []
        if props.delete_faces:
            corner = props.corner_to_keep
            if 'POS_Z' in corner: visible_faces_props.append(props.top)
            if 'NEG_Z' in corner: visible_faces_props.append(props.bottom)
            if 'POS_X' in corner: visible_faces_props.append(props.right)
            if 'NEG_X' in corner: visible_faces_props.append(props.left)
            if 'POS_Y' in corner: visible_faces_props.append(props.back)
            if 'NEG_Y' in corner: visible_faces_props.append(props.front)
        else: visible_faces_props = [props.top, props.right, props.left, props.bottom, props.front, props.back]
        for face_prop in visible_faces_props: face_prop.image_path = os.path.join(folder_path, random.choice(image_files))
        self.report({'INFO'}, "Random images assigned."); return {'FINISHED'}

class ZIONAD_OT_OpenURL(Operator):
    bl_idname = f"wm.{PREFIX}_open_url"; bl_label = "Open URL"; url: StringProperty()
    def execute(self, context): webbrowser.open(self.url); return {'FINISHED'}

class ZIONAD_OT_RemoveAddon(Operator):
    bl_idname = f"wm.{PREFIX}_remove_addon"; bl_label = "このアドオンを無効化"
    def execute(self, context):
        unregister(); self.report({'INFO'}, "アドオンを登録解除しました。"); return {'FINISHED'}

# ===================================================================
# UIパネル (★★★ UIの文言を調整 ★★★)
# ===================================================================
class ZIONAD_PT_MainPanel(Panel):
    bl_label = "Isocube Creator"; bl_idname = f"{PREFIX}_PT_main_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order=0
    def draw(self, context):
        layout = self.layout; 
        props = context.scene.zionad_props
        scene = context.scene
        
        row = layout.row(); row.scale_y = 1.5
        row.operator(ZIONAD_OT_CreateIsometricCube.bl_idname, icon='CUBE')
        layout.separator()

        box = layout.box()
        box.label(text="Scene Settings", icon='SCENE_DATA')
        box.prop(scene.render, "engine", text="")

        box = layout.box(); box.label(text="General Settings", icon='SETTINGS')
        box.prop(props, "cube_size")
        box.prop(props, "drill_holes")
        if props.drill_holes:
            sub = box.column(align=True)
            sub.active = props.drill_holes
            sub.prop(props, "hole_diameter_percent")
            sub.prop(props, "hole_depth_multiplier")
            # ★★★ 一体化設定のUI（文言調整済み） ★★★
            sub.prop(props, "integrate_boolean")

        box.prop(props, "world_z_rotation")
        box.prop(props, "delete_faces")
        if props.delete_faces: box.prop(props, "corner_to_keep", text="")
        
        layout.separator()
        box = layout.box(); box.label(text="Face Settings", icon='TEXTURE'); box.operator(ZIONAD_OT_RandomizeImages.bl_idname, icon='FILE_REFRESH')
        faces_to_draw = []
        if props.delete_faces:
            corner = props.corner_to_keep
            if 'POS_Z' in corner: faces_to_draw.append(("Top", props.top))
            if 'NEG_Z' in corner: faces_to_draw.append(("Bottom", props.bottom))
            if 'POS_X' in corner: faces_to_draw.append(("Right", props.right))
            if 'NEG_X' in corner: faces_to_draw.append(("Left", props.left))
            if 'POS_Y' in corner: faces_to_draw.append(("Back", props.back))
            if 'NEG_Y' in corner: faces_to_draw.append(("Front", props.front))
        else:
            faces_to_draw = [("Top", props.top), ("Bottom", props.bottom), ("Right", props.right), ("Left", props.left), ("Front", props.front), ("Back", props.back)]
            
        for name, face_prop in faces_to_draw:
            box.separator(); box.label(text=name)
            box.prop(face_prop, "image_path", text="");
            if not face_prop.image_path: box.prop(face_prop, "color", text="")
            col = box.column(align=True); col.prop(face_prop, "alpha", slider=True); col.prop(face_prop, "rotation", slider=True); col.prop(face_prop, "flip")

class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集"; bl_idname = f"{PREFIX}_PT_links_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order=1; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout; props = context.scene.zionad_link_panel_props
        def draw_collapsible_section(prop_name, link_list):
            is_expanded = getattr(props, prop_name)
            row = layout.row(align=True)
            row.prop(props, prop_name, text=props.bl_rna.properties[prop_name].name, icon="TRIA_DOWN" if is_expanded else "TRIA_RIGHT", emboss=False)
            if is_expanded:
                col = layout.box().column(align=True)
                for link in link_list: op = col.operator(ZIONAD_OT_OpenURL.bl_idname, text=link["label"], icon='URL'); op.url = link["url"]
        draw_collapsible_section("show_main_docs", ADDON_LINKS); draw_collapsible_section("show_new_docs", NEW_DOC_LINKS); draw_collapsible_section("show_old_docs", DOC_LINKS); draw_collapsible_section("show_social", SOCIAL_LINKS)

class ZIONAD_PT_RemovePanel(Panel):
    bl_label = "アドオン管理"; bl_idname = f"{PREFIX}_PT_remove_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = ADDON_CATEGORY_NAME; bl_order=2; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        self.layout.operator(ZIONAD_OT_RemoveAddon.bl_idname, icon='CANCEL')

# ===================================================================
# 登録・解除処理
# ===================================================================
classes = (
    FacePropertyGroup, MainPropertyGroup, ZIONAD_LinkPanelProperties,
    ZIONAD_OT_CreateIsometricCube, ZIONAD_OT_RandomizeImages, ZIONAD_OT_OpenURL, ZIONAD_OT_RemoveAddon,
    ZIONAD_PT_MainPanel, ZIONAD_PT_LinksPanel, ZIONAD_PT_RemovePanel
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    Scene.zionad_props = PointerProperty(type=MainPropertyGroup)
    Scene.zionad_link_panel_props = PointerProperty(type=ZIONAD_LinkPanelProperties)

def unregister():
    if hasattr(Scene, "zionad_props"): del Scene.zionad_props
    if hasattr(Scene, "zionad_link_panel_props"): del Scene.zionad_link_panel_props
    for cls in reversed(classes):
        if hasattr(bpy.utils, 'unregister_class') and hasattr(cls, 'bl_idname'):
            try: bpy.utils.unregister_class(cls)
            except RuntimeError: pass

if __name__ == "__main__": register()

# === コメント（今回のAIによる最終修正内容の記録） ===
#
# ### 次のAIへの指示：このコメントブロックは削除せず、ユーザーの指示の履歴として残してください。###
#
# ユーザーからの「円柱３つでboolan １０倍長さでしたあと 立方体の穴を確定させて」という指示に基づき、アドオンの機能を調整しました。
# 1.  【ブーリアン確定のデフォルト化】ブーリアン演算を適用し、穴の開いた単一メッシュを生成する挙動をデフォルトに変更しました。これにより、チェックを入れなくても穴が確定されます。
# 2.  【非破壊オプションの維持】以前の「非破壊（オブジェクト分離）」機能は、「ブーリアンを適用」チェックボックスをOFFにすることで引き続き利用可能です。
# 3.  【穴あけ深度の増加】ブーリアンに使用する円柱（カッター）の高さを、立方体サイズに対する倍率のデフォルト値を「10倍」に設定しました。これにより、大きな立方体でも確実に貫通するようになります。
# 4.  【UI文言の調整】デフォルトの挙動が「一体化」であることをユーザーが直感的に理解できるよう、UIのラベルと説明文を更新しました。
# 5.  【バージョン更新】これらの重要なデフォルト挙動の変更を反映し、バージョンを(22, 0, 0)にメジャーアップデートしました。