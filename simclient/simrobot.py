"""
simrobot.py replicates the interface style of the real initio and pi2go libraries. This makes switching between the
simulator and real robot a matter of changing an import statement.
"""

from simclient import SimulatorClient

PAN = 1
VERSION = 1
sim = None


def init():
    """initializes the simulator client"""
    global sim
    sim = SimulatorClient()


def cleanup():
    """stops the simulator client"""
    global sim
    sim.stop()
    pass


def version():
    """returns the version, in the case of the sim client this always returns 1"""
    return VERSION


def startServos():
    """Has no effect, added to keep compatibility with real robot"""
    pass


def stopServos():
    """Has no effect, added to keep compatibility with real robot"""
    pass


def startServod():
    """Has no effect, added to keep compatibility with real robot"""
    pass


def pinServod():
    """Has no effect, added to keep compatibility with real robot"""
    pass


def stopServod():
    """Has no effect, added to keep compatibility with real robot"""
    pass


def setServo(servo, degrees):
    """Sets the servo to position in degrees -90 to +90"""
    global sim
    sim.setServo(servo, degrees)


def getDistance():
    """Returns the distance in cm to the nearest reflecting object"""
    global sim
    return sim.getDistance()


def irLeft():
    """Returns state of Left IR Obstacle sensor"""
    global sim
    return sim.irLeft()


def irRight():
    """Returns state of Right IR Obstacle sensor"""
    global sim
    return sim.irRight()


def irCentre():
    """Returns state of Centre IR Obstacle sensor (Pi2Go Only)"""
    global sim
    return sim.irCentre()


def irAll():
    """Returns true if any of the Obstacle sensors are triggered"""
    global sim
    if sim.robot_name == "Initio":
        return sim.irLeft() or sim.irRight()
    else:
        return sim.irLeft() or sim.irRight() or sim.irCentre()


def irLeftLine():
    """Returns state of Left IR Line sensor"""
    global sim
    return sim.irLeftLine()


def irRightLine():
    """Returns state of Right IR Line sensor"""
    global sim
    return sim.irRightLine()


def forward(speed):
    """Sets both motors to move forward at speed. 0 <= speed <= 100"""
    global sim
    sim.forward(speed)


def reverse(speed):
    """Sets both motors to reverse at speed. 0 <= speed <= 100"""
    global sim
    sim.reverse(speed)


def spinLeft(speed):
    """Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
    global sim
    sim.spinLeft(speed)


def spinRight(speed):
    """Sets motors to turn opposite directions at speed. 0 <= speed <= 100"""
    global sim
    sim.spinRight(speed)


def turnForward(left_speed, right_speed):
    """Moves forwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100"""
    global sim
    sim.turnForward(left_speed, right_speed)


def turnReverse(left_speed, right_speed):
    """Moves backwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100"""
    global sim
    sim.turnReverse(left_speed, right_speed)


def stop():
    """Stops both motors"""
    global sim
    sim.stop()

#======================================================================
# Pi2Go only functions
#======================================================================

def getSwitch():
    """Returns the value of the tact switch: True==pressed"""
    global sim
    sim.getSwitch()

def getLight(sensor):
    """Returns the value 0..1023 for the selected sensor, 0 <= Sensor <= 3"""
    global sim
    sim.getLight(sensor)

def getLightFL():
    """Returns the value 0..1023 for Front-Left light sensor"""
    global sim
    sim.getLightFL()

def getLightFR(sensor):
    """Returns the value 0..1023 for Front-Right light sensor.  NB sensor input is an error"""
    global sim
    sim.getLightFR()

def getLightBL(sensor):
    """Returns the value 0..1023 for Back-Left light sensor"""
    global sim
    sim.getLightBL()

def getLightBR(sensor):
    """Returns the value 0..1023 for Back-Right light sensor"""
    global sim
    sim.getLightBR()

def setLED(LED, red, green, blue):
    """Sets the LED specified to required RGB value. 0 >= LED <= 3; 0 <= R,G,B <= 4095"""
    global sim
    sim.setLED(LED, red, green, blue)

def setAllLEDs(red, green, blue):
    """Sets all LEDs to required RGB. 0 <= R,G,B <= 4095"""
    global sim
    sim.setAllLEDs(red, green,blue)



