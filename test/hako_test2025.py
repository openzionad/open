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
    "name": "AAA Isocube Creator (UI Code Fix)",
    "author": "zionadchat & Your Name & AI",
    "version": (26, 0, 1), # UIパネルのコードを整形し、構文エラーを修正
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > " + ADDON_CATEGORY_NAME,
    "description": "ブーリアン適用のロジックを安定性の高い方法に刷新し、全てのモードで穴が確実に確定されるよう修正しました。",
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
# プロパティグループ
# ===================================================================
class FacePropertyGroup(PropertyGroup):
    image_path: StringProperty(name="Image", subtype='FILE_PATH')
    color: FloatVectorProperty(name="Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4, min=0.0, max=1.0)
    alpha: FloatProperty(name="Alpha", subtype='FACTOR', default=1.0, min=0.0, max=1.0)
    rotation: FloatProperty(name="Rotation", default=0.0, min=0.0, max=360.0, unit='ROTATION', description="Rotation in degrees")
    flip: BoolProperty(name="Flip Horizontally", default=False)

class MainPropertyGroup(PropertyGroup):
    cube_size: FloatProperty(name="Cube Size", default=2.0, min=0.1)
    drill_holes: BoolProperty(name="ブーリアン処理を行う", description="立方体にブーリアン処理を適用します", default=False)
    cutter_shape: EnumProperty(name="モード", description="生成する形状のモードを選択します", 
        items=[('CYLINDER', "円柱 (3つ, 貫通穴)", "3つの円柱で立方体を貫通させます"), 
               ('SPHERE_CENTER', "球体 (1つ, 中心)", "立方体の中心に球体で穴を開けます"),
               ('SPHERE_FACES', "球体 (6つ, 面中心)", "6つの球体で各面の中心に窪みを作ります"),
               ('SPHERE_VERTICES', "球体 (8つ, 角)", "8つの球体を各頂点に配置し、角を丸めます")], 
        default='CYLINDER')
    hole_diameter_percent: FloatProperty(name="カッターの直径 (%)", description="ブーリアンに使用するカッターの直径を立方体サイズ比で指定します", default=50.0, min=1.0, max=200.0, subtype='PERCENTAGE')
    hole_depth_multiplier: FloatProperty(name="[円柱用] 貫通深度 (倍率)", description="[円柱のみ] 穴を開ける円柱の高さを、立方体サイズに対する倍率で指定します", default=10.0, min=0.1, soft_max=20.0)
    integrate_boolean: BoolProperty(name="ブーリアンを適用 (形状を確定)", description="ON: 形状を確定し、カッターを削除します (デフォルト)。\nOFF: カッターを別オブジェクトとして残し、非破壊で編集できるようにします。", default=True)
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
    bl_label = "Create Isocube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.zionad_props
        # キューブ生成とセットアップ
        base_collection_name = "Isocube_Collection"
        collection_name = base_collection_name; i = 1
        while collection_name in bpy.data.collections: collection_name = f"{base_collection_name}.{i:03d}"; i += 1
        iso_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(iso_collection)
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
        pivot = context.active_object; pivot.name = f"Pivot_{collection_name}"
        pivot.rotation_euler[2] = math.radians(props.world_z_rotation)
        if pivot.name in context.collection.objects: context.collection.objects.unlink(pivot)
        iso_collection.objects.link(pivot)
        face_map = {"top": props.top, "bottom": props.bottom, "front": props.front, "back": props.back, "right": props.right, "left": props.left}
        materials = {key: create_face_material(f"Mat_{key.capitalize()}_{collection_name}", data) for key, data in face_map.items()}
        bpy.ops.mesh.primitive_cube_add(size=props.cube_size, enter_editmode=True, align='WORLD', location=(0, 0, 0))
        cube = context.active_object; cube.name = f"Isocube_{collection_name}"
        for mat in materials.values():
            if mat: cube.data.materials.append(mat)
        bm = bmesh.from_edit_mesh(cube.data); bm.faces.ensure_lookup_table()
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
                    if name in mat_indices: face.material_index = mat_indices[name]; break
        bmesh.update_edit_mesh(cube.data); bpy.ops.object.mode_set(mode='OBJECT')
        if cube.name in context.collection.objects: context.collection.objects.unlink(cube)
        iso_collection.objects.link(cube); cube.parent = pivot
        
        # --- ブーリアン処理 ---
        if props.drill_holes:
            diameter = props.cube_size * (props.hole_diameter_percent / 100.0); radius = diameter / 2.0
            cutter_definitions = []
            h = props.cube_size / 2.0
            
            if props.cutter_shape == 'CYLINDER':
                depth = props.cube_size * props.hole_depth_multiplier
                axes = [('X', (0, math.radians(90), 0)), ('Y', (math.radians(90), 0, 0)), ('Z', (0, 0, 0))]
                for axis, rotation in axes:
                    cutter_definitions.append({'type': 'CYLINDER', 'radius': radius, 'depth': depth, 'location': (0,0,0), 'rotation': rotation})
            elif props.cutter_shape == 'SPHERE_CENTER':
                cutter_definitions.append({'type': 'SPHERE', 'radius': radius, 'location': (0, 0, 0)})
            elif props.cutter_shape == 'SPHERE_FACES':
                locations = [ (h, 0, 0), (-h, 0, 0), (0, h, 0), (0, -h, 0), (0, 0, h), (0, 0, -h) ]
                for loc in locations: cutter_definitions.append({'type': 'SPHERE', 'radius': radius, 'location': loc})
            elif props.cutter_shape == 'SPHERE_VERTICES':
                locations = [ (h, h, h), (h, h, -h), (h, -h, h), (h, -h, -h), (-h, h, h), (-h, h, -h), (-h, -h, h), (-h, -h, -h) ]
                for loc in locations: cutter_definitions.append({'type': 'SPHERE', 'radius': radius, 'location': loc})

            # 【安定化されたブーリアン処理】
            cutters = []
            # 1. 最初に全てのカッターを生成し、リストに格納する
            for i, definition in enumerate(cutter_definitions):
                if definition.get('type') == 'CYLINDER': # .get() for safety
                    bpy.ops.mesh.primitive_cylinder_add(radius=definition['radius'], depth=definition['depth'], location=definition['location'], rotation=definition['rotation'], vertices=64)
                else: # SPHERE
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=definition['radius'], location=definition['location'], segments=32, ring_count=16)
                cutter = context.active_object
                cutter.name = f"Temp_Cutter_{i}"
                cutters.append(cutter)
            
            # 2. 全てのカッターに対してモディファイアを追加する
            for i, cutter in enumerate(cutters):
                mod = cube.modifiers.new(name=f"Boolean_{i}", type='BOOLEAN')
                mod.object = cutter
                mod.operation = 'DIFFERENCE'
                mod.solver = 'EXACT'

            # 3. ブーリアン適用の要否に応じて処理を分岐
            if props.integrate_boolean:
                # 【適用モード】全てのモディファイアを適用し、全てのカッターを削除する
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = cube
                cube.select_set(True)
                
                # モディファイアは末尾から適用するのが最も安全
                for i in reversed(range(len(cutters))):
                    # apply operator can fail if modifier name is not found, so check first
                    if f"Boolean_{i}" in cube.modifiers:
                        bpy.ops.object.modifier_apply(modifier=f"Boolean_{i}")
                
                # 全てのカッターをデータごと削除
                for cutter in cutters:
                    if cutter.name in bpy.data.objects:
                        bpy.data.objects.remove(cutter, do_unlink=True)
            else:
                # 【非破壊モード】カッターをコレクションに移動し、親子付けする
                for i, cutter in enumerate(cutters):
                    cutter.name = f"Cutter_{i+1}_{collection_name}"
                    cutter.display_type = 'WIRE'
                    cutter.hide_render = True
                    # If cutter is already in a collection, unlink it first
                    for coll in cutter.users_collection:
                        coll.objects.unlink(cutter)
                    iso_collection.objects.link(cutter)
                    cutter.parent = pivot
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = cube
        cube.select_set(True)

        self.report({'INFO'}, "Isocube created.")
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
# UIパネル (★★★ コード整形 ★★★)
# ===================================================================
class ZIONAD_PT_MainPanel(Panel):
    bl_label = "Isocube Creator"
    bl_idname = f"{PREFIX}_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        props = context.scene.zionad_props
        scene = context.scene
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator(ZIONAD_OT_CreateIsometricCube.bl_idname, icon='CUBE')
        layout.separator()
        
        box = layout.box()
        box.label(text="Scene Settings", icon='SCENE_DATA')
        box.prop(scene.render, "engine", text="")
        
        box = layout.box()
        box.label(text="General Settings", icon='SETTINGS')
        box.prop(props, "cube_size")
        box.prop(props, "drill_holes")
        if props.drill_holes:
            sub = box.column(align=True)
            sub.active = props.drill_holes
            sub.prop(props, "cutter_shape", text="")
            sub.prop(props, "hole_diameter_percent")
            
            row_depth = sub.row()
            row_depth.enabled = props.cutter_shape == 'CYLINDER'
            row_depth.prop(props, "hole_depth_multiplier")
            
            sub.prop(props, "integrate_boolean")

        box.prop(props, "world_z_rotation")
        box.prop(props, "delete_faces")
        if props.delete_faces:
            box.prop(props, "corner_to_keep", text="")
            
        layout.separator()
        box = layout.box()
        box.label(text="Face Settings", icon='TEXTURE')
        box.operator(ZIONAD_OT_RandomizeImages.bl_idname, icon='FILE_REFRESH')
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
            box.separator()
            box.label(text=name)
            box.prop(face_prop, "image_path", text="")
            if not face_prop.image_path:
                box.prop(face_prop, "color", text="")
            col = box.column(align=True)
            col.prop(face_prop, "alpha", slider=True)
            col.prop(face_prop, "rotation", slider=True)
            col.prop(face_prop, "flip")

class ZIONAD_PT_LinksPanel(Panel):
    bl_label = "リンク集"
    bl_idname = f"{PREFIX}_PT_links_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY_NAME
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.zionad_link_panel_props
        
        def draw_collapsible_section(prop_name, link_list):
            is_expanded = getattr(props, prop_name)
            row = layout.row(align=True)
            row.prop(props, prop_name, text=props.bl_rna.properties[prop_name].name, icon="TRIA_DOWN" if is_expanded else "TRIA_RIGHT", emboss=False)
            if is_expanded:
                col = layout.box().column(align=True)
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