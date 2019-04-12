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
        irLL = robohat.irLeftLine()
        beliefbase['no_line_left'] = irLL
        irRL = robohat.irRightLine()
        beliefbase['no_line_right'] = irRL
        super()
        return

    def cleanup(self):
        robohat.cleanup()
