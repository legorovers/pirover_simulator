"""
sonar.py defines a map and sensor class to simulate a typical sinar sensor. This is achieved using a 2D grid map which
is defined in the Map class. The grid is a binary occupancy grid meaning a value of 1=occpied and 0=free.

The Sonar class contains functions for ray tracing in order to compute distance values based on obstacles defined by
the grid map and the various properties of the materials. The Sonar class uses multiple rays to replicate the wide
conical nature of typical sonar sensor beams. Note the sonar sensor will be triggered by the edges of the map/screen
as well as the obstacles defined in the grid map.

"""

from math import pi, cos, sin, atan2
from numpy import mean

from src.sensors.ray import Ray
from src.robots.robotconstants import SONAR_INTENSITY, SONAR_MIN_INTENSITY
import src.sprites.materialconstants as alpha

try:
    import numpy as np
except ImportError:
    import src.numpysim as np
import pyglet

SONAR_BEAM_STEP = pi / 25.0
DS = 330 * (1 / 60)  # Distance per dt


class Map(object):
    def __init__(self, window_width, window_height, cell_size):
        self.origin_x = 0
        self.origin_y = 0
        self.resolution = cell_size
        self.height = int(window_height / cell_size)
        self.width = int(window_width / cell_size)
        self.grid = [[0 for x in range(self.width)] for y in range(self.height)]

    def clear_map(self):
        """Removes all obstacles from the Grid Map."""
        self.grid = [[0 for x in range(self.width)] for y in range(self.height)]

    def insert_rectangle(self, ctr_x, ctr_y, size_x, size_y, cell_value=1):
        """Insert a rectangle into the Grid Map at position defined by (ctr_x, ctr_y) and
            size (size_x, size_y). The optional cell value allows this function to be used to
            delete a rectangle."""
        ctr_x_cells = int(ctr_x / self.resolution)
        ctr_y_cells = int(ctr_y / self.resolution)
        # size_x_cells = int(size_x / self.resolution)
        # size_y_cells = int(size_y / self.resolution)
        size_x_cells = int(size_x / self.resolution / 2)
        size_y_cells = int(size_y / self.resolution / 2)
        for x in range(ctr_x_cells - size_x_cells,
                       ctr_x_cells + size_x_cells + 1):
            for y in range(ctr_y_cells - size_y_cells,
                           ctr_y_cells + size_y_cells + 1):
                self.set_cell(int(x), int(y), cell_value)

    def delete_rectangle(self, ctr_x, ctr_y, size_x, size_y):
        """Delete a rectangle into the Grid Map at position defined by (ctr_x, ctr_y) and
            size (size_x, size_y). Uses the code from the insert_rectangle function to
            avoid duplication."""
        self.insert_rectangle(ctr_x, ctr_y, size_x, size_y, 0)

    def set_cell(self, x, y, val):
        """Set the value of a grid cell (x, y)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = val

    def draw(self):
        """Draw the Grid Map."""
        cell_size = self.resolution
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[y][x]:
                    square_coords = (x * cell_size, y * cell_size,
                                     x * cell_size, y * cell_size + cell_size,
                                     x * cell_size + cell_size, y * cell_size,
                                     x * cell_size + cell_size,
                                     y * cell_size + cell_size)
                    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
                                                 [0, 1, 2, 1, 2, 3],
                                                 ('v2i', square_coords))
class Sonar(object):
    """
    TODO:
    - add gaussian noise / variance
    - use OpenGL to draw the rays
    """
    BEAMS = 30
    def __init__(self, sensor_map, min_range, max_range, cone_angle, beams):
        self.min_range = min_range
        self.max_range = max_range
        self.cone_angle = cone_angle
        self.sensor_map = sensor_map
        self.beams = beams
        self.current_range = -1.0

    def update_sonar(self, x, y, theta):
        """Returns the distance to the nearest obstacle for a sensor at
        position (x, y) and at angle theta."""
        sensor_pos_map = [int(x / self.sensor_map.resolution),
                          int(y / self.sensor_map.resolution)]
        self.current_range = self.max_range

        step = self.cone_angle / self.beams
        sweep = np.arange(-self.cone_angle / 2, self.cone_angle / 2, step)
        sensor_rays = []
        ray_num = 0
        #print("sweep")
        #print(f"sensor position: ({x}, {y})")
        for angle in sweep:  # Emit rays in a fan
            x1 = x  # x1 represents the previous x value before collision
            y1 = y
            ray = Ray(x, y, SONAR_INTENSITY, angle + theta)
            while ray.intensity > SONAR_MIN_INTENSITY and ray.bounces < 15:
                # Continue until ray is no longer detectable or has bounced
                # too many times
                xmap = int(ray.x / self.sensor_map.resolution)
                ymap = int(ray.y / self.sensor_map.resolution)
                # Check if ray is out of bounds, it should bounce.
                if xmap < 0 or xmap >= self.sensor_map.width or ymap < 0 or ymap >= self.sensor_map.height:
                    #print(f"Ray {ray_num} (out of bounds) bounced at: ({x1},{y1})!")
                    ray.bounce(x1, y1, xmap, ymap)
                    x1 = ray.x
                    y1 = ray.y
                elif self.sensor_map.grid[ymap][xmap]:  # Obstacle detected or hit the edge.
                    #print(f"Ray {ray_num} bounced at: ({x1},{y1})!")
                    ray.bounce(x1, y1, xmap, ymap)
                    x1 = ray.x
                    y1 = ray.y
                    ray.reduce_intensity(alpha.BOX)  # Reduce intensity due to collision
                    #print(f"Ray {ray_num} intensity is now: {ray.intensity}")

                elif int(ray.x) == int(x) and int(ray.y) == int(y) and ray.bounces != 0:
                    sensor_rays.append(ray)
                    print(f"Ray {ray_num} hit the sensor at: ({x},{y})!")
                    break
                else:  # Move ray forward.
                    ray.x += cos(ray.theta)
                    ray.y += sin(ray.theta)
            ray_num += 1

        if sensor_rays:  # Update distance if rays hit the sensor and is in range.
            if self.min_range >= self.current_range >= self.max_range:
                self.current_range = mean([ray.distance for ray in sensor_rays])
            else:
                pass
        else:  # Blind spot so don't update
            pass
            #print(f"Sensor blindspot at: ({x},{y})!")
        return self.current_range
