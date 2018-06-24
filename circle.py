# circle.py
# by Dave Pape, for DMS 423
#
# draws a circle, where the points for the vertex list are computed at run-time

from math import *
from pyglet.gl import *

window = pyglet.window.Window()

def makeCircle(numPoints):
    verts = []
    verts += [50,50]
    for i in range(100, 135):
        angle = radians(i)
        x = 50*cos(angle) + 50
        y = 50*sin(angle) + 50
        verts += [x,y]
    global circle
    circle = pyglet.graphics.vertex_list(36, ('v2f', verts))

makeCircle(360)

@window.event
def on_draw():
    global circle
    glClear(pyglet.gl.GL_COLOR_BUFFER_BIT)
    glColor3f(1,1,0)
    circle.draw(GL_TRIANGLE_FAN)

pyglet.app.run()