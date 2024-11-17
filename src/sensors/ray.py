"""
ray.py defines an ultrasonic ray used for ray tracing.
"""
from math import cos, sin, atan2, log10

SPEED_OF_SOUND = 330  # Assumes no air pressure variations


# I could vary this but the effect on ultrasonic is in a small room is small.


class Ray:
    def __init__(self, x, y, intensity, theta):
        self.x = x
        self.y = y
        self.speed = SPEED_OF_SOUND
        self.intensity = intensity  # Intensity of ultrasonic in dB
        self.theta = theta
        self.bounces = 0  # Used to prevent the ray from bouncing infinitely
        self.distance = 0  # Distance travelled by the ray

    """
    Reduces the intensity given the coefficient of absorption of a material.
    Note that decibels are a logarithmic scale!
    """

    def reduce_intensity(self, coeff):
        reduction = 10 * log10(coeff)
        self.intensity += reduction

    """
    Reflects a ray given the position of the obstacle 
    and updates distance traveled
    """
    def bounce(self, x1, y1, xmap, ymap):
        # Use pythagoras to calculate distance from previous
        # position to collision point
        self.distance += ((self.x - x1) ** 2 + (
                self.y - y1) ** 2) ** 0.5
        # Calculate the new angle of the ray
        dx = self.x - xmap
        dy = self.y - ymap
        normal_angle = atan2(dy, dx)
        self.theta = 2 * normal_angle - self.theta
        # Move the ray out of the obstacle
        self.x -= dx
        self.y -= dy
        self.x += cos(self.theta)
        self.y += sin(self.theta)
        #self.reduce_intensity(alpha.BOX)  # Reduce intensity due to
        # collision
        self.bounces += 1
