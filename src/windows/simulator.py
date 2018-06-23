"""
simulator.py contains the main class for the simulator. It handles rendering the main window together with the main
user interaction code.
"""
import itertools
import pyglet
import math
import src.util as util
import src.sensors.lightsensor
from pyglet.window import key
from pyglet.window import mouse
from src.resources import DynamicAsssets
from src.robots.initio import Initio
from src.robots.pi2go import Pi2Go
from src.sprites.basicsprite import BasicSprite
from src.windows.objectwindow import ObjectWindow


LIGHT_BEAM_ANGWIDTH = src.sensors.lightsensor.LIGHT_BEAM_ANGWIDTH

class Simulator(pyglet.window.Window):
    def __init__(self, world_file="default.xml", selected_robot="Initio"):
        # create the rendering batches and groups
        self.sprites = {}
        self.batches = {}
        self.subgroups = {}
        self._handles = {}

        self.batches['bg_batch'] = pyglet.graphics.Batch()
        self.batches['fg_batch'] = pyglet.graphics.Batch()
        self.subgroups['background_group'] = pyglet.graphics.OrderedGroup(0)
        self.subgroups['foreground_group'] = pyglet.graphics.OrderedGroup(1)

        # load all the dynamic assets
        self.dyn_assets = DynamicAsssets(world_file, self.batches['bg_batch'], self.batches['fg_batch'],
                                         self.subgroups['background_group'], self.subgroups['foreground_group'])

        # create the window
        super(Simulator, self).__init__(self.dyn_assets.background_image.width, self.dyn_assets.background_image.height,
                                        fullscreen=False)
        self.object_window = None
        self.edit_mode = False
        self.fps_display = pyglet.clock.ClockDisplay()

        # decide which type of robot to load
        if selected_robot == "Initio":
            self.robot = Initio(line_map_sprite=self.dyn_assets.line_map_sprite,
                                sonar_map=self.dyn_assets.sonar_map,
                                static_objects=self.dyn_assets.static_objects,
                                batch=self.batches['fg_batch'],
                                window_width=self.dyn_assets.background_image.width,
                                window_height=self.dyn_assets.background_image.height)
        elif selected_robot == "Pi2Go":
            self.robot = Pi2Go(line_map_sprite=self.dyn_assets.line_map_sprite,
                               sonar_map=self.dyn_assets.sonar_map,
                               static_objects=self.dyn_assets.static_objects,
                               batch=self.batches['fg_batch'],
                               window_width=self.dyn_assets.background_image.width,
                               window_height=self.dyn_assets.background_image.height)

        # bind the robot to the control switch
        self.dyn_assets.switch_sprite.set_target_robot(self.robot)
        
        # set the robot position based on the xml file
        self.robot.x = self.dyn_assets.robot_position[0]
        self.robot.y = self.dyn_assets.robot_position[1]
        self.robot.rotation = self.dyn_assets.robot_rotation

        # load all the keyboard and mouse handlers
        self.edit_mode_handlers = []
        
        # light ray handle
        self.light_ray = None
        self.x_ray_end = 0.0
        self.y_ray_end = 0.0
        self.is_ray_being_dragged = False
        self.ray_was_dragged = False
        self.light_source = None
        self.switch_on = False   # Robot switch control
        self.light_source_dragged = False
        
        # enable color transparency
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # to activate an event handler we need to 'push' it
        self.push_handlers(self.on_mouse_drag)
        self.push_handlers(self.on_mouse_press)
        self.push_handlers(self.on_mouse_release)
        
        for handler in self.robot.event_handlers:
            self.push_handlers(handler)
            
        for obj in self.dyn_assets.static_objects:
            for handler in obj.event_handlers:
                self.edit_mode_handlers.append(handler)

        for handler in self.dyn_assets.switch_sprite.event_handlers:
            self.push_handlers(handler)
            
        if self.dyn_assets.line_map_sprite is not None:
            for handler in self.dyn_assets.line_map_sprite.event_handlers:
                self.edit_mode_handlers.append(handler)

        self.switch_handlers()
        # light up the LEDs
        if self.robot.robot_name.startswith("PI2GO"):
            self.robot.light_leds()
        
        #pyglet.clock.schedule_interval(self.print_lightsensor_values, 0.5)  # for debugging purposes.
        self.robot.stop_robot()
        print("Robot is switched OFF...")


    def print_lightsensor_values(self, dt):
         print("printing light sensor values:\n")
         print("FL = %f; FR = %f; BL = %f; BR = %f\n\n" % (
               self.robot.light_frontleft_sensor.value,
               self.robot.light_frontright_sensor.value,
               self.robot.light_backleft_sensor.value,
               self.robot.light_backright_sensor.value))
               
               
    def switch_handlers(self):
        """Switches between the edit mode and non edit mode handlers."""
        if self.edit_mode:
            for handler in self.edit_mode_handlers:
                self.push_handlers(handler)
        else:
            for handler in self.edit_mode_handlers:
                self.remove_handlers(handler)

    def on_draw(self):
        """Entry point for the main rendering function."""
        self.render()

    def render(self):
        """Main rendering function."""
        self.clear()
        self.batches['bg_batch'].draw()
        self.batches['fg_batch'].draw()
        # self.fps_display.draw()

    def spawn_edit_window(self):
        """Opens the edit toolbar."""
        self.object_window = ObjectWindow(160, self.dyn_assets.background_image.height, self.dyn_assets)
        x, y = self.get_location()
        self.object_window.set_location(x + self.dyn_assets.background_image.width, y)
        

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            # we use the left mouse button to move the terminal points of the light ray around.
            if self.light_ray is not None:
                self.is_ray_being_dragged = True
                self.light_follow_mouse(x, y) 
    
    def robot_lightray_area_cover(self): 
        """ obtain the span of the robot that the light beam/ray can encapsulate (this depends 
        on the position of the light source with respect to the position of the robot,
        and the angle of the robot).
        for the ray to be touching/crossing the radius, the ray terminal has to fall into
        the field enclosed by angle 'thresh_theta' computed above, i.e. the field covered 
        by the maximum span of the robot given the direction of the light ray and the rotation 
        of the robot. so below we compute the maximum angle of seperation of the ray from 
        either of the vertices that mark the span of the robot.
        """
        thresh_theta, ray_boundaries_robot = self.robot.light_ray_boundary_vertices(self.light_source.x, self.light_source.y) 
        vertex_a = ray_boundaries_robot[0]
        vertex_b = ray_boundaries_robot[1]        
        ray_terminus = (self.x_ray_end, self.y_ray_end)   
         
        # "max" below because we need to use the boundary vertex that is farther from the ray terminal to calculate
        # the maximum span deviation of the ray from the robot
        angle_sep = max(self.robot.positive_angle_radians(self.robot.seperation_angle(vertex_a, ray_terminus, self.light_source.x, self.light_source.y)),
                        self.robot.positive_angle_radians(self.robot.seperation_angle(vertex_b, ray_terminus, self.light_source.x, self.light_source.y))) 
        return angle_sep, thresh_theta
           
    def light_follow_mouse(self, x, y):
        """ compute the ray end based on the direction of the ray: if it is touching the robot, stop it on the body
        of the robot; but if it is not touching the robot, allow it to continue to the boundaries of the window
        """
        self.x_ray_end = x
        self.y_ray_end = y
        
        # begin by checking that the light is ON
        if self.light_source is None: return
        
        angle_sep, thresh_theta = self.robot_lightray_area_cover()
        
        # compute the ray end based on the direction of the ray: if it is touching the robot, stop it on the body
        # of the robot; but if it is not touching the robot, allow it to continue to the boundaries of the window
        window_x, window_y = self.get_location()
        if angle_sep > thresh_theta:
            if angle_sep > thresh_theta+LIGHT_BEAM_ANGWIDTH/2:  # set sensor values to zero only when the ray is not touching the robot at all
                self.robot.receiving_light_focus = False
            else:
                self.robot.receiving_light_focus = True
            # increase the ray terminus in the direction of the gradient up to near window boundary
            delta_x = math.fabs(x - self.light_source.x)
            incr_x = 0
            incr_y = 0
            if delta_x == 0: 
                if self.light_source.y < y: 
                    incr_y = (self.dyn_assets.background_image.height - 10) - y 
                else:    
                    incr_y = y - 10
            elif math.fabs(y - self.light_source.y)/delta_x > 1:
                inv_grad = (delta_x/math.fabs(y - self.light_source.y))
                if self.light_source.x < x:
                    incr_x = ((self.dyn_assets.background_image.width - 10) - x) * inv_grad
                else:
                    incr_x = (x - 10)      
                incr_y = incr_x * math.fabs(y - self.light_source.y)/delta_x
            elif math.fabs(y - self.light_source.y)/delta_x <= 1:
                if self.light_source.x < x:
                    incr_x = ((self.dyn_assets.background_image.width - 10) - x)
                else:
                    incr_x = (x - 10)
                incr_y = incr_x * math.fabs(y - self.light_source.y)/delta_x
                
            if self.light_source.x < x:
                self.x_ray_end = x + incr_x
            else:
                self.x_ray_end = x - incr_x    
            
            if self.light_source.y < y:     
                #self.y_ray_end = window_y + (self.dyn_assets.background_image.width - 10) * light_ray_gradient
                self.y_ray_end = y + incr_y
            else:
                self.y_ray_end = y - incr_y
        else:
            self.robot.receiving_light_focus = True
            # as it were: improve this so that width/height are normalised based on the rotation of the robot
            # that is, the "width" should actually be the rotation component, and height the same.
            if self.light_source.x < self.robot.x:
                self.x_ray_end = self.robot.x - self.robot.image.width/4  
            else:
                self.x_ray_end = self.robot.x + self.robot.image.width/4      
            if self.light_source.y < self.robot.y:     
                self.y_ray_end = self.robot.y - self.robot.image.height/4  
            else:
                self.y_ray_end = self.robot.y + self.robot.image.height/4
        self.shine_light()            
            
            
    def on_mouse_press(self, x, y, button, modifiers):
        """Main entry point for a lot of the world editing interface code"""
        try:          
            if self.edit_mode and button == 4:
                # if we're in edit mode (edit toolbar visible) and the user presses the right mouse button an
                # an operation is created

                # here we decide what operation is being performed based on the output of the object toolbar
                operation = None
                sprite_name, sprite_idx = self.object_window.get_selected_sprite_name()
                if sprite_name.startswith("delete"):
                    operation = "delete"
                elif sprite_name.startswith("line_map"):
                    operation = "line_map"
                elif sprite_name.startswith("background"):
                    operation = "background"
                elif sprite_name.startswith("light"):
                    operation = "light_source"
                else:
                    operation = "add"
                print operation
                selected_obj = None
                too_close = False

                # for add and delete operations we need to know where all the objects (including the line map) are
                # so we make a copy of the dynamic objects list so we can modify it without affecting other
                # parts of the simualator
                #<Maduka>: No, a change to the object_list slice below WILL affect the original list.
                # if a COPY is really necessary then we need to use copy or deepcopy instead.
                #</Maduka>
                objects_list = self.dyn_assets.static_objects[:]

                # here we add the line map to our list of editable objects (only if we are looking to delete)
                if operation == "delete" and self.dyn_assets.line_map_sprite is not None:
                    objects_list.append(self.dyn_assets.line_map_sprite)

                # here we loop through all objects and do a radius check to see if the point at which the user
                # has clicked either contains an object or is very close to an existing object
                for obj in objects_list:
                    dsq = util.distancesq((x, y), (obj.x, obj.y))
                    thresh = min(obj.width, obj.height) ** 2
                    if operation == "delete":
                        thresh *= 0.25
                    if dsq < thresh:
                        selected_obj = obj
                        too_close = True

                # handling the background switching operation
                if operation == "background":
                    self.dyn_assets.background_sprite.delete()
                    sprite_image = self.object_window.get_selected_sprite_image()
                    util.center_image(sprite_image)
                    self.dyn_assets.background_sprite = BasicSprite(sprite_image,
                                                                    sprite_image.width / 2,
                                                                    sprite_image.height / 2,
                                                                    self.batches['bg_batch'],
                                                                    self.subgroups['background_group'], "background",
                                                                    sprite_idx)
                # handling the change line map operation
                elif operation == "line_map":
                    # if a line map already exists we need to delete it's handlers then delete the sprite itself
                    if self.dyn_assets.line_map_sprite is not None:
                        for handler in self.dyn_assets.line_map_sprite.event_handlers:
                            self.edit_mode_handlers.remove(handler)
                        self.dyn_assets.line_map_sprite.delete()

                    # create a new line map sprite
                    sprite_image = self.object_window.get_selected_sprite_image()
                    util.center_image(sprite_image)
                    self.dyn_assets.line_map_sprite = BasicSprite(sprite_image, x, y, self.batches['bg_batch'],
                                                                  self.subgroups['foreground_group'], "line_map",
                                                                  sprite_idx)

                    # update the actual line sensor used by the robot
                    self.robot.line_sensor_map.set_line_map(self.dyn_assets.line_map_sprite)

                    # add the new line maps handlers
                    for handler in self.dyn_assets.line_map_sprite.event_handlers:
                        self.edit_mode_handlers.append(handler)
                    self.switch_handlers()
                
                elif operation == "light_source" and not too_close:
                    # a new light source have been placed in the world
                    # first delete any other light source -- here, I assume only one light source can be in the world.
                    self.delete_light_source_any() 
                    # process the light sprite image and shine the light 
                    self.light_source = self.process_light_sprite(x, y, sprite_idx)
                    # initialising x_ray_end and y_ray_end for when the light source is introduced
                    # into the world.
                    if self.light_source.x < self.robot.x:
                        self.x_ray_end = self.robot.x - self.robot.image.width/4  
                    else:
                        self.x_ray_end = self.robot.x + self.robot.image.width/4 
                 
                    if self.light_source.y < self.robot.y:     
                        self.y_ray_end = self.robot.y - self.robot.image.height/4  
                    else:
                        self.y_ray_end = self.robot.y + self.robot.image.height/4
                    self.light_ray = None
                    # point the light ray to the robot - by default - once the light ray is dropped
                    self.robot.receiving_light_focus = True
                    self.shine_light()  
                  
                
                elif operation == "add" and not too_close:
                    # get the new object image
                    sprite_image = self.object_window.get_selected_sprite_image()
                    if sprite_image is not None:
                        # create the new sprite
                        sprt_obj = BasicSprite(sprite_image, x, y, self.batches['fg_batch'],
                                               self.subgroups['foreground_group'], "object", sprite_idx)

                        # add it to the list of dynamic objects and update the object handlers
                        self.dyn_assets.static_objects.append(sprt_obj)
                        for handler in sprt_obj.event_handlers:
                            self.edit_mode_handlers.append(handler)
                        self.switch_handlers()
                elif operation == "delete":
                    if selected_obj is not None:
                        # check if the object to delete is a line map or a regular static object
                        if selected_obj is self.dyn_assets.line_map_sprite:
                            self.robot.line_sensor_map.set_line_map(None)
                            self.dyn_assets.line_map_sprite = None
                        else:
                            self.dyn_assets.sonar_map.delete_rectangle(x, y, selected_obj.width, selected_obj.height)
                            self.dyn_assets.static_objects.remove(selected_obj)

                        # remove the object handlers
                        for handler in selected_obj.event_handlers:
                            if handler in self.edit_mode_handlers:
                                self.edit_mode_handlers.remove(handler)

                        # remove the object from the rendering batches and order
                        selected_obj.batch = None
                        selected_obj.group = None
                        
                        # if the deleted object was a light source, delete also the ray
                        if selected_obj.object_type.startswith("light"):
                            self.delete_light_source_any()
                            if self.light_ray is not None:
                                self.light_ray.delete()

                        # then delete the sprite and update the object handlers
                        selected_obj.delete()
                        del(self.light_ray)
                        self.switch_handlers()  
        except AttributeError as e:
            print str(e)

    def on_key_press(self, symbol, modifiers):
        """Handler user keypresses
            E  =  Enable/Disable edit mode
            Q  =  Quit the simulator
        ."""
        if symbol == key.E:
            if self.edit_mode:
                print "edit mode disabled"
                self.edit_mode = False
                self.object_window.close()
                self.object_window = None
                self.redraw_sonar_map()
                self.dyn_assets.save_to_file()
            else:
                print "edit mode enabled"
                self.edit_mode = True
                self.spawn_edit_window()
            self.switch_handlers()
        if symbol == key.Q:
            pyglet.app.exit()

    def redraw_sonar_map(self):
        """This function updates the sonar map ensuring all new objects are added."""
        self.dyn_assets.sonar_map.clear_map()
        for obj in self.dyn_assets.static_objects:
            self.dyn_assets.sonar_map.insert_rectangle(obj.x, obj.y, obj.width, obj.height)
    
         
    def delete_light_source_any(self):
        """delete any already existing light source 
        (for now we assume there can only be one light source in the world at a time)
        """
        obj_to_delete = None
        for obj in self.dyn_assets.static_objects:
            if obj.object_type is not None and obj.object_type.startswith("light"):
                obj_to_delete = obj
                break
        if obj_to_delete is not None:
            # remove any existing handlers
            if hasattr(obj_to_delete, 'event_handlers'):
                for handler in obj_to_delete.event_handlers:
                    self.edit_mode_handlers.remove(handler)
            # then delete the light source sprite 
                # remove it from visuals
            self.dyn_assets.sonar_map.delete_rectangle(obj_to_delete.x, obj_to_delete.y, obj_to_delete.width, obj_to_delete.height)
                # remove it from the static objects data structure
            self.dyn_assets.static_objects.remove(obj_to_delete)
            # remove the object from the rendering batches and order
            obj_to_delete.batch = None
            obj_to_delete.group = None

            # then delete the sprite and update the object handlers
            obj_to_delete.delete()
            # delete its ray too
            self.light_ray.delete() 
            del(self.light_ray)
    
 
    def process_light_sprite(self, mouse_xpos, mouse_ypos, sprite_idx):
        """ Get a new light source image
        """
        sprite_image = self.object_window.get_selected_sprite_image()
        light_sprite_obj = None
        if sprite_image is not None:
            # create the new sprite
            light_sprite_obj = BasicSprite(sprite_image, mouse_xpos, mouse_ypos, self.batches['fg_batch'],
                                   self.subgroups['foreground_group'], "light", sprite_idx)

            # add it to the list of dynamic objects and update the object handlers
            self.dyn_assets.static_objects.append(light_sprite_obj)
            for handler in light_sprite_obj.event_handlers:
                self.edit_mode_handlers.append(handler)
            self.switch_handlers() 
        return light_sprite_obj
    
    
      
    def shine_light(self):  #, light_sprite_obj
        """ Given a valid light source, produce a ray from that light source towards the center 
        of the robot in the world. I assume there can be only one robot, for now, in the world.
        """  
        # delete the current light ray
        if self.light_ray is not None:
            self.light_ray.delete()
            del(self.light_ray) 
                           
        if self.light_source is not None:    
            # let the light shine:
            # find the center of the light source sprite
            x_light_center = self.light_source.x 
            y_light_center = self.light_source.y 
        
            # find the light center c of the robot (later, the nearest light sensor on the robot)
            x_robot_center = self.robot.x 
            y_robot_center = self.robot.y 
            
            length_of_ray = math.sqrt((x_light_center - self.x_ray_end)**2 + (y_light_center - self.y_ray_end)**2)
            delta_x = (x_light_center - self.x_ray_end)
            angle_dir = math.pi/2 if delta_x == 0 else math.atan2((y_light_center - self.y_ray_end), delta_x)
                
            verts = self.make_ray(source_x=x_light_center, source_y=y_light_center, 
                                 length=length_of_ray, angle_width_rad=LIGHT_BEAM_ANGWIDTH,
                                 angle_dir_rad=angle_dir) 
                                  
            self.light_ray = self.batches['fg_batch'].add(len(verts)/2, pyglet.gl.GL_TRIANGLE_FAN, None, 
                    ('v2f', verts),
                    ('c4B', (255, 255, 0, 150)*(len(verts)/2)))
                
            # update the light sensors
            self.robot.update_light_sensors(self)
            
    
    def make_ray(self, source_x, source_y, length, angle_width_rad, angle_dir_rad):
        verts = []
        verts += [source_x, source_y]
        start_angle = angle_dir_rad - angle_width_rad/2
        stop_angle = angle_dir_rad + angle_width_rad/2
        for i in range(int(math.degrees(start_angle)), int(math.degrees(stop_angle))):
            angle = math.radians(i)
            x = length* -math.cos(angle) + source_x
            y = length* -math.sin(angle) + source_y
            verts += [x,y]      
        return verts
           
                 
    def update(self, dt):
        """This function updates the simulator at each time step during normal operation this involves
         updating the position of the robot and check for any collisions between the robot and static
         objects.

         In edit mode this function also handles the destruction of the edit mode toolbar, allows static objects to
         be dragged around the screen using the mouse. Allows the line map to be moved using the mouse. And finally
          does collision checking between the static objects (which can be moved as we are in edit mode).
         """
        try:                           
            if self.edit_mode:
                # handle to closing of the edit toolbar
                if self.object_window is not None and self.object_window.close_me:
                    print "edit mode disabled"
                    self.edit_mode = False
                    self.object_window.close()
                    self.object_window = None
                    self.switch_handlers()
                    self.redraw_sonar_map()
            
                # handle mouse move for the static objects
                for obj in self.dyn_assets.static_objects:
                    if obj.object_type.startswith("switch"):  # Do nothing for the switch sprite
                        continue
                    if obj.mouse_move_state:
                        obj.prev_x = obj.x
                        obj.prev_y = obj.y
                        
                        if obj.object_type.startswith("light"):
                            self.light_source_dragged = True
                            
                            # remove previous line/ray from the batch
                            self.light_ray.delete()
                            del(self.light_ray)
                            
                            # find the center of the light source sprite
                            x_light_center = obj.x 
                            y_light_center = obj.y 
                        
                            x_robot_center = self.robot.x 
                            y_robot_center = self.robot.y 
                           
                            # for effect: light ray points/flickers in the direction of motion as the light source is dragged around.
                            length_of_ray = math.sqrt((x_light_center - self.x_ray_end)**2 + (y_light_center - self.y_ray_end)**2)
                            delta_x = (x_light_center - self.x_ray_end)
                            angle_dir = math.pi/2 if delta_x == 0 else math.atan2((y_light_center - self.y_ray_end), delta_x)
                
                            self.light_ray_vertices = self.make_ray(source_x=x_light_center, source_y=y_light_center, 
                                                 length=length_of_ray, angle_width_rad=LIGHT_BEAM_ANGWIDTH,
                                                 angle_dir_rad=angle_dir) 
                                 
                            self.light_ray = self.batches['fg_batch'].add(len(self.light_ray_vertices)/2, pyglet.gl.GL_TRIANGLE_FAN, None, 
                                    ('v2f', self.light_ray_vertices),
                                    ('c4B', (255, 255, 0, 150)*(len(self.light_ray_vertices)/2)))
                            
                            sensor_angles = self.robot.update_light_sensors(self)
                                       
                        for other_obj in self.dyn_assets.static_objects:
                            if obj is not other_obj and obj.collides_with(other_obj):
                                obj.mouse_target_x = obj.prev_x
                                obj.mouse_target_y = obj.prev_y
                        obj.x = obj.mouse_target_x
                        obj.y = obj.mouse_target_y

                # collision checking for static objects
                for pair in itertools.combinations(self.dyn_assets.static_objects, 2):
                    if pair[0].collides_with(pair[1]):
                        if pair[0].mouse_move_state:
                            pair[0].x = pair[0].prev_x
                            pair[0].y = pair[0].prev_y
                        elif pair[1].mouse_move_state:
                            pair[1].x = pair[1].prev_x
                            pair[1].y = pair[1].prev_y

                # mouse move for the line map
                if self.dyn_assets.line_map_sprite is not None:
                    if self.dyn_assets.line_map_sprite.mouse_move_state:
                        self.dyn_assets.line_map_sprite.x = self.dyn_assets.line_map_sprite.mouse_target_x
                        self.dyn_assets.line_map_sprite.y = self.dyn_assets.line_map_sprite.mouse_target_y

            # update the robot position
            self.robot.update(dt, self)
            #self.robot.indicate_position() 

            # robot to static object collision checking
            for obj in self.dyn_assets.static_objects:
                if self.robot.robot_collides_with(obj):
                    vec_x = self.robot.x - obj.x
                    vec_y = self.robot.y - obj.y
                    self.robot.velocity_x += vec_x * 2
                    self.robot.velocity_y += vec_y * 2
                    
        except AttributeError:
            pass

    def on_mouse_release(self, x, y, button, modifiers):
        """ Make some ancillary updates if needed e.g update the light ray if the light source was being 
        dragged around prior to the mouse release."""
        # update ray being dragged status
        if self.is_ray_being_dragged: 
            self.is_ray_being_dragged = False
            self.ray_was_dragged = True
        
        # update light source being dragged status
        if self.light_source_dragged == True:
            self.light_source_dragged = False
            self.ray_was_dragged = False
            
            self.x_ray_end = self.robot.x - self.robot.image.width/4 if self.light_source.x < self.robot.x  else self.robot.x + self.robot.image.width/4 
            self.y_ray_end = self.robot.y - self.robot.image.height/4 if self.light_source.y < self.robot.y  else self.robot.y + self.robot.image.height/4
          
            # point the light ray to the robot - by default - once the light ray is dropped
            angle_sep, thresh_theta = self.robot_lightray_area_cover()
            
            # compute the ray end based on the direction of the ray: if it is touching the robot, stop it on the body
            # of the robot; but if it is not touching the robot, allow it to continue to the boundaries of the window
            if angle_sep > thresh_theta+LIGHT_BEAM_ANGWIDTH/2:  # set sensor values to zero only when the ray is not touching the robot at all
                self.robot.receiving_light_focus = False
                self.robot.reset_light_sensors()
            else:
                self.robot.receiving_light_focus = True
            self.shine_light()