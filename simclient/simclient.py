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
        self.robot_name = "Not Connected"

        self.update_thread = threading.Thread(target=self.update_state)
        self.update_thread.setDaemon(True)
        self.update_thread.start()

        self.cmd_thread = threading.Thread(target=self.send_commands)
        self.cmd_thread.setDaemon(True)
        self.cmd_thread.start()

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

    def cmd_vel(self, vx, vth):
        """Control the robot by giving it a linear (vx) and angular velocity (vth)"""
        self.vx = vx
        self.vth = vth

    def send_commands(self):
        """Thread function which sends commands to the simulator via a UDP socket.

        Commands for the initio robot take the form:

            <<LINEAR_VELOCITY;ANGULAR_VELOCITY;SONAR_SERVO_ANGLE>>

        Commands for the pi2go robot take the form:

            <<LINEAR_VELOCITY;ANGULAR_VELOCITY>>
        """
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        while True:
            if self.robot_name == "INITIO":
                message = "<<%f;%f;%f>>" % (self.vx, self.vth, self.sonar_angle)
                sock.sendto(message, (UDP_IP, UDP_COMMAND_PORT))
            elif self.robot_name == "PI2GO":
                message = "<<%f;%f>>" % (self.vx, self.vth)
                sock.sendto(message, (UDP_IP, UDP_COMMAND_PORT))
            time.sleep(0.15)

    def update_state(self):
        """Thread function which receives the state of the robot from the simulator via a UDP socket.

        State strings for the initio take the form:

            <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;RIGHT_IR>>

        State strings for the pi2go take the form:

             <<ROBOT_NAME;SONAR_RANGE;LEFT_LINE;RIGHT_LINE;LEFT_IR;MIDDLE_IR;RIGHT_IR>>
        """
        print "starting update thread"
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind((UDP_IP, UDP_DATA_PORT))
        while True:
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            if data.startswith("<<") and data.endswith(">>"):
                data = data.replace("<<", "")
                data = data.replace(">>", "")
                values_list = data.split(";")
                if len(values_list) == 6:
                    self.robot_name = str(values_list[0])
                    self.sonar_range = float(values_list[1])
                    self.left_line_sensor_triggered = int(values_list[2])
                    self.right_line_sensor_triggered = int(values_list[3])
                    self.ir_left_triggered = int(values_list[4])
                    self.ir_right_triggered = int(values_list[5])
                elif len(values_list) == 7:
                    self.robot_name = str(values_list[0])
                    self.sonar_range = float(values_list[1])
                    self.left_line_sensor_triggered = int(values_list[2])
                    self.right_line_sensor_triggered = int(values_list[3])
                    self.ir_left_triggered = int(values_list[4])
                    self.ir_middle_triggered = int(values_list[5])
                    self.ir_right_triggered = int(values_list[6])
                    # print "received message:", data
