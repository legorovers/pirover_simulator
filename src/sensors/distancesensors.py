"""
distancesensors.py defines two types of distance sensor:

    FixedTransformDistanceSensor is just a fixed sensor.

    PanningDistanceSensor is a distance sensor attached to a panning servo.

Both sensors make use of the Sonar class defined in sonar.py
"""
import math
import pyglet
import src.resources
import src.sprites.basicsprite
import src.util
from sonar import Sonar


class FixedTransformDistanceSensor(object):
    def __init__(self, parent_robot, sensor_map, offset_x, offset_y, sensor_rot, min_range, max_range, beam_angle):
        self.parent_robot = parent_robot
        self.sensor = Sonar(sensor_map, min_range, max_range, beam_angle)
        self.sensor_offset_x = offset_x
        self.sensor_offset_y = offset_y
        self.sensor_rotation = sensor_rot
        self.sensor_range = 0
        self.sensor_x = 0
        self.sensor_y = 0

    def update_sensor(self):
        """Calculates the XY position of the sensor origin based on the current position of the robot and
            then takes a reading."""
        angle_radians = -math.radians(self.parent_robot.rotation)
        beam_angle = angle_radians + self.sensor_rotation
        beam_angle = src.util.wrap_angle(beam_angle)
        self.sensor_x = self.parent_robot.x + (
            self.sensor_offset_x * math.cos(angle_radians) - (self.sensor_offset_y * math.sin(angle_radians)))
        self.sensor_y = self.parent_robot.y + (
            self.sensor_offset_x * math.sin(angle_radians) + (self.sensor_offset_y * math.cos(angle_radians)))
        self.sensor_range = self.sensor.update_sonar(self.sensor_x, self.sensor_y, beam_angle)

    def get_distance(self):
        """Returns the last reading taken by this sensor."""
        return self.sensor_range

    def get_fixed_triggered(self, trigger_distance):
        """Returns true is the last reading is less than or equal to trigger_distance"""
        if self.sensor_range < trigger_distance:
            return True
        else:
            return False

    def draw_sensor_position(self):
        """Draws a circle at the origin of the sensor"""
        src.util.circle(self.sensor_x, self.sensor_y, 5)


class PanningDistanceSensor(src.sprites.basicsprite.BasicSprite):
    def __init__(self, *args, **kwargs):
        batch = kwargs.pop('batch')
        robot = kwargs.pop('robot')
        sonar_map = kwargs.pop('sonar_map')
        offset_x = kwargs.pop('offset_x')
        min_range = kwargs.pop('min_range')
        max_range = kwargs.pop('max_range')
        beam_angle = kwargs.pop('beam_angle')
        sonar_group = pyglet.graphics.OrderedGroup(2)
        super(PanningDistanceSensor, self).__init__(src.resources.sonar_image, 0, 0, batch, sonar_group)
        self.parent_robot = robot
        self.sonar_offset_x = offset_x
        self.sonar_angle_max = 90
        self.sonar_angle_min = -90
        self.sonar_angle = 0
        self.sonar_angle_target = 0
        self.sonar_sensor = Sonar(sonar_map, min_range, max_range, beam_angle)
        self.sensor_offset_x = self.width - 8
        self.sensor_offset_y = 0
        self.sonar_range = 0.0
        self.sensor_x = 0
        self.sensor_y = 0

    def set_target(self, target):
        """Set the target angle for the panning sonar."""
        if target >= self.sonar_angle_max:
            target = self.sonar_angle_max
        elif target <= self.sonar_angle_min:
            target = self.sonar_angle_min
        self.sonar_angle_target = target

    def update_sensor(self):
        """Calculates the XY position of the sensor origin based on the current position of the robot and
            then takes a reading."""
        angle_radians = -math.radians(self.rotation)
        self.sensor_x = self.x + (
            self.sensor_offset_x * math.cos(angle_radians) - (self.sensor_offset_y * math.sin(angle_radians)))
        self.sensor_y = self.y + (
            self.sensor_offset_x * math.sin(angle_radians) + (self.sensor_offset_y * math.cos(angle_radians)))
        self.sonar_range = self.sonar_sensor.update_sonar(self.sensor_x, self.sensor_y, angle_radians)

    def get_distance(self):
        """Returns the last reading taken by this sensor."""
        return self.sonar_range

    def update(self, dt):
        """Updates the position of the sprite representing the panning servo head."""
        angle_radians = -math.radians(self.parent_robot.rotation)
        self.x = self.parent_robot.x + (self.sonar_offset_x * math.cos(angle_radians))
        self.y = self.parent_robot.y + (self.sonar_offset_x * math.sin(angle_radians))

        if (self.sonar_angle_target - self.sonar_angle) > 0:
            self.sonar_angle += 5
        elif (self.sonar_angle_target - self.sonar_angle) < 0:
            self.sonar_angle -= 5
        self.rotation = self.parent_robot.rotation - self.sonar_angle

    def draw_sensor_position(self):
        """Draws a circle at the origin of the sensor."""
        src.util.circle(self.sensor_x, self.sensor_y, 5)
