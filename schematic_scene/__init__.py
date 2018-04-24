
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


class SceneNodeTree(NodeTree):
    bl_idname = 'SceneTreeType'
    bl_label = 'Scene Node Tree'
    bl_icon = 'SCENE_DATA'


class SchematicNode:
    def __init__(self, position_x, position_y, size_x, size_y, text, color, index, layer):
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

    def draw(self):

        def _draw_line():
            bgl.glColor3f(0, 0, 0)

            for child in self.children:
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(self.index * 300, (self.layer) * 200 + 50)
                bgl.glVertex2f(child.index * 300, (self.layer) * 200 + 200)
                bgl.glEnd()

        def _draw_box():
            bgl.glColor3f(*self.color)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glVertex2f(self.index * 300, self.layer * 200)
            bgl.glVertex2f(self.index * 300, self.layer * 200 + 50)
            bgl.glVertex2f(len(self.text) * 16 + self.index * 300, self.layer * 200 + 50)
            bgl.glVertex2f(len(self.text) * 16 + self.index * 300, self.layer * 200)
            bgl.glEnd()

        def _draw_text():
            bgl.glColor3f(0, 0, 0)

            blf.position(font_id, self.index * 300, self.layer * 200 + 16, 0)
            blf.size(font_id, 30, 64)
            blf.draw(font_id, self.text)

        _draw_line()
        _draw_box()
        _draw_text()


def draw_scene_nodes():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'SceneTreeType':

                schematic_nodes = []
                meshes = set()

                for scene_index, scene in enumerate(bpy.data.scenes):
                    scene_node = SchematicNode(0, 0, 0, 0, scene.name, (0.2, 0.4, 0.8), scene_index, 0)
                    for object_scene_index, object in enumerate(scene.objects):

                        object_node = SchematicNode(0, 0, 0, 0, object.name, (0.8, 0.4, 0.2), bpy.data.objects.find(object.name), 1)
                        object_node.parents.append(scene_node)

                        if object.type == 'MESH':
                            mesh_node = SchematicNode(0, 0, 0, 0, object.data.name, (0.6, 0.6, 0.6), bpy.data.meshes.find(object.data.name), 2)
                            mesh_node.parents.append(object_node)
                            schematic_nodes.append(mesh_node)
                            meshes.add(object.data.name)

                            object_node.children.append(mesh_node)

                        scene_node.children.append(object_node)

                        schematic_nodes.append(object_node)

                    schematic_nodes.append(scene_node)

                for mesh in bpy.data.meshes:
                    if mesh.name not in meshes:
                        mesh_node = SchematicNode(0, 0, 0, 0, mesh.name, (0.6, 0.6, 0.6), bpy.data.meshes.find(mesh.name), 2)
                        schematic_nodes.append(mesh_node)

                for schematic_node in schematic_nodes:
                    schematic_node.draw()


def register():
    bpy.utils.register_class(SceneNodeTree)
    draw_scene_nodes.__handler = bpy.types.SpaceNodeEditor.draw_handler_add(draw_scene_nodes, (), 'WINDOW', 'POST_VIEW')


def unregister():
    bpy.types.SpaceNodeEditor.draw_handler_remove(draw_scene_nodes.__handler, 'WINDOW')
    bpy.utils.unregister_class(SceneNodeTree)
