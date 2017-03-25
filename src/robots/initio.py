"""
initio.py is a subclass of BasicSprite and creates a simulated INITIO robot
with appropriate sensros. This module also handles communication between
the simulator and any external scripts. Communicate is done via simple
string messeages passed via UDP socket.
"""
import math
import socket
import threading
import time
from src.sensors.linesensor import FixedLineSensor
from src.sensors.linesensor import LineSensorMap
from src.sensors.distancesensors import FixedTransformDistanceSensor, PanningDistanceSensor
from src.sprites import basicsprite
import pyglet
import src.resources
import src.util
from robotconstants import SONAR_BEAM_ANGLE, SONAR_MAX_RANGE, SONAR_MIN_RANGE, IR_MAX_RANGE, IR_MIN_RANGE, \
    UDP_COMMAND_PORT, UDP_DATA_PORT, UDP_IP, IR_BEAM_ANGLE

# Constants specific to the Initio robot.

IR_SENSOR_ANGLE = 0.80
IR_OFFSET_X = 40
IR_OFFSET_Y = 18
LINE_OFFSET_X = 40
LINE_OFFSET_Y = 5
SONAR_OFFSET_X = 25


class Initio(basicsprite.BasicSprite):
    def __init__(self, *args, **kwargs):
        self.sonar_map = kwargs.pop('sonar_map')
        line_map_sprite = kwargs.pop('line_map_sprite')
        batch = kwargs.pop('batch')
        window_width = kwargs.pop('window_width')
        window_height = kwargs.pop('window_height')

        robot_group = pyglet.graphics.OrderedGroup(1)

        super(Initio, self).__init__(src.resources.robot_image, 0, 0, batch, robot_group, window_width=window_width,
                                     window_height=window_height)

        # drawing batch
        self.batch = batch
        self.group = robot_group
        self.robot_name = "INITIO"
        self.radius = max(self.image.width, self.image.height) / 2.0
        self.sonar_sensor = PanningDistanceSensor(batch=batch, robot=self, sonar_map=self.sonar_map, offset_x=25,
                                                  min_range=SONAR_MIN_RANGE, max_range=SONAR_MAX_RANGE,
                                                  beam_angle=SONAR_BEAM_ANGLE)

        self.ir_left_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, IR_OFFSET_Y,
                                                           IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, IR_BEAM_ANGLE)

        self.ir_right_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, -IR_OFFSET_Y,
                                                            -IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, IR_BEAM_ANGLE)

        self.line_sensor_map = LineSensorMap(line_map_sprite)
        self.left_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, LINE_OFFSET_Y)
        self.right_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, -LINE_OFFSET_Y)

        self.mouse_move_state = False
        self.mouse_position = [0, 0]

        self.vx = 0.0
        self.vth = 0.0

        self.event_handlers = [self, self.on_mouse_release, self.on_mouse_drag]

        self.publish_thread = threading.Thread(target=self.publish_state_udp)
        self.publish_thread.setDaemon(True)
        self.publish_thread.start()

        self.cmd_thread = threading.Thread(target=self.recv_commands)
        self.cmd_thread.setDaemon(True)
        self.cmd_thread.start()

        pyglet.clock.schedule_interval(self.update_sensors, 1.0 / 30)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Allows the robot to be dragged around using the mouse."""
        if self.mouse_move_state:
            self.x = x
            self.y = y

            self.velocity_x = 0
            self.velocity_y = 0
            self.sonar_sensor.update(1)

    def recv_commands(self):
        """Thread function which handles incomming commands for an external python script via a UDP socket.

        Commands are strings and take the form: <<LINEAR_VELOCITY;ANGULAR_VELOCITY;SONAR_SERVO_ANGLE>>
        """
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind((UDP_IP, UDP_COMMAND_PORT))
        while True:
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            if data.startswith("<<") and data.endswith(">>"):
                data = data.replace("<<", "")
                data = data.replace(">>", "")
                values_list = data.split(";")
                if len(values_list) == 3:
                    self.vx = float(values_list[0])
                    self.vth = float(values_list[1])
                    self.sonar_sensor.set_target(float(values_list[2]))

    def publish_state_udp(self):
        """Thread function which publishes the state of the robot to an external python script via UDP socket.

        State strings take the form: <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;RIGHT_IR>>
        """
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        while True:
            ir_left = self.ir_left_sensor.get_fixed_triggered(IR_MAX_RANGE)
            ir_right = self.ir_right_sensor.get_fixed_triggered(IR_MAX_RANGE)
            line_left = self.left_line_sensor.get_triggered()
            line_right = self.right_line_sensor.get_triggered()
            message = "<<%s;%f;%d;%d;%d;%d>>" % (self.robot_name, self.sonar_sensor.sonar_range, line_left,
                                                 line_right, ir_left,
                                                 ir_right)
            sock.sendto(message, (UDP_IP, UDP_DATA_PORT))
            time.sleep(0.03)

    def update_sensors(self, dt):
        """Take a new reading for each sensor."""
        self.sonar_sensor.update_sensor()
        self.ir_left_sensor.update_sensor()
        self.ir_right_sensor.update_sensor()
        self.left_line_sensor.update_sensor()
        self.right_line_sensor.update_sensor()

    def update(self, dt):
        """Update the state of the robot. This updates the velocity of the robot based on the current velocity commands
        self.vx and self.vth. Also updates the position of the sonar sensor sprite accordingly. This function will not
        update the robots state if the robot is currently being moved by the user (via mouse drag). """

        super(Initio, self).update(dt)

        if not self.mouse_move_state:
            angle_radians = -math.radians(self.rotation)
            self.velocity_x = self.vx * math.cos(angle_radians)
            self.velocity_y = self.vx * math.sin(angle_radians)
            self.rotation -= self.vth * dt
            self.sonar_sensor.update(dt)

    def robot_collides_with(self, other_object):
        """Collision checking between the robot and another object. This function uses ver simple radius based collision
        detection."""
        # Calculate distance between object centers that would be a collision,
        # assuming square resources
        collision_distance = self.image.width / 2.0 + other_object.image.width / 3.0

        # Get distance using position tuples
        actual_distance = src.util.distance(self.position, other_object.position)

        return actual_distance <= collision_distance

    def delete(self):
        """Deletes the robot sprite."""
        super(Initio, self).delete()

    def draw_robot_position(self):
        """Draws a white circle on the screen at the current position of the robot."""
        src.util.circle(self.x, self.y, 5)
