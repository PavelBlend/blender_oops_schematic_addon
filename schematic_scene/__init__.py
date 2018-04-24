
bl_info = {
    'name':     'Schematic Scene',
    'author':   'Pavel_Blend',
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


# dir_path = os.path.abspath(os.path.dirname(__file__)) + os.sep
# font_path = dir_path + 'bmonofont-i18n.ttf'
# font_id = blf.load(font_path)
font_id = 0
char_size = 8
y_distance = 100
x_distance = 25
node_hight = 25


class SceneNodeTree(NodeTree):
    bl_idname = 'SceneTreeType'
    bl_label = 'Scene Node Tree'
    bl_icon = 'SCENE_DATA'


class SchematicNode:
    def __init__(self, position_x, position_y, size_x, size_y, text, color, index, layer, offset_x):
        self.children = []
        self.parents = []
        self.position_x = position_x
        self.position_y = position_y
        self.size_x = size_x
        self.size_y = size_y
        self.text = text
        self.color = color
        self.index = index
        self.layer = layer
        self.offset_x = offset_x

    def draw(self):

        def _draw_line():
            bgl.glColor3f(0, 0, 0)

            for child in self.children:
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(self.offset_x + len(self.text) * (char_size / 2), (self.layer) * y_distance + node_hight)
                bgl.glVertex2f(child.offset_x + len(child.text) * (char_size / 2), (self.layer) * y_distance + y_distance)
                bgl.glEnd()

        def _draw_box():
            bgl.glColor3f(*self.color)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glVertex2f(self.offset_x, self.layer * y_distance)
            bgl.glVertex2f(self.offset_x, self.layer * y_distance + node_hight)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x, self.layer * y_distance + node_hight)
            bgl.glVertex2f(len(self.text) * char_size + self.offset_x, self.layer * y_distance)
            bgl.glEnd()

        def _draw_text():
            bgl.glColor3f(0, 0, 0)

            blf.position(font_id, self.offset_x, self.layer * y_distance + node_hight / 4, 0)
            blf.blur(font_id, 0)
            blf.size(font_id, 30, 30)
            blf.draw(font_id, self.text)

        _draw_line()
        _draw_box()
        _draw_text()


def draw_scene_nodes():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'SceneTreeType':

                schematic_nodes = []
                object_nodes = {}
                scene_nodes = {}
                meshes_nodes = {}

                last_offset = 0
                for mesh_index, mesh in enumerate(bpy.data.meshes):
                    mesh_node = SchematicNode(0, 0, 0, 0, mesh.name, (0.6, 0.6, 0.6), mesh_index, 2, last_offset)
                    last_offset += len(mesh.name) * char_size + x_distance
                    meshes_nodes[mesh.name] = mesh_node
                    schematic_nodes.append(mesh_node)

                last_offset = 0
                for scene_index, scene in enumerate(bpy.data.scenes):
                    scene_node = SchematicNode(0, 0, 0, 0, scene.name, (0.2, 0.4, 0.8), scene_index, 0, last_offset)
                    last_offset += len(scene.name) * char_size + x_distance
                    scene_nodes[scene.name] = scene_node
                    schematic_nodes.append(scene_node)

                last_offset = 0
                for object_index, object in enumerate(bpy.data.objects):
                    object_node = SchematicNode(0, 0, 0, 0, object.name, (0.8, 0.4, 0.2), object_index, 1, last_offset)
                    last_offset += len(object.name) * char_size + x_distance
                    if object.type == 'MESH':
                        mesh_node = meshes_nodes[object.data.name]
                        mesh_node.parents.append(object_node)
                        object_node.children.append(mesh_node)
                    for scene in object.users_scene:
                        scene_node = scene_nodes[scene.name]
                        scene_node.children.append(object_node)
                        object_node.parents.append(scene_node)
                    object_nodes[object.name] = object_node
                    schematic_nodes.append(object_node)

                for schematic_node in schematic_nodes:
                    schematic_node.draw()


def register():
    bpy.utils.register_class(SceneNodeTree)
    draw_scene_nodes.__handler = bpy.types.SpaceNodeEditor.draw_handler_add(draw_scene_nodes, (), 'WINDOW', 'POST_VIEW')


def unregister():
    bpy.types.SpaceNodeEditor.draw_handler_remove(draw_scene_nodes.__handler, 'WINDOW')
    bpy.utils.unregister_class(SceneNodeTree)
