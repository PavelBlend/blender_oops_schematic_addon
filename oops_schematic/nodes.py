
import bpy
import bgl
import blf
import mathutils

from .constants import *


class SchematicNode:
    def __init__(self, text, color, index, type):
        self.children = []
        self.parents = []
        self.text = text
        self.color = color
        self.index = index
        self.offset_x = 0
        self.offset_y = 0
        self.active = False
        self.active_child = []
        self.border_select = False
        self.type = type

    def draw_lines(self):
        for child in self.children:
            # Color choosing
            bgl.glLineWidth(1)
            color = (0.5, 0.5, 0.5)
            if self.active and child in self.active_child:
                color = (1, 1, 0)
                bgl.glLineWidth(2)
            if not child.border_select and (self.type in {'BLEND_FILE', 'LIBRARY'}) and not self.border_select:
                bgl.glLineWidth(1)
                color = (0.5, 0.5, 0.5)
            # Vertices calculation
            if self.offset_y < child.offset_y:
                handle_coefficient = 4
            else:
                handle_coefficient = 1 / 2
            start = mathutils.Vector((self.offset_x + len(self.text) * (CHAR_SIZE / 2), self.offset_y + NODE_HIGHT))
            finish = mathutils.Vector((child.offset_x + len(child.text) * (CHAR_SIZE / 2), child.offset_y))
            handle1 = start.copy()
            handle1.y += (child.offset_y - self.offset_y + NODE_HIGHT) / handle_coefficient
            handle2 = finish.copy()
            handle2.y -= (child.offset_y - self.offset_y + NODE_HIGHT) / handle_coefficient
            curve_resolution = bpy.context.window_manager.oops_schematic.curve_resolution
            vertices = [vertex for vertex in mathutils.geometry.interpolate_bezier(start, handle1, handle2, finish, curve_resolution)]
            # Drawing
            bgl.glColor3f(*color)
            bgl.glBegin(bgl.GL_LINES)
            for i in range(len(vertices)-1):
                bgl.glVertex2f(vertices[i].x, vertices[i].y)
                bgl.glVertex2f(vertices[i+1].x, vertices[i+1].y)
            bgl.glEnd()

    def draw_box(self):
        if self.border_select:
            self._draw_border_box()

        bgl.glColor3f(*self.color)

        bgl.glBegin(bgl.GL_QUADS)
        bgl.glVertex2f(self.offset_x, self.offset_y)
        bgl.glVertex2f(self.offset_x, self.offset_y + NODE_HIGHT)
        bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x, self.offset_y + NODE_HIGHT)
        bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x, self.offset_y)
        bgl.glEnd()

    def _draw_border_box(self):
        bgl.glColor3f(0, 0, 0)

        bgl.glBegin(bgl.GL_QUADS)
        bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y - BORDER_SIZE)
        bgl.glVertex2f(self.offset_x - BORDER_SIZE, self.offset_y + NODE_HIGHT + BORDER_SIZE)
        bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x + BORDER_SIZE, self.offset_y + NODE_HIGHT + BORDER_SIZE)
        bgl.glVertex2f(len(self.text) * CHAR_SIZE + self.offset_x + BORDER_SIZE, self.offset_y - BORDER_SIZE)
        bgl.glEnd()

    def draw_text(self):
        bgl.glColor3f(0, 0, 0)

        blf.position(FONT_ID, self.offset_x, self.offset_y + NODE_HIGHT / 4, 0)
        blf.blur(FONT_ID, 0)
        blf.size(FONT_ID, 30, 30)
        blf.draw(FONT_ID, self.text)
