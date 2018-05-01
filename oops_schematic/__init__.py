
bl_info = {
    'name':     'OOPS Schematic',
    'author':   'Pavel_Blend, Bibo',
    'version':  (0, 0, 0),
    'blender':  (2, 79, 0),
    'category': 'Node',
    'location': 'Node Editor > OOPS Schematic',
    'description': 'Object-Oriented Programming System Schematic View'
}


import os

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


class OopsSchematicNodeTree(NodeTree):
    bl_idname = 'OopsSchematic'
    bl_label = 'OOPS Schematic'
    bl_icon = 'OOPS'


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

    def draw(self):

        def _draw_line():
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
                start = Vector((self.offset_x + len(self.text) * (CHAR_SIZE / 2), self.offset_y + NODE_HIGHT))
                finish = Vector((child.offset_x + len(child.text) * (CHAR_SIZE / 2), child.offset_y))
                handle1 = start.copy()
                handle1.y += (child.offset_y - self.offset_y) / 4
                handle2 = finish.copy()
                handle2.y -= (child.offset_y - self.offset_y) / 4
                curve_resolution = bpy.context.window_manager.oops_schematic.curve_resolution
                vertices = [vertex for vertex in interpolate_bezier(start, handle1, handle2, finish, curve_resolution)]
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

    def _select_children(schematic_node):
        for child in schematic_node.children:
            schematic_node.active_child.append(child)
            if not child.active:
                child.active = True
                child.color[0] += LIGHT_ADD_COLOR
                child.color[1] += LIGHT_ADD_COLOR
                child.color[2] += LIGHT_ADD_COLOR
            _select_children(child)

    def _select_parents(schematic_node):
        for parent in schematic_node.parents:
            parent.active_child.append(schematic_node)
            if not parent.active:
                parent.active = True
                parent.color[0] += LIGHT_ADD_COLOR
                parent.color[1] += LIGHT_ADD_COLOR
                parent.color[2] += LIGHT_ADD_COLOR
            _select_parents(parent)

    s = bpy.context.window_manager.oops_schematic    # s - schematic
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'OopsSchematic':

                # 0 Libraries 1 Scenes, 2 Objects, 3 Meshes, 4 Materials, 5 Textures, 6 Images
                schematic_nodes = [[], [], [], [], [], [], []]
                blend_file = SchematicNode('Blend File: {}'.format(os.path.basename(bpy.data.filepath)), list(s.color_blend_file_nodes), 0, 'BLEND_FILE')
                if s.show_libraries:
                    libraries_nodes = {None: blend_file}
                    schematic_nodes[0].append(blend_file)
                scenes_nodes = {library.name: {} for library in bpy.data.libraries}
                scenes_nodes[None] = {}
                objects_nodes = scenes_nodes.copy()
                meshes_nodes = scenes_nodes.copy()
                materials_nodes = scenes_nodes.copy()
                textures_nodes = scenes_nodes.copy()
                images_nodes = scenes_nodes.copy()

                # Generate libraries nodes
                if s.show_libraries:
                    for library_index, library in enumerate(bpy.data.libraries):
                        library_node = SchematicNode('{}: {}'.format(library.name, os.path.basename(library.filepath.replace('//', ''))), list(s.color_libraries_nodes), library_index + 1, 'LIBRARY')
                        libraries_nodes[library.name] = library_node
                        schematic_nodes[0].append(library_node)

                # Generate images nodes
                if s.show_images:
                    for image_index, image in enumerate(bpy.data.images):
                        image_node = SchematicNode(image.name, list(s.color_images_nodes), image_index, 'IMAGE')
                        library_name = getattr(image.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            image_node.parents.append(library_node)
                            library_node.children.append(image_node)
                        images_nodes[library_name][image.name] = image_node
                        schematic_nodes[6].append(image_node)

                # Generate textures nodes
                if s.show_textures:
                    for texture_index, texture in enumerate(bpy.data.textures):
                        texture_node = SchematicNode(texture.name, list(s.color_textures_nodes), texture_index, 'TEXTURE')
                        library_name = getattr(texture.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            texture_node.parents.append(library_node)
                            library_node.children.append(texture_node)

                        # Assign Children and Parents
                        if texture.type == 'IMAGE':
                            image = texture.image
                            if image:
                                image_node = images_nodes.get(getattr(image.library, 'name', None)).get(image.name, None)
                                if image_node:
                                    image_node.parents.append(texture_node)
                                    texture_node.children.append(image_node)

                        schematic_nodes[5].append(texture_node)
                        textures_nodes[library_name][texture.name] = texture_node

                # Generate materials nodes
                if s.show_materials:
                    for material_index, material in enumerate(bpy.data.materials):
                        material_node = SchematicNode(material.name, list(s.color_materials_nodes), material_index, 'MATERIAL')
                        library_name = getattr(material.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            material_node.parents.append(library_node)
                            library_node.children.append(material_node)

                        # Assign Children and Parents
                        for texture_slot in material.texture_slots:
                            if texture_slot:
                                texture = texture_slot.texture
                                texture_node = textures_nodes.get(getattr(texture.library, 'name', None)).get(texture.name, None)
                                if texture_node:
                                    texture_node.parents.append(material_node)
                                    material_node.children.append(texture_node)
                        # Assign Images
                        if s.show_images:
                            node_tree = material.node_tree
                            if node_tree:
                                for node in node_tree.nodes:
                                    if node.type == 'TEX_IMAGE':
                                        image = node.image
                                        if image:
                                            image_node = images_nodes.get(getattr(image.library, 'name', None)).get(image.name, None)
                                            if image_node:
                                                image_node.parents.append(material_node)
                                                material_node.children.append(image_node)
                        # Assign Textures
                        if s.show_textures:
                            node_tree = material.node_tree
                            if node_tree:
                                for node in node_tree.nodes:
                                    if node.type == 'TEXTURE':
                                        texture = node.texture
                                        if texture:
                                            texture_node = textures_nodes.get(getattr(texture.library, 'name', None)).get(texture.name, None)
                                            if texture_node:
                                                texture_node.parents.append(material_node)
                                                material_node.children.append(texture_node)

                        schematic_nodes[4].append(material_node)
                        materials_nodes[library_name][material.name] = material_node

                # Generate meshes nodes
                if s.show_meshes:
                    for mesh_index, mesh in enumerate(bpy.data.meshes):
                        mesh_node = SchematicNode(mesh.name, list(s.color_meshes_nodes), mesh_index, 'MESH')
                        library_name = getattr(mesh.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            mesh_node.parents.append(library_node)
                            library_node.children.append(mesh_node)
                        # Assign Children and Parents
                        for material in mesh.materials:
                            if material:
                                material_node = materials_nodes.get(getattr(material.library, 'name', None)).get(material.name, None)
                                if material_node:
                                    material_node.parents.append(mesh_node)
                                    mesh_node.children.append(material_node)
                        schematic_nodes[3].append(mesh_node)
                        meshes_nodes[library_name][mesh.name] = mesh_node

                # Generate objects nodes
                if s.show_objects:
                    for object_index, object in enumerate(bpy.data.objects):
                        object_node = SchematicNode(object.name, list(s.color_objects_nodes), object_index, 'OBJECT')

                        # Assign Children and Parents
                        if object.type == 'MESH':
                            mesh_node = meshes_nodes.get(getattr(object.data.library, 'name', None)).get(object.data.name, None)
                            if mesh_node:
                                mesh_node.parents.append(object_node)
                                object_node.children.append(mesh_node)

                        library_name = getattr(object.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            object_node.parents.append(library_node)
                            library_node.children.append(object_node)

                        # Select Node
                        if s.select_3d_view and object in bpy.context.selected_objects:
                            object_node.active = True
                            object_node.color[0] += LIGHT_ADD_COLOR
                            object_node.color[1] += LIGHT_ADD_COLOR
                            object_node.color[2] += LIGHT_ADD_COLOR
                            object_node.border_select = True
                            _select_children(object_node)
                            _select_parents(object_node)

                        schematic_nodes[2].append(object_node)
                        objects_nodes[library_name][object.name] = object_node

                # Generate scenes nodes
                if s.show_scenes:
                    for scene_index, scene in enumerate(bpy.data.scenes):
                        scene_node = SchematicNode(scene.name, list(s.color_scenes_nodes), scene_index, 'SCENE')
                        library_name = getattr(scene.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            scene_node.parents.append(library_node)
                            library_node.children.append(scene_node)
                        for object in scene.objects:
                            object_node = objects_nodes.get(getattr(object.library, 'name', None)).get(object.name, None)
                            if object_node:
                                scene_node.children.append(object_node)
                                object_node.parents.append(scene_node)
                        schematic_nodes[1].append(scene_node)
                        scenes_nodes[library_name][scene.name] = scene_node

                # Set Nodes Coordinates
                last_offset_x = 0
                last_offset_y = 0
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        if last_offset_x > s.tree_width:
                            last_offset_x = 0
                            last_offset_y += Y_DISTANCE
                        schematic_node.offset_x = last_offset_x
                        schematic_node.offset_y = last_offset_y
                        # Select Node
                        node_size_x = len(schematic_node.text) * CHAR_SIZE + X_DISTANCE
                        for click in s.multi_click:
                            if last_offset_x < click.x < (last_offset_x + node_size_x) and \
                                    last_offset_y < click.y < (last_offset_y + NODE_HIGHT) and \
                                    not s.select_3d_view:
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
                    if schematic_nodes_group:
                        last_offset_y += Y_DISTANCE

                # Draw nodes
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw()


class OopsSchematicShow(bpy.types.Operator):
    bl_idname = "node.oops_schematic_show"
    bl_label = "Show/Hide Oops Schematic"

    _handle = None

    @staticmethod
    def handle_add():
        OopsSchematicShow._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_schematic_scene, (), 'WINDOW', 'POST_VIEW')

    @staticmethod
    def handle_remove():
        if OopsSchematicShow._handle is not None:
            bpy.types.SpaceNodeEditor.draw_handler_remove(OopsSchematicShow._handle, 'WINDOW')
        OopsSchematicShow._handle = None

    def cancel(self, context):
        self.handle_remove()

    def modal(self, context, event):
        s = context.window_manager.oops_schematic
        if event.type == 'RIGHTMOUSE' and event.value == 'CLICK' and not s.select_3d_view:
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        click_x, click_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                        use_multi_select = event.shift
                        if not use_multi_select:
                            s.multi_click.clear()
                        click = s.multi_click.add()
                        click.x = click_x
                        click.y = click_y
                        region.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        s = context.window_manager.oops_schematic
        if not s.show:
            s.show = True
            if context.area.type == 'NODE_EDITOR':
                self.handle_add()
                context.area.tag_redraw()
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        else:
            s.show = False
            self.handle_remove()
            context.area.tag_redraw()
            return {'CANCELLED'}


class OopsSchematicDisplayOptionsPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_oops_schematic_display_options"
    bl_label = "Display Options"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "OOPS Schematic"

    def draw(self, context):
        layout = self.layout
        s = context.window_manager.oops_schematic
        layout.prop(s, 'select_3d_view')
        layout.prop(s, 'tree_width')
        layout.prop(s, 'curve_resolution')
        layout.label('Library Options:')


class OopsSchematicUsedNodesPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_oops_schematic_used_nodes"
    bl_label = "Used Nodes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "OOPS Schematic"

    def draw(self, context):
        layout = self.layout
        s = context.window_manager.oops_schematic
        row = layout.row()
        row.prop(s, 'show_libraries', icon='LIBRARY_DATA_DIRECT', toggle=True, icon_only=True)
        row = layout.row()
        row.prop(s, 'show_scenes', icon='SCENE_DATA', toggle=True, icon_only=True)
        row.prop(s, 'show_objects', icon='OBJECT_DATA', toggle=True, icon_only=True)
        row.prop(s, 'show_meshes', icon='MESH_DATA', toggle=True, icon_only=True)
        row = layout.row()
        row.prop(s, 'show_materials', icon='MATERIAL_DATA', toggle=True, icon_only=True)
        row.prop(s, 'show_textures', icon='TEXTURE_DATA', toggle=True, icon_only=True)
        row.prop(s, 'show_images', icon='IMAGE_DATA', toggle=True, icon_only=True)


class OopsSchematicNodesColorsPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_oops_schematic_nodes_colors"
    bl_label = "Nodes Colors"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "OOPS Schematic"

    def draw(self, context):
        layout = self.layout
        s = context.window_manager.oops_schematic
        layout.prop(s, 'color_blend_file_nodes')
        layout.prop(s, 'color_libraries_nodes')
        layout.prop(s, 'color_scenes_nodes')
        layout.prop(s, 'color_objects_nodes')
        layout.prop(s, 'color_meshes_nodes')
        layout.prop(s, 'color_materials_nodes')
        layout.prop(s, 'color_textures_nodes')
        layout.prop(s, 'color_images_nodes')


class OopsSchematicClick(bpy.types.PropertyGroup):
    x = bpy.props.FloatProperty(default=-1000.0)
    y = bpy.props.FloatProperty(default=-1000.0)


def draw_operator(self, context):
    if context.area.spaces[0].tree_type == 'OopsSchematic':
        self.layout.operator('node.oops_schematic_show')


class OopsSchematicPropertyGroup(bpy.types.PropertyGroup):
    show = bpy.props.BoolProperty(default=False)
    select_3d_view = bpy.props.BoolProperty(name='3D View Select', default=False)
    tree_width = bpy.props.FloatProperty(name='Tree Width', default=1000.0)

    show_libraries = bpy.props.BoolProperty(name='Libraries', default=False)
    show_scenes = bpy.props.BoolProperty(name='Scenes', default=True)
    show_objects = bpy.props.BoolProperty(name='Objects', default=True)
    show_meshes = bpy.props.BoolProperty(name='Meshes', default=True)
    show_materials = bpy.props.BoolProperty(name='Materials', default=True)
    show_textures = bpy.props.BoolProperty(name='Textures', default=True)
    show_images = bpy.props.BoolProperty(name='Images', default=True)

    color_blend_file_nodes = bpy.props.FloatVectorProperty(
        name='Blend File', default=[0.0, 0.2, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    color_libraries_nodes = bpy.props.FloatVectorProperty(
        name='Libraries', default=[0.6, 0.2, 0.0], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    color_scenes_nodes = bpy.props.FloatVectorProperty(
        name='Scenes', default=[0.2, 0.4, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    color_objects_nodes = bpy.props.FloatVectorProperty(
        name='Objects', default=[0.6, 0.4, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    color_meshes_nodes = bpy.props.FloatVectorProperty(
        name='Meshes', default=[0.6, 0.6, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')
    color_materials_nodes = bpy.props.FloatVectorProperty(
        name='Materials', default=[0.6, 0.2, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    color_textures_nodes = bpy.props.FloatVectorProperty(
        name='Textures', default=[0.2, 0.6, 0.2], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    color_images_nodes = bpy.props.FloatVectorProperty(
        name='Images', default=[0.6, 0.2, 0.6], min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        subtype='COLOR')

    curve_resolution = bpy.props.IntProperty(name='Curve Resolution', default=40,
        min=2, max=100, soft_min=2, soft_max=100)

    multi_click = bpy.props.CollectionProperty(type=OopsSchematicClick)


def register():
    bpy.utils.register_class(OopsSchematicClick)
    bpy.utils.register_class(OopsSchematicPropertyGroup)
    bpy.types.WindowManager.oops_schematic = bpy.props.PointerProperty(type=OopsSchematicPropertyGroup)
    bpy.utils.register_class(OopsSchematicNodeTree)
    bpy.utils.register_class(OopsSchematicShow)
    bpy.utils.register_class(OopsSchematicDisplayOptionsPanel)
    bpy.utils.register_class(OopsSchematicUsedNodesPanel)
    bpy.utils.register_class(OopsSchematicNodesColorsPanel)
    bpy.types.NODE_HT_header.append(draw_operator)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_operator)
    bpy.utils.unregister_class(OopsSchematicDisplayOptionsPanel)
    bpy.utils.unregister_class(OopsSchematicUsedNodesPanel)
    bpy.utils.unregister_class(OopsSchematicNodesColorsPanel)
    bpy.utils.unregister_class(OopsSchematicShow)
    bpy.utils.unregister_class(OopsSchematicNodeTree)
    del bpy.types.WindowManager.oops_schematic
    bpy.utils.unregister_class(OopsSchematicPropertyGroup)
    bpy.utils.unregister_class(OopsSchematicClick)
