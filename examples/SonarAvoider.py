import time
import simclient.simrobot as initio

stop_range = 100.0
turn_speed = 50
move_speed = 60
sonar_wait = 1.5
PAN = 0

initio.init()

try:
    while True:
        print(initio.getDistance(), initio.irLeft(), initio.irRight())
        if initio.getDistance() < stop_range:
            initio.stop()
            print("range less than %f, looking around" % stop_range)
            left = right = 0
            initio.setServo(PAN, -70)
            time.sleep(sonar_wait)
            right = initio.getDistance()
            print("right range: %f" % right)

            initio.setServo(PAN, 70)
            time.sleep(sonar_wait)
            left = initio.getDistance()
            print("left range: %f" % left)

            initio.setServo(PAN, 0)
            time.sleep(sonar_wait)
            turn = 0
            if left > right:
                print("left wins")
                initio.spinLeft(turn_speed)
            elif right > left:
                print("right wins")
                initio.spinRight(turn_speed)
            else:
                initio.spinLeft(turn_speed+20)
            while True:
                print("turning")
                time.sleep(0.25)
                if initio.getDistance() > stop_range:
                    break
            initio.stop()
        else:
            # drive forwards
            initio.forward(move_speed)
        time.sleep(0.1)
except KeyboardInterrupt:
    initio.cleanup()
