#<Maduka>

"""
linesensor.py defines a map and sensor class to simulate a typical line sensor on a robot. This is achieved using
 an image of the line itself. The image must be transparent except where the line itself exists. This image is used
 in the creation of the LineSensorMap which simple stores the raw image data. Checking the line sensor is triggered
 is done by simply acccessing the raw pixel values of the image and checking the average intensity.

 The FixedLineSensor class is used to represent a sensor that is mounted offset from the cetre of the robot.
"""
import math
import src.util
import pyglet

LIGHT_INTENSITY_MEAN_ANGLE = 0.0
LIGHT_INTENSITY_STDDEV_ANGLE = math.pi/3.0  #60 deg
GAUSSIAN_REGULARISER = 2.624947501    # with the light_intensity_stddev_angle and mean above, this makes the gaussian's peak value = 1.0
MAX_LIGHT_INTENSITY = 1023
LIGHT_BEAM_ANGWIDTH = math.pi/10
MAX_VALUED_DIST_TO_RAYEND = LIGHT_BEAM_ANGWIDTH

class FixedLightSensor(object):
    def __init__(self, parent_robot, offset_x, offset_y, name="Unnamed_Light_Sensor", drawing_colour=(0,255,0,255)):
        self.parent_robot = parent_robot
        self.light_sensor_triggered = False
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.value = 0
        self.x = self.sensor_x = 0.0
        self.y = self.sensor_y = 0.0
        self.name = name
        self.angdist_to_rayend = MAX_VALUED_DIST_TO_RAYEND  # by default 
        self.beam_cone_or_std_dev = LIGHT_INTENSITY_STDDEV_ANGLE  # by default
        self.update_sensor(None)
        self.drawing = None
        self.drawing_colour = drawing_colour

    def get_triggered(self):
        """Returns the last reading taken from the sensor."""
        return self.line_sensor_triggered

    def update_sensor(self, simulator):
        """Computes the xy position of the light sensor based on the position of the robot and queries the
        line sensor map.
        Determines the sensor value using angular distance and a guassian distribution over angular distances
        """
        angle_radians = -math.radians(self.parent_robot.rotation)
        
        self.set_xvalue(self.parent_robot.x + (
            self.offset_x * math.cos(angle_radians) - (self.offset_y * math.sin(angle_radians))))
            
        self.set_yvalue(self.parent_robot.y + (
            self.offset_x * math.sin(angle_radians) + (self.offset_y * math.cos(angle_radians))))
  
        # ask dynamic asset's static object list whether it's holding a source of light; and, ask host 
        # robot whether this sensor is the one closest to the source of that ray.
        if hasattr(self.parent_robot, 'static_objects'):
            light_source = None
            for obj in self.parent_robot.static_objects:
                if obj.object_type is not None and obj.object_type.startswith("light"):
                    light_source = obj
                    break
        if light_source is not None and self.parent_robot.receiving_light_focus==True:
            self.light_sensor_triggered = True
            ang_dist = self.angular_distance(light_source, simulator)
            self.value = MAX_LIGHT_INTENSITY * math.fabs(self.gaussian_probability(ang_dist, LIGHT_INTENSITY_MEAN_ANGLE, LIGHT_INTENSITY_STDDEV_ANGLE))
            return math.degrees(ang_dist)
        else: 
            self.light_sensor_triggered = False
            self.value = 0  # no light is shining
            return 0
    
    def set_xvalue(self, xvalue):
        self.x = self.sensor_x = xvalue
    
    def set_yvalue(self, yvalue): 
        self.y = self.sensor_y = yvalue     
        
    def draw_sensor_position(self):
        """Draws a circle at the origin of the sensor."""
        src.util.circle(self.sensor_x, self.sensor_y, 20)
    
    def angular_distance(self, light_source, simulator):
        """Calculates the angular distance between a source of light and this sensor.
        """
        x_ray_end = simulator.x_ray_end
        y_ray_end = simulator.y_ray_end
        is_ray_being_dragged = simulator.is_ray_being_dragged
        robot = self.parent_robot
        alpha_delta_x = light_source.x - robot.x
        _, thresh_theta = simulator.robot_lightray_area_cover()
        
        if alpha_delta_x == 0:
            alpha = math.pi/2
        else:
            alpha = math.atan2(float(light_source.y - robot.y), float(alpha_delta_x))  # atan2 computes the angle within the actual quadrant
        
        #normalise alpha to a positive angle if it is a negative angle
        if alpha < 0: alpha += math.pi
        
        gamma = 0
        if is_ray_being_dragged == True:
            gamma_delta_x = light_source.x - x_ray_end
            if gamma_delta_x == 0:
                gamma = math.pi/2
            else:
                gamma = math.atan2(float(light_source.y - y_ray_end), float(gamma_delta_x))  # atan2 computes the angle within the actual quadrant
            
            # normalise gamma to a positive angle if it is a negative angle
            if gamma < 0: gamma += math.pi
            
            # normalise the light source coordinates here to account for the shift in light ray center
            # do this by using the coordinate of a rotated light source, rotated by the angle of drag/shift from the ray passing through
            # the center of the robot.
            ray_drag_angle = gamma - alpha
            # scale ray drag angle appropriately to 90 degrees
            ray_drag_angle = ray_drag_angle/thresh_theta * (math.pi/2)
            # when the ray is dragged over the body of the robot, away from the center of the robot,
            # keep reducing the beam cone size (std_dev of gaussian) so that the virtual rotation of 
            # light source which accounts for this drag does not lead to increased light intensity
            # on surrounding sensors - i.e at a point in the drag, light intensity changes affects 
            # mostly only the sensors still being touched or covered by the light ray.  
            #cone_beam_width = (thresh_theta - math.fabs(ray_drag_angle))/thresh_theta * LIGHT_INTENSITY_STDDEV_ANGLE
            # rotate the light source around the center of the robot by ray_drag_angle
            ##radius_of_rotation = ((light_source.x - robot.x)**2 + (light_source.y - robot.y)**2)**0.5
            radius_along_x = (light_source.x - robot.x)
            radius_along_y = (light_source.y - robot.y)
            rot_light_source_x = robot.x + (
                                 radius_along_x * math.cos(ray_drag_angle) - (radius_along_y * math.sin(ray_drag_angle)))
            rot_light_source_y = robot.y + (
                                 radius_along_x * math.sin(ray_drag_angle) + (radius_along_y * math.cos(ray_drag_angle)))

            # recompute alpha based on the adjusted/rotated light source coordinates
            alpha_delta_x = rot_light_source_x - robot.x
            if alpha_delta_x == 0:
                alpha = math.pi/2
            else:
                alpha = math.atan2(float(rot_light_source_y - robot.y), float(alpha_delta_x))  # atan2 computes the angle within the actual quadrant
            
            # normalise alpha to a positive angle if it is a negative angle
            if alpha < 0: alpha += math.pi
            
        beta_delta_x = robot.x - self.x
        if beta_delta_x == 0:
            beta = math.pi/2
        else:
            beta = math.atan2(float(robot.y - self.y), float(beta_delta_x))                      
        
        # normalise beta to a positive angle if it is a negative angle
        if beta < 0: beta += math.pi
        
        # account for the direction of light i.e. if light source and sensor are on the 
        # same side of the robot (on the vertical axis), or on different sides
        if (light_source.y - robot.y) * (self.y - robot.y) < 0: # light and sensor are on opposite sides
            # account for light coming from opposite side by rotating alpha (angle of light source)
            # by 180 degrees.
            return math.pi - math.fabs(beta - alpha) 
        elif (light_source.y - robot.y) * (self.y - robot.y) == 0: # here will be because (light_source.y - robot.y) is zero
            if (light_source.x - robot.x) * (self.x - robot.x) < 0: # different x-sides of robot center
                return math.pi - math.fabs(beta - alpha)
            else: return math.fabs(beta - alpha)
        else: return math.fabs(beta - alpha)
        
    
    def angdistance_to_rayend(self, simulator):
        """ Calculate the Euclidean distance between the sensor and the end of the light ray
        """
        if simulator.light_source is None: return None       
        delta_x_sen = (self.x - simulator.light_source.x)
        if delta_x_sen == 0:
            alpha = math.pi / 2  # sensor angle to the horizontal is 90 degrees
        else:
            alpha = math.atan2((self.y - simulator.light_source.y), delta_x_sen)
        if alpha < 0: alpha += math.pi   # ensuring alpha is between 0 and 180 degrees
        
        delta_x_light = (simulator.x_ray_end - simulator.light_source.x)
        if delta_x_light == 0:
            delta = math.pi / 2 # sensor angle to the horizontal is 90 degrees
        else:
            delta = math.atan2((simulator.y_ray_end - simulator.light_source.y), delta_x_light)
        if delta < 0: delta += math.pi  # ensuring delta is between 0 and 180 degrees
        # return the angle between the (spine of) the light beam and the sensor    
        return math.fabs(delta - alpha)
        
        
    def normalise_value(self, angdist_to_rayend, simulator):
        """ When the robot is moving closer or away from the light source, normalise the 
        value of the sensor based on the distance of the sensor to the end of the light 
        source.
        """
        if angdist_to_rayend is None:
            # light is not ON
            self.value = 0
            return
        angle_sep, thresh_theta = simulator.robot_lightray_area_cover()
        
        if angle_sep > thresh_theta+LIGHT_BEAM_ANGWIDTH/2:  # set sensor values to zero only when the ray is not touching the robot at all
                return 0
   
        if angdist_to_rayend > MAX_VALUED_DIST_TO_RAYEND: 
            self.value = 0
            return 
            
        if self.angdist_to_rayend < angdist_to_rayend:  # the ray is further away now from sensor
            self.value -= (self.value * (angdist_to_rayend - self.angdist_to_rayend) / (MAX_VALUED_DIST_TO_RAYEND - self.angdist_to_rayend))
        elif self.angdist_to_rayend > angdist_to_rayend: # the ray is nearer now from the sensor
            self.value += ((MAX_LIGHT_INTENSITY - self.value) * (self.angdist_to_rayend - angdist_to_rayend) / (self.angdist_to_rayend))
        else:  # the ray has moved neither nearer nor farer from the sensor, from where it was previously
            pass
        self.angdist_to_rayend = angdist_to_rayend
    
             
    def gaussian_probability(self, x_value, mean, std_dev):
        if std_dev <= 0: return 0
        alpha = 1/math.sqrt(2 * math.pi * std_dev ** 2)
        beta = -((x_value - mean) ** 2)/(2 * std_dev ** 2)     
        return alpha * (math.e ** beta) * GAUSSIAN_REGULARISER
        
    def reset_beam_cone_stddev(self):
        self.beam_cone_or_std_dev = LIGHT_INTENSITY_STDDEV_ANGLE
        
    def indicate_position(self):
        """ lights up the led at its position with its colour value
        """
        #vertices_outline = self.make_circle()  
        vertices_fill = self.make_circle_filled()                                                   
          
        fill_colour = self.drawing_colour
        if self.drawing is not None:
            self.drawing.delete()
             
        # now fill the LED with the current light setting
        self.drawing = self.parent_robot.batch.add(int(len(vertices_fill)/2), pyglet.gl.GL_POINTS, None, 
                ('v2f', vertices_fill),
                ('c4B', fill_colour*int(len(vertices_fill)/2)))


    def make_circle_filled(self):
        verts = []
        for radius in range(4, 0, -1):  # LED_RADIUS-1 so we don't cover the outline of the circle
            num_points = int(100.0 * radius/4.0)
            for i in range(num_points):
                angle = math.radians(float(i)/num_points * 360.0)
                x = radius*math.cos(angle) + self.x
                y = radius*math.sin(angle) + self.y
                verts += [x,y]
        return verts