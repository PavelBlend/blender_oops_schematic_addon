
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


class SceneNodeTree(NodeTree):
    bl_idname = 'SceneTreeType'
    bl_label = 'Scene Node Tree'
    bl_icon = 'SCENE_DATA'


# dir_path = os.path.abspath(os.path.dirname(__file__)) + os.sep
# font_path = dir_path + 'bmonofont-i18n.ttf'
# font_id = blf.load(font_path)
font_id = 0


def draw_line(root_index, child_index, layer):
    bgl.glColor4f(0, 0, 0, 1.0)

    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(root_index * 300, layer * 200 + 50)
    bgl.glVertex2f(child_index * 300, layer * 200 + 200)
    bgl.glEnd()


def draw_node(r, g, b, text, index, layer):
    bgl.glColor4f(r, g, b, 1.0)

    bgl.glBegin(bgl.GL_QUADS)
    bgl.glVertex2f(index * 300, layer * 200)
    bgl.glVertex2f(index * 300, layer * 200 + 50)
    bgl.glVertex2f(len(text) * 16 + index * 300, layer * 200 + 50)
    bgl.glVertex2f(len(text) * 16 + index * 300, layer * 200)
    bgl.glEnd()

    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    blf.position(font_id, index * 300, layer * 200 + 16, 0)
    blf.size(font_id, 30, 64)
    blf.draw(font_id, text)


def draw_scene_nodes():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'SceneTreeType':

                for scene_index, scene in enumerate(bpy.data.scenes):
                    for object_scene_index, object in enumerate(scene.objects):
                        draw_line(scene_index, bpy.data.objects.find(object.name), 0)
                        if object.type == 'MESH':
                            draw_line(bpy.data.objects.find(object.name), bpy.data.meshes.find(object.data.name), 1)

                for scene_index, scene in enumerate(bpy.data.scenes):
                    draw_node(0.2, 0.4, 0.8, scene.name, scene_index, 0)
                for object_index, object in enumerate(bpy.data.objects):
                    draw_node(0.8, 0.4, 0.2, object.name, object_index, 1)
                for mesh_index, mesh in enumerate(bpy.data.meshes):
                    draw_node(0.6, 0.6, 0.6, mesh.name, mesh_index, 2)


def register():
    bpy.utils.register_class(SceneNodeTree)
    draw_scene_nodes.__handler = bpy.types.SpaceNodeEditor.draw_handler_add(draw_scene_nodes, (), 'WINDOW', 'POST_VIEW')


def unregister():
    bpy.types.SpaceNodeEditor.draw_handler_remove(draw_scene_nodes.__handler, 'WINDOW')
    bpy.utils.unregister_class(SceneNodeTree)
