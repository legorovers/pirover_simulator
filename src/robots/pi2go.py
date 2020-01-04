"""
pi2go.py is a subclass of BasicSprite and creates a simulated PI2GO robot
with appropriate sensros. This module also handles communication between
the simulator and any external scripts. Communicate is done via simple
string messeages passed via UDP socket.
"""

import math
import random
import socket
import time
import pyglet
import src.resources
import src.util
import src.sensors.led as theled
from src.sensors.lightsensor import FixedLightSensor
from src.sensors.led import FixedLED
from src.sensors.distancesensors import FixedTransformDistanceSensor
from src.sensors.linesensor import LineSensorMap, FixedLineSensor
from src.sprites import basicsprite
from .robotconstants import SONAR_BEAM_ANGLE, SONAR_MAX_RANGE, SONAR_MIN_RANGE, IR_MAX_RANGE, IR_MIN_RANGE, \
    UDP_COMMAND_PORT, UDP_DATA_PORT, UDP_IP
    
import threading

# Constants specific to the PI2GO robot.

IR_SENSOR_ANGLE = 0.785
IR_OFFSET_X_MIDDLE = 52
IR_OFFSET_X = 33
IR_OFFSET_Y = 21
LINE_OFFSET_X = 40
LINE_OFFSET_Y = 14
SONAR_OFFSET_X = 50
LED_INIT_FLASH_COUNT = 5

READ_INTERVAL = 0.01
PUBLISH_INTERVAL = 0.03


class Pi2Go(basicsprite.BasicSprite):
    def __init__(self, *args, **kwargs):
        self.sonar_map = kwargs.pop('sonar_map')
        line_map_sprite = kwargs.pop('line_map_sprite')
        self.static_objects = kwargs.pop('static_objects')
        batch = kwargs.pop('batch')
        window_width = kwargs.pop('window_width')
        window_height = kwargs.pop('window_height')

        robot_group = pyglet.graphics.OrderedGroup(1)

        super(Pi2Go, self).__init__(src.resources.pi2go_image, 0, 0, batch, robot_group, window_width=window_width,
                                    window_height=window_height)

        # drawing batch
        self.batch = batch
        self.group = robot_group
        self.robot_name = "PI2GO"
        self.radius = max(self.image.width, self.image.height) / 2.0
        
        x_light_offset = self.image.width/2
        y_light_offset = self.image.height/2
        
        self.sonar_sensor = FixedTransformDistanceSensor(self, self.sonar_map, SONAR_OFFSET_X, 0, 0, SONAR_MIN_RANGE,
                                                         SONAR_MAX_RANGE, SONAR_BEAM_ANGLE)

        self.ir_left_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, IR_OFFSET_Y,
                                                           IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, 0.25)

        self.ir_middle_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X_MIDDLE, 0,
                                                             0, IR_MIN_RANGE, IR_MAX_RANGE, 0.25)

        self.ir_right_sensor = FixedTransformDistanceSensor(self, self.sonar_map, IR_OFFSET_X, -IR_OFFSET_Y,
                                                            -IR_SENSOR_ANGLE, IR_MIN_RANGE, IR_MAX_RANGE, 0.25)
                                                            
        self.light_frontleft_sensor = FixedLightSensor(self, x_light_offset, y_light_offset-10, "FrontLeft", drawing_colour=(255,0,0,255))
        self.light_frontright_sensor = FixedLightSensor(self, x_light_offset, -y_light_offset+10, "FrontRight", drawing_colour=(0,255,0,255))
        self.light_backleft_sensor = FixedLightSensor(self, -x_light_offset, y_light_offset-10, "BackLeft", drawing_colour=(0,0,255,255))
        self.light_backright_sensor = FixedLightSensor(self, -x_light_offset, -y_light_offset+10, "BackRight", drawing_colour=(255,255,255,255))
           
        self.light_sensors = []
        self.light_sensors.append(self.light_frontleft_sensor)
        self.light_sensors.append(self.light_frontright_sensor)
        self.light_sensors.append(self.light_backleft_sensor)
        self.light_sensors.append(self.light_backright_sensor)
        
        # add the LEDs - radius of the light is 10, a gap of 3 is added between neighbouring leds
        # left side leds
        self.left_led1 = FixedLED(self, 1, y_light_offset-22, "left_led1")
        self.left_led2 = FixedLED(self, 12, y_light_offset-22, "left_led2")
        
        # right side leds
        self.right_led1 = FixedLED(self, 1, -y_light_offset+22, "right_led1")
        self.right_led2 = FixedLED(self, 12, -y_light_offset+22, "right_led2")
        
        # front side leds
        self.front_led1 = FixedLED(self, x_light_offset-17, -15, "front_led1")
        self.front_led2 = FixedLED(self, x_light_offset-17, +15, "front_led2")
        
        # back side leds
        self.back_led1 = FixedLED(self, -x_light_offset+10, -10, "back_led1")
        self.back_led2 = FixedLED(self, -x_light_offset+10, +10, "back_led2")
        
        self.leds = []
        self.leds.append(self.left_led1)
        self.leds.append(self.left_led2)
        self.leds.append(self.right_led1)
        self.leds.append(self.right_led2)
        self.leds.append(self.front_led1)
        self.leds.append(self.front_led2)
        self.leds.append(self.back_led1)
        self.leds.append(self.back_led2)

        self.line_sensor_map = LineSensorMap(line_map_sprite)
        self.left_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, LINE_OFFSET_Y)
        self.right_line_sensor = FixedLineSensor(self, self.line_sensor_map, LINE_OFFSET_X, -LINE_OFFSET_Y)

        self.mouse_move_state = False
        self.mouse_position = [0, 0]

        self.vx = 0.0
        self.vth = 0.0
        
        self.publish_continue = True
        self.receive_continue = True
        
        self.led_init_anim_on = True
        self.led_init_anim_count = 0
        self.leds_prev_values = []   
        
        self.control_switch_on = False
        self.turn_off_leds()  

        self.event_handlers = [self, self.on_mouse_release, self.on_mouse_drag]

        self.publish_thread = threading.Thread(target=self.publish_state_udp)
        # self.publish_thread.setDaemon(True)
        self.publish_thread.start()

        self.cmd_thread = threading.Thread(target=self.recv_commands)
        # self.cmd_thread.setDaemon(True)
        self.cmd_thread.start()

        # pyglet.clock.schedule_interval(self.update_sensors, 1.0 / 30)

    
    def start_robot(self):
        self.publish_continue = True 
        self.receive_continue = True
        # reset the movement values
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.vx = 0.0
        self.vth = 0.0
        # this method is called when the robot control switch is switched ON
        self.control_switch_on = True
        # release the brakes on movement
        # pyglet.clock.unschedule(self.stop_robot_movement)

      
    def stop_robot(self):
        # cause the publish and command threads to stop
        self.publish_continue = False 
        self.receive_continue = False
        self.control_switch_on = False
        self.turn_off_leds()
        # stop movement
        # pyglet.clock.unschedule(self.stop_robot_movement)
        time.sleep(0.3)
        # # stop robot movement using a background thread - the target method is called continually when the robot control switch is OFF       
        #stop_movement_thread = threading.Thread(target=pyglet.clock.schedule_interval, args=(self.stop_robot_movement, 1.0 / 30))
        #stop_movement_thread.setDaemon(True)
        #stop_movement_thread.start()
        # pyglet.clock.schedule_interval(self.stop_robot_movement, 1.0 / 30)

    def stop_robot_movement(self, dt):
        # stop movement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.vx = 0.0
        self.vth = 0.0

        
    def light_leds(self):
        # first refresh the lights and then light them up
        for led in self.leds:
            if led.fill_rep is not None:
                led.fill_rep.delete()
                led.outline_rep.delete()     
            led.shine()
            

    def turn_off_leds(self):
        # first refresh the lights and then light them up
        for led in self.leds:
            if led.fill_rep is not None:
                led.fill_rep.delete()
                led.outline_rep.delete()     
            led.shine()
            led.turn_off()
            
            
    def perform_led_init_animation(self):
        self.led_init_anim_on = True
        self.led_init_anim_count = 0
        self.leds_prev_values = []
        # pyglet.clock.schedule_interval(self.led_init_animation, 1.0)
        
        
    def led_init_animation(self, dt): 
        if self.led_init_anim_on == True:
            self.leds_prev_values = []           
            for led in self.leds:
                # save off the original values of light for each led
                self.leds_prev_values.append([led.red_value, led.green_value, led.blue_value])
                # animate the leds with random values of light
                led.red_value = int(random.uniform(0, theled.MAX_VALUE))
                led.green_value = int(random.uniform(0, theled.MAX_VALUE))
                led.blue_value = int(random.uniform(0, theled.MAX_VALUE))
            self.light_leds()
        elif self.led_init_anim_on == False:
            for id, led in enumerate(self.leds):
                # reinstate the value before flash
                led.red_value = self.leds_prev_values[id][0]
                led.green_value = self.leds_prev_values[id][1]
                led.blue_value = self.leds_prev_values[id][2]
            self.light_leds()
        # toggle the on state for the next clock interval schedule
        self.led_init_anim_on = True if self.led_init_anim_on == False else False
        # update the count for the flashes
        self.led_init_anim_count += 1
        if self.led_init_anim_count > LED_INIT_FLASH_COUNT:
            # stop the schedules
            self.led_init_anim_count = 0
            pyglet.clock.unschedule(self.led_init_animation)
            self.turn_off_leds()
   
         
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Allows the robot to be dragged around using the mouse."""
        if self.mouse_move_state:
            self.x = x
            self.y = y
            self.velocity_x = 0
            self.velocity_y = 0             
            #self.sonar_sensor.update(1)
            
    
    #def on_mouse_release(self, x, y, button, modifiers):
    #    super(Pi2Go, self).on_mouse_release(x, y, button, modifiers)
        # update the LEDs
    #    self.perform_led_init_animation()
    #    self.light_leds() 
            
            
    def recv_commands(self):
        """Thread function which handles incomming commands for an external python script via a UDP socket.

        Commands are strings and take the form: <<LINEAR_VELOCITY;ANGULAR_VELOCITY;
        FRONT_LED1_RED_VALUE;FRONT_LED1_GREEN_VALUE;FRONT_LED1_BLUE_VALUE;
        FRONT_LED2_RED_VALUE;FRONT_LED2_GREEN_VALUE;FRONT_LED2_BLUE_VALUE;
        LEFT_LED1_RED_VALUE;LEFT_LED1_GREEN_VALUE;LEFT_LED1_BLUE_VALUE;
        LEFT_LED2_RED_VALUE;LEFT_LED2_GREEN_VALUE;LEFT_LED2_BLUE_VALUE;
        BACK_LED1_RED_VALUE;BACK_LED1_GREEN_VALUE;BACK_LED1_BLUE_VALUE;
        BACK_LED2_RED_VALUE;BACK_LED2_GREEN_VALUE;BACK_LED2_BLUE_VALUE;
        RIGHT_LED1_RED_VALUE;RIGHT_LED1_GREEN_VALUE;RIGHT_LED1_BLUE_VALUE;
        RIGHT_LED2_RED_VALUE;RIGHT_LED2_GREEN_VALUE;RIGHT_LED2_BLUE_VALUE>>
        """
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
                        #  print (data);
                        if len(values_list) == 26:
                            self.vx = float(values_list[0])
                            self.vth = float(values_list[1])
                            if self.vx == 0 and self.vth != 0:
                                self.is_rotating = True
                            else: self.is_rotating = False

                            self.front_led1.red_value = values_list[2]
                            self.front_led1.green_value = values_list[3]
                            self.front_led1.blue_value = values_list[4]
                            self.front_led2.red_value = values_list[5]
                            self.front_led2.green_value = values_list[6]
                            self.front_led2.blue_value = values_list[7]

                            self.right_led1.red_value = values_list[8]
                            self.right_led1.green_value = values_list[9]
                            self.right_led1.blue_value = values_list[10]
                            self.right_led2.red_value = values_list[11]
                            self.right_led2.green_value = values_list[12]
                            self.right_led2.blue_value = values_list[13]

                            self.back_led1.red_value = values_list[14]
                            self.back_led1.green_value = values_list[15]
                            self.back_led1.blue_value = values_list[16]
                            self.back_led2.red_value = values_list[17]
                            self.back_led2.green_value = values_list[18]
                            self.back_led2.blue_value = values_list[19]

                            self.left_led1.red_value = values_list[20]
                            self.left_led1.green_value = values_list[21]
                            self.left_led1.blue_value = values_list[22]
                            self.left_led2.red_value = values_list[23]
                            self.left_led2.green_value = values_list[24]
                            self.left_led2.blue_value = values_list[25]
                except Exception:
                     pass
            time.sleep(READ_INTERVAL)
            # we need to call stop_robot() again since the values for vx and vth and velocities may
            # already have been reinstated by an update from the client just before the inner while loop
            # above stopped (due to self.receive_continue being set to false)
            #self.stop_robot()
        print("closing receive socket")
        self.sock_recv.close()


    def publish_state_udp(self):
        """Thread function which publishes the state of the robot to an external python script via UDP socket.

           State strings take the form: 
           <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;RIGHT_IR;
             FRONT_LEFT_LIGHTSENSOR; FRONT_RIGHT_LIGHTSENSOR; 
             BACK_RIGHT_LIGHTSENSOR; BACK_LEFT_LIGHTSENSOR;
             FRONT_LED1_RED_VALUE;FRONT_LED1_GREEN_VALUE;FRONT_LED1_BLUE_VALUE;
             FRONT_LED2_RED_VALUE;FRONT_LED2_GREEN_VALUE;FRONT_LED2_BLUE_VALUE;
             BACK_LED1_RED_VALUE;BACK_LED1_GREEN_VALUE;BACK_LED1_BLUE_VALUE;
             BACK_LED2_RED_VALUE;BACK_LED2_GREEN_VALUE;BACK_LED2_BLUE_VALUE;
             LEFT_LED1_RED_VALUE;LEFT_LED1_GREEN_VALUE;LEFT_LED1_BLUE_VALUE;
             LEFT_LED2_RED_VALUE;LEFT_LED2_GREEN_VALUE;LEFT_LED2_BLUE_VALUE;
             RIGHT_LED1_RED_VALUE;RIGHT_LED1_GREEN_VALUE;RIGHT_LED1_BLUE_VALUE;
             RIGHT_LED2_RED_VALUE;RIGHT_LED2_GREEN_VALUE;RIGHT_LED2_BLUE_VALUE; CONTROL_SWITCH>>        
        """
        self.sock_publish = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        while self.publish_continue is True:
            while self.publish_continue is True:
                ir_left = self.ir_left_sensor.get_fixed_triggered(IR_MAX_RANGE)
                ir_mid = self.ir_middle_sensor.get_fixed_triggered(IR_MAX_RANGE)
                ir_right = self.ir_right_sensor.get_fixed_triggered(IR_MAX_RANGE)
                line_left = self.left_line_sensor.get_triggered()
                line_right = self.right_line_sensor.get_triggered()
            
                light_fl = int(self.light_frontleft_sensor.value)
                light_fr = int(self.light_frontright_sensor.value)
                light_bl = int(self.light_backleft_sensor.value)
                light_br = int(self.light_backright_sensor.value)
                     
                message = "<<%s;%f;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d>>" % (
                          self.robot_name, self.sonar_sensor.get_distance(), 
                          line_left, line_right, ir_left, ir_mid, ir_right,
                           light_fl, light_fr, light_br, light_bl,
                           int(self.front_led1.red_value),
                           int(self.front_led1.green_value),
                           int(self.front_led1.blue_value),
                           int(self.front_led2.red_value),
                           int(self.front_led2.green_value),
                           int(self.front_led2.blue_value),
                        
                           int(self.back_led1.red_value),
                           int(self.back_led1.green_value),
                           int(self.back_led1.blue_value),
                           int(self.back_led2.red_value),
                           int(self.back_led2.green_value),
                           int(self.back_led2.blue_value),
                        
                           int(self.right_led1.red_value),
                           int(self.right_led1.green_value),
                           int(self.right_led1.blue_value),
                           int(self.right_led2.red_value),
                           int(self.right_led2.green_value),
                           int(self.right_led2.blue_value),
                        
                           int(self.left_led1.red_value),
                           int(self.left_led1.green_value),
                           int(self.left_led1.blue_value),
                           int(self.left_led2.red_value),
                           int(self.left_led2.green_value),
                           int(self.left_led2.blue_value),
                           int(self.control_switch_on))
                try:
                    self.sock_publish.sendto(message.encode('utf-8'), (UDP_IP, UDP_DATA_PORT))
                    updated_switch_finally = False
                    time.sleep(PUBLISH_INTERVAL)
                except Exception:
                    pass
            # send again, once, to update the control switch    
            if updated_switch_finally is False:
                message = "<<%s;%f;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d>>" % (
                          self.robot_name, self.sonar_sensor.get_distance(), 
                          line_left, line_right, ir_left, ir_mid, ir_right,
                           light_fl, light_fr, light_br, light_bl,
                           int(self.front_led1.red_value),
                           int(self.front_led1.green_value),
                           int(self.front_led1.blue_value),
                           int(self.front_led2.red_value),
                           int(self.front_led2.green_value),
                           int(self.front_led2.blue_value),
                        
                           int(self.back_led1.red_value),
                           int(self.back_led1.green_value),
                           int(self.back_led1.blue_value),
                           int(self.back_led2.red_value),
                           int(self.back_led2.green_value),
                           int(self.back_led2.blue_value),
                        
                           int(self.right_led1.red_value),
                           int(self.right_led1.green_value),
                           int(self.right_led1.blue_value),
                           int(self.right_led2.red_value),
                           int(self.right_led2.green_value),
                           int(self.right_led2.blue_value),
                        
                           int(self.left_led1.red_value),
                           int(self.left_led1.green_value),
                           int(self.left_led1.blue_value),
                           int(self.left_led2.red_value),
                           int(self.left_led2.green_value),
                           int(self.left_led2.blue_value),
                           int(self.control_switch_on))
                try:
                    print(message)
                    self.sock_publish.sendto(message.encode('utf-8'), (UDP_IP, UDP_DATA_PORT))
                    updated_switch_finally = True
                    time.sleep(PUBLISH_INTERVAL)
                except Exception:
                    pass
        print("closing publish socket")
        self.sock_publish.close()


    
    def update_sensors(self):
        """Take a new reading for each sensor."""
        self.sonar_sensor.update_sensor()
        self.ir_left_sensor.update_sensor()
        self.ir_middle_sensor.update_sensor()
        self.ir_right_sensor.update_sensor()
        self.left_line_sensor.update_sensor()
        self.right_line_sensor.update_sensor()


    def update_light_sensors(self, simulator):
        """ Updates the light sensors """   
        # compute the angular distance of each light sensor to the light source.
        # based on the angular distance, use a gaussian to determine the sensor
        # value for the light source.
        sensor_angles = []
        for ls in self.light_sensors:
            sensor_angles.append((ls.name, ls.update_sensor(simulator)))  # ls.update_sensor() will update each sensor's value
            # ls.make_circle()
        return sensor_angles
                
    def reset_light_sensors(self):
        for ls in self.light_sensors:
            ls.reset_beam_cone_stddev()
            ls.value = 0
    
    
    def update(self, dt, simulator):
        """Update the state of the robot. This updates the velocity of the robot based on the current velocity commands
        self.vx and self.vth. Also updates the position of the sonar sensor sprite accordingly. This function will not
        update the robots state if the robot is currently being moved by the user (via mouse drag). """
        # Do all the normal physics stuff
        super(Pi2Go, self).update(dt)
        if not self.mouse_move_state:
            angle_radians = -math.radians(self.rotation)
            self.velocity_x = self.vx * math.cos(angle_radians)
            self.velocity_y = self.vx * math.sin(angle_radians)
            self.rotation -= self.vth * dt
            self.update_sensors()
        # src.util.circle(self.left_line_sensor.sensor_x, self.left_line_sensor.sensor_y, 10, 10)
        # src.util.circle(30, 30, 30)
        # self.update_sensors
        self.update_light_sensors(simulator)
        self.light_leds()
        # self.left_line_sensor.make_circle()
        # self.right_line_sensor.make_circle()
        # self.sonar_sensor.make_circle()
        # self.ir_left_sensor.make_circle()
        # self.ir_right_sensor.make_circle()
        # self.ir_middle_sensor.make_circle()
        # Let the light ray track the robot when it moves normally - NO!
        # if simulator.light_source is not None and not simulator.is_ray_being_dragged \
        #    and not simulator.ray_was_dragged:
        #     if simulator.light_source.x < self.x: px = self.x - self.image.width/2
        #     elif simulator.light_source.x == self.x: px = self.x
        #     else: px = self.x + self.image.width/2
        #     if simulator.light_source.y < self.y: py = self.y - self.image.height/2
        #     elif simulator.light_source.y == self.y: py = self.y
        #     else: py = self.y + self.image.height/2
        #     simulator.light_follow_mouse(px, py) 
        
        
    def robot_collides_with(self, other_object):
        """Collision checking between the robot and another object. This function uses ver simple radius based collision
        detection."""
        # Calculate distance between object centers that would be a collision,
        # assuming square resources
        collision_distance = self.radius + other_object.image.width / 2.0
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
        super(Pi2Go, self).delete()

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
        self.batch.add(int(len(vertices_fill)/2), pyglet.gl.GL_POINTS, None, 
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

    def switch_on(self):
        self.control_switch_on = True

    def switch_off(self):
        self.control_switch_on = False
