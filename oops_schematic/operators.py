
import bpy

from . import build


def toggle_select(s):
    data_blocks = [
        bpy.data.scenes,
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.libraries,
        bpy.data.cameras,
        bpy.data.lamps,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.worlds,
    ]

    select = True

    for data in data_blocks:
        for block in data:
            if block.oops_schematic.select:
                select = False
                break

    if not select:
        s.multi_click.clear()
    else:
        for data in data_blocks:
            for block in data:
                click = s.multi_click.add()
                click.x = block.oops_schematic.position_x
                click.y = block.oops_schematic.position_y


class OopsSchematicShow(bpy.types.Operator):
    bl_idname = "node.oops_schematic_show"
    bl_label = "Show/Hide Oops Schematic"

    _handle = None

    @staticmethod
    def handle_add():
        OopsSchematicShow._handle = bpy.types.SpaceNodeEditor.draw_handler_add(build.build_schematic_scene, (), 'WINDOW', 'POST_VIEW')

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
        elif event.type == 'G' and event.value == 'RELEASE':
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        self.start_mouse_x, self.start_mouse_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                        s.grab_mode = True
        elif event.type == 'MOUSEMOVE' and s.grab_mode:
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        mouse_x, mouse_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                        s.move_offset_x = mouse_x - self.start_mouse_x
                        s.move_offset_y = mouse_y - self.start_mouse_y
                        region.tag_redraw()
        elif (event.type == 'LEFTMOUSE' or event.type == 'RIGHTMOUSE') and s.grab_mode:
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        if event.type == 'LEFTMOUSE':
                            s.apply_location = True
                        s.grab_mode = False
                        region.tag_redraw()
        elif event.type == 'A' and event.value == 'RELEASE':
            area = context.area
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        toggle_select(s)
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
