"""Compatibility functions for numpy 

np.arange
---------
This is the only routine from numpy that is used within the robot simulator.
It is used for implementing the sonar sensor as a fan of beams within a defined cone

Implement a simplified version of this routine using a suggestion from
https://stackoverflow.com/questions/7267226/range-for-floats/7267280#7267280

Note: the 'dtype' parameter is ignored
"""

try:
    import numpy as np
    def arange( start, stop, step=1 ):
        np.arange( start, stop, step )

except ImportError:
    def arange( start, stop, step=1 ):
        while start < stop:
            yield start
            start += step

