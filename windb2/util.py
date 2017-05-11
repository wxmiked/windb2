import math
import sys
from datetime import datetime
import pytz
import numpy

def speed(uWind, vWind):
    """Returns wind speed from orthogonal (u and v) wind components which can be scalars, lists, or numpy.arrays."""

    speed = numpy.sqrt(numpy.power(numpy.array(uWind), 2.0) + numpy.power(numpy.array(vWind), 2.0))

    if speed.shape == (1, ):
        return speed[0]
    else:
        return speed


def u_flow(speed, direction):
    """Returns the U-direction scalar (degrees, north-up)."""

    # Convert to numpy arrays
    speed = numpy.array(speed)
    direction = numpy.array(direction)

    # Check args
    assert(numpy.all(speed >= 0))
    assert(numpy.all(0 <= direction) and numpy.all(direction < 360))

    u = numpy.sin(numpy.radians(direction))*speed

    if u.shape == (1, ):
        return u[0]
    else:
        return numpy.array(u)


def u_met(speed, direction):
    """Returns the speed in the U using the meteorological convention of FROM."""

    return -u_flow(speed, direction)


def v_flow(speed, direction):
    """Returns the V-direction scalar (degrees, north-up)."""

    # Convert to numpy arrays
    speed = numpy.array(speed)
    direction = numpy.array(direction)

    # Check args
    assert(numpy.all(speed >= 0))
    assert(numpy.all(0 <= direction) and numpy.all(direction < 360))

    v = numpy.cos(numpy.radians(direction))*speed

    if v.shape == (1, ):
        return v[0]
    else:
        return numpy.array(v)


def v_met(speed, direction):
    """Returns the speed in the V using the meteorological convention of FROM."""

    return -v_flow(speed, direction)


def calc_dir_deg(u, v):
    """Calculates the direction from the orthogonal wind components.
    *
    * u U wind scalar velocity.
    * v V wind scalar velocity.

    * Returns he direction that a flow is going (i.e. not wind direction which is 180 degrees opposite).
    """

    import math

    # Calculate the direction and round it into a integer
    direction = math.degrees(math.atan2(u, v))

    # Convert to a positive direction
    if direction < 0:
        direction += 360

    return direction

def nanHelper(y):
    """Helper to handle indices and logical indices of NaNs.
       From: http://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= numpy.array(np.interp(x(nans), x(~nans), y[~nans]),dtype=np.float32)
    """
    import numpy as np

    return np.isnan(y), lambda z: z.nonzero()[0]

def getDomainExtents(geogridFilename,paddingDegrees = 0.):
    """Finds the latitude and longitude domain extent from a geo_em.d0[X].nc .

    geogridFile - geo_em.d0[X].nc file name, can include directories
    paddingDegrees - decimal degrees to pad the domain with, default 0

    return minLong, maxLong, minLat, maxLat
    """

    import scipy.io.netcdf as nc
    import numpy as np


    # Open the file
    file = open(geogridFilename, 'r')
    ncFile = nc.netcdf_file(file, 'r')

    # Get the lat and long dimensions
    xDim = ncFile.dimensions['west_east_stag']
    yDim = ncFile.dimensions['south_north_stag']

    # Get the long and lat variables, using the U and V respectively because the extend out of the domain the most
    longVar = ncFile.variables['XLONG_U']
    latVar = ncFile.variables['XLAT_V']

    # Get the mins and maxes
    minLong = np.min(longVar[0,:,0])
    maxLong = np.max(longVar[0,:,xDim - 1])
    minLat = np.min(latVar[0,0,:])
    maxLat = np.max(latVar[0,yDim - 1, :])

    # Close the file
    ncFile.close()

    return minLong - paddingDegrees, maxLong + paddingDegrees, minLat - paddingDegrees, maxLat + paddingDegrees

def get_deg_from_cardinal(cardinal):
    """Returns the direction in degrees for a 16-sector cardinal direction (e.g. WSW, NE, etc...)
    """

    dirdeg = {'N': 0,'NNE': 22.5, 'NE': 45.0, 'ENE': 67.5, 'E': 90.0, 'ESE': 112.5, 'SE': 135.0, 'SSE': 157.5,
              'S': 180.0, 'SSW': 202.5, 'SW': 225.0, 'WSW': 247.5, 'W': 270.0, 'WNW': 292.5, 'NW': 315.0, 'NNW': 337.5}

    # Raises key error if not found
    try:
        return dirdeg[cardinal]
    except:
        raise

def get_cardinal_from_deg(dir):
    """Returns a 16-sector cardinal direction (e.g. WSW, NE, etc...) for a direction in degrees
    """

    if dir >= 337.5 and dir < 360 or dir < 22.5:
       return 'N';
    elif dir >= 22.5  and dir < 67.5:
        return 'NE'
    elif dir >= 67.5  and dir < 112.5:
    	   return 'E'
    elif dir >= 112.5 and dir < 157.5:
        return 'SE'
    elif dir >= 157.5 and dir < 202.5:
    	   return 'S'
    elif dir >= 202.5 and dir < 247.5:
        return 'SW'
    elif dir >= 247.5 and dir < 292.5:
    	   return 'W'
    elif dir >= 292.5 and dir < 337.5:
        return 'NW'
    else:
        return None
