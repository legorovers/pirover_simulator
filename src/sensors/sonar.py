"""
sonar.py defines a map and sensor class to simulate a typical sinar sensor. This is achieved using a 2D grid map which
is defined in the Map class. The grid is a binary occupancy grid meaning a value of 1=occpied and 0=free.

The Sonar class contains functions for ray casting in order to compute distance values based on obstacles defined
by the grid map. The Sonar class uses multiple rays to replicate the wide conical nature of typical sonar sensor beams.
Note the sonar sensor will be triggered by the edges of the map/screen as well as the obstacles defined in the grid map.
"""

from math import pi, cos, sin
from src.sensors.ray import Ray
from src.robots.robotconstants import SONAR_INTENSITY
try:
    import numpy as np
except ImportError:
    import src.numpysim as np
import pyglet
SONAR_BEAM_STEP = pi / 25.0


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
        for x in range(ctr_x_cells - size_x_cells, ctr_x_cells + size_x_cells + 1):
            for y in range(ctr_y_cells - size_y_cells, ctr_y_cells + size_y_cells + 1):
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
                                     x * cell_size + cell_size, y * cell_size + cell_size)
                    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
                                                 [0, 1, 2, 1, 2, 3],
                                                 ('v2i', square_coords))


class Sonar(object):
    def __init__(self, sensor_map, min_range, max_range, cone_angle):
        self.min_range = min_range
        self.max_range = max_range
        self.cone_angle = cone_angle
        self.sensor_map = sensor_map
        self.current_range = -1.0

    def update_sonar(self, x, y, theta):
        """Returns the distance to the nearest obstacle for a sensor at position (x, y) and at angle theta."""
        # start at max range
        self.current_range = self.max_range
        # create a bundle of rays to replicate a sonar beam
        sweep = np.arange(-self.cone_angle / 2.0, self.cone_angle / 2.0, SONAR_BEAM_STEP)
        # cast each ray until it hits an obstacle or the end of the map
        # print (self.sensor_map.grid)
        for angle in sweep:
            """
            distance = 1
            while distance <= (self.max_range / self.sensor_map.resolution):

                xmap = x / self.sensor_map.resolution
                xmap += distance * cos(angle + theta)
                xmap = int(xmap)

                ymap = y / self.sensor_map.resolution
                ymap += distance * sin(angle + theta)
                ymap = int(ymap)

                if ymap > self.sensor_map.height - 1 or xmap > self.sensor_map.width - 1:
                    break

                if ymap < 1 or xmap < 1:
                    break

                if self.sensor_map.grid[ymap][xmap]:
                    # print(xmap)
                    break
                distance += 1
            range = distance * self.sensor_map.resolution
            if range < self.max_range and range < self.current_range:
                self.current_range = range

        # cap the distance to the min and max values of the sensors
        if self.current_range < self.min_range:
            self.current_range = self.min_range
        elif self.current_range >= self.max_range:
            self.current_range = self.max_range
        """
            ray = Ray(x, y, SONAR_INTENSITY, angle + theta)
            print(f"I={ray.intensity}, theta={ray.theta}")
        return self.current_range
