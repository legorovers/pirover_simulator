import simclient.simrobot as initio
import time

speed = 60
turn_speed = 50

initio.init()

# main loop
try:
    while True:
        print initio.irLeft(), initio.irRight()
        if initio.irAll():
            if initio.irLeft():
                initio.spinRight(turn_speed)
            elif initio.irRight():
                initio.spinLeft(turn_speed)
            while initio.irAll():
                time.sleep(0.2)
        else:
            initio.forward(speed)
        time.sleep(0.2)
except KeyboardInterrupt:
    initio.cleanup()
