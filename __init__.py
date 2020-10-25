
bl_info = {
	"name": "Extrude block",
	"author": "JuhaW",
	"version": (1, 0),
	"blender": (2, 83, 0),
	"location": "Edit mode > 'D'",
	"description": "Extrude selected faces",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"
	}


import bpy
import bmesh
from bpy.props import FloatProperty, PointerProperty
from mathutils import Vector
from math import degrees


def edge_length(face):
	
	def error_text(text):
		print (text, "used length 1")
	
	for edge in face.edges:
		
		#edge = face.edges[0]
		print ("face, edge", face.index, edge.index)
		#face has no linked faces so its a plane
		if len(edge.link_faces) == 1:
			error_text("no linked faces")
			continue
		
		face2 = [i for i in edge.link_faces if i is not face][0]
		#compare two face normal angle differences
		angle = degrees(face.normal.angle(face2.normal))
		print ("angle difference", angle)
		if angle < 10:
			error_text("too small angle difference")
			continue
		
		index = face2.edges[:].index(edge)-1
		
		#compare face normals
		f1_normal = face.normal
		f2_normal = face2.normal
		print ("edge connected to face:",face2.index)
		edge1 = face2.edges[index]
		print ("edge", edge1.index)
		print ("original face normal", f1_normal)
		print ("second   face normal", f2_normal)
		return edge1.calc_length(), True
	
	error_text("Loop finished, extruding without duplicate")
	
	return 1, False
	"""
	v = face.verts[0]
	for i in v.link_edges:
		if i not in face.edges:
			return i.calc_length()
	return 1
	"""
class block_settings(bpy.types.PropertyGroup):

	offset :		FloatProperty(default = 0)
	length : 		FloatProperty(default = 0, description = "Absolute length")
	percentage : FloatProperty(default = 100)

	

class Mesh_OT_ExtrudeBlock(bpy.types.Operator):
	"""Object Cursor Array"""
	bl_idname = "mesh.extrude_block"
	bl_label = "Extrude block"
	bl_options = {'REGISTER', 'UNDO'}

	percentage	: FloatProperty(default = 100,min=0,soft_max=1000,step=1, name ="Relative length", subtype = "PERCENTAGE")
	length 		: FloatProperty(default = 0, name = "Additional length")
	offset 		: FloatProperty(default = 0)
		
	
	def execute(self, context):
	
		o = bpy.context.object
		bm = bmesh.from_edit_mesh(o.data)

		faces = [i for i in bm.faces if i.select]

		for i in faces:
			
			i.select_set(False)

			#relationship length
			length, duplicate_face = edge_length(i)
			length = (length * self.percentage) / 100
			#additional absolute length
			length += self.length
			
			if duplicate_face:
				geom = bmesh.ops.duplicate(bm, geom = [i])
				verts = [j for j in geom['geom'] if isinstance(j, bmesh.types.BMVert)]
				face =  [j for j in geom['geom'] if isinstance(j, bmesh.types.BMFace)]
				calculate_normals = False
			else:
				verts = i.verts
				face = [i]
				i.normal_flip()
				calculate_normals = True
				#bm.normal_update() # not sure if req'd

			n = i.normal
			norm = n * self.offset
			bmesh.ops.translate(bm, vec=Vector(norm), verts=verts)
			
			geom = bmesh.ops.extrude_face_region(bm,geom=face,use_normal_flip=calculate_normals, use_select_history = True )
			verts = [j for j in geom['geom'] if isinstance(j, bmesh.types.BMVert)]
			face =  [j for j in geom['geom'] if isinstance(j, bmesh.types.BMFace)]
			print ("face", face[:])
			face[0].select_set(True)
			#offset
			n = n * length 	
			bmesh.ops.translate(bm, vec=Vector(n), verts=verts)
			if calculate_normals:
				face.append(i)
				bmesh.ops.recalc_face_normals(bm , faces = face )


		bmesh.update_edit_mesh(o.data )


		return {'FINISHED'}



addon_keymaps = []

def register():

	bpy.utils.register_class(Mesh_OT_ExtrudeBlock)
	bpy.utils.register_class(block_settings)

	# handle the keymap
	wm = bpy.context.window_manager
	km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY', region_type = 'WINDOW')
	kmi = km.keymap_items.new(Mesh_OT_ExtrudeBlock.bl_idname, 'D', 'PRESS', ctrl=False, shift=False)
	kmi.active = True
	addon_keymaps.append((km, kmi))
	bpy.types.Scene.block 	= PointerProperty(type = block_settings)
	print ("Extrude block registered")

def unregister():

	# handle the keymap
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()
	
	bpy.utils.unregister_class(Mesh_OT_ExtrudeBlock)
	bpy.utils.unregister_class(block_settings)
	
	del bpy.types.Scene.block
	
if (__name__ == "__main__"):

	register()
	print ("register")
