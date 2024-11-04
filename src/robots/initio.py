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
from src.sensors.lightsensor import FixedLightSensor
from src.sensors.linesensor import LineSensorMap
from src.sensors.distancesensors import FixedTransformDistanceSensor, PanningDistanceSensor
from src.sprites import basicsprite
import pyglet
import src.resources
import src.util
from .robotconstants import SONAR_BEAM_ANGLE, SONAR_MAX_RANGE, SONAR_MIN_RANGE, IR_MAX_RANGE, IR_MIN_RANGE, \
    UDP_COMMAND_PORT, UDP_DATA_PORT, UDP_IP, IR_BEAM_ANGLE

# Constants specific to the Initio robot.

IR_SENSOR_ANGLE = 0.80
IR_OFFSET_X = 40
IR_OFFSET_Y = 18
LINE_OFFSET_X = 40
LINE_OFFSET_Y = 5

SONAR_OFFSET_X = 80

READ_INTERVAL = 0.01
PUBLISH_INTERVAL = 0.03
BEAMS = 30


class Initio(basicsprite.BasicSprite):
    def __init__(self, *args, **kwargs):
        self.sonar_map = kwargs.pop('sonar_map')
        line_map_sprite = kwargs.pop('line_map_sprite')
        self.static_objects = kwargs.pop('static_objects')
        batch = kwargs.pop('batch')
        window_width = kwargs.pop('window_width')
        window_height = kwargs.pop('window_height')

        robot_group = pyglet.graphics.Group(1)

        super(Initio, self).__init__(src.resources.robot_image, 0, 0, batch, robot_group, window_width=window_width,
                                     window_height=window_height)

        # drawing batch
        self.batch = batch
        self.group = robot_group
        self.robot_name = "INITIO"
        self.radius = max(self.image.width, self.image.height) / 2.0

        x_light_offset = self.image.width / 2
        y_light_offset = self.image.height / 2

        self.sonar_sensor = PanningDistanceSensor(batch=batch, robot=self, sonar_map=self.sonar_map,
                                                  offset_x=SONAR_OFFSET_X,
                                                  offset_y=0,
                                                  min_range=SONAR_MIN_RANGE, max_range=SONAR_MAX_RANGE,
                                                  beam_angle=SONAR_BEAM_ANGLE)

        self.ir_left_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, IR_OFFSET_Y,
                                                           IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, IR_BEAM_ANGLE,BEAMS)

        self.ir_right_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, -IR_OFFSET_Y,
                                                            -IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, IR_BEAM_ANGLE, BEAMS)

        self.light_frontleft_sensor = FixedLightSensor(self, x_light_offset, y_light_offset - 10, "FrontLeft",
                                                       drawing_colour=(255, 0, 0, 255))
        self.light_frontright_sensor = FixedLightSensor(self, x_light_offset, -y_light_offset + 10, "FrontRight",
                                                        drawing_colour=(0, 255, 0, 255))
        self.light_backleft_sensor = FixedLightSensor(self, -x_light_offset, y_light_offset - 10, "BackLeft",
                                                      drawing_colour=(0, 0, 255, 255))
        self.light_backright_sensor = FixedLightSensor(self, -x_light_offset, -y_light_offset + 10, "BackRight",
                                                       drawing_colour=(255, 255, 255, 255))

        self.light_sensors = []
        self.light_sensors.append(self.light_frontleft_sensor)
        self.light_sensors.append(self.light_frontright_sensor)
        self.light_sensors.append(self.light_backleft_sensor)
        self.light_sensors.append(self.light_backright_sensor)

        self.line_sensor_map = LineSensorMap(line_map_sprite)
        self.left_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, LINE_OFFSET_Y)
        self.right_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, -LINE_OFFSET_Y)

        self.mouse_move_state = False
        self.mouse_position = [0, 0]

        self.vx = 0.0
        self.vth = 0.0
        # self.schedule_lock = False

        # self.sock_recv = None
        # self.sock_publish = None

        self.publish_continue = True
        self.receive_continue = True

        # self.sonar_sensor.update(1)
        # self.sonar_sensor.update_sensor()

        self.event_handlers = [self, self.on_mouse_release, self.on_mouse_drag]
        self.control_switch_on = True

        # pyglet.clock.schedule_interval(self.update_sensors, 1.0 / 30)

        self.publish_thread = threading.Thread(target=self.publish_state_udp)
        # self.publish_thread.setDaemon(True)
        self.publish_thread.start()

        self.cmd_thread = threading.Thread(target=self.recv_commands)
        # self.cmd_thread.setDaemon(True)
        self.cmd_thread.start()
        # self.start_robot()

    def start_robot(self):
        self.publish_continue = True
        self.receive_continue = True
        # this method is called when the robot control switch is switched ON
        self.control_switch_on = False
        # release the brakes on movement
        # pyglet.clock.unschedule(self.stop_robot_movement)

    def stop_robot(self):
        # cause the publish and command threads to stop
        self.publish_continue = False
        self.receive_continue = False
        # this method is called when the robot control switch is switched ON
        self.control_switch_on = False
        # stop movement
        # pyglet.clock.unschedule(self.stop_robot_movement)
        time.sleep(0.3)
        # stop robot movement using a background thread
        # stop_movement_thread = threading.Thread(target=pyglet.clock.schedule_interval, args=(self.stop_robot_movement, 1.0 / 30))
        # stop_movement_thread.setDaemon(True)
        # stop_movement_thread.start()
        # pyglet.clock.schedule_interval(self.stop_robot_movement, 1.0 / 30)

    def stop_robot_movement(self, dt):
        # stop movement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.vx = 0.0
        self.vth = 0.0

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Allows the robot to be dragged around using the mouse."""
        if self.mouse_move_state:
            self.x = x
            self.y = y
            self.velocity_x = 0
            self.velocity_y = 0
            # self.sonar_sensor.update(1)

    def recv_commands(self):
        """Thread function which handles incomming commands for an external python script via a UDP socket.

        Commands are strings and take the form: <<LINEAR_VELOCITY;ANGULAR_VELOCITY;SONAR_SERVO_ANGLE>>
        """
        # Initialise the socket used by the command/receiving thread
        self.sock_recv = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP
        self.sock_recv.bind((UDP_IP, UDP_COMMAND_PORT))
        self.sock_recv.settimeout(1)
        
        #  double loop is a hack - changing while True to while self.receive_continue while debugging
        while self.receive_continue is True:
            while self.receive_continue is True:
                try:
                    data_e, addr = self.sock_recv.recvfrom(1024)  # buffer size is 1024 bytes
                    data = data_e.decode()
                    if data.startswith("<<") and data.endswith(">>"):
                        data = data.replace("<<", "")
                        data = data.replace(">>", "")
                        values_list = data.split(";")
                        if len(values_list) == 3:
                            self.sonar_sensor.set_target(float(values_list[2]))
                            self.vx = float(values_list[0])
                            # if spin_time > 0.0:
                            #                             if self.schedule_lock == False:
                            #                                 self.unschedule_angvelreset()  # unschedule any previous schedule made.
                            #                                 self.vth = float(values_list[1])
                            #                                 pyglet.clock.schedule_interval(self.reset_angular_velocity, spin_time)
                            #                                 self.schedule_lock = True  # deny any new schedule to be made on reset_angular_velocity
                            #                                 if self.vx == 0.0 and self.vth <> 0.0:
                            #                                     self.is_rotating = True
                            #                         else:
                            self.vth = float(values_list[1])
                            if self.vx == 0 and self.vth != 0:
                                self.is_rotating = True
                            else:
                                self.is_rotating = False
                except Exception:
                    pass
            time.sleep(READ_INTERVAL)

            # we need to call stop_robot() again since the values for vx and vth and velocities may
            # already have been reinstated by an update from the client just before the inner while loop
            # above stopped (due to self.receive_continue being set to false)
            # self.stop_robot()
        print("closing receive socket")
        self.sock_recv.close()

    def publish_state_udp(self):
        """Thread function which publishes the state of the robot to an external python script via UDP socket.

        State strings take the form: <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;RIGHT_IR;
                                        FRONT_LEFT_LIGHTSENSOR, FRONT_RIGHT_LIGHTSENSOR, 
                                        BACK_LEFT_LIGHTSENSOR, BACK_RIGHT_LIGHTSENSOR; CONTROL_SWITCH>>
        """
        # Initialise the socket used by the publish thread
        self.sock_publish = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP
        while self.publish_continue is True:
            while self.publish_continue is True:
                try:
                    ir_left = self.ir_left_sensor.get_fixed_triggered(IR_MAX_RANGE)
                    ir_right = self.ir_right_sensor.get_fixed_triggered(IR_MAX_RANGE)
                    line_left = self.left_line_sensor.get_triggered()
                    line_right = self.right_line_sensor.get_triggered()

                    light_fl = int(self.light_frontleft_sensor.value)
                    light_fr = int(self.light_frontright_sensor.value)
                    light_bl = int(self.light_backleft_sensor.value)
                    light_br = int(self.light_backright_sensor.value)

                    message = "<<%s;%f;%d;%d;%d;%d;%d;%d;%d;%d;%d>>" % (
                        self.robot_name, self.sonar_sensor.sonar_range,
                        line_left, line_right,
                        ir_left, ir_right,
                        light_fl, light_fr, light_br, light_bl, self.control_switch_on)
                    self.sock_publish.sendto(message.encode('utf-8'), (UDP_IP, UDP_DATA_PORT))
                    updated_switch_finally = False
                    time.sleep(PUBLISH_INTERVAL)
                except Exception:
                    pass
            try:
                # send again, once, to update the control switch
                if updated_switch_finally is False:
                    message = "<<%s;%f;%d;%d;%d;%d;%d;%d;%d;%d;%d>>" % (
                        self.robot_name, self.sonar_sensor.sonar_range,
                        line_left, line_right,
                        ir_left, ir_right,
                        light_fl, light_fr, light_br, light_bl, self.control_switch_on)
                    self.sock_publish.sendto(message.encode('utf-8'), (UDP_IP, UDP_DATA_PORT))
                    updated_switch_finally = True
                    time.sleep(PUBLISH_INTERVAL)
            except Exception:
                pass
        print("closing publish socket")
        self.sock_publish.close()

    def update_sensors(self, dt):
        """Take a new reading for each sensor."""
        self.sonar_sensor.update_sensor()
        self.sonar_sensor.update(dt)
        self.ir_left_sensor.update_sensor()
        self.ir_right_sensor.update_sensor()
        self.left_line_sensor.update_sensor()
        self.right_line_sensor.update_sensor()

    #     def reset_angular_velocity(self, st):
    #         self.velocity_x = 0.0
    #         self.velocity_y = 0.0
    #         self.vx = 0.0
    #         self.vth = 0.0
    #         time.sleep(1.0)
    #         print("RESEeeeeeeeeeeeeeeeeting......^^^^^^^^^^^..........")
    #         self.is_rotating = False
    #         self.schedule_lock = False  # allow a new schedule to be made on reset_angular_velocity.
    #
    #     def unschedule_angvelreset(self):
    #         pyglet.clock.unschedule(self.reset_angular_velocity)
    #         print("unscheduled*******************+++++++++++++++++++++++++++................")

    def update_light_sensors(self, simulator):
        """ Updates the light sensors """
        # light_source = self.get_shining_light()
        # compute the angular distance of each light sensor to the light source.
        # based on the angular distance, use a gaussian to determine the sensor
        # value for the light source.
        sensor_angles = []
        for ls in self.light_sensors:
            sensor_angles.append(
                (ls.name, ls.update_sensor(simulator)))  # ls.update_sensor() will update each sensor's value
            # if self.position_changed() and not self.is_rotating:
            # update sensor values based on euclidean distance from ray end
            # dist = ls.angdistance_to_rayend(simulator)
            # ls.normalise_value(dist, simulator)
        return sensor_angles

    def reset_light_sensors(self):
        for ls in self.light_sensors:
            ls.reset_beam_cone_stddev()
            ls.value = 0

    def update(self, dt, simulator):
        """Update the state of the robot. This updates the velocity of the robot based on the current velocity commands
        self.vx and self.vth. Also updates the position of the sonar sensor sprite accordingly. This function will not
        update the robots state if the robot is currently being moved by the user (via mouse drag). """
        super(Initio, self).update(dt)
        if not self.mouse_move_state:
            angle_radians = -math.radians(self.rotation)
            self.velocity_x = self.vx * math.cos(angle_radians)
            self.velocity_y = self.vx * math.sin(angle_radians)
            self.rotation -= self.vth * dt
            self.update_sensors(dt)
        # self.sonar_sensor.update(dt)
        # self.ir_left_sensor.update_sensor()
        # self.ir_right_sensor.update_sensor()
        # self.left_line_sensor.update_sensor()
        # self.right_line_sensor.update_sensor()
        # self.left_line_sensor.make_circle()
        # self.right_line_sensor.make_circle()
        # self.sonar_sensor.make_circle()
        # self.ir_left_sensor.make_circle()
        # self.ir_right_sensor.make_circle()

        # self.update_light_sensors(simulator)
        # Let the light ray track the robot when it moves normally - NO!
        # if simulator.light_source is not None and not simulator.is_ray_being_dragged \
        #         and not simulator.ray_was_dragged:
        #     if simulator.light_source.x < self.x:
        #         px = self.x - self.image.width / 2
         #    elif simulator.light_source.x == self.x:
        #         px = self.x
        #     else:
        #         px = self.x + self.image.width / 2
        #     if simulator.light_source.y < self.y:
        #         py = self.y - self.image.height / 2
        #     elif simulator.light_source.y == self.y:
        #         py = self.y
        #     else:
        #         py = self.y + self.image.height / 2
         #    simulator.light_follow_mouse(px, py)

    def robot_collides_with(self, other_object):
        """Collision checking between the robot and another object. This function uses ver simple radius based collision
        detection."""
        # Calculate distance between object centers that would be a collision,
        # assuming square resources
        collision_distance = self.image.width / 2.0 + other_object.image.width / 3.0
        # Get distance using position tuples
        actual_distance = src.util.distance(self.position, other_object.position)
        return actual_distance <= collision_distance

    def get_shining_light(self):
        """Checks if there is a light source in the world and returns it
        """
        if self.static_objects is not None:
            for obj in self.static_objects:
                if obj.object_type.startswith("light"):
                    return obj
        return None

    def delete(self):
        """Deletes the robot sprite."""
        super(Initio, self).delete()

    def draw_robot_position(self):
        """Draws a white circle on the screen at the current position of the robot."""
        src.util.circle(self.x, self.y, 5)

    def indicate_position(self):
        """ lights up the led at its position with its colour value
        """
        vertices_fill = self.make_circle_filled()

        colour_opacity = 255

        fill_colour = (255, 255, 255, colour_opacity)

        # now fill the LED with the current light setting
        self.batch.add(int(len(vertices_fill) / 2), pyglet.gl.GL_POINTS, None,
                       ('v2f', vertices_fill),
                       ('c4B', fill_colour * int(len(vertices_fill) / 2)))

    def make_circle_filled(self):
        verts = []
        for radius in range(4, 0, -1):  # LED_RADIUS-1 so we don't cover the outline of the circle
            num_points = int(100.0 * radius / 4.0)
            for i in range(num_points):
                angle = math.radians(float(i) / num_points * 360.0)
                x = radius * math.cos(angle) + self.x
                y = radius * math.sin(angle) + self.y
                verts += [x, y]
        return verts

    def switch_on(self):
        self.control_switch_on = False

    def switch_off(self):
        self.control_switch_on = False
