
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
from pyglet.graphics.shader import Shader, ShaderProgram #We need to create a ShaderProgram

LED_RADIUS = 4
LED_NUMPOINTS_CIRCLE = 100
MAX_VALUE = 4095
#Vertex and Fragment source for the ShaderProgram below:
vertex_source = """#version 150 core
    in vec2 position;
    in vec4 colors;
    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 0.0, 1.0);
        vertex_colors = colors;
    }
"""

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_colors;
    }
"""

class FixedLED(object):
    def __init__(self, parent_robot, offset_x, offset_y, name="UnNamed"):
        self.parent_robot = parent_robot
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.x = self.sensor_x = 0.0
        self.y = self.sensor_y = 0.0
        self.name = name
        self.red_value = 0
        self.green_value = 0
        self.blue_value = 0
        self.outline_rep = None
        self.fill_rep = None


    def update_position(self):
        """Computes the xy position of the LED based on the position of the robot.
        """
        angle_radians = -math.radians(self.parent_robot.rotation)
		
        self.set_xvalue(self.parent_robot.x + (
            self.offset_x * math.cos(angle_radians) - (self.offset_y * math.sin(angle_radians))))
            
        self.set_yvalue(self.parent_robot.y + (
            self.offset_x * math.sin(angle_radians) + (self.offset_y * math.cos(angle_radians))))
   
    def set_colour(self, red, green, blue):
        """ Accepts RGB value and sets the colour of this LED"""
        self.red_value = red
        self.green_value = green
        self.blue_value = blue
        
    def get_colour(self):
        """ Returns the RGB colour value of this LED"""
        return (self.red_value, self.green_value, self.blue_value)
        
    def turn_off(self):
        """ Turns off the LED by setting it's colour value to black"""
        self.set_colour(0, 0, 0)
        
    def set_xvalue(self, xvalue):
        self.x = self.sensor_x = xvalue
    
    def set_yvalue(self, yvalue): 
        self.y = self.sensor_y = yvalue   	
        
    def draw_sensor_position(self):
        """Draws a circle at the origin of the sensor."""
        src.util.circle(self.sensor_x, self.sensor_y, 20)
        
    def shine(self):
        """ lights up the led at its position with its colour value
        """
        #ShaderProgram
        vert_shader = Shader(vertex_source, 'vertex')
        frag_shader = Shader(fragment_source, 'fragment')
        program = ShaderProgram(vert_shader, frag_shader)
        #ShaderProgram
        self.update_position()
        vertices_outline = self.make_circle()  
        vertices_fill = self.make_circle_filled()                                                   
        
       #if self.red_value == self.green_value == self.blue_value == 0:
       #    colour_opacity = 0
         
        colour_opacity = 255
        # print(self.red_value, self.green_value, self.blue_value)
        
        fill_colour = (int(self.red_value)%256, int(self.green_value)%256, int(self.blue_value)%256, colour_opacity)
        
        # create the outline of the circle representing the led with red colour
        #self.outline_rep = self.parent_robot.batch.add(int(len(vertices_outline)/2), pyglet.gl.GL_POINTS, None, 
                #('v2f', vertices_outline),
                #('c4B', (255, 0, 0, 255)*int(len(vertices_outline)/2)))  
        self.outline_rep = program.vertex_list(int(len(vertices_outline)/2), pyglet.gl.GL_POINTS, position = ('f', vertices_outline), batch=self.parent_robot.batch, colors=('i', (255, 0, 0, 255)*int(len(vertices_outline)/2)))
        # now fill the LED with the current light setting
        #self.fill_rep = self.parent_robot.batch.add(int(len(vertices_fill)/2), pyglet.gl.GL_POINTS, None, 
                #('v2f', vertices_fill),
                #('c4B', fill_colour*int(len(vertices_fill)/2)))
        self.fill_rep = program.vertex_list(int(len(vertices_fill)/2), pyglet.gl.GL_POINTS, position = ('f', vertices_fill), batch = self.parent_robot.batch, colors = ('i', fill_colour*int(len(vertices_fill)/2)))

    def make_circle_filled(self):
        verts = []
        for radius in range(LED_RADIUS-1, 0, -1):  # LED_RADIUS-1 so we don't cover the outline of the circle
            num_points = int(LED_NUMPOINTS_CIRCLE * radius/LED_RADIUS)
            for i in range(num_points):
                angle = math.radians(float(i)/num_points * 360.0)
                x = radius*math.cos(angle) + self.x
                y = radius*math.sin(angle) + self.y
                verts += [x,y]
        return verts
        
    def make_circle(self):
        verts = []
        for i in range(LED_NUMPOINTS_CIRCLE):
            angle = math.radians(float(i)/LED_NUMPOINTS_CIRCLE * 360.0)
            x = LED_RADIUS*math.cos(angle) + self.x
            y = LED_RADIUS*math.sin(angle) + self.y
            verts += [x,y]
        return verts
