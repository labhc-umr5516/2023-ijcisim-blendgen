import bpy
import math
import random
import os
import numpy as np

bl_info = {
    "name": "BlendGen",
    "author": "Cédric Maron [Segula Technologies - Hubert Curien Laboratory]",
    "version": (0, 0, 0, 20),
    "blender": (3, 2, 1)    
}

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )
                       


def update_use_background_image(self, context):
    scene = bpy.context.scene.dataset_general.scene_ptr
    dataset_general = scene.dataset_general
    if(dataset_general.use_background_image==False):
        scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [0,0,0,1]
        scene.world.node_tree.links.new(scene.world.node_tree.nodes["Emission"].outputs[0],
                                        scene.world.node_tree.nodes["World Output"].inputs[0])
    elif(dataset_general.use_background_image==True and dataset_general.background_image_path != ""):
        scene.world.node_tree.links.new(scene.world.node_tree.nodes["Mix Shader"].outputs[0],
                                        scene.world.node_tree.nodes["World Output"].inputs[0])
    return

def update_generation_type(self, context):
    dataset_general = bpy.context.scene.dataset_general
    camera = bpy.data.objects[dataset_general.camera_ptr.name]
    if(dataset_general.generation_type=={'RANDOM'}):
        dataset_general.camera_is_following_curve = False
        follow_constraint = camera.constraints.get('CameraFollowPath')
        if(follow_constraint != None):
            camera.constraints.remove(follow_constraint)   
        camera.animation_data_clear()

def update_camera_is_tracking(self, context):
    dataset_general = bpy.context.scene.dataset_general
    camera = bpy.data.objects[dataset_general.camera_ptr.name]
    if(dataset_general.camera_is_tracking==True):
        tracking_constraint = camera.constraints.get('CameraTracking')
        if(tracking_constraint != None):
            camera.constraints.remove(tracking_constraint)
        tracking_constraint = camera.constraints.new(type='TRACK_TO')
        tracking_constraint.name = 'CameraTracking'
        tracking_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        tracking_constraint.up_axis = 'UP_Y'
    else:
        tracking_constraint = camera.constraints.get('CameraTracking')
        if(tracking_constraint != None):
            camera.constraints.remove(tracking_constraint)
    return

def update_camera_is_following_curve(self, context):
    dataset_general = bpy.context.scene.dataset_general
    camera = bpy.data.objects[dataset_general.camera_ptr.name]
    if(dataset_general.camera_is_following_curve==True):
        follow_constraint = camera.constraints.get('CameraFollowPath')
        if(follow_constraint != None):
            camera.constraints.remove(follow_constraint)
        follow_constraint = camera.constraints.new(type='FOLLOW_PATH')
        follow_constraint.name = 'CameraFollowPath'
        follow_constraint.forward_axis = 'FORWARD_Y'
        follow_constraint.up_axis = 'UP_Z'
    else:
        follow_constraint = camera.constraints.get('CameraFollowPath')
        if(follow_constraint != None):
            camera.constraints.remove(follow_constraint)   
        camera.animation_data_clear()
    return

def update_camera_ptr(self, context):
    dataset_general = bpy.context.scene.dataset_general
    if(dataset_general.camera_ptr!=None):
        camera = bpy.data.objects[dataset_general.camera_ptr.name]
        update_camera_is_tracking(self, context)
        update_camera_is_following_curve(self, context)
    else:
        dataset_general.camera_is_following_curve = False
        dataset_general.camera_is_tracking = False
    return

         
def update_background_image_path(self, context):
    scene = bpy.context.scene.dataset_general.scene_ptr
    dataset_general = scene.dataset_general
    
    world = scene.world
    world.use_nodes = True
    for node in world.node_tree.nodes:
        world.node_tree.nodes.remove(node)
    node_texCoord = world.node_tree.nodes.new('ShaderNodeTexCoord')
    node_mapping = world.node_tree.nodes.new('ShaderNodeMapping')
    node_mapping.vector_type = 'VECTOR'
    node_texEnv = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    node_emission = world.node_tree.nodes.new('ShaderNodeEmission')  
    node_output = world.node_tree.nodes.new('ShaderNodeOutputWorld') 
    node_lightpath = world.node_tree.nodes.new('ShaderNodeLightPath') 
    node_background_1 = world.node_tree.nodes.new('ShaderNodeBackground') 
    node_background_2 = world.node_tree.nodes.new('ShaderNodeBackground') 
    node_mixshader = world.node_tree.nodes.new('ShaderNodeMixShader')
     
    world.node_tree.links.new(node_texCoord.outputs[0],node_mapping.inputs[0])
    world.node_tree.links.new(node_mapping.outputs[0],node_texEnv.inputs[0])
    
    world.node_tree.links.new(node_lightpath.outputs[0],node_mixshader.inputs[0])
    world.node_tree.links.new(node_texEnv.outputs[0],node_background_1.inputs[0])
    world.node_tree.links.new(node_texEnv.outputs[0],node_background_2.inputs[0])
    world.node_tree.links.new(node_background_1.outputs[0],node_mixshader.inputs[1])
    world.node_tree.links.new(node_background_2.outputs[0],node_mixshader.inputs[2])
    world.node_tree.links.new(node_mixshader.outputs[0],node_output.inputs[0])
    
    d = node_mapping.inputs[2].driver_add("default_value",2)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_rotation' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",0)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[0]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",1)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[1]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",2)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[2]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression

    d = node_background_1.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.objects_intensity' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_background_2.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_intensity' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    if(dataset_general.background_image_path == ""):
        scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [0.02,0.02,0.02,1]
        scene.world.node_tree.links.new(node_emission.outputs[0],
                                        node_output.inputs[0])
    else:
        scene.world.node_tree.links.new(node_mixshader.outputs[0],
                                        node_output.inputs[0])
        node_texEnv.image = bpy.data.images.load(bpy.context.scene.dataset_general.background_image_path)
    

# ------------------------------------------------------------------------
#    Object Properties
# ------------------------------------------------------------------------
class ButtonCopyCameraPos(bpy.types.Operator):
    bl_idname = 'ops.copy_camera_pos'
    bl_label = 'Copy Camera Pos'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Copy the current camera position to min and max vectors'
    
    def execute(self, context):
        if bpy.context.scene.dataset_general.camera_ptr is not None:
            print(bpy.context.scene.dataset_general.camera_ptr.name)
            bpy.context.scene.dataset_general.camera_offset_min_location = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name].location
            bpy.context.scene.dataset_general.camera_offset_max_location = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name].location
        return {"FINISHED"}
    
class ButtonCopyCameraRot(bpy.types.Operator):
    bl_idname = 'ops.copy_camera_rot'
    bl_label = 'Copy Camera Rot'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Copy the current camera rotation to min and max vectors'
    
    def execute(self, context):
        if bpy.context.scene.dataset_general.camera_ptr is not None:
            bpy.context.scene.dataset_general.camera_offset_min_rotation = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name].rotation_euler
            bpy.context.scene.dataset_general.camera_offset_max_rotation = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name].rotation_euler
        return {"FINISHED"}
    
class ButtonCopyObjectPos(bpy.types.Operator):
    bl_idname = 'ops.copy_object_pos'
    bl_label = 'Copy Object Pos'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Copy the current object position to min and max vectors'
    
    def execute(self, context):
        bpy.context.object.dataset_object.offset_min_location = bpy.context.object.location
        bpy.context.object.dataset_object.offset_max_location = bpy.context.object.location
        return {"FINISHED"}
    
class ButtonCopyObjectRot(bpy.types.Operator):
    bl_idname = 'ops.copy_object_rot'
    bl_label = 'Copy Object Rot'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Copy the current object rotation to min and max vectors'
    
    def execute(self, context):
        bpy.context.object.dataset_object.offset_min_rotation = bpy.context.object.rotation_euler
        bpy.context.object.dataset_object.offset_max_rotation = bpy.context.object.rotation_euler
        return {"FINISHED"}
    
    
class ButtonGenerateCameraAnimation(bpy.types.Operator):
    bl_idname = 'ops.generate_camera_animation'
    bl_label = 'Generate Camera Animation'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Generate camera animation by placing keyframes at the first and last animation frames'
    
    def execute(self, context):
        dataset_general = bpy.context.scene.dataset_general
        if(dataset_general.camera_ptr!=None):
            camera = bpy.data.objects.get(dataset_general.camera_ptr.name)
            camera.animation_data_clear()
            if(dataset_general.camera_is_following_curve==True):
                follow_constraint = camera.constraints.get('CameraFollowPath')
                if(follow_constraint!=None):
                    if(follow_constraint.target!=None):
                        camera.location = [0,0,0]
                        camera.rotation_euler = [math.pi/2,0,0]
                        camera.animation_data_clear()
                        follow_constraint.offset = 0
                        follow_constraint.keyframe_insert(data_path="offset",frame=0)
                        follow_constraint.offset = -100
                        follow_constraint.keyframe_insert(data_path="offset",frame=bpy.context.scene.frame_end)
                        fc = camera.animation_data.action.fcurves
                        for curve in fc:
                            for k in curve.keyframe_points:
                                k.interpolation = 'LINEAR'
        return {"FINISHED"}

class ButtonSetLabelsToObjects(bpy.types.Operator):
    bl_idname = 'ops.set_labels_to_objects'
    bl_label = 'Set Labels To Objects'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Set a unique label value for every object in the scene'
    
    def execute(self, context):
        cnt = 1
        for mesh in bpy.data.meshes:
            obj = bpy.data.objects.get(mesh.name)
            if(obj != None):
                obj.dataset_object.label_value = cnt
                cnt += 1
        return {"FINISHED"}

def generate_depth_mat():
    mat = bpy.data.materials.get("Depth_mat")
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new("Depth_mat")
    mat.use_nodes = True
    node_to_remove = mat.node_tree.nodes.get("Principled BSDF")
    mat.node_tree.nodes.remove(node_to_remove)
    node_geometry = mat.node_tree.nodes.new('ShaderNodeNewGeometry')
    node_combineXYZ = mat.node_tree.nodes.new('ShaderNodeCombineXYZ')
    node_substraction = mat.node_tree.nodes.new('ShaderNodeVectorMath')
    node_substraction.operation = 'SUBTRACT'
    node_vector_rotate = mat.node_tree.nodes.new('ShaderNodeVectorRotate')
    node_vector_rotate.invert = True
    node_vector_rotate.rotation_type = 'EULER_XYZ'
    node_separateXYZ = mat.node_tree.nodes.new('ShaderNodeSeparateXYZ')
    node_lenght = mat.node_tree.nodes.new('ShaderNodeVectorMath')
    node_lenght.operation = 'LENGTH'
    node_addition = mat.node_tree.nodes.new('ShaderNodeMath')
    node_addition.operation = 'ADD'
    node_divide = mat.node_tree.nodes.new('ShaderNodeMath')
    node_divide.operation = 'DIVIDE'
    node_output = mat.node_tree.nodes.get('Material Output')
    
    mat.node_tree.links.new(node_combineXYZ.outputs[0],node_substraction.inputs[0])
    mat.node_tree.links.new(node_geometry.outputs[0],node_substraction.inputs[1])
    mat.node_tree.links.new(node_substraction.outputs[0],node_vector_rotate.inputs[0])
    mat.node_tree.links.new(node_vector_rotate.outputs[0],node_separateXYZ.inputs[0])
    mat.node_tree.links.new(node_vector_rotate.outputs[0],node_lenght.inputs[0])
    if(bpy.context.scene.dataset_general.camera_depth_type=={"FRONT-AXIS"}):
        mat.node_tree.links.new(node_separateXYZ.outputs[2],node_addition.inputs[0])
    elif(bpy.context.scene.dataset_general.camera_depth_type=={"NORM"}):
        mat.node_tree.links.new(node_lenght.outputs["Value"],node_addition.inputs[0])
    mat.node_tree.links.new(node_addition.outputs[0],node_divide.inputs[0])
    mat.node_tree.links.new(node_divide.outputs[0],node_output.inputs[0])
    
    
    d = node_combineXYZ.inputs[0].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'location[0]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_combineXYZ.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'location[1]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_combineXYZ.inputs[2].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'location[2]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_addition.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.depth_min' # link the custom property
    d.driver.expression = '-'+var.name # set the variable with the custom attribute value as an expression
    
    d = node_divide.inputs[1].driver_add("default_value")
    var_min = d.driver.variables.new() # add a driver variable
    var_min.name = "var_min" # add a name to this variable
    var_min.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var_min.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var_min.targets[0].data_path = 'dataset_general.depth_min' # link the custom property
    var_max = d.driver.variables.new() # add a driver variable
    var_max.name = "var_max" # add a name to this variable
    var_max.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var_max.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var_max.targets[0].data_path = 'dataset_general.depth_max' # link the custom property
    d.driver.expression = '('+var_max.name+' - '+var_min.name+')*2' # set the variable with the custom attribute value as an expression
    
    d = node_vector_rotate.inputs[4].driver_add("default_value",0)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'rotation_euler[0]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_vector_rotate.inputs[4].driver_add("default_value",1)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'rotation_euler[1]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_vector_rotate.inputs[4].driver_add("default_value",2)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'OBJECT' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name] # set the object as ID
    var.targets[0].data_path = 'rotation_euler[2]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    return

def generate_label_mat():
    list_label = []
    for obj in bpy.data.objects:
        if obj.dataset_object.label_value not in list_label:
            list_label.append(obj.dataset_object.label_value)
    for label in list_label:
        mat = bpy.data.materials.get('Label'+str(label))
        if mat is not None:
            bpy.data.materials.remove(mat)
        mat = bpy.data.materials.new('Label'+str(label))
        mat.use_nodes = True
        mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BSDF'])
        node_emission = mat.node_tree.nodes.new('ShaderNodeEmission')
        node_output = mat.node_tree.nodes['Material Output']
        mat.node_tree.links.new(node_emission.outputs["Emission"],node_output.inputs["Surface"])
        mat.node_tree.nodes["Emission"].inputs[0].default_value = (label/65535.0, label/65535.0, label/65535.0, 1)
 
def generate_world_shading():
    scene = bpy.context.scene.dataset_general.scene_ptr
    dataset_general = scene.dataset_general
    
    world = bpy.context.scene.world
    world.use_nodes = True
    for node in world.node_tree.nodes:
        world.node_tree.nodes.remove(node)
    node_texCoord = world.node_tree.nodes.new('ShaderNodeTexCoord')
    node_mapping = world.node_tree.nodes.new('ShaderNodeMapping')
    node_mapping.vector_type = 'VECTOR'
    node_texEnv = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    if(bpy.context.scene.dataset_general.background_image_path != ''):
        node_texEnv.image = bpy.data.images.load(bpy.context.scene.dataset_general.background_image_path)
        
    node_emission = world.node_tree.nodes.new('ShaderNodeEmission')  
    node_output = world.node_tree.nodes.new('ShaderNodeOutputWorld')  
    node_lightpath = world.node_tree.nodes.new('ShaderNodeLightPath') 
    node_background_1 = world.node_tree.nodes.new('ShaderNodeBackground') 
    node_background_2 = world.node_tree.nodes.new('ShaderNodeBackground') 
    node_mixshader = world.node_tree.nodes.new('ShaderNodeMixShader')
     
    world.node_tree.links.new(node_texCoord.outputs[0],node_mapping.inputs[0])
    world.node_tree.links.new(node_mapping.outputs[0],node_texEnv.inputs[0])
    
    world.node_tree.links.new(node_lightpath.outputs[0],node_mixshader.inputs[0])
    world.node_tree.links.new(node_texEnv.outputs[0],node_background_1.inputs[0])
    world.node_tree.links.new(node_texEnv.outputs[0],node_background_2.inputs[0])
    world.node_tree.links.new(node_background_1.outputs[0],node_mixshader.inputs[1])
    world.node_tree.links.new(node_background_2.outputs[0],node_mixshader.inputs[2])
    world.node_tree.links.new(node_mixshader.outputs[0],node_output.inputs[0])
    
    d = node_mapping.inputs[2].driver_add("default_value",2)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_rotation' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",0)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[0]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",1)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[1]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_mapping.inputs[3].driver_add("default_value",2)
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_scale[2]' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression

    d = node_background_1.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.objects_intensity' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    d = node_background_2.inputs[1].driver_add("default_value")
    var = d.driver.variables.new() # add a driver variable
    var.name = "var" # add a name to this variable
    var.targets[0].id_type = 'SCENE' # set ID type to a target object with the custom attribute
    var.targets[0].id = bpy.data.scenes[bpy.context.scene.dataset_general.scene_ptr.name] # set the object as ID
    var.targets[0].data_path = 'dataset_general.background_intensity' # link the custom property
    d.driver.expression = var.name # set the variable with the custom attribute value as an expression
    
    if(dataset_general.background_image_path == ""):
        scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [0.02,0.02,0.02,1]
        scene.world.node_tree.links.new(node_emission.outputs[0],
                                        node_output.inputs[0])
    else:
        scene.world.node_tree.links.new(node_mixshader.outputs[0],
                                        node_output.inputs[0])
        node_texEnv.image = bpy.data.images.load(bpy.context.scene.dataset_general.background_image_path)
    return
 
class DatasetPieces():
    def __init__(self,piece_name,location,rotation,base_location,base_rotation,tab_mat_name):
        self.piece_name = piece_name
        self.location = location
        self.rotation = rotation
        self.base_location = base_location
        self.base_rotation = base_rotation
        self.tab_mat_name = tab_mat_name
        
class Dataset():
    def __init__(self,camera_pos,camera_rot,world_rot_z,tab_piece):
        self.camera_pos = camera_pos
        self.camera_rot = camera_rot
        self.world_rot_z = world_rot_z
        self.tab_piece = tab_piece
        
def generate_tab_states():
    dataset_general = bpy.context.scene.dataset_general
    tab_states = []
    if(dataset_general.generate_depth==True):
        tab_states.append('depth')
    if(dataset_general.generate_label==True):
        tab_states.append('label')
    if(dataset_general.generate_rgb==True):
        tab_states.append('rgb')
    return tab_states

def generate_tab_dataset():
    dataset_general = bpy.context.scene.dataset_general
    tab_dataset = []
    camera = bpy.data.objects.get(dataset_general.camera_ptr.name)
    if(dataset_general.generation_type=={'RANDOM'}):
        start = 0
        finish = dataset_general.nb_data
    else:
        start = bpy.context.scene.frame_start
        finish = bpy.context.scene.frame_end
    
    for i in range(start, finish):
        if(dataset_general.generation_type=={"RANDOM"}):
            camera_pos = [(dataset_general.camera_offset_max_location[0] - dataset_general.camera_offset_min_location[0])*random.random()+dataset_general.camera_offset_min_location[0],
                            (dataset_general.camera_offset_max_location[1] - dataset_general.camera_offset_min_location[1])*random.random()+dataset_general.camera_offset_min_location[1],
                            (dataset_general.camera_offset_max_location[2] - dataset_general.camera_offset_min_location[2])*random.random()+dataset_general.camera_offset_min_location[2]]
            if(dataset_general.camera_is_tracking==False):
                camera_rot = [(dataset_general.camera_offset_max_rotation[0] - dataset_general.camera_offset_min_rotation[0])*random.random()+dataset_general.camera_offset_min_rotation[0],
                                (dataset_general.camera_offset_max_rotation[1] - dataset_general.camera_offset_min_rotation[1])*random.random()+dataset_general.camera_offset_min_rotation[1],
                                (dataset_general.camera_offset_max_rotation[2] - dataset_general.camera_offset_min_rotation[2])*random.random()+dataset_general.camera_offset_min_rotation[2]]
            else:
                loc, rot, scale = camera.matrix_world.decompose()
                camera_rot = rot.to_euler()
        else:
            bpy.context.scene.frame_current = i
            loc, rot, scale = camera.matrix_world.decompose()
            camera_pos = loc
            camera_rot = rot.to_euler()
        bpy.context.view_layer.update()
        world_rot_z = ((dataset_general.background_rotation_max - dataset_general.background_rotation_min) * random.random() + dataset_general.background_rotation_min) / 360 *  (2 * math.pi)
        tab_piece = []
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and bpy.context.scene.objects.get(obj.name) != None:
                index = 0
                tab_mat_name = []
                if(len(obj.material_slots)==0):
                    obj.data.materials.append(bpy.data.materials.new(name="Material"))
                for mat in obj.material_slots:
                    obj.active_material_index = index
                    tab_mat_name.append(obj.active_material.name)
                    index += 1
                if obj.dataset_object.movable_object==True:
                    min_location = np.array(obj.dataset_object.offset_min_location)
                    max_location = np.array(obj.dataset_object.offset_max_location)
                    min_rotation = np.array(obj.dataset_object.offset_min_rotation)
                    max_rotation = np.array(obj.dataset_object.offset_max_rotation)
                    tab_piece.append(DatasetPieces(piece_name=obj.name,
                                                    location = np.random.rand(3) * (max_location - min_location) + min_location,
                                                    rotation = np.random.rand(3) * (max_rotation - min_rotation) + min_rotation,
                                                    base_location = obj.location.copy(),
                                                    base_rotation = obj.rotation_euler.copy(),
                                                    tab_mat_name = tab_mat_name))
                                                
                else:
                    tab_piece.append(DatasetPieces(piece_name=obj.name,
                                                    location = obj.location.copy(),
                                                    rotation = obj.rotation_euler.copy(),
                                                    base_location = obj.location.copy(),
                                                    base_rotation = obj.rotation_euler.copy(),
                                                    tab_mat_name = tab_mat_name))
        tab_dataset.append(Dataset(camera_pos,camera_rot,world_rot_z,tab_piece))
    return tab_dataset

def generate_csv_file(tab_dataset):
    dataset_general = bpy.context.scene.dataset_general
    if(dataset_general.generate_csv==True):
        f = open(dataset_general.csv_dir+'summary.csv',"w")
        f.write('object name; label value\n')
        for piece in tab_dataset[0].tab_piece:
            f.write(str(piece.piece_name)+';'+str(bpy.data.objects.get(piece.piece_name).dataset_object.label_value)+'\n')
        for i in range(0,len(tab_dataset)):
            f.write('data number;'+str(i + dataset_general.nb_start_dataset)+'\n')
            f.write('camera pos;'+str(tab_dataset[i].camera_pos[0])+';'+str(tab_dataset[i].camera_pos[1])+';'+str(tab_dataset[i].camera_pos[2])+'\n')
            f.write('camera rot;'+str(tab_dataset[i].camera_rot[0])+';'+str(tab_dataset[i].camera_rot[1])+';'+str(tab_dataset[i].camera_rot[2])+'\n')
            f.write('world rot z;'+str(tab_dataset[i].world_rot_z)+'\n')
            f.write('object name;location x;location y;location z;rotation x;rotation y;rotation z\n')
            for piece in tab_dataset[i].tab_piece:
                f.write(str(piece.piece_name)+';'
                +str(piece.location[0])+';'+str(piece.location[1])+';'+str(piece.location[2])+';'
                +str(piece.rotation[0])+';'+str(piece.rotation[1])+';'+str(piece.rotation[2])+';'
                +str(piece.base_location[0])+';'+str(piece.base_location[1])+';'+str(piece.base_location[2])+';'
                +str(piece.base_rotation[0])+';'+str(piece.base_rotation[1])+';'+str(piece.base_rotation[2])+'\n')
        f.close() 

class ButtonGenerateImages(bpy.types.Operator):
    bl_idname = 'ops.generate_images'
    bl_label = 'Generate Images'
    bl_options = {"REGISTER","UNDO"}
    bl_description = 'Generate images based on all the parameters chosen'
    
    def execute(self, context):
        if bpy.context.scene.dataset_general.scene_ptr != None and bpy.context.scene.dataset_general.camera_ptr != None:
            
            dataset_general = bpy.context.scene.dataset_general
            
            generate_depth_mat()                    # Generate depth materials
            generate_label_mat()                    # Generate labels materials
            generate_world_shading()                # World shading
            tab_states = generate_tab_states()      # Generate states table (rgb, depth, label) 
            tab_dataset = generate_tab_dataset()    # Generate tab_dataset
            generate_csv_file(tab_dataset)          # Generate the csv file
                                                                            

            save_render_type = bpy.context.scene.render.engine
            bpy.context.scene.render.image_settings.compression = 0
            bpy.context.scene.render.image_settings.file_format = 'PNG'
            

            cnt = dataset_general.nb_start_dataset
            for i in range(0,len(tab_dataset)):
                dataset = tab_dataset[i]
                camera = bpy.data.objects[bpy.context.scene.dataset_general.camera_ptr.name]
                if(dataset_general.generation_type=={"ANIM"}):
                    bpy.context.scene.frame_current = i
                    bpy.context.view_layer.objects.active = camera
                    bpy.ops.object.visual_transform_apply()
                else:
                    camera.location = dataset.camera_pos
                    camera.rotation_euler = dataset.camera_rot
                dataset_general.background_rotation = dataset.world_rot_z
                
                for state in tab_states:
                    for obj_defect in dataset.tab_piece:
                        obj = bpy.context.scene.objects[obj_defect.piece_name]
                        obj.select_set(True)
                        obj.location[0] = obj_defect.location[0] 
                        obj.location[1] = obj_defect.location[1]
                        obj.location[2] = obj_defect.location[2]
                        
                        obj.rotation_euler[0] = obj_defect.rotation[0]
                        obj.rotation_euler[1] = obj_defect.rotation[1] 
                        obj.rotation_euler[2] = obj_defect.rotation[2]
                        index = 0
                        if(state=='rgb'):
                            for mat_name in obj_defect.tab_mat_name:
                                obj.active_material_index = index
                                obj.active_material = bpy.data.materials[mat_name]
                                index += 1
                            if(obj.dataset_object.visible_object_rgb==False):
                                obj.hide_render = True
                            else:
                                obj.hide_render = False
                        elif(state=='depth'):
                            for mat_name in obj_defect.tab_mat_name:
                                obj.active_material_index = index
                                obj.active_material = bpy.data.materials['Depth_mat']
                                index += 1
                            if(obj.dataset_object.visible_object_depth==False):
                                obj.hide_render = True
                            else:
                                obj.hide_render = False
                        elif(state=='label'):
                            for mat_name in obj_defect.tab_mat_name:
                                obj.active_material_index = index
                                obj.active_material = bpy.data.materials['Label'+str(obj.dataset_object.label_value)]
                                index += 1
                            if(obj.dataset_object.visible_object_label==False):
                                obj.hide_render = True
                            else:
                                obj.hide_render = False
                            
                    if(state=='rgb'):
                        if(dataset_general.rgb_render_type == {'EEVEE'}):
                            bpy.context.scene.render.engine = 'BLENDER_EEVEE'
                        elif(dataset_general.rgb_render_type == {'CYCLES'}):
                            bpy.context.scene.render.engine = 'CYCLES'
                        if(dataset_general.use_background_image==True):
                            bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Mix Shader"].outputs[0],
                                                                        bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
                        else:
                            bpy.context.scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [0,0,0,1]
                            bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Emission"].outputs[0],
                                                                    bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
                                                                        
                        bpy.context.scene.render.image_settings.color_mode = 'RGB'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.filter_size = 1.5
                        
                        bpy.context.scene.view_settings.view_transform = 'Standard'
                        file_path = dataset_general.rgb_dir+'rgb_'+str(cnt)+'.png'
                    elif(state=='depth'):
                        bpy.context.scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [1,1,1,1]
                        bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Emission"].outputs[0],
                                                                    bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.color_depth = '16'
                        bpy.context.scene.render.filter_size = 0
                        
                        bpy.context.scene.view_settings.view_transform = 'Raw'
                        file_path = dataset_general.depth_dir+'depth_'+str(cnt)+'.png'
                    elif(state=='label'):
                        bpy.context.scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [dataset_general.background_label_value/65535.0,
                                                                                                        dataset_general.background_label_value/65535.0,
                                                                                                        dataset_general.background_label_value/65535.0,
                                                                                                        1]
                        bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Emission"].outputs[0],
                                                                    bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.color_depth = '16'
                        bpy.context.scene.render.filter_size = 0
                        bpy.context.scene.view_settings.view_transform = 'Raw'
                        file_path = dataset_general.label_dir+'label_'+str(cnt)+'.png'
                        
                    bpy.context.scene.render.filepath = file_path
                    bpy.ops.render.render(use_viewport = True, write_still=True)
                cnt += 1
            
            if(len(tab_dataset)!=0):
                for obj_defect in tab_dataset[0].tab_piece:
                    obj = bpy.context.scene.objects.get(obj_defect.piece_name)
                    obj.location[0] = obj_defect.base_location[0]
                    obj.location[1] = obj_defect.base_location[1]
                    obj.location[2] = obj_defect.base_location[2]
                    obj.rotation_euler[0] = obj_defect.base_rotation[0]
                    obj.rotation_euler[1] = obj_defect.base_rotation[1]
                    obj.rotation_euler[2] = obj_defect.base_rotation[2]
                    print(obj.name, obj.location, obj.rotation_euler)
                    print(obj.name, obj_defect.base_location, obj_defect.base_rotation)
                    print(obj.name, obj_defect.location, obj_defect.rotation)
                    index = 0
                    for mat_name in obj_defect.tab_mat_name:
                        obj = bpy.context.scene.objects.get(obj_defect.piece_name)
                        obj.active_material_index = index
                        obj.active_material = bpy.data.materials.get(mat_name)
                        index += 1
                    
            if(dataset_general.use_background_image==True):
                bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Mix Shader"].outputs[0],
                bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
            else:
                bpy.context.scene.world.node_tree.nodes["Emission"].inputs[0].default_value = [0,0,0,1]
                bpy.context.scene.world.node_tree.links.new(bpy.context.scene.world.node_tree.nodes["Emission"].outputs[0],
                                                        bpy.context.scene.world.node_tree.nodes["World Output"].inputs[0])
                                                        
            bpy.context.scene.render.image_settings.color_mode = 'RGB'
            bpy.context.scene.render.image_settings.color_depth = '8'
            bpy.context.scene.render.filter_size = 1.5
            bpy.context.scene.view_settings.view_transform = 'Standard'
                    
            bpy.context.scene.render.engine = save_render_type
            
        return {"FINISHED"}
          
          
class DatasetGeneralProperties(PropertyGroup):
    nb_start_dataset: IntProperty(
        name = "Dataset starting number",
        description="Number from which the database will be generated",
        default = 0,
        min = 0
        )
    rgb_render_type: EnumProperty(
        items=[('CYCLES', "Cycles", "Use cycles to render rgb images"),
                ('EEVEE', "Eevee", "Use eevee to render rgb images")
                ],
        name="RGB Render Engine",
        description="Type of render used to generate rgb images",
        default={'EEVEE'},
        options={'ENUM_FLAG'},
        )
        
    scene_ptr: PointerProperty(name="Scene",
        type=bpy.types.Scene
        )

    generate_rgb: BoolProperty(
        name="RGB",
        description="If activated, RGB images will be generated",
        default = True
        )
        
    generate_depth: BoolProperty(
        name="Depth",
        description="If activated, depth images will be generated",
        default = True
        )
        
    generate_label: BoolProperty(
        name="Label",
        description="If activated, label images will be generated",
        default = True
        )
        
    depth_min: FloatProperty(
        name = "Depth min",
        description = "Minimum depth of for the depth rendering (correspond to the 0 value in 16 bit range).",
        default = 0,
        min = 0,
        max = 100.0
        )
        
    depth_max: FloatProperty(
        name = "Depth max",
        description = "Maximum depth of for the depth rendering (correspond to the 65535 value in 16 bit range).",
        default = 100,
        min = 0,
        max = 65535.0
        )
        
    camera_depth_type: EnumProperty(
        items=[('FRONT-AXIS', "Front-axis", "Use the front axis of the camera to calculate the depth"),
                ('NORM', "Norm", "Use the norm between objects and the camera as the depth")
                ],
        name="Camera depth type",
        description="Type of acquisition of the depth",
        default={'FRONT-AXIS'},
        options={'ENUM_FLAG'}
        )
        
    label_value: IntProperty(
        name = "Label value",
        description="Value of the label in grayscale between 0 and 65535",
        default = 0,
        min = 0,
        max = 65535
        )
        
    rgb_dir: StringProperty(
        name="RGB dir",
        description="Path to the rgb directory",
        default = "//dataset/rgb/",
        subtype = "DIR_PATH"
        )
        
    depth_dir: StringProperty(
        name="Depth dir",
        description="Path to the depth directory",
        default = "//dataset/depth/",
        subtype = "DIR_PATH"
        )
        
    label_dir: StringProperty(
        name="Label dir",
        description="Path to the label directory",
        default = "//dataset/label/",
        subtype = "DIR_PATH"
        )
        
    nb_data: IntProperty(
        name = "Number of data",
        description="Number of data to generate",
        default = 0,
        min = 0
        )
        
    camera_ptr: PointerProperty(name="Camera",
        type=bpy.types.Camera,
        update = update_camera_ptr
        )
        
    generation_type: EnumProperty(
        items=[('RANDOM', "Random", "Use random location and rotation or random location and a tracking point to position the camera"),
                ('ANIM', "Animation", "Use the animation tab to position the camera")
                ],
        name="Type of generation",
        description="Type of generation",
        default={'RANDOM'},
        options={'ENUM_FLAG'},
        update=update_generation_type
        )
       
    camera_is_tracking: BoolProperty(
        name="Camera is tracking",
        description="If activated, the camera will track the selected object",
        default = False,
        update = update_camera_is_tracking
        )
        
    camera_is_following_curve: BoolProperty(
        name="Camera is following curve",
        description="If activated, the camera location will follow the selected curve",
        default = False,
        update = update_camera_is_following_curve
        )
    
    camera_offset_min_location: FloatVectorProperty(
        name = "",
        description = "Offset min location of the camera",
        default = (0.0,0.0,0.0),
        unit='LENGTH',
        subtype='XYZ'
        )
        
    camera_offset_max_location: FloatVectorProperty(
        name = "",
        description = "Offset max location of the camera",
        default = (0.0,0.0,0.0),
        unit='LENGTH',
        subtype='XYZ'
        )
        
    camera_offset_min_rotation: FloatVectorProperty(
        name = "",
        description = "Offset min rotation of the camera",
        default = (0.0,0.0,0.0),
        unit='ROTATION',
        subtype='XYZ'
        )
        
    camera_offset_max_rotation: FloatVectorProperty(
        name = "",
        description = "Offset max rotation of the camera",
        default = (0.0,0.0,0.0),
        unit='ROTATION',
        subtype='XYZ'
        )
        
    use_background_image: BoolProperty(
        name="Use background image",
        description="If activated, an image will be used for the background",
        default = False,
        update = update_use_background_image
        )
        
    background_image_path: StringProperty(
        name="Background img",
        description="Background image",
        default = "",
        subtype = "FILE_PATH",
        update = update_background_image_path
        )
        
    background_label_value: IntProperty(
        name = "Background label value",
        description="Value of the background's label in grayscale between 0 and 65535",
        default = 0,
        min = 0,
        max = 65535
        )
    
    background_intensity: FloatProperty(
        name = "Background intensity",
        description = "Intensity factor of the background",
        default = 1,
        min = 0
        )
    
    objects_intensity: FloatProperty(
        name = "Objects intensity",
        description = "Intensity of the light received by objects",
        default = 1,
        min = 0
        )
        
    background_rotation: FloatProperty(
        name = "Background rotation",
        description="Background rotation angle",
        default = 0.0,
        min = -360.0,
        max = 360.0,
        unit = 'ROTATION'
        )
        
    background_rotation_min: FloatProperty(
        name = "Minimum background rotation",
        description="Minimum background rotation angle",
        default = 0.0,
        min = -360.0,
        max = 360.0,
        unit = 'ROTATION'
        )
    
    background_rotation_max: FloatProperty(
        name = "Maximum background rotation",
        description="Maximum background rotation angle",
        default = 0.0,
        min = -360.0,
        max = 360.0,
        unit = 'ROTATION'
        )
        
    background_scale: FloatVectorProperty(
        name = "Background scale",
        description = "Scaling factor of the background",
        default = (1.0,1.0,1.0),
        subtype='XYZ'
        )
        
    generate_csv: BoolProperty(
        name="Metadata file (.csv)",
        description="If activated, a .csv file containing the metadata of the dataset will be generated",
        default = False
        )
        
    csv_dir: StringProperty(
        name=".csv dir",
        description="Dir where the .csv file named summary.csv will be save",
        default = "",
        subtype = "DIR_PATH"
        )
        
    
        
class DatasetObjectProperties(PropertyGroup):
    movable_object: BoolProperty(
        name="Movable object",
        description="If activated, the object will move during the generation of the dataset.",
        default = False
        )
        
    base_location: FloatVectorProperty(
        name = "",
        description = "Base location",
        default = (0.0,0.0,0.0),
        unit='LENGTH',
        subtype='XYZ'
        )
        
    offset_min_location: FloatVectorProperty(
        name = "",
        description = "Offset min location",
        default = (0.0,0.0,0.0),
        unit='LENGTH',
        subtype='XYZ'
        )
        
    offset_max_location: FloatVectorProperty(
        name = "",
        description = "Offset max location",
        default = (0.0,0.0,0.0),
        unit='LENGTH',
        subtype='XYZ'
        )
    
    base_rotation: FloatVectorProperty(
        name = "",
        description = "Base rotation",
        default = (0.0,0.0,0.0),
        unit='ROTATION',
        subtype='XYZ'
        )
        
    offset_min_rotation: FloatVectorProperty(
        name = "",
        description = "Offset min rotation",
        default = (0.0,0.0,0.0),
        unit='ROTATION',
        subtype='XYZ'
        )
        
    offset_max_rotation: FloatVectorProperty(
        name = "",
        description = "Offset max rotation",
        default = (0.0,0.0,0.0),
        unit='ROTATION',
        subtype='XYZ'
        )
        
    visible_object_rgb: BoolProperty(
        name="RGB",
        description="If activated, the object will be visible during the RGB rendering",
        default = True
        )
        
    visible_object_depth: BoolProperty(
        name="Depth",
        description="If activated, the object will be visible during the depth rendering",
        default = True
        )
        
    visible_object_label: BoolProperty(
        name="Label",
        description="If activated, the object will be visible during the label rendering",
        default = True
        )
        
    label_value: IntProperty(
        name = "Label value",
        description="Value of the label in grayscale between 0 and 65535",
        default = 0,
        min = 0,
        max = 65535
        )

        
# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------


class OBJECT_PT_DatasetPanel(Panel):
    bl_label = "RGBD-BlendGen"
    bl_idname = "OBJECT_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dataset_general = context.scene.dataset_general

        obj = context.object
        # General
        layout = self.layout.box()
        col = layout.column(align = True)  
        col.operator("ops.generate_images")
        col.prop(dataset_general, "nb_start_dataset")
        
        col = layout.column(align = True) 
        col.prop(dataset_general, "scene_ptr")
        col.prop(dataset_general, "camera_ptr")
        
        col = layout.column(align = True)
        col.label(text="Generation type")
        row = col.split().row()
        row.prop(dataset_general, "generation_type")
        
        col = layout.column(align = True)
        row = col.split().row(align=True)
        row.label(text="Number of data")
        if(dataset_general.generation_type=={"ANIM"}):
            row.enabled = False
        row.prop(dataset_general, "nb_data",text="")
        row = col.split().row(align=True)
        row.label(text="Resolution X")
        row.prop(context.scene.render,"resolution_x",text="")
        row = col.split().row(align=True)
        row.label(text="Y")
        row.prop(context.scene.render,"resolution_y",text="")
        row = col.split().row(align=True)
        row.label(text="%")
        row.prop(context.scene.render,"resolution_percentage",text="")
    
        
        col = layout.column(align = True)
        col.label(text="Rendering type")
        row = col.split().row()
        row.prop(dataset_general, "generate_rgb")
        row.prop(dataset_general, "generate_depth")
        row.prop(dataset_general, "generate_label")
        row = col.split().row()
        row.label(text="RGB Render Engine")
        row.prop(dataset_general, "rgb_render_type")
        if(dataset_general.generate_rgb==False):
            row.enabled = False

        col = layout.column(align = True)
        row = col.split().row()
        row.prop(dataset_general, "rgb_dir")
        if(dataset_general.generate_rgb==False):
            row.enabled = False
        row = col.split().row()
        row.prop(dataset_general, "depth_dir")
        if(dataset_general.generate_depth==False):
            row.enabled = False
        row = col.split().row()
        row.prop(dataset_general, "label_dir")
        if(dataset_general.generate_label==False):
            row.enabled = False

        col = layout.column(align = True)
        row = col.split().row()
        row.prop(dataset_general, "generate_csv")
        col = layout.column()
        col.prop(dataset_general, "csv_dir")
        if(dataset_general.generate_csv==False):
            col.enabled = False

        # Background
        layout = self.layout.box()
        col = layout.column(align = True)
        col_a = col.split()
        col_a.label(text="Background properties")
        col_b = col.split()
        col_b.prop(dataset_general, "use_background_image")
        col_c = col.split().column(align = True)
        col_c.prop(dataset_general, "background_image_path",text="Image path")
        col_d = col.split().column(align = True)
        col_d.prop(dataset_general, "background_label_value")
        col_e = col.split().column(align = True)
        col_e.prop(dataset_general, "background_rotation")
        row = col_e.split().row(align=True)
        row.prop(dataset_general, "background_rotation_min",text="Min angle")
        row.prop(dataset_general, "background_rotation_max",text="Max angle")
        col_e.label(text="Background scale")
        row = col_e.split().row(align=True)
        row.prop(dataset_general, "background_scale",text="")
        col_e.label(text="Background intensity")
        row = col_e.split().row(align=True)
        row.prop(dataset_general, "background_intensity",text="")
        col_e.label(text="Objects intensity")
        row = col_e.split().row(align=True)
        row.prop(dataset_general, "objects_intensity",text="")
        if(dataset_general.use_background_image==False):
            col_e.enabled = False
            col_c.enabled = False

        # Camera
        layout = self.layout.box()
        col = layout.column(align = True)
        col.label(text="Camera properties")
        if(dataset_general.camera_ptr == None):
            col.label(text="No camera selected !")
        else:
            row_a = col.split().row(align=True)
            row_a.label(text="Depth type:")
            row_a.prop(dataset_general, "camera_depth_type",text="Depth acquisition")
            row_b = col.split().row(align=True)
            row_b.prop(dataset_general, "depth_min")
            row_b.prop(dataset_general, "depth_max")
            row_c = col.split().row(align=True)
            row_c.label(text='Resolution : '+str(round(((dataset_general.depth_max-dataset_general.depth_min)/65535.0),6))+'m')
            if(dataset_general.generate_depth==False):
                row_a.enabled = False
                row_b.enabled = False
                row_c.enabled = False
                
            camera = bpy.data.objects.get(dataset_general.camera_ptr.name)
            if(dataset_general.generation_type== {"RANDOM"}):
                col.label(text="Camera location")
                col.row().operator("ops.copy_camera_pos")
                col.row().prop(dataset_general, "camera_offset_min_location", text="Min")
                col.row().prop(dataset_general, "camera_offset_max_location", text="Max")
                
                col.prop(dataset_general, "camera_is_tracking")
                if(dataset_general.camera_is_tracking==False):
                    col.label(text="Camera rotation")
                    col.row().operator("ops.copy_camera_rot")
                    col.row().prop(dataset_general, "camera_offset_min_rotation", text="Min")
                    col.row().prop(dataset_general, "camera_offset_max_rotation", text="Max")
                else:
                    col.row().prop(camera.constraints.get('CameraTracking'), "target")
 
            else:
                col.prop(dataset_general, "camera_is_following_curve")
                if(dataset_general.camera_is_following_curve==True):
                    col.prop(camera.constraints.get('CameraFollowPath'), "target")
                    col.operator("ops.generate_camera_animation")
                col.prop(dataset_general, "camera_is_tracking")
                if(dataset_general.camera_is_tracking==True):
                    col.prop(camera.constraints.get('CameraTracking'), "target")
        
        
        # Object
        if context.object.type != 'CAMERA':
            dataset_object = context.object.dataset_object
            layout = self.layout.box()
            col = layout.column(align = True)
            col.label(text="Object properties")
            col.prop(dataset_object, "movable_object")
            if(dataset_object.movable_object==True):
                col.row().label(text="Object position")
                col.row().operator("ops.copy_object_pos")
                col.row().prop(dataset_object, "offset_min_location",text="Min")
                col.row().prop(dataset_object, "offset_max_location",text="Max")
                
                col.row().label(text="Object rotation")
                col.row().operator("ops.copy_object_rot")
                col.row().prop(dataset_object, "offset_min_rotation",text="Min")
                col.row().prop(dataset_object, "offset_max_rotation",text="Max")
            
 
            col.row().label(text="Label properties",)
            col.row().prop(dataset_object, "label_value")
            col.row().operator("ops.set_labels_to_objects")
            if(dataset_general.generate_label==False):
                col.enabled = False


            col.label(text="Visible in")
            row = col.split().row()
            col = row.split().column(align = True)
            col.prop(dataset_object, "visible_object_rgb")
            if(dataset_general.generate_rgb==False):
                col.enabled = False
            col = row.split().column(align = True)
            col.prop(dataset_object, "visible_object_depth")
            if(dataset_general.generate_depth==False):
                col.enabled = False
            col = row.split().column(align = True)
            col.prop(dataset_object, "visible_object_label")
            if(dataset_general.generate_label==False):
                col.enabled = False
        
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    DatasetObjectProperties,
    DatasetGeneralProperties,
    OBJECT_PT_DatasetPanel,
    ButtonGenerateImages,
    ButtonCopyCameraPos,
    ButtonCopyCameraRot,
    ButtonCopyObjectPos,
    ButtonCopyObjectRot,
    ButtonGenerateCameraAnimation,
    ButtonSetLabelsToObjects
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    bpy.types.Object.dataset_object = PointerProperty(type=DatasetObjectProperties)
    bpy.types.Scene.dataset_general = PointerProperty(type=DatasetGeneralProperties)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Object.dataset_object
    del bpy.types.Scene.dataset_general


if __name__ == "__main__":
    register()
