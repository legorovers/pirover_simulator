"""
basicsprite.py is a subclass of pyglets sprite class and adds some additional data members and convenience functions
in particular it adds a velocity model, window bounds checking, mouse handlers and AABB collision checking.
"""

import pyglet
import math
import src.resources


class BasicSprite(pyglet.sprite.Sprite):
    def __init__(self, texture, x, y, batch, subgroup, object_type="sprite", idx=-1, window_width=800,
                 window_height=600):
        self.texture = texture
        super(BasicSprite, self).__init__(self.texture, batch=batch, group=subgroup)
        self.x = x
        self.y = y
        self.window_width = window_width
        self.window_height = window_height
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.mouse_move_state = False
        self.min_rad_sq = (0.5 * min(self.width, self.height)) ** 2
        self.in_collision = False
        self.event_handlers = [self, self.on_mouse_press, self.on_mouse_release, self.on_mouse_drag]
        self.prev_x = x
        self.prev_y = y
        self.mouse_target_x = x
        self.mouse_target_y = y
        self.object_type = object_type
        self.idx = idx
        self.is_rotating = False
        self.receiving_light_focus = False  # keep track of when this sprite is receiving light focus
		
    def update(self, dt):
        """Update position based on current velocity also check window bounds."""
        self.setx(self.x + self.velocity_x * dt)
        self.sety(self.y + self.velocity_y * dt)
        self.check_bounds()

	def is_rotating(self):
	    return self.is_rotating
	    
    def check_bounds(self):
        """Check window bounds"""
        rad = max(self.image.width, self.image.height) / 2.0
        min_x = rad
        min_y = rad
        max_x = self.window_width - rad
        max_y = self.window_height - rad
        if self.x < min_x:
            self.setx(min_x)
        if self.y < min_y:
            self.sety(min_y)
        if self.x > max_x:
            self.setx(max_x)
        if self.y > max_y:
            self.sety(max_y)

    def on_mouse_press(self, x, y, button, modifiers):
        """Uses a radius check to see if the sprite has been clicked, then sets the mouse move state to True so the
        sprite can be moved using the mouse."""
        if button == 1:
            dsq = (self.x - x) ** 2 + (self.y - y) ** 2
            # print dsq
            if dsq < self.min_rad_sq:
                self.mouse_move_state = True

    def on_mouse_release(self, x, y, button, modifiers):
        """Sets the mouse move state to false once the mouse button is released."""
        self.mouse_move_state = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Sets target x,y position for the sprite based on the mouse pointer."""
        if self.mouse_move_state:
            self.mouse_target_x = x
            self.mouse_target_y = y

    def collides_with(self, other_object, use_mouse=False):
        """Simple axis aligned bounding box collision detections to check if this sprite collides with another."""
        # AABB collision detection
        if use_mouse:
            if self.mouse_target_x < other_object.x + other_object.width and \
                                    self.mouse_target_x + self.width > other_object.x and \
                            self.mouse_target_y < other_object.y + other_object.height and \
                                    self.height + self.mouse_target_y > other_object.y:
                return True
        else:
            if self.x < other_object.x + other_object.width and \
                                    self.x + self.width > other_object.x and \
                            self.y < other_object.y + other_object.height and \
                                    self.height + self.y > other_object.y:
                return True
        return False
    
    
    def get_vertices(self):
        """ Returns the vertices of the image of the sprite
        """
        vertices = []
        angle_radians = -math.radians(self.rotation) 
        dx = self.width/2
        dy = self.height/2
        offsets = [(dx * sign_x, dy * sign_y) for sign_x in [1, -1] for sign_y in [1, -1]]
        # calculate the x, y points from the center using the offsets, and apply the current rotation of the sprite's image
        for offset_x, offset_y in offsets:
            vertices.append(((self.x + (offset_x * math.cos(angle_radians) - (offset_y * math.sin(angle_radians)))),
                self.y + (offset_x * math.sin(angle_radians) + (offset_y * math.cos(angle_radians)))))
        return vertices
      
        
    def light_ray_boundary_vertices(self, light_source_x, light_source_y):
        """ Which two vertices enclose the most amount (width-wise) of light ray from the light source
        """
        vertices = self.get_vertices()
        boundary_vertices = ()
        max_angle = 0
        if vertices is not None:
            boundary_vertices = (vertices[0], vertices[0])
        for i, v1 in enumerate(vertices):
            for j in range(i+1, len(vertices)):
                #if v1 == v2: continue
                angle_of_sep = self.seperation_angle(v1, vertices[j], light_source_x, light_source_y)
                if angle_of_sep > max_angle: # this pair of vertices give a wider angle, that is enclose more of the light beam/ray
                    max_angle = angle_of_sep
                    boundary_vertices = (v1, vertices[j])
        return (max_angle, boundary_vertices)
    
    
    def seperation_angle(self, vertex_a, vertex_b, light_x, light_y):
        """ calculates the angle between the lines produced from the light souce to each of vertex_a and vertex_b
        """ 
        delta_x_a = (light_x - vertex_a[0])
        delta_x_b = (light_x - vertex_b[0])
        angle_a = 0.0
        angle_b = 0.0
        if delta_x_a == 0: angle_a = math.pi/2
        else: angle_a = math.atan2((light_y - vertex_a[1]), delta_x_a)
        
        if delta_x_b == 0: angle_b = math.pi/2
        else: angle_b = math.atan2((light_y - vertex_b[1]), delta_x_b)
        return math.fabs(angle_a - angle_b)


    def centralray_incidence_point(self, ray_hor_angle_deg):
        """ Calculate the coordinates of the point on the perimeter of the surface of the 
        robot where the central ray of light struck.
        """
        alpha = self.positive_angle_degrees(ray_hor_angle_deg)
        rho = self.positive_angle_degrees(self.rotation)
        alpha_norm = math.fabs(alpha - rho)
        h = self.image.height/2
        w = self.image.width/2
        
        ratio = float(h/w)
        theta_radians = math.atan(ratio)
        theta = math.degrees(theta_radians)
        gamma = 90 - theta
        gamma_radians = math.radians(gamma)
         
        x_norm = self.x
        y_norm = self.y
         
        if alpha_norm >= 0 and alpha_norm <= theta:
            x_norm += w
            y_norm -= math.tan(theta_radians) * w
        elif alpha_norm > theta and alpha_norm <= 90:
            x_norm += math.tan(gamma_radians) * h
            y_norm -= h
        elif alpha_norm > 90 and alpha_norm <= 90+gamma:
            x_norm -= math.tan(gamma_radians) * h
            y_norm -= h 
        elif alpha_norm > 90+gamma and alpha_norm <= 180:
            x_norm -= w
            y_norm -= math.tan(theta_radians) * w
        elif alpha_norm > 180 and alpha_norm <= 180+theta:
            x_norm -= w
            y_norm += math.tan(theta_radians) * w
        elif alpha_norm > 180+theta and alpha_norm <= 270:
            x_norm -= math.tan(gamma_radians) * h
            y_norm += h
        elif alpha_norm > 270 and alpha_norm <= 270+gamma:
            x_norm += math.tan(gamma_radians) * h
            y_norm += h
        elif alpha_norm > 270+gamma and alpha_norm <= 360:
            x_norm += w
            y_norm += math.tan(theta_radians) * w
        # now that we have x_norm and y_norm, apply the rotation to get their actual coordinates
        return self.rotate_deg(x_norm, y_norm, -self.rotation)
        
        
    def rotate_deg(self, x, y, angle_deg):
        angle_radians = math.radians(angle_deg)
        x_rot = x * math.cos(angle_radians) - (y * math.sin(angle_radians))
        y_rot = x * math.sin(angle_radians) + (y * math.cos(angle_radians))
        return (x_rot, y_rot)
            
    def positive_angle_degrees(self, angle_deg):
        """ Converts a negative angle to a positive one between 0 and 360
        """     
        if angle_deg < 0:
            angle_norm = angle_deg % -360
            angle_norm = angle_norm + 360
        else:
            angle_norm = angle_deg % 360
        return angle_norm
        
    def positive_angle_radians(self, angle_rad):
        """ Converts a negative angle to a positive one between 0 and 360
        """    
        angle_deg = math.degrees(angle_rad) 
        if angle_deg < 0:
            angle_norm = angle_deg % -360.0
            angle_norm = angle_norm + 360.0
        else:
            angle_norm = angle_deg % 360.0
        return math.radians(angle_norm)
    
    def setx(self, val):
        self.prev_x = self.x
        self.x = val
        self._update_position()
    
    def sety(self, val):
        self.prev_y = self.y
        self.y = val
        self._update_position()
    
    def position_changed(self):
        if self.prev_x == self.x or self.prev_y == self.y:
            return False
        return True
    #</Maduka>
         
class SwitchSprite(BasicSprite):    
    def __init__(self, texture, x, y, batch, subgroup, object_type="switch", idx=-1, window_width=800,
                 window_height=600):
        super(SwitchSprite, self).__init__(texture, x, y, batch, subgroup, object_type="switch", idx=-1, window_width=800,
                 window_height=600)
        self.switch_is_on = False
        self.target_robot = None
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Uses a radius check to see if the sprite has been clicked, then sets the 'switch_is_on'
        property adequately."""
        if button == 1:
            dsq = (self.x - x) ** 2 + (self.y - y) ** 2
            # print dsq
            if dsq < self.min_rad_sq:
                if self.switch_is_on == False:
                    self.switch_is_on = True               
                    self._set_image(src.resources.switch_image_off)
                    self.target_robot.start_robot()
                    if self.target_robot.robot_name.startswith("PI2GO"):
                        self.target_robot.perform_led_init_animation()
                    print("Robot is switched ON...")           
                else:
                    self.switch_is_on = False
                    self._set_image(src.resources.switch_image_on)
                    self.target_robot.stop_robot()
                    print("Robot is switched OFF...")
    
     
                  
    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass
    
    def set_target_robot(self, robot):
        self.target_robot = robot