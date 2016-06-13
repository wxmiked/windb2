from windb2.struct.winddata import WindData
import math


class WindData3D(WindData):
    """Vertical velocity in units (up is positive)"""
    wSpeed = None

    """Returns the speed in the W direction."""

    def getWSpeed(self):
        return self.wSpeed

    """Creates a new WindData object with speed"""

    def __init__(self, time, height, speed, direction, wSpeed, units="ms^-1"):
        # Call the super constructor
        super(WindData, self).__init__(time, height, speed, direction, units="ms^-1")

        # Init w speed
        self.wSpeed = float(wSpeed)

    """Creates a new WindData object with u,v components"""

    def __init__(self, time, height, u, v, wSpeed, units="ms^-1"):
        # Call the super constructor
        super(WindData, self).__init__(time, height, float(pow(pow(u, 2) + pow(v, 2), 0.5)), float(calcDirDeg(u, v)),
                                       units="ms^-1")

        # Init w speed
        self.wSpeed = float(wSpeed)
