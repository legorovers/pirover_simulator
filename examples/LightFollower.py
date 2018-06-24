import simclient.simrobot as initio
import time


speed = 20
turn_speed = 10

initio.init()

def max_value_light_sensor():
    max_sensor = 0
    max_val = 0
    for i in range(4):
        val = initio.getLight(i)
        if val > max_val:
            max_val = val
            max_sensor = i
    return max_sensor
    
def sensor_values_equal(sensor_a, sensor_b):
    if sensor_a > 3 or sensor_a < 0: return False
    if sensor_b > 3 or sensor_b < 0: return False
    val_a = initio.getLight(sensor_a)
    val_b = initio.getLight(sensor_b)
    abs_diff = ((val_a - val_b)**2)**0.5
    if abs_diff <= 100: return True
    else: return False
    
# main loop
try:
    while True:
        while not (initio.getLight(0) > 800 and sensor_values_equal(0, 1)):
            initio.spinRight(turn_speed)
            time.sleep(0.05)
    
        while (initio.getLight(0) > 800 and sensor_values_equal(0, 1)):
            initio.forward(speed+10)

except KeyboardInterrupt:
    initio.cleanup()

