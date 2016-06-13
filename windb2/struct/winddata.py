from windb2.struct.flowdata import FlowData
import math


class WindData(FlowData):
    """Direction the wind came FROM (meteorological direction) [degrees]"""
    direction = None

    """Returns the speed in the U direction."""

    def getUSpeed(self):
        return math.sin(math.radians(self.direction + 180)) * self.speed

    """Returns the speed in the V direction."""

    def getVSpeed(self):
        return math.cos(math.radians(self.direction + 180)) * self.speed

    """Returns the speed in the U direction."""

    def getUSpeed(self):
        return math.sin(math.radians(self.direction + 180)) * self.speed

    """Returns the speed in the V direction."""

    def getVSpeed(self):
        return math.cos(math.radians(self.direction + 180)) * self.speed

    """Subtracts CurrentData from WindData."""

    def __sub__(self, flowData):

        # Make sure the times match
        if self.time != flowData.time:
            raise ValueError("FlowData times do not match.")

        # Make sure the units match
        if self.units != flowData.units:
            raise ValueError("FlowData units do not match.")

        uDiff = self.getUSpeed() - flowData.getUSpeed()
        vDiff = self.getVSpeed() - flowData.getVSpeed()

        # Calculate the direction from north


        return FlowData(self.time, 0, math.sqrt(math.pow(uDiff, 2) + math.pow(vDiff, 2)), calcDirDeg(uDiff, vDiff))


def calcDirDeg(uWind, vWind):
    """Calculates the direction THAT THE WIND IS BLOWING FROM (not the vector direction).
     *
     * uWind U wind scalar velocity.
     * vWind V wind scalar velocity.
     * Returns he direction that the wind is blowing from.
    """

    # Calculate the direction and round it into a integer
    try:
        directionDouble = math.degrees(math.atan(math.fabs(vWind / uWind)))
    except ZeroDivisionError:
        # This can happen if uWind is zero, see what vWind is and return 0 i.e. arctangent
        # The sign will be sorted out below
        directionDouble = 0

    # Convert to an int
    directionInt = round(directionDouble);

    # Division by zero case from above
    if uWind == 0.0 and vWind >= 0:
        directionInt = 0
    elif uWind == 0.0 and vWind < 0:
        directionInt = 180

    # Calculate the quadrant of the wind
    # NE quadrant
    elif uWind > 0 and vWind >= 0:
        directionInt = 90 - directionInt;

    # SE quadrant
    elif uWind >= 0 and vWind < 0:
        directionInt += 90;

    # SW quadrant
    elif uWind < 0 and vWind <= 0:
        directionInt = 270 - directionInt;

    # NW quadrant
    elif uWind <= 0 and vWind > 0:
        directionInt += 270;


    # SWITCH FOR METEOROLOGICAL WIND DIRECTION INSTEAD OF THE VECTOR DIRECTION
    directionInt = (directionInt + 180) % 360;

    # Throw an exception if the wind direction is greater than 360 or negative
    if directionInt < 0:
        raise ValueError("You cannot have a negative wind direction here: " + directionInt + " degrees is invalid.")

    if directionInt >= 360:
        raise ValueError("You cannot have a wind direction >= 360 here: " + directionInt + " degrees is invalid.")

    return directionInt
