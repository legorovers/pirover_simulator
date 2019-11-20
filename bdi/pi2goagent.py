import bdi.bdiagent as agent
import simclient.simrobot as pi2go

class Pi2GoAgent(agent.Agent):
    def __init__(self):
        agent.Agent.__init__(self)
        self.initialised = 0
        self.robot = pi2go

    def getpercepts(self, beliefbase):
        dist = pi2go.getDistance()
        beliefbase['distance'] = dist
        irR = pi2go.irRight()
        beliefbase['obstacle_right'] = irR
        irL = pi2go.irLeft()
        beliefbase['obstacle_left'] = irL
        irC = pi2go.irCentre()
        beliefbase['obstacle_centre'] = irC
        irLL = pi2go.irLeftLine()
        beliefbase['line_left'] = irLL
        irRL = pi2go.irRightLine()
        beliefbase['line_right'] = irRL
        switch = pi2go.getSwitch()
        beliefbase['switch_pressed']= switch
        lightFL = pi2go.getLightFL()
        beliefbase['lightFL'] = lightFL
        lightFR = pi2go.getLightFR()
        beliefbase['lightFR'] = lightFR
        lightBL = pi2go.getLightBL()
        beliefbase['lightBL'] = lightBL
        lightBR = pi2go.getLightBR()
        beliefbase['lightBR'] = lightBR
        super()
        return
        
    def getPercepts(self):
        self.getpercepts(self.beliefbase)
        
    def run_agent(self):
        if not (initialised):
            pi2go.init()
            self.initialised = 1
        super().run_agent()

    def init(self):
        pi2go.init()
        
    def cleanup(self):
        pi2go.cleanup()
        
        
