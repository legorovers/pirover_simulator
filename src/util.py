"""
util.py contains some general helper functions used throughout the simulator.
"""
import math
import pyglet
import sys
import os
import threading


def resource_path(relative):
    """Get a relative path."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


def get_resource_path():
    """Get the path to the resources folder."""
    resource_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
    return resource_path(resource_folder)


def get_world_path():
    """Get the path to the world folder."""
    resource_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'worlds')
    return resource_path(resource_folder)


def rotate(point, angle):
    """Rotate a point around a given angle"""
    px, py = point
    qx = math.cos(angle) * px - math.sin(angle) * py
    qy = math.sin(angle) * px + math.cos(angle) * py
    return qx, qy


def rotate_around_og(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def wrap_angle(angle):
    """Wrap an angle between 0 and PI*2"""
    if angle >= (math.pi * 2.0):
        angle -= math.pi * 2.0
    elif angle < 0.0:
        angle += math.pi * 2
    return angle


def distancesq(point1=(0, 0), point2=(0, 0)):
    """Returns the squared distance between two points"""
    return (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2


def distance(point_1=(0, 0), point_2=(0, 0)):
    """Returns the distance between two points"""
    return math.sqrt((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2)


def center_image(image):
    """Sets an image's anchor point to its center"""
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2


# generic pyglet drawing functions
# sourced from:
# http://nullege.com/codes/show/src%40s%40p%40Space-Train-HEAD%40engine%40util%40draw.py/19/pyglet.graphics.draw/python


def line(x1, y1, x2, y2, colors=None):
    if colors is None:
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (x1, y1, x2, y2)))
    else:
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (x1, y1, x2, y2)), ('c4f', colors))


def line_loop(points, colors=None):
    """
    @param points: A list formatted like [x1, y1, x2, y2...]
    @param colors: A list formatted like [r1, g1, b1, a1, r2, g2, b2 a2...]
    """
    if colors is None:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_LINE_LOOP, ('v2f', points))
    else:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_LINE_LOOP, ('v2f', points), ('c4f', colors))


def rect(x1, y1, x2, y2):
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2f', (x1, y1, x1, y2, x2, y2, x2, y1)))


def rect_outline(x1, y1, x2, y2):
    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP, ('v2f', (x1, y1, x1, y2, x2, y2, x2, y1)))


def _concat(it):
    return list(y for x in it for y in x)


def _iter_ellipse(x1, y1, x2, y2, da=None, step=None, dashed=False):
    xrad = abs((x2 - x1) / 2.0)
    yrad = abs((y2 - y1) / 2.0)
    x = (x1 + x2) / 2.0
    y = (y1 + y2) / 2.0

    if da and step:
        raise ValueError("Can only set one of da and step")

    if not da and not step:
        step = 8.0

    if not da:
        # use the average of the radii to compute the angle step
        # shoot for segments that are 8 pixels long
        step = 32.0
        rad = max((xrad + yrad) / 2, 0.01)
        rad_ = max(min(step / rad / 2.0, 1), -1)

        # but if the circle is too small, that would be ridiculous
        # use pi/16 instead.
        da = min(2 * math.asin(rad_), math.pi / 16)

    a = 0.0
    while a <= math.pi * 2:
        yield (x + math.cos(a) * xrad, y + math.sin(a) * yrad)
        a += da
        if dashed: a += da


def ellipse(x1, y1, x2, y2):
    points = _concat(_iter_ellipse(x1, y1, x2, y2))
    pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_TRIANGLE_FAN, ('v2f', points))


def ellipse_outline(x1, y1, x2, y2):
    points = _concat(_iter_ellipse(x1, y1, x2, y2))
    pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_LINE_LOOP, ('v2f', points))


def circle(x, y, rad):
    ellipse(x - rad, y - rad, x + rad, y + rad)


def _iter_ngon(x, y, r, sides, start_angle=0.0):
    rad = max(r, 0.01)
    rad_ = max(min(sides / rad / 2.0, 1), -1)
    da = math.pi * 2 / sides
    a = start_angle
    while a <= math.pi * 2 + start_angle:
        yield (x + math.cos(a) * r, y + math.sin(a) * r)
        a += da


def ngon(x, y, r, sides, start_angle=0.0):
    points = _concat(_iter_ngon(x, y, r, sides, start_angle))
    pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_TRIANGLE_FAN, ('v2f', points))


def ngon_outline(x, y, r, sides, start_angle=0.0):
    points = _concat(_iter_ngon(x, y, r, sides, start_angle))
    pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_LINE_LOOP, ('v2f', points))


def points(points, colors=None):
    """
    @param points: A list formatted like [x1, y1, x2, y2...]
    @param colors: A list formatted like [r1, g1, b1, a1, r2, g2, b2 a2...]
    """
    if colors == None:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_POINTS, ('v2f', points))
    else:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_POINTS, ('v2f', points), ('c4f', colors))


def polygon(points, colors=None):
    """
    @param points: A list formatted like [x1, y1, x2, y2...]
    @param colors: A list formatted like [r1, g1, b1, a1, r2, g2, b2 a2...]
    """
    if colors == None:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_POLYGON, ('v2f', points))
    else:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_POLYGON, ('v2f', points), ('c4f', colors))


def quad(points, colors=None):
    if colors == None:
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2f', points))
    else:
        pyglet.graphics.draw(len(points) / 2, pyglet.gl.GL_POINTS, ('v2f', points), ('c4f', colors))


GRID_SPACING = 50


def grid(x, y, width, height):
    x_start, y_start = x, y
    x_end, y_end = x + width, y + height
    x -= x % GRID_SPACING
    y -= y % GRID_SPACING
    while x < x_end:
        line(x, y, x, y + height)
        x += GRID_SPACING
    x = x_start
    while y < y_end:
        line(x, y, x + width, y)
        y += GRID_SPACING


def draw_rect(x, y, width, height):
    pyglet.gl.glBegin(pyglet.gl.GL_LINE_LOOP)
    pyglet.gl.glVertex2f(x, y)
    pyglet.gl.glVertex2f(x + width, y)
    pyglet.gl.glVertex2f(x + width, y + height)
    pyglet.gl.glVertex2f(x, y + height)
    pyglet.gl.glEnd()
    
class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        """ constructor, setting initial variables """
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stopevent = threading.Event(  )
        self._sleepperiod = 1.0

    def run(self):
        """ main control loop """
        while not self._stopevent.isSet(  ):
            print("running stoppable thread")
            self._stopevent.wait(self._sleepperiod)

    def join(self, timeout=None):
        """ Stop the thread. """
        self._stopevent.set(  )
        threading.Thread.join(self, timeout)

