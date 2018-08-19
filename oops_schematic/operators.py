
import bpy

from . import draw


class OopsSchematicShow(bpy.types.Operator):
    bl_idname = "node.oops_schematic_show"
    bl_label = "Show/Hide Oops Schematic"

    _handle = None

    @staticmethod
    def handle_add():
        OopsSchematicShow._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw.draw_schematic_scene, (), 'WINDOW', 'POST_VIEW')

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
