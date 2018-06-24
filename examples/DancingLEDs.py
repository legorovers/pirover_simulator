import simclient.simrobot as initio
import time


NUM_LEDS = 8
step = 0

initio.init()
colour = [(244, 66, 66),
             (122, 145, 10),
             (66, 244, 125),
             (181, 182, 183),
             (122, 161, 186),
             (89, 244, 66),
             (200, 66, 244),
             (66, 244, 241)]
    
# main loop
try:
    # wait for the robot control switch to be turned ON
    while initio.getSwitch() == False:
        time.sleep(1.0)
    # ensure that the selected robot is one that has LEDs    
    assert(initio.getRobotName() == "PI2GO"), "Choose a robot with LEDs. Only Pi2Go robots have LEDs here."
    while True:
        for i in range(NUM_LEDS):
            c = (i + step) % NUM_LEDS
            initio.setLED(i, colour[c][0], colour[c][1], colour[c][2])
        time.sleep(0.7)
        #initio.spinLeft(20)
        # check that led values on simulator reflects the values set here (not necessary 
        # for dancing lights but good to see more API methods being used),
        for i in range(NUM_LEDS):
            c = (i + step) % NUM_LEDS
            try: 
                assert(initio.getLED(i) == colour[c])
                print("Light update in sync...")
            except AssertionError:
                print("Light update lag...")
        
        # turn of lights (black), to make colour change animation more pronounced
        for i in range(NUM_LEDS):
            c = (i + step) % NUM_LEDS
            initio.setLED(i, 0, 0, 0)
        time.sleep(0.1)
            
        # now rotate the lights
        step = (step + 1) % (NUM_LEDS+1)
        
except KeyboardInterrupt, AssertionError:
    initio.cleanup()

