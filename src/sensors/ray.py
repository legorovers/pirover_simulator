"""
ray.py defines an ultrasonic ray used for ray tracing.
"""
import math

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
        reduction = 10 * math.log10(coeff)
        self.intensity -= reduction