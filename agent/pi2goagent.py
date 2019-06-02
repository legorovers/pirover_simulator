import agent.bdiagent as agent, simclient.simrobot as robohat

class Pi2GoAgent(agent.Agent):

    def __init__(self):
        robohat.init()
        agent.Agent.__init__(self)

    def getpercepts(self, beliefbase):
        dist = 50
        beliefbase['distance'] = dist
        irR = robohat.irRight()
        beliefbase['obstacle_right'] = irR
        irL = robohat.irLeft()
        beliefbase['obstacle_left'] = irL
        irC = robohat.irCentre()
        beliefbase['obstacle_centre'] = irC
        irLL = robohat.irLeftLine()
        beliefbase['no_line_left'] = irLL
        irRL = robohat.irRightLine()
        beliefbase['no_line_right'] = irRL
        switch = robohat.getSwitch()
        beliefbase['switch_pressed']= switch
        lightFL = robohat.getLightFL()
        beliefbase['lightFL'] = lightFL
        lightFR = robohat.getLightFR()
        beliefbase['lightFR'] = lightFR
        lightBL = robohat.getLightBL()
        beliefbase['lightBL'] = lightBL
        lightBR = robohat.getLightBR()
        beliefbase['lightBR'] = lightBR
        super()
        return

    def cleanup(self):
        robohat.cleanup()
