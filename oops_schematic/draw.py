
import os

import bpy

from . import nodes
from . import select
from .constants import *


def draw_schematic_scene():
    s = bpy.context.window_manager.oops_schematic    # s - schematic
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'OopsSchematic':

                # 0 Libraries 1 Scenes, 2 Objects, 3 Meshes, 4 Cameras, 5 Materials, 6 Textures, 7 Images, 8 Worlds
                schematic_nodes = [[], [], [], [], [], [], [], [], []]
                blend_file = nodes.SchematicNode('Blend File: {}'.format(os.path.basename(bpy.data.filepath)), list(s.color_blend_file_nodes), 0, 'BLEND_FILE')
                if s.show_libraries:
                    libraries_nodes = {None: blend_file}
                    schematic_nodes[0].append(blend_file)

                scenes_nodes = {library.name: {} for library in bpy.data.libraries}
                scenes_nodes[None] = {}

                worlds_nodes = {library.name: {} for library in bpy.data.libraries}
                worlds_nodes[None] = {}

                objects_nodes = {library.name: {} for library in bpy.data.libraries}
                objects_nodes[None] = {}

                meshes_nodes = {library.name: {} for library in bpy.data.libraries}
                meshes_nodes[None] = {}

                cameras_nodes = {library.name: {} for library in bpy.data.libraries}
                cameras_nodes[None] = {}

                materials_nodes = {library.name: {} for library in bpy.data.libraries}
                materials_nodes[None] = {}

                textures_nodes = {library.name: {} for library in bpy.data.libraries}
                textures_nodes[None] = {}

                images_nodes = {library.name: {} for library in bpy.data.libraries}
                images_nodes[None] = {}

                # Generate libraries nodes
                if s.show_libraries:
                    for library_index, library in enumerate(bpy.data.libraries):
                        library_node = nodes.SchematicNode('{}: {}'.format(library.name, os.path.basename(library.filepath.replace('//', ''))), list(s.color_libraries_nodes), library_index + 1, 'LIBRARY')
                        libraries_nodes[library.name] = library_node
                        schematic_nodes[0].append(library_node)

                # Generate images nodes
                if s.show_images:
                    for image_index, image in enumerate(bpy.data.images):
                        image_node = nodes.SchematicNode(image.name, list(s.color_images_nodes), image_index, 'IMAGE')
                        library_name = getattr(image.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            image_node.parents.append(library_node)
                            library_node.children.append(image_node)
                        images_nodes[library_name][image.name] = image_node
                        schematic_nodes[7].append(image_node)

                # Generate textures nodes
                if s.show_textures:
                    for texture_index, texture in enumerate(bpy.data.textures):
                        texture_node = nodes.SchematicNode(texture.name, list(s.color_textures_nodes), texture_index, 'TEXTURE')
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

                        schematic_nodes[6].append(texture_node)
                        textures_nodes[library_name][texture.name] = texture_node

                # Generate materials nodes
                if s.show_materials:
                    for material_index, material in enumerate(bpy.data.materials):
                        material_node = nodes.SchematicNode(material.name, list(s.color_materials_nodes), material_index, 'MATERIAL')
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

                        schematic_nodes[5].append(material_node)
                        materials_nodes[library_name][material.name] = material_node

                # Generate meshes nodes
                if s.show_meshes:
                    for mesh_index, mesh in enumerate(bpy.data.meshes):
                        mesh_node = nodes.SchematicNode(mesh.name, list(s.color_meshes_nodes), mesh_index, 'MESH')
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

                # Generate cameras nodes
                if s.show_cameras:
                    for camera_index, camera in enumerate(bpy.data.cameras):
                        camera_node = nodes.SchematicNode(camera.name, list(s.color_cameras_nodes), camera_index, 'CAMERA')
                        library_name = getattr(camera.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            camera_node.parents.append(library_node)
                            library_node.children.append(camera_node)
                        schematic_nodes[4].append(camera_node)
                        cameras_nodes[library_name][camera.name] = camera_node

                # Generate objects nodes
                if s.show_objects:
                    for object_index, object in enumerate(bpy.data.objects):
                        object_node = nodes.SchematicNode(object.name, list(s.color_objects_nodes), object_index, 'OBJECT')

                        # Assign Children and Parents
                        if object.type == 'MESH':
                            mesh_node = meshes_nodes.get(getattr(object.data.library, 'name', None)).get(object.data.name, None)
                            if mesh_node:
                                mesh_node.parents.append(object_node)
                                object_node.children.append(mesh_node)
                        elif object.type == 'CAMERA':
                            camera_node = cameras_nodes.get(getattr(object.data.library, 'name', None)).get(object.data.name, None)
                            if camera_node:
                                camera_node.parents.append(object_node)
                                object_node.children.append(camera_node)

                        library_name = getattr(object.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            object_node.parents.append(library_node)
                            library_node.children.append(object_node)

                        objects_nodes[library_name][object.name] = object_node
                        schematic_nodes[2].append(object_node)

                # Generate worlds nodes
                if s.show_worlds:
                    for world_index, world in enumerate(bpy.data.worlds):
                        world_node = nodes.SchematicNode(world.name, list(s.color_worlds_nodes), world_index, 'WORLD')
                        library_name = getattr(world.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            world_node.parents.append(library_node)
                            library_node.children.append(world_node)
                        worlds_nodes[library_name][world.name] = world_node
                        schematic_nodes[8].append(world_node)

                # Generate scenes nodes
                if s.show_scenes:
                    for scene_index, scene in enumerate(bpy.data.scenes):
                        scene_node = nodes.SchematicNode(scene.name, list(s.color_scenes_nodes), scene_index, 'SCENE')
                        library_name = getattr(scene.library, 'name', None)
                        if s.show_libraries:
                            library_node = libraries_nodes[library_name]
                            scene_node.parents.append(library_node)
                            library_node.children.append(scene_node)
                        for object in scene.objects:
                            object_node = objects_nodes.get(getattr(object.library, 'name', None)).get(object.name, None)
                            if object_node:
                                # Assign Children and Parent Links
                                for child in object.children:
                                    child_library_name = getattr(child.library, 'name', None)
                                    child_object_node = objects_nodes[child_library_name].get(child.name)
                                    object_node.children.append(child_object_node)
                                    child_object_node.parents.append(object_node)
                                scene_node.children.append(object_node)
                                object_node.parents.append(scene_node)
                                # Select Object Node in 3D View
                                if s.select_3d_view and object in bpy.context.selected_objects:
                                    object_node.active = True
                                    object_node.color[0] += LIGHT_ADD_COLOR
                                    object_node.color[1] += LIGHT_ADD_COLOR
                                    object_node.color[2] += LIGHT_ADD_COLOR
                                    object_node.border_select = True
                                    select.select_children(object_node)
                                    select.select_parents(object_node)
                        world = scene.world
                        if world:
                            world_node = worlds_nodes.get(getattr(world.library, 'name', None)).get(world.name, None)
                            if world_node:
                                scene_node.children.append(world_node)
                                world_node.parents.append(scene_node)
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
                                select.select_children(schematic_node)
                                select.select_parents(schematic_node)
                        last_offset_x += node_size_x
                    last_offset_x = 0
                    if schematic_nodes_group:
                        last_offset_y += Y_DISTANCE

                # Draw nodes
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw_lines()
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw_box()
                for schematic_nodes_group in schematic_nodes:
                    for schematic_node in schematic_nodes_group:
                        schematic_node.draw_text()
