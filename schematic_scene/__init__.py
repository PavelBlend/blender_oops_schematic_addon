
bl_info = {
    'name':     'Schematic Scene',
    'author':   'Pavel_Blend, Bibo',
    'version':  (0, 0, 0),
    'blender':  (2, 79, 0),
    'category': 'Node',
    'location': 'Node Editor > Scene Nodes'
}


import os
import time

import bpy
import bgl
import blf
from bpy.types import NodeTree
from mathutils.geometry import interpolate_bezier
from mathutils import Vector


# dir_path = os.path.abspath(os.path.dirname(__file__)) + os.sep
# font_path = dir_path + 'bmonofont-i18n.ttf'
# font_id = blf.load(font_path)
font_id = 0
char_size = 8
y_distance = 50
x_distance = 25
node_hight = 25
BORDER_SIZE = 4
operator_text = 'Show Schematic Scene'


class SceneNodeTree(NodeTree):
    bl_idname = 'SceneTreeType'
    bl_label = 'Scene Node Tree'
    bl_icon = 'SCENE_DATA'


class SchematicNode:
    def __init__(self, text, color, index, offset_x, offset_y):
        self.children = []
        self.parents = []
        self.text = text
        self.color = color
        self.index = index
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.active = False
        self.active_child_name = []
        self.border_select = False

    def draw(self):

        def _draw_line():
            for child in self.children:
                # Vertices calculation
                start = Vector((self.offset_x + len(self.text) * (char_size / 2), self.offset_y + node_hight))
                finish = Vector((child.offset_x + len(child.text) * (char_size / 2), child.offset_y))
                handle1 = start.copy()
                handle1.y += (child.offset_y - self.offset_y) / 4
                handle2 = finish.copy()
                handle2.y -= (child.offset_y - self.offset_y) / 4
                vertices = [vertex for vertex in interpolate_bezier(start, handle1, handle2, finish, 40)]
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
            bgl.glVertex2f(self.offset_x, self.offset_y + node_hight)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x, self.offset_y + node_hight)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x, self.offset_y)
            bgl.glEnd()

        def _draw_border_box():
            bgl.glColor3f(0, 0, 0)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y - BORDER_SIZE)
            bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y + node_hight + BORDER_SIZE)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x + BORDER_SIZE, self.offset_y + node_hight + BORDER_SIZE)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x + BORDER_SIZE, self.offset_y - BORDER_SIZE)
            bgl.glEnd()

        def _draw_text():
            bgl.glColor3f(0, 0, 0)

            blf.position(font_id, self.offset_x, self.offset_y + node_hight / 4, 0)
            blf.blur(font_id, 0)
            blf.size(font_id, 30, 30)
            blf.draw(font_id, self.text)

        _draw_line()
        if self.border_select:
            _draw_border_box()
        _draw_box()
        _draw_text()


def draw_scene_nodes():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'SceneTreeType':

                schematic_nodes = [[], [], [], []]
                object_nodes = {}
                scene_nodes = {}
                meshes_nodes = {}
                materials_nodes = {}

                for material_index, material in enumerate(bpy.data.materials):
                    material_node = SchematicNode(material.name, [0.8, 0.2, 0.2], material_index, 0, 0)
                    materials_nodes[material.name] = material_node
                    schematic_nodes[3].append(material_node)

                for mesh_index, mesh in enumerate(bpy.data.meshes):
                    mesh_node = SchematicNode(mesh.name, [0.6, 0.6, 0.6], mesh_index, 0, 0)
                    meshes_nodes[mesh.name] = mesh_node
                    schematic_nodes[2].append(mesh_node)
                    for material in mesh.materials:
                        if material:
                            material_node = materials_nodes[material.name]
                            material_node.parents.append(mesh_node)
                            mesh_node.children.append(material_node)

                for scene_index, scene in enumerate(bpy.data.scenes):
                    scene_node = SchematicNode(scene.name, [0.2, 0.4, 0.8], scene_index, 0, 0)
                    scene_nodes[scene.name] = scene_node
                    schematic_nodes[0].append(scene_node)

                if bpy.context.scene.objects.active:
                    if bpy.context.scene.objects.active.select:
                        active_object_name = bpy.context.scene.objects.active.name
                    else:
                        active_object_name = None
                else:
                    active_object_name = None

                for object_index, object in enumerate(bpy.data.objects):
                    object_node = SchematicNode(object.name, [0.8, 0.4, 0.2], object_index, 0, 0)
                    if object.name == active_object_name:
                        object_node.active = True
                        if object.type == 'MESH':
                            object_node.active_child_name.append(object.data.name)
                        object_node.color = [1.0, 0.6, 0.4]
                        object_node.border_select = True
                    if object.type == 'MESH':
                        mesh_node = meshes_nodes[object.data.name]
                        mesh_node.parents.append(object_node)
                        object_node.children.append(mesh_node)
                        if object.name == active_object_name:
                            mesh_node.active = True
                            mesh_node.color = [0.8, 0.8, 0.8]
                            for material_node in mesh_node.children:
                                material_node.active = True
                                mesh_node.active_child_name.append(material_node.text)
                                material_node.color = [1.0, 0.4, 0.4]
                    for scene in object.users_scene:
                        scene_node = scene_nodes[scene.name]
                        scene_node.children.append(object_node)
                        object_node.parents.append(scene_node)
                        if object.name == active_object_name:
                            scene_node.active = True
                            scene_node.active_child_name.append(active_object_name)
                            scene_node.color = [0.4, 0.6, 1.0]
                    object_nodes[object.name] = object_node
                    schematic_nodes[1].append(object_node)

                def _select_children(schematic_node):
                    for child in schematic_node.children:
                        schematic_node.active_child_name.append(child.text)
                        if not child.active:
                            child.active = True
                            child.color[0] += 0.2
                            child.color[1] += 0.2
                            child.color[2] += 0.2
                        _select_children(child)

                def _select_parents(schematic_node):
                    for parent in schematic_node.parents:
                        parent.active_child_name.append(schematic_node.text)
                        if not parent.active:
                            parent.active = True
                            parent.color[0] += 0.2
                            parent.color[1] += 0.2
                            parent.color[2] += 0.2
                        _select_parents(parent)

                last_offset_x = 0
                last_offset_y = 0
                click_x = bpy.context.window_manager.click_x
                click_y = bpy.context.window_manager.click_y
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        if last_offset_x > 1000:
                            last_offset_x = 0
                            last_offset_y += y_distance
                        schematic_node.offset_x = last_offset_x
                        schematic_node.offset_y = last_offset_y
                        node_size_x = len(schematic_node.text) * char_size + x_distance
                        if last_offset_x < click_x < (last_offset_x + node_size_x) and \
                                last_offset_y < click_y < (last_offset_y + node_hight):
                            schematic_node.active = True
                            schematic_node.color[0] += 0.2
                            schematic_node.color[1] += 0.2
                            schematic_node.color[2] += 0.2
                            schematic_node.border_select = True
                            _select_children(schematic_node)
                            _select_parents(schematic_node)
                        last_offset_x += node_size_x
                    last_offset_x = 0
                    last_offset_y += y_distance

                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw()


class ShowSchematicScene(bpy.types.Operator):
    bl_idname = "node.show_schematics_scene"
    bl_label = "Show Schematic Scene"
    bl_description = ""

    _handle = None
    operator_text = 'Show/Hide Schematic Scene'

    @staticmethod
    def handle_add():
        ShowSchematicScene._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_scene_nodes, (), 'WINDOW', 'POST_VIEW')

    @staticmethod
    def handle_remove():
        if ShowSchematicScene._handle is not None:
            bpy.types.SpaceNodeEditor.draw_handler_remove(ShowSchematicScene._handle, 'WINDOW')
        ShowSchematicScene._handle = None

    def cancel(self, context):
        self.handle_remove()

    def modal(self, context, event):
        if not context.window_manager.show_schematic_scene:
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        context.window_manager.click_x, context.window_manager.click_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                        context.object.select = False
                        region.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if not context.window_manager.show_schematic_scene:
            self.operator_text = 'Hide Schematic Scene'
            context.window_manager.show_schematic_scene = True
            if context.area.type == 'NODE_EDITOR':
                self.handle_add()
                context.area.tag_redraw()
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        else:
            self.operator_text = 'Show Schematic Scene'
            context.window_manager.show_schematic_scene = False
            self.handle_remove()
            context.area.tag_redraw()
            return {'CANCELLED'}


def init_properties():
    wm = bpy.types.WindowManager
    wm.show_schematic_scene = bpy.props.BoolProperty(default=False)
    wm.click_x = bpy.props.FloatProperty(default=-1000.0)
    wm.click_y = bpy.props.FloatProperty(default=-1000.0)


def clear_properties():
    del bpy.types.WindowManager.show_schematic_scene


def draw_operator(self, context):
    if context.area.spaces[0].tree_type == 'SceneTreeType':
        self.layout.operator('node.show_schematics_scene', bpy.types.NODE_OT_show_schematics_scene.operator_text)


def register():
    init_properties()
    bpy.utils.register_class(SceneNodeTree)
    bpy.utils.register_class(ShowSchematicScene)
    bpy.types.NODE_HT_header.append(draw_operator)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_operator)
    bpy.utils.unregister_class(ShowSchematicScene)
    bpy.utils.unregister_class(SceneNodeTree)
    clear_properties()
