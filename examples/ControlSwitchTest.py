import simclient.simrobot as initio
import time

switch_on_status = 0

initio.init()

    
# main loop
try:
    # initially
    sim_switch_status = int(initio.getSwitch())
    if sim_switch_status:
        print("Robot control switch is ON now...")
    else:
        print("Robot control switch is OFF now...")
            
    while True:        
        while sim_switch_status == switch_on_status:
            #time.sleep(0.8)  # wait a bit before checking again
            sim_switch_status = int(initio.getSwitch())
        
        if sim_switch_status:
            print("Robot control switch is ON now...")
        else:
            print("Robot control switch is OFF now...")
        
        # update switch_on_status with the updated sim_switch_status to make the value of both variables equal
        switch_on_status = sim_switch_status 
        # check switch status again     
        sim_switch_status = int(initio.getSwitch())
except KeyboardInterrupt:
    initio.cleanup()

