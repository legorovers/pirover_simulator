"""
simclient.py provides the interface between the simulator and external python code. The simulator client connects
to the simulator via two udp sockets and exchanges robot state and command messages with the simulator. The command
exchange is done in the background using two daemon threads to minimize any timing issues.
"""

import time
import socket
import threading

UDP_IP = "127.0.0.1"
UDP_DATA_PORT = 5000
UDP_COMMAND_PORT = 5001
PAN = 0
PUBLISH_INTERVAL = 0.02  # seconds


class SimulatorClient:
    def __init__(self):
        self.mutex = threading.Lock()
        self.running = True
        self.sonar_range = 1700.0
        self.sonar_angle = 0
        self.left_line_sensor_triggered = False
        self.right_line_sensor_triggered = False
        self.ir_left_triggered = False
        self.ir_middle_triggered = False
        self.ir_right_triggered = False
        self.vx = 0
        self.vth = 0
        self.front_led1_red_value = 0
        self.front_led1_green_value = 0
        self.front_led1_blue_value = 0
        self.front_led2_red_value = 0
        self.front_led2_green_value = 0
        self.front_led2_blue_value = 0
        
        self.left_led1_red_value = 0
        self.left_led1_green_value = 0
        self.left_led1_blue_value = 0
        self.left_led2_red_value = 0
        self.left_led2_green_value = 0
        self.left_led2_blue_value = 0
        
        self.right_led1_red_value = 0
        self.right_led1_green_value = 0
        self.right_led1_blue_value = 0
        self.right_led2_red_value = 0
        self.right_led2_green_value = 0
        self.right_led2_blue_value = 0
        
        self.back_led1_red_value = 0
        self.back_led1_green_value = 0
        self.back_led1_blue_value = 0
        self.back_led2_red_value = 0
        self.back_led2_green_value = 0
        self.back_led2_blue_value = 0
        
        self.fr_light_sensor = 0
        self.fl_light_sensor = 0
        self.br_light_sensor = 0
        self.bl_light_sensor = 0
        
        self.robot_control_switch_on = False
        
        self.robot_name = "Not Connected"

        self.update_thread = threading.Thread(target=self.update_state)
        self.update_thread.setDaemon(True)
        self.update_thread.start()

        self.cmd_thread = threading.Thread(target=self.send_commands)
        self.cmd_thread.setDaemon(True)
        self.cmd_thread.start()
        time.sleep(1)
        print("initialisation complete")

    
    def getRobotName(self):
        return self.robot_name
        
    def setServo(self, servo, degrees):
        """Set the angle of the panning sonar on the robot."""
        if servo == PAN:
            self.sonar_angle = degrees

    def getDistance(self):
        """Returns the current range detected by the sonar sensor measurements are in centimetres."""
        return self.sonar_range

    def irLeft(self):
        """Returns the state of the LEFT IR sensor, returns True if an obstacle is detected."""
        return self.ir_left_triggered

    def irRight(self):
        """Returns the state of the RIGHT IR sensor, returns True if an obstacle is detected."""
        return self.ir_right_triggered

    def irCentre(self):
        """Returns the state of the CENTRE IR sensor, returns True if an obstacle is detected."""
        return self.ir_middle_triggered

    def irAll(self):
        """Returns the state of the ALL IR sensors, returns True if an obstacle is detected."""
        if self.robot_name == "Initio":
            return self.ir_left_triggered or self.ir_right_triggered
        else:
            return self.ir_left_triggered or self.ir_right_triggered or self.ir_middle_triggered

    def irLeftLine(self):
        """Returns the state of the LEFT line sensor, returns True if a line is detected."""
        return self.left_line_sensor_triggered

    def irRightLine(self):
        """Returns the state of the RIGHT line sensor, returns True if a line is detected."""
        return self.right_line_sensor_triggered

    def forward(self, speed):
        """forward(speed): Sets both motors to move forward at speed. 0 <= speed <= 100"""
        self.vx = speed
        self.vth = 0

    def reverse(self, speed):
        """reverse(speed): Sets both motors to reverse at speed. 0 <= speed <= 100"""
        self.vx = -speed
        self.vth = 0

    def spinLeft(self, speed):
        """spinLeft(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
        self.vx = 0
        self.vth = speed

    def spinRight(self, speed):
        """spinRight(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
        self.vx = 0
        self.vth = -speed

#   def spinLeftBriefly(self, speed, spin_time):
#         """spinLeft(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
#         self.spinLeft(speed)
#         self.spin_time = spin_time
# 
#     def spinRightBriefly(self, speed, spin_time):
#         """spinRight(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
#         self.spinRight(speed)
#         self.spin_time = spin_time
        
    def turnForward(self, left_speed, right_speed):
        """turnForward(leftSpeed, rightSpeed): Moves forwards in an arc by setting different speeds.
            0 <= leftSpeed,rightSpeed <= 100"""
        self.vx = left_speed + right_speed / 2.0
        self.vth = right_speed - left_speed

    def turnReverse(self, left_speed, right_speed):
        """turnReverse(leftSpeed, rightSpeed): Moves backwards in an arc by setting different speeds.
            0 <= leftSpeed,rightSpeed <= 100"""
        self.vx = -(left_speed + right_speed / 2.0)
        self.vth = right_speed - left_speed

    def stop(self):
        """Stops both motors"""
        self.vx = 0
        self.vth = 0
        
    
    def getSwitch(self):
        """Returns the value of the tact switch: True==pressed"""
        return self.robot_control_switch_on
    
    def getLight(self, sensor):
        """Returns the value 0..1023 for the selected sensor, 0 <= Sensor <= 3"""
        if sensor == 0:
            return self.getLightFL()
        elif sensor == 1:
            return self.getLightFR()
        elif sensor == 2:
            return self.getLightBR()
        elif sensor == 3:
            return self.getLightBL()
        else:
            return 0
    
    def getLightFL(self):
        """Returns the value 0..1023 for Front-Left light sensor"""
        return self.fl_light_sensor
    
    def getLightFR(self):
        """Returns the value 0..1023 for Front-Right light sensor."""
        return self.fr_light_sensor
    
    def getLightBL(self):
        """Returns the value 0..1023 for Back-Left light sensor"""
        return self.bl_light_sensor
    
    def getLightBR(self):
        """Returns the value 0..1023 for Back-Right light sensor"""
        return self.br_light_sensor

    def cmd_vel(self, vx, vth):
        """Control the robot by giving it a linear (vx) and angular velocity (vth)"""
        self.vx = vx
        self.vth = vth
 
#======================================================================
# Pi2Go only functions - placeholders for now
#======================================================================
   
    def setLED(self, LED, red, green, blue):
        """Sets the LED specified to required RGB value. 0 >= LED <= 7; 0 <= R,G,B <= 4095"""
        # print ("setting leds")
        if (LED == 0): # first front led (front-left)
            self.front_led1_red_value = red
            self.front_led1_green_value = green
            self.front_led1_blue_value = blue
         # elif (LED == 1): # second front led (front-right)
            self.front_led2_red_value = red
            self.front_led2_green_value = green
            self.front_led2_blue_value = blue
        elif (LED == 1): # first right-side led
            self.right_led1_red_value = red
            self.right_led1_green_value = green
            self.right_led1_blue_value = blue
         # elif (LED == 3): # second right-side led
            self.right_led2_red_value = red
            self.right_led2_green_value = green
            self.right_led2_blue_value = blue
        elif (LED == 2): # first back-side led
            self.back_led1_red_value = red
            self.back_led1_green_value = green
            self.back_led1_blue_value = blue
         # elif (LED == 5): # second back-side led
            self.back_led2_red_value = red
            self.back_led2_green_value = green
            self.back_led2_blue_value = blue
        elif (LED == 3): # first left-side led
            self.left_led1_red_value = red
            self.left_led1_green_value = green
            self.left_led1_blue_value = blue
         # elif (LED == 7): # second left-side led
            self.left_led2_red_value = red
            self.left_led2_green_value = green
            self.left_led2_blue_value = blue
        #else:
        #    self.setAllLEDs(red, green, blue)


    def setAllLEDs(self, red, green, blue):
        """Sets all LEDs to required RGB. 0 <= R,G,B <= 4095"""
        for i in range(4):
            self.setLED(i, red, green, blue)
    
    def getLED(self, LED):
        """Gets the RGB colour value of the LED specified. 0 >= LED <= 7; 0 <= R,G,B <= 4095"""
        if (LED == 0): # first front led (front-left) 
            return (self.front_led1_red_value, self.front_led1_green_value, self.front_led1_blue_value)
        elif (LED == 1): # second front led (front-right)
            return (self.front_led2_red_value, self.front_led2_green_value, self.front_led2_blue_value)
        elif (LED == 2): # first right-side led
            return (self.right_led1_red_value, self.right_led1_green_value, self.right_led1_blue_value)
        elif (LED == 3): # second right-side led
            return (self.right_led2_red_value, self.right_led2_green_value, self.right_led2_blue_value)
        elif (LED == 4): # first back-side led
            return (self.back_led1_red_value, self.back_led1_green_value, self.back_led1_blue_value)
        elif (LED == 5): # second back-side led
            return (self.back_led2_red_value, self.back_led2_green_value, self.back_led2_blue_value)
        elif (LED == 6): # first left-side led
            return (self.left_led1_red_value, self.left_led1_green_value, self.left_led1_blue_value)
        elif (LED == 7): # second left-side led
            return (self.left_led2_red_value, self.left_led2_green_value, self.left_led2_blue_value)
        #else:
        #    self.setAllLEDs(red, green, blue)


    def getAllLEDs(self):
        """Gets the RGB values of all LEDs. 0 <= R,G,B <= 4095"""
        all_led_values = []
        for i in range(8):
            all_led_values.append(getLED(i))
        return all_led_values
        
        

    def send_commands(self):
        """Thread function which sends commands to the simulator via a UDP socket.

        Commands for the initio robot take the form:

            <<LINEAR_VELOCITY;ANGULAR_VELOCITY;SONAR_SERVO_ANGLE>>

        Commands for the pi2go robot take the form:

            <<LINEAR_VELOCITY;ANGULAR_VELOCITY; RED_LED; 
              FRONT_LED1_RED_VALUE;FRONT_LED1_GREEN_VALUE;FRONT_LED1_BLUE_VALUE;
              FRONT_LED2_RED_VALUE;FRONT_LED2_GREEN_VALUE;FRONT_LED2_BLUE_VALUE;
              LEFT_LED1_RED_VALUE;LEFT_LED1_GREEN_VALUE;LEFT_LED1_BLUE_VALUE;
              LEFT_LED2_RED_VALUE;LEFT_LED2_GREEN_VALUE;LEFT_LED2_BLUE_VALUE;
              BACK_LED1_RED_VALUE;BACK_LED1_GREEN_VALUE;BACK_LED1_BLUE_VALUE;
              BACK_LED2_RED_VALUE;BACK_LED2_GREEN_VALUE;BACK_LED2_BLUE_VALUE;
              RIGHT_LED1_RED_VALUE;RIGHT_LED1_GREEN_VALUE;RIGHT_LED1_BLUE_VALUE;
              RIGHT_LED2_RED_VALUE;RIGHT_LED2_GREEN_VALUE;RIGHT_LED2_BLUE_VALUE>>
        """
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        while self.running:
            if self.robot_name == "INITIO":
                message = "<<%f;%f;%f>>" % (
                self.vx, self.vth, self.sonar_angle)
                sock.sendto(message, (UDP_IP, UDP_COMMAND_PORT))
            elif self.robot_name == "PI2GO":
                # print(self.front_led1_red_value)
                message = "<<%f;%f;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d>>" % (
                self.vx, self.vth,
                int(self.front_led1_red_value),
                int(self.front_led1_green_value),
                int(self.front_led1_blue_value),
                int(self.front_led2_red_value),
                int(self.front_led2_green_value),
                int(self.front_led2_blue_value),
                
                int(self.right_led1_red_value),
                int(self.right_led1_green_value),
                int(self.right_led1_blue_value),
                int(self.right_led2_red_value),
                int(self.right_led2_green_value),
                int(self.right_led2_blue_value),
                        
                int(self.back_led1_red_value),
                int(self.back_led1_green_value),
                int(self.back_led1_blue_value),
                int(self.back_led2_red_value),
                int(self.back_led2_green_value),
                int(self.back_led2_blue_value),
                            
                int(self.left_led1_red_value),
                int(self.left_led1_green_value),
                int(self.left_led1_blue_value),
                int(self.left_led2_red_value),
                int(self.left_led2_green_value),
                int(self.left_led2_blue_value))
                sock.sendto(message.encode('utf-8'), (UDP_IP, UDP_COMMAND_PORT))
            time.sleep(PUBLISH_INTERVAL)

    def update_state(self):
        """Thread function which receives the state of the robot from the simulator via a UDP socket.

        State strings for the initio take the form:

            <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;RIGHT_IR;
            FRONT_LEFT_LIGHT_SENSOR;FRONT_RIGHT_LIGHT_SENSOR; 
             BACK_RIGHT_LIGHT_SENSOR;BACK_LEFT_LIGHT_SENSOR;>>

        State strings for the pi2go take the form:

             <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;MIDDLE_IR;RIGHT_IR;
             FRONT_LEFT_LIGHT_SENSOR;FRONT_RIGHT_LIGHT_SENSOR; 
              BACK_RIGHT_LIGHT_SENSOR; BACK_LEFT_LIGHT_SENSOR;
             RED_LED_STATE; GREEN_LED_STATE; BLUE_LED_STATE; CONTROL_SWITCH>>
        """
        print("starting update thread")
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind((UDP_IP, UDP_DATA_PORT))
        while self.running:
            data_e, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            data = data_e.decode();
            if data.startswith("<<") and data.endswith(">>"):
                data = data.replace("<<", "")
                data = data.replace(">>", "")
                values_list = data.split(";")
                self.robot_name = str(values_list[0])
                if self.robot_name.startswith("INITIO"):
                    self.sonar_range = float(values_list[1])
                    self.left_line_sensor_triggered = int(values_list[2])
                    self.right_line_sensor_triggered = int(values_list[3])
                    self.ir_left_triggered = int(values_list[4])
                    self.ir_right_triggered = int(values_list[5])
                    self.fl_light_sensor = int(values_list[6])
                    self.fr_light_sensor = int(values_list[7])
                    self.br_light_sensor = int(values_list[8])
                    self.bl_light_sensor = int(values_list[9])
                    self.robot_control_switch_on = int(values_list[10])
                elif self.robot_name.startswith("PI2GO"):
                    self.sonar_range = float(values_list[1])
                    self.left_line_sensor_triggered = int(values_list[2])
                    self.right_line_sensor_triggered = int(values_list[3])
                    self.ir_left_triggered = int(values_list[4])
                    self.ir_middle_triggered = int(values_list[5])
                    self.ir_right_triggered = int(values_list[6])
                    self.fl_light_sensor = int(values_list[7])
                    self.fr_light_sensor = int(values_list[8])
                    self.br_light_sensor = int(values_list[9])
                    self.bl_light_sensor = int(values_list[10])
                    
                    # self.front_led1_red_value = int(values_list[11])
                    # self.front_led1_green_value = int(values_list[12])
                    # self.front_led1_blue_value = int(values_list[13])
                    # self.front_led2_red_value = int(values_list[14])
                    # self.front_led2_green_value = int(values_list[15])
                    # self.front_led2_blue_value = int(values_list[16])
                    
                    # self.right_led1_red_value = int(values_list[17])
                    # self.right_led1_green_value = int(values_list[18])
                    # self.right_led1_blue_value = int(values_list[19])
                    # self.right_led2_red_value = int(values_list[20])
                    # self.right_led2_green_value = int(values_list[21])
                    # self.right_led2_blue_value = int(values_list[22])
                       
                    # self.back_led1_red_value = int(values_list[23])
                    # self.back_led1_green_value = int(values_list[24])
                    # self.back_led1_blue_value = int(values_list[25])
                    # self.back_led2_red_value = int(values_list[26])
                    # self.back_led2_green_value = int(values_list[27])
                    # self.back_led2_blue_value = int(values_list[28])
     
                    # self.left_led1_red_value = int(values_list[29])
                    # self.left_led1_green_value = int(values_list[30])
                    # self.left_led1_blue_value = int(values_list[31])
                    # self.left_led2_red_value = int(values_list[32])
                    # self.left_led2_green_value = int(values_list[33])
                    # self.left_led2_blue_value = int(values_list[34])
                    self.robot_control_switch_on = int(values_list[35])
                    # print "received message:", data
            time.sleep(PUBLISH_INTERVAL)
        sock.close()

    def cleanup(self):
        self.running = False
