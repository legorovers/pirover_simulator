import pytest
from src.sensors.led import FixedLED

@pytest.fixture(scope='session', autouse=True)
def init_led():
    return FixedLED(None, 0, 0)
