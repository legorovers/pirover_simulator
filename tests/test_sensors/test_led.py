import pytest
from src.sensors.led import FixedLED

def setUp():
    led = FixedLED(None, 0, 0)

def test_update_position():
    pass

def test_set_colour():
    led.set_colour(2, 2, 2)
    asset led.red_value == 2