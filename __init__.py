bl_info = {
	"name": "Easy Curve Array",
	"author": "Kenetics",
	"version": (0, 1),
	"blender": (2, 93, 0),
	"location": "View3D > Edit Mode > Add Mesh",
	"description": "Makes it easier to add array curve of objects to line of verts.",
	"warning": "",
	"wiki_url": "",
	"category": "Object"
}

import bpy
from bpy.props import EnumProperty, IntProperty, FloatVectorProperty, BoolProperty, FloatProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel, AddonPreferences


## Helper Functions



## Structs



## Operators
def get_curve_obj_enum_items(self, context):
	enum_list = []
	
	for obj in bpy.data.collections["EasyCurveObjects"].objects:
		enum_list.append( (obj.name, obj.name, "") )
	
	return enum_list

class ECA_OT_create_curve_array(Operator):
	"""Creates curve array from selected vertex line"""
	bl_idname = "eca.create_curve_array"
	bl_label = "Create Curve Array"
	bl_options = {'REGISTER','UNDO'}

	curve_obj : EnumProperty(
		items=get_curve_obj_enum_items,
		name="Curve Object",
		description="Object to place along curve"
	)

	curve_axis : EnumProperty(
		name="Curve Axis",
		items=[
			("POS_X", "+X", ""),
			("POS_Y", "+Y", ""),
			("POS_Z", "+Z", ""),
			("NEG_X", "-X", ""),
			("NEG_Y", "-Y", ""),
			("NEG_Z", "-Z", "")
		]
	)

	spacing : FloatVectorProperty(name="Spacing", size=3, default=(2,0,0))

	@classmethod
	def poll(cls, context):
		return context.active_object and context.mode == "EDIT_MESH"

	def invoke(self, context, event):
		if "EasyCurveObjects" not in bpy.data.collections:
			new_col = bpy.data.collections.new("EasyCurveObjects")
			context.scene.collection.children.link(new_col)
		elif "EasyCurveObjects" not in context.scene.collection.children:
			context.scene.collection.children.link(bpy.data.collections["EasyCurveObjects"])
		
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		## Separate mesh
		before_sep = {obj for obj in bpy.data.objects}
		bpy.ops.mesh.separate(type='SELECTED')
		after_sep = {obj for obj in bpy.data.objects}
		# set that has more should be first in difference operation
		curves_to_use = list(after_sep - before_sep)
		bpy.ops.object.editmode_toggle()
		# Deselect all objects
		for obj in bpy.data.objects:
			obj.select_set(False)
		# Set as active
		curves_to_use[0].select_set(True)
		context.view_layer.objects.active = curves_to_use[0]

		bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

		## Separate curves
		before_sep = {obj for obj in bpy.data.objects}
		bpy.ops.mesh.separate(type='LOOSE')
		after_sep = {obj for obj in bpy.data.objects}
		curves_to_use += list(after_sep - before_sep)
		## Convert meshes to curve
		bpy.ops.object.convert(target='CURVE')
		for curve_to_use in curves_to_use:
			for spline in curve_to_use.data.splines:
				spline.type = "BEZIER"
			## Duplicate mesh from CurveObjs Collection
			curve_obj_mesh = bpy.data.collections["EasyCurveObjects"].objects[self.curve_obj].data.copy()
			curve_obj = bpy.data.objects.new("EasyCurveObj", curve_obj_mesh)
			# Add curve obj to active collection
			context.collection.objects.link(curve_obj)
			
			# Parent
			curve_to_use.parent = curve_obj
			#curve_to_use.location = (0,0,0)

			## Add array mod curve mode to obj
			array_mod = curve_obj.modifiers.new("EasyCurveArray", "ARRAY")
			array_mod.curve = curve_to_use
			array_mod.fit_type = "FIT_CURVE"
			array_mod.relative_offset_displace = self.spacing
			curve_mod = curve_obj.modifiers.new("EasyCurveCurve", "CURVE")
			curve_mod.object = curve_to_use
			curve_mod.deform_axis = self.curve_axis

		return {'FINISHED'}

## UI



## Append to UI Helper Functions
def draw_add_mesh_menu(self, context):
	self.layout.operator(ECA_OT_create_curve_array.bl_idname)


## Register
classes = (
	ECA_OT_create_curve_array,
)

def register():
	## Add Custom Properties
	#bpy.Types.Scene.something = IntProperty()
	
	for cls in classes:
		bpy.utils.register_class(cls)
	
	## Append to UI
	bpy.types.VIEW3D_MT_mesh_add.append(draw_add_mesh_menu)
	

def unregister():
	## Remove from UI
	bpy.types.VIEW3D_MT_mesh_add.remove(draw_add_mesh_menu)
	
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	
	## Remove Custom Properties
	#del bpy.Types.Scene.something

if __name__ == "__main__":
	register()
