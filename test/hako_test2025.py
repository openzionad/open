# blender_version: 3.0.0
# アドオンの完全なコード (ここから)
bl_info = {
    "name": "Isometric Cube Image Placer",
    "author": "AI Assistant",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N key) > Isometric Cube",
    "description": "Creates an isometric cube with three user-specified images on its faces.",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy
import bmesh
import math
from mathutils import Vector

def cleanup_scene(collection_name):
    """古いオブジェクトやデータをクリーンアップする"""
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in collection.objects:
            # メッシュデータも削除
            if obj.data and obj.data.users == 1:
                bpy.data.meshes.remove(obj.data)
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)

    # 孤立したマテリアルも削除
    for mat in bpy.data.materials:
        if "Isometric_Material_" in mat.name and mat.users == 0:
            bpy.data.materials.remove(mat)

def create_image_material(name, image_path):
    """画像テクスチャを持つマテリアルを作成する"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    
    # 画像テクスチャノードを作成
    tex_image = nodes.new(type='ShaderNodeTexImage')
    tex_image.location = bsdf.location - Vector((300, 0))
    
    # 画像を読み込み
    if image_path:
        try:
            tex_image.image = bpy.data.images.load(image_path)
        except RuntimeError:
            print(f"Warning: Could not load image file: {image_path}")
            # 画像が読み込めない場合はピンク色にする
            bsdf.inputs['Base Color'].default_value = (1.0, 0.0, 0.5, 1.0)
            return mat

    # ノードを接続
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    
    return mat

class ISO_PROPS_PropertyGroup(bpy.types.PropertyGroup):
    """アドオンのプロパティを保持するクラス"""
    top_image: bpy.props.StringProperty(
        name="Top Image",
        description="Image for the top face of the cube",
        subtype='FILE_PATH'
    )
    right_image: bpy.props.StringProperty(
        name="Right Image",
        description="Image for the right face of the cube",
        subtype='FILE_PATH'
    )
    left_image: bpy.props.StringProperty(
        name="Left Image",
        description="Image for the left face of the cube",
        subtype='FILE_PATH'
    )

class OBJECT_OT_CreateIsometricCube(bpy.types.Operator):
    """アイソメトリックキューブを生成するオペレーター"""
    bl_idname = "object.create_isometric_cube"
    bl_label = "Create Isometric Cube"
    bl_description = "Generates a cube with images on its faces and sets up an isometric camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.iso_cube_props
        collection_name = "Isometric_Cube_Collection"

        # 0. 古いオブジェクトを削除
        cleanup_scene(collection_name)

        # 1. 新しいコレクションを作成
        iso_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(iso_collection)

        # 2. マテリアルを作成
        materials = [
            create_image_material("Isometric_Material_Top", props.top_image),
            create_image_material("Isometric_Material_Right", props.right_image),
            create_image_material("Isometric_Material_Left", props.left_image),
        ]

        # 3. 立方体を生成
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        cube = context.active_object
        cube.name = "Isometric_Cube"
        iso_collection.objects.link(cube)
        context.collection.objects.unlink(cube) # 元のコレクションからアンリンク

        # 4. マテリアルを立方体に割り当て
        for mat in materials:
            cube.data.materials.append(mat)

        # 5. UV展開と面の割り当て
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.mode_set(mode='EDIT')
        
        bm = bmesh.from_edit_mesh(cube.data)
        uv_layer = bm.loops.layers.uv.verify()

        # UV展開のためにシームを付ける (見えない辺に)
        for edge in bm.edges:
            is_back_edge = all(v.co.x < 0 or v.co.y < 0 or v.co.z < 0 for v in edge.verts)
            if is_back_edge:
                edge.seam = True
        
        # 全面を選択してUV展開
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

        # 各面にマテリアルインデックスを割り当て
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            # 面の法線ベクトルで上面、右面、左面を判断
            if face.normal.z > 0.9: # 上面
                face.material_index = 0
            elif face.normal.y > 0.9: # 右面 (Y+)
                face.material_index = 1
            elif face.normal.x > 0.9: # 左面 (X+)
                face.material_index = 2
        
        bmesh.update_edit_mesh(cube.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        # 6. カメラを設置
        bpy.ops.object.camera_add(location=(10, 10, 10))
        camera = context.active_object
        camera.name = "Isometric_Camera"
        iso_collection.objects.link(camera)
        context.collection.objects.unlink(camera)

        # アイソメトリック設定
        camera.data.type = 'ORTHO'
        camera.rotation_euler.x = math.radians(54.736)
        camera.rotation_euler.y = math.radians(0)
        camera.rotation_euler.z = math.radians(45)
        camera.data.ortho_scale = 5 # ズーム具合を調整

        # カメラが立方体を向くようにする
        constraint = camera.constraints.new(type='TRACK_TO')
        constraint.target = cube
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        # 7. ライトを設置
        bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
        light = context.active_object
        light.name = "Isometric_Light"
        light.data.energy = 3
        iso_collection.objects.link(light)
        context.collection.objects.unlink(light)
        
        self.report({'INFO'}, "Isometric cube created successfully.")
        return {'FINISHED'}

class VIEW3D_PT_IsometricCubePanel(bpy.types.Panel):
    """3DビューのサイドバーにUIパネルを作成する"""
    bl_label = "Isometric Cube Creator"
    bl_idname = "VIEW3D_PT_iso_cube_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Isometric Cube' # Nパネルのタブ名

    def draw(self, context):
        layout = self.layout
        props = context.scene.iso_cube_props

        box = layout.box()
        box.label(text="Assign Images to Faces", icon='IMAGE_DATA')
        box.prop(props, "top_image")
        box.prop(props, "right_image")
        box.prop(props, "left_image")
        
        layout.separator()
        
        # 実行ボタン
        row = layout.row()
        row.scale_y = 1.5 # ボタンを大きくする
        row.operator(OBJECT_OT_CreateIsometricCube.bl_idname, icon='CUBE')

# アドオンを登録・解除するためのクラスと関数
classes = (
    ISO_PROPS_PropertyGroup,
    OBJECT_OT_CreateIsometricCube,
    VIEW3D_PT_IsometricCubePanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.iso_cube_props = bpy.props.PointerProperty(type=ISO_PROPS_PropertyGroup)

def unregister():
    del bpy.types.Scene.iso_cube_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()