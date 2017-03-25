import simclient.simrobot as initio
import time

speed = 20
turn_speed = 10

initio.init()

# main loop
try:
    while True:
        if initio.irLeftLine():
            initio.turnForward(speed-turn_speed, speed+turn_speed)
            time.sleep(0.1)
        elif initio.irRightLine():
            initio.turnForward(speed+turn_speed, speed-turn_speed)
            time.sleep(0.1)
        else:
            initio.forward(speed)

except KeyboardInterrupt:
    initio.cleanup()
