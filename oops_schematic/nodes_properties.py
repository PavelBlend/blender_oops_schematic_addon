
import bpy


class OopsSchematicNodePropertyGroup(bpy.types.PropertyGroup):
    offset = bpy.props.BoolProperty(default=False)
    position_x = bpy.props.FloatProperty(default=0.0)
    position_y = bpy.props.FloatProperty(default=0.0)
