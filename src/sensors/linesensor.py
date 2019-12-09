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


class LineSensorMap(object):
    def __init__(self, line_map_sprite):
        if line_map_sprite is None:
            self.line_map_sprite = None
            self.line_data = None
            self.x_offset = 0
            self.y_offset = 0
        else:
            self.line_map_sprite = line_map_sprite
            self.x_offset = self.line_map_sprite.x - int(self.line_map_sprite.image.width / 2.0)
            self.y_offset = self.line_map_sprite.y - int(self.line_map_sprite.image.height / 2.0)
            self.line_data = self.line_map_sprite.image.get_image_data()

    def set_line_map(self, line_map_sprite):
        """Update the line sensor map with a new image."""
        if line_map_sprite is None:
            self.line_map_sprite = None
            self.line_data = None
            self.x_offset = 0
            self.y_offset = 0
        else:
            self.line_map_sprite = line_map_sprite
            self.x_offset = self.line_map_sprite.x - int(self.line_map_sprite.image.width / 2.0)
            self.y_offset = self.line_map_sprite.y - int(self.line_map_sprite.image.height / 2.0)
            self.line_data = self.line_map_sprite.image.get_image_data()

    def check_triggered(self, x, y):
        """Takes as input the current xy position of the line sensor in screen coordinates, this function will then
        translate those to the coordinate system of the image (which may be arbitrarily positioned/rotated) so the
        correct image coordiates can be checked. Returns true if the average intensity of the pixel is greater than
        zero."""
        try:
            if self.line_data is not None:
                theta = -math.radians(self.line_map_sprite.rotation)

                px, py = src.util.rotate_around_og((self.line_map_sprite.x, self.line_map_sprite.y), (x, y), -theta)
                px -= self.x_offset
                py -= self.y_offset

                if px < 0 or px > self.line_map_sprite.width:
                     # print("out of region")
                    return False

                if py < 0 or py > self.line_map_sprite.height:
                     # print("out of region")
                    return False

                pix = self.line_data.get_region(int(px), int(py), 1, 1).get_data("RGBA", 4)
                # print (self.line_data.get_data("RGBA", 4))
                # print ('r = ' + str(pix[0]))
                # print ('g = ' + str(pix[1]))
                # print ('b = ' + str(pix[2]))
                # print ('a = ' + str(pix[3]))

                if len(pix) > 3:
                    r = int(pix[0])
                    g = int(pix[1])
                    b = int(pix[2])
                    a = int(pix[3])
                    # avg = float(r + g + b + a) / 4.0
                    # print(x, y, px, py, self.x_offset, self.y_offset)
                    # print (r, g, b, a)
                    # pprint(px)
                    # print(avg)
                    # return avg > 0
                    return a == 0
                else:
                    return False
            else:
                return False
        except AttributeError:
            print("Error reading line sensor")
            return False


class FixedLineSensor(object):
    def __init__(self, parent_robot, sensor_map, offset_x, offset_y):
        self.parent_robot = parent_robot
        self.sensor_map = sensor_map
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.line_sensor_triggered = False
        self.sensor_x = 0
        self.sensor_y = 0

    def get_triggered(self):
        """Returns the last reading taken from the sensor."""
        return self.line_sensor_triggered

    def update_sensor(self):
        """Computes the xy position of the line sensor based on the position of the robot and queries the
        line sensor map."""
        angle_radians = -math.radians(self.parent_robot.rotation)

        self.sensor_x = self.parent_robot.x + (
            self.offset_x * math.cos(angle_radians) - (self.offset_y * math.sin(angle_radians)))
        self.sensor_y = self.parent_robot.y + (
            self.offset_x * math.sin(angle_radians) + (self.offset_y * math.cos(angle_radians)))

        # print(self.sensor_x)
        self.line_sensor_triggered = self.sensor_map.check_triggered(int(self.sensor_x), int(self.sensor_y))

    def draw_sensor_position(self):
        """Draws a circle at the origin of the sensor."""
        src.util.circle(self.sensor_x, self.sensor_y, 5)
        
    def make_circle(self):
        verts = []
        for i in range(100):
            angle = math.radians(float(i)/100 * 360.0)
            x = 5*math.cos(angle) + self.sensor_x
            y = 5*math.sin(angle) + self.sensor_y
            verts += [x,y]
        outline_rep = self.parent_robot.batch.add(int(len(verts)/2), pyglet.gl.GL_POINTS, None,
        ('v2f', verts),
        ('c4B', (255, 255, 255, 255)*int(len(verts)/2)))
        """ return verts """
