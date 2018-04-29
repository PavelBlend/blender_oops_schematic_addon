
bl_info = {
    'name':     'Schematic Scene',
    'author':   'Pavel_Blend, Bibo',
    'version':  (0, 0, 0),
    'blender':  (2, 79, 0),
    'category': 'Node',
    'location': 'Node Editor > Schematic Scene'
}


import bpy
import bgl
import blf
from bpy.types import NodeTree
from mathutils.geometry import interpolate_bezier
from mathutils import Vector


FONT_ID = 0
CHAR_SIZE = 8
X_DISTANCE = 25
Y_DISTANCE = 50
NODE_HIGHT = 25
BORDER_SIZE = 4
LIGHT_ADD_COLOR = 0.4


class SceneNodeTree(NodeTree):
    bl_idname = 'SchematicScene'
    bl_label = 'Schematic Scene'
    bl_icon = 'SCENE_DATA'


class SchematicNode:
    def __init__(self, text, color, index):
        self.children = []
        self.parents = []
        self.text = text
        self.color = color
        self.index = index
        self.offset_x = 0
        self.offset_y = 0
        self.active = False
        self.active_child_name = []
        self.border_select = False

    def draw(self):

        def _draw_line():
            for child in self.children:
                # Vertices calculation
                start = Vector((self.offset_x + len(self.text) * (CHAR_SIZE / 2), self.offset_y + NODE_HIGHT))
                finish = Vector((child.offset_x + len(child.text) * (CHAR_SIZE / 2), child.offset_y))
                handle1 = start.copy()
                handle1.y += (child.offset_y - self.offset_y) / 4
                handle2 = finish.copy()
                handle2.y -= (child.offset_y - self.offset_y) / 4
                curve_resolution = bpy.context.window_manager.schematic_scene_curve_resolution
                vertices = [vertex for vertex in interpolate_bezier(start, handle1, handle2, finish, curve_resolution)]
                # Color choosing
                bgl.glLineWidth(1)
                color = (0.5, 0.5, 0.5)
                if self.active and child.text in self.active_child_name:
                    color = (1, 1, 0)
                    bgl.glLineWidth(2)
                # Drawing
                bgl.glColor3f(*color)
                bgl.glBegin(bgl.GL_LINES)
                for i in range(len(vertices)-1):
                    bgl.glVertex2f(vertices[i].x, vertices[i].y)
                    bgl.glVertex2f(vertices[i+1].x, vertices[i+1].y)
                bgl.glEnd()

        def _draw_box():
            bgl.glColor3f(*self.color)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glVertex2f(self.offset_x, self.offset_y)
            bgl.glVertex2f(self.offset_x, self.offset_y + NODE_HIGHT)
            bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x, self.offset_y + NODE_HIGHT)
            bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x, self.offset_y)
            bgl.glEnd()

        def _draw_border_box():
            bgl.glColor3f(0, 0, 0)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y - BORDER_SIZE)
            bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y + NODE_HIGHT + BORDER_SIZE)
            bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x + BORDER_SIZE, self.offset_y + NODE_HIGHT + BORDER_SIZE)
            bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x + BORDER_SIZE, self.offset_y - BORDER_SIZE)
            bgl.glEnd()

        def _draw_text():
            bgl.glColor3f(0, 0, 0)

            blf.position(FONT_ID, self.offset_x, self.offset_y + NODE_HIGHT / 4, 0)
            blf.blur(FONT_ID, 0)
            blf.size(FONT_ID, 30, 30)
            blf.draw(FONT_ID, self.text)

        _draw_line()
        if self.border_select:
            _draw_border_box()
        _draw_box()
        _draw_text()


def draw_schematic_scene():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'SchematicScene':

                # 0 Scenes, 1 Objects, 2 Meshes, 3 Materials, 4 Textures, 5 Images
                schematic_nodes = [[], [], [], [], [], []]
                scene_nodes = {}
                meshes_nodes = {}
                materials_nodes = {}
                textures_nodes = {}
                images_nodes = {}
                wm = bpy.context.window_manager

                # Generate images nodes
                if wm.schematic_scene_show_images:
                    for image_index, image in enumerate(bpy.data.images):
                        image_node = SchematicNode(image.name, list(wm.schematic_scene_color_images_nodes), image_index)
                        images_nodes[image.name] = image_node
                        schematic_nodes[5].append(image_node)

                # Generate textures nodes
                if wm.schematic_scene_show_textures:
                    for texture_index, texture in enumerate(bpy.data.textures):
                        texture_node = SchematicNode(texture.name, list(wm.schematic_scene_color_textures_nodes), texture_index)
                        textures_nodes[texture.name] = texture_node
                        schematic_nodes[4].append(texture_node)

                        # Assign Children and Parents
                        if texture.type == 'IMAGE':
                            image = texture.image
                            if image:
                                image_node = images_nodes.get(image.name, None)
                                if image_node:
                                    image_node.parents.append(texture_node)
                                    texture_node.children.append(image_node)

                # Generate materials nodes
                if wm.schematic_scene_show_materials:
                    for material_index, material in enumerate(bpy.data.materials):
                        material_node = SchematicNode(material.name, list(wm.schematic_scene_color_materials_nodes), material_index)
                        materials_nodes[material.name] = material_node
                        schematic_nodes[3].append(material_node)

                        # Assign Children and Parents
                        for texture_slot in material.texture_slots:
                            if texture_slot:
                                texture = texture_slot.texture
                                texture_node = textures_nodes.get(texture.name, None)
                                if texture_node:
                                    texture_node.parents.append(material_node)
                                    material_node.children.append(texture_node)

                # Generate meshes nodes
                if wm.schematic_scene_show_meshes:
                    for mesh_index, mesh in enumerate(bpy.data.meshes):
                        mesh_node = SchematicNode(mesh.name, list(wm.schematic_scene_color_meshes_nodes), mesh_index)
                        meshes_nodes[mesh.name] = mesh_node
                        schematic_nodes[2].append(mesh_node)

                        # Assign Children and Parents
                        for material in mesh.materials:
                            if material:
                                material_node = materials_nodes.get(material.name, None)
                                if material_node:
                                    material_node.parents.append(mesh_node)
                                    mesh_node.children.append(material_node)

                # Generate scenes nodes
                if wm.schematic_scene_show_scenes:
                    for scene_index, scene in enumerate(bpy.data.scenes):
                        scene_node = SchematicNode(scene.name, list(wm.schematic_scene_color_scenes_nodes), scene_index)
                        scene_nodes[scene.name] = scene_node
                        schematic_nodes[0].append(scene_node)

                def _select_children(schematic_node):
                    for child in schematic_node.children:
                        schematic_node.active_child_name.append(child.text)
                        if not child.active:
                            child.active = True
                            child.color[0] += LIGHT_ADD_COLOR
                            child.color[1] += LIGHT_ADD_COLOR
                            child.color[2] += LIGHT_ADD_COLOR
                        _select_children(child)

                def _select_parents(schematic_node):
                    for parent in schematic_node.parents:
                        parent.active_child_name.append(schematic_node.text)
                        if not parent.active:
                            parent.active = True
                            parent.color[0] += LIGHT_ADD_COLOR
                            parent.color[1] += LIGHT_ADD_COLOR
                            parent.color[2] += LIGHT_ADD_COLOR
                        _select_parents(parent)

                # Generate objects nodes
                if wm.schematic_scene_show_objects:
                    for object_index, object in enumerate(bpy.data.objects):
                        object_node = SchematicNode(object.name, list(wm.schematic_scene_color_objects_nodes), object_index)

                        # Assign Children and Parents
                        if object.type == 'MESH':
                            mesh_node = meshes_nodes.get(object.data.name, None)
                            if mesh_node:
                                mesh_node.parents.append(object_node)
                                object_node.children.append(mesh_node)
                        for scene in object.users_scene:
                            scene_node = scene_nodes.get(scene.name, None)
                            if scene_node:
                                scene_node.children.append(object_node)
                                object_node.parents.append(scene_node)
                        schematic_nodes[1].append(object_node)

                        # Select Node
                        if bpy.context.window_manager.schematic_scene_3d_view_select and object in bpy.context.selected_objects:
                            object_node.active = True
                            object_node.color[0] += LIGHT_ADD_COLOR
                            object_node.color[1] += LIGHT_ADD_COLOR
                            object_node.color[2] += LIGHT_ADD_COLOR
                            object_node.border_select = True
                            _select_children(object_node)
                            _select_parents(object_node)

                # Set Nodes Coordinates
                last_offset_x = 0
                last_offset_y = 0
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        if last_offset_x > bpy.context.window_manager.schematic_scene_tree_width:
                            last_offset_x = 0
                            last_offset_y += Y_DISTANCE
                        schematic_node.offset_x = last_offset_x
                        schematic_node.offset_y = last_offset_y
                        # Select Node
                        node_size_x = len(schematic_node.text) * CHAR_SIZE + X_DISTANCE
                        for click in bpy.context.window_manager.schematic_scene_multi_click:
                            if last_offset_x < click.x < (last_offset_x + node_size_x) and \
                                    last_offset_y < click.y < (last_offset_y + NODE_HIGHT) and \
                                    not bpy.context.window_manager.schematic_scene_3d_view_select:
                                if not schematic_node.active:
                                    schematic_node.active = True
                                    schematic_node.color[0] += LIGHT_ADD_COLOR
                                    schematic_node.color[1] += LIGHT_ADD_COLOR
                                    schematic_node.color[2] += LIGHT_ADD_COLOR
                                if not schematic_node.border_select:
                                    schematic_node.border_select = True
                                _select_children(schematic_node)
                                _select_parents(schematic_node)
                        last_offset_x += node_size_x
                    last_offset_x = 0
                    last_offset_y += Y_DISTANCE

                # Draw nodes
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw()


class SchematicSceneShow(bpy.types.Operator):
    bl_idname = "node.schematic_scene_show"
    bl_label = "Show/Hide Schematic Scene"

    _handle = None

    @staticmethod
    def handle_add():
        SchematicSceneShow._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_schematic_scene, (), 'WINDOW', 'POST_VIEW')

    @staticmethod
    def handle_remove():
        if SchematicSceneShow._handle is not None:
            bpy.types.SpaceNodeEditor.draw_handler_remove(SchematicSceneShow._handle, 'WINDOW')
        SchematicSceneShow._handle = None

    def cancel(self, context):
        self.handle_remove()

    def modal(self, context, event):
        wm = context.window_manager
        if event.type == 'RIGHTMOUSE' and event.value == 'CLICK' and not wm.schematic_scene_3d_view_select:
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        click_x, click_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                        use_multi_select = event.shift
                        if not use_multi_select:
                            wm.schematic_scene_multi_click.clear()
                        click = wm.schematic_scene_multi_click.add()
                        click.x = click_x
                        click.y = click_y
                        region.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        wm = context.window_manager
        if not wm.schematic_scene_show:
            wm.schematic_scene_show = True
            if context.area.type == 'NODE_EDITOR':
                self.handle_add()
                context.area.tag_redraw()
                wm.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        else:
            wm.schematic_scene_show = False
            self.handle_remove()
            context.area.tag_redraw()
            return {'CANCELLED'}


class SchematicSceneDisplayOptionsPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_schematic_scene_display_options"
    bl_label = "Display Options"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Schematic Scene"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, 'schematic_scene_3d_view_select')
        layout.prop(wm, 'schematic_scene_tree_width')
        layout.prop(wm, 'schematic_scene_curve_resolution')


class SchematicSceneUsedNodesPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_schematic_scene_used_nodes"
    bl_label = "Used Nodes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Schematic Scene"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        wm = context.window_manager
        row.prop(wm, 'schematic_scene_show_scenes', icon='SCENE_DATA', toggle=True, icon_only=True)
        row.prop(wm, 'schematic_scene_show_objects', icon='OBJECT_DATA', toggle=True, icon_only=True)
        row.prop(wm, 'schematic_scene_show_meshes', icon='MESH_DATA', toggle=True, icon_only=True)
        row = layout.row()
        row.prop(wm, 'schematic_scene_show_materials', icon='MATERIAL_DATA', toggle=True, icon_only=True)
        row.prop(wm, 'schematic_scene_show_textures', icon='TEXTURE_DATA', toggle=True, icon_only=True)
        row.prop(wm, 'schematic_scene_show_images', icon='IMAGE_DATA', toggle=True, icon_only=True)


class SchematicSceneNodesColorsPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_schematic_scene_nodes_colors"
    bl_label = "Nodes Colors"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Schematic Scene"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, 'schematic_scene_color_scenes_nodes')
        layout.prop(wm, 'schematic_scene_color_objects_nodes')
        layout.prop(wm, 'schematic_scene_color_meshes_nodes')
        layout.prop(wm, 'schematic_scene_color_materials_nodes')
        layout.prop(wm, 'schematic_scene_color_textures_nodes')
        layout.prop(wm, 'schematic_scene_color_images_nodes')


class SchematicSceneClick(bpy.types.PropertyGroup):
    x = bpy.props.FloatProperty(default=-1000.0)
    y = bpy.props.FloatProperty(default=-1000.0)


def init_properties():
    wm = bpy.types.WindowManager
    wm.schematic_scene_show = bpy.props.BoolProperty(default=False)
    wm.schematic_scene_3d_view_select = bpy.props.BoolProperty(name='3D View Select', default=False)
    wm.schematic_scene_tree_width = bpy.props.FloatProperty(name='Tree Width', default=1000.0)

    wm.schematic_scene_show_scenes = bpy.props.BoolProperty(name='Scenes', default=True)
    wm.schematic_scene_show_objects = bpy.props.BoolProperty(name='Objects', default=True)
    wm.schematic_scene_show_meshes = bpy.props.BoolProperty(name='Meshes', default=True)
    wm.schematic_scene_show_materials = bpy.props.BoolProperty(name='Materials', default=True)
    wm.schematic_scene_show_textures = bpy.props.BoolProperty(name='Textures', default=True)
    wm.schematic_scene_show_images = bpy.props.BoolProperty(name='Images', default=True)

    wm.schematic_scene_color_scenes_nodes = bpy.props.FloatVectorProperty(
        name='Scenes', default=[0.2, 0.4, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    wm.schematic_scene_color_objects_nodes = bpy.props.FloatVectorProperty(
        name='Objects', default=[0.6, 0.4, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    wm.schematic_scene_color_meshes_nodes = bpy.props.FloatVectorProperty(
        name='Meshes', default=[0.6, 0.6, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    wm.schematic_scene_color_materials_nodes = bpy.props.FloatVectorProperty(
        name='Materials', default=[0.6, 0.2, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    wm.schematic_scene_color_textures_nodes = bpy.props.FloatVectorProperty(
        name='Textures', default=[0.2, 0.6, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    wm.schematic_scene_color_images_nodes = bpy.props.FloatVectorProperty(
        name='Images', default=[0.6, 0.2, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    wm.schematic_scene_curve_resolution = bpy.props.IntProperty(name='Curve Resolution', default=40,
        min=2, max=100, soft_min=2, soft_max=100)

    bpy.utils.register_class(SchematicSceneClick)
    wm.schematic_scene_multi_click = bpy.props.CollectionProperty(type=SchematicSceneClick)


def clear_properties():
    del bpy.types.WindowManager.schematic_scene_show
    del bpy.types.WindowManager.schematic_scene_3d_view_select
    del bpy.types.WindowManager.schematic_scene_tree_width

    del bpy.types.WindowManager.schematic_scene_show_scenes
    del bpy.types.WindowManager.schematic_scene_show_objects
    del bpy.types.WindowManager.schematic_scene_show_meshes
    del bpy.types.WindowManager.schematic_scene_show_materials
    del bpy.types.WindowManager.schematic_scene_show_textures

    del bpy.types.WindowManager.schematic_scene_color_scenes_nodes
    del bpy.types.WindowManager.schematic_scene_color_objects_nodes
    del bpy.types.WindowManager.schematic_scene_color_meshes_nodes
    del bpy.types.WindowManager.schematic_scene_color_materials_nodes
    del bpy.types.WindowManager.schematic_scene_color_textures_nodes
    del bpy.types.WindowManager.schematic_scene_color_images_nodes

    del bpy.types.WindowManager.schematic_scene_curve_resolution

    del bpy.types.WindowManager.schematic_scene_multi_click
    bpy.utils.unregister_class(SchematicSceneClick)


def draw_operator(self, context):
    if context.area.spaces[0].tree_type == 'SchematicScene':
        self.layout.operator('node.schematic_scene_show')


def register():
    init_properties()
    bpy.utils.register_class(SceneNodeTree)
    bpy.utils.register_class(SchematicSceneShow)
    bpy.utils.register_class(SchematicSceneDisplayOptionsPanel)
    bpy.utils.register_class(SchematicSceneUsedNodesPanel)
    bpy.utils.register_class(SchematicSceneNodesColorsPanel)
    bpy.types.NODE_HT_header.append(draw_operator)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_operator)
    bpy.utils.unregister_class(SchematicSceneDisplayOptionsPanel)
    bpy.utils.unregister_class(SchematicSceneUsedNodesPanel)
    bpy.utils.unregister_class(SchematicSceneNodesColorsPanel)
    bpy.utils.unregister_class(SchematicSceneShow)
    bpy.utils.unregister_class(SceneNodeTree)
    clear_properties()
