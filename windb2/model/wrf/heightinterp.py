#!/usr/bin/python
#
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2010-10-20
# Modified: 2015-11-13
#
#
# Description: Calculates height of an Eta level if the argument given
# is less than one.  This method was
# adopted from a fortran code that Cristina Archer, Stanford
# University implemented (Archer, 2003).  The method to calculate the
# height of each sigma level is documented at:
# http://fluid.stanford.edu/~lozej/Public/sigma.pdf
#
# This code was also adopted from the "wind-field-interp" suite of MM5/WRF
# utilities.  See the
# WindFieldInterp.calculateHeightAtSingleEtaTerrainPoint Java method
# for details.
#

import math
from windb2.model.wrf import constants
import logging
import numpy
from scipy import linalg
from windb2 import util

# Set up logging for this package
logger = logging.getLogger('windb2')

def calculate_height(etaLevel, terrainHeight = 0,
                    baseSeaLevelPressure = constants.baseSeaLevelPressure,
                    baseSeaLevelTemperature = constants.baseSeaLevelTemperature,
                    baseLapseRate = constants.baseLapseRate,
                    topPressure = constants.topPressure):
    """Calculate the height of an eta level. Returns the eta height in m.

    Keyword arguments:
    etaLevel -- float between 0 and 1 (unitless)
    terrainHeight -- height of terrain in meters
    baseSeaLevelPressure - base state sea-level pressure in Pa (WRF P00 variable)
    baseSeaLevelTemperature -- base state sea-level temperature (K) (WRF T00 variable)
    baseLapseRate -- base state lapse rate d(T)/d(lnp) (TLP variable)
    pTop --  top pressure (Pa) (P_TOP variable)
    """

    # Make sure this is an appropriate eta value
    if etaLevel is None:
        raise ValueError('Eta value is not between zero and one. etaLevel=' + str(etaLevel))
    elif float(etaLevel) > 1 or float(etaLevel) < 0:
        raise ValueError('Eta value is not between zero and one. etaLevel=' + str(etaLevel))

    # Calculate the column pressure over the sea
    columnPressure = baseSeaLevelPressure - topPressure

    # Calculate the "base state pressure" at this height by solving the for p0 (see the definition of
    # the sigma level (same thing as the eta level) in (Archer, 2003)).
    p0 = etaLevel*columnPressure + topPressure

    # Temp term
    term = math.log(p0 / baseSeaLevelPressure);

    # Return the height of the eta level
    returnVal = -constants.R_CONST/constants.G_CONST*(baseSeaLevelTemperature*term + (baseLapseRate/2.0)*math.pow(term,2.0)) - terrainHeight

    # Make sure this is a sane value
    if returnVal < 0:
        raise ValueError('You cannot have a negative height above ground level for a eta level.  Something is wrong.  z=' + str(returnVal))

    return returnVal

def log_law_interp(speed, z, z_interp, z_max=None):
    """
    Performs a log-linear interpolation of log(z) vs wind speed.

    :parameter
    speed - Value or array of wind speed.
    z - Heights of the know wind speeds.
    z_interp - Desired wind speed heights.
    z_max - Maximum height to include in the interpolation.

    :returns
    Numpy array of interpolated wind speeds.
    """

    # Check sane value of z_max otherwise
    if numpy.max(z_interp) > 130 and z_max is None:
        raise ValueError('By default cannot interpolate above 130 if z_max not explicitly set.')
    # Otherwise use the last z height as the maximum if not explicitly specified
    elif z_max is None:
        z_max = 100
    assert(z_max is not None)

    # Check for non-physical heights and speeds
    if numpy.min(speed) < 0 or numpy.min(z) < 0 or numpy.min(z_interp) < 0 or numpy.min(z_max) < 0:
        raise ValueError('Negative value for speed or height above ground level detected.')

    # Do the linear regression
    z_log = numpy.log(z[z <= z_max])
    z_interp_log = numpy.log(z_interp)
    regression_coeffs = linalg.lstsq(numpy.array([z_log,
                                                        numpy.ones(z_log.shape[0])]).T,
                                           speed[z <= z_max])[0]  # solve y = m*x + b
    speed_interp = regression_coeffs[0]*z_interp_log + regression_coeffs[1]

    # Institute the no-slip condition at the ground (wall)
    if numpy.any([speed_interp < 0]):
        logger.info('log_law_interp had ' + str(numpy.size(numpy.where(speed_interp < 0))) +
                      ' negative speed values which were reset to zero')
        speed_interp[speed_interp < 0] = 0

    return speed_interp



def uv_column_interp(u_mass_column, v_mass_column, heights_above_ground, heights_to_interp, z_o=None):
    """Calculate the wind speeds at a given height (in meters) using the two adjacent pressure levels u and v
    wind components. Uses a log-law approximation from the ground to 100 m for points that are lower than the
    lowest eta level in the model. Direction interpolation is not performed for levels where the log-law
    approximation is used.

    :param u_mass_column: WRF U wind speed already interpolated to the mass coordinate system (native is flux coordinate)
    :param v_mass_column: WRF V wind speed already interpolated to the mass coordinate system (native is flux coordinate)
    :param heights_above_ground:
    :param heights_to_interp:

    :returns 2, 1D arrays u, v of the height interpolated wind speed and direction in the column.

    """

    # Make sure array lengths match
    assert(u_mass_column.shape == v_mass_column.shape)
    assert(u_mass_column.shape == heights_above_ground.shape)

    # Make sure we've only been given a column
    assert(u_mass_column.ndim == 1)
    assert(v_mass_column.ndim == 1)
    assert(heights_above_ground.ndim == 1)

    # Convert heights_to_interp to an numpy array so we can mask it
    heights_to_interp = numpy.array(heights_to_interp)

    # Find the heights that need log-law interpolation i.e. below 100 m and lower than the lowest eta-half level
    mask_heights_to_interp_log_law = heights_to_interp < numpy.min(heights_above_ground)

    # Linear interp where we have model data
    if numpy.size(heights_to_interp[~mask_heights_to_interp_log_law]) > 0:
        u_mass_coord_interp_linear = numpy.interp(heights_to_interp[~mask_heights_to_interp_log_law],
                                                  heights_above_ground, u_mass_column)
        v_mass_coord_interp_linear = numpy.interp(heights_to_interp[~mask_heights_to_interp_log_law],
                                                  heights_above_ground, v_mass_column)
    else:
        logger.info('No eta-level heights were in the range of LINEAR interpolation.')
        u_mass_coord_interp_linear = []
        v_mass_coord_interp_linear = []

    # Log-law interp for speed using heights 100 m and below, if WRF ZNT was NOT provided
    speed = util.speed(u_mass_column, v_mass_column)
    if numpy.size(heights_to_interp[mask_heights_to_interp_log_law]) > 0 and z_o is None:

        # Make sure there is more than one height to linearly interpolate with below 100 m
        if heights_above_ground[1] < 100:
            speed_interp_log_law = log_law_interp(speed, heights_above_ground,
                                                  heights_to_interp[mask_heights_to_interp_log_law], 100)

        # Otherwise, issue a warning and include the second height above ground
        # This situation can sometimes occur at the edges of nested domains when the PSFC value
        # is lower than the lowest level of (P + PB). Speculate this is a bug in WRF where the PSFC is being taken
        # from the lower resolution domain rather than being calculated with the new topo height in the higher
        # resolution domain.
        else:
            speed_interp_log_law = log_law_interp(speed, heights_above_ground,
                                                  heights_to_interp[mask_heights_to_interp_log_law], heights_above_ground[1])
            logger.info('Had to use height above 100 m for log-linear log-law interp')
            logger.info('Heights used for log-linear log-law interp: {} m and {} m'
                        .format(heights_above_ground[0], heights_above_ground[1]))

    # Use the log-law with the WRF ZNT (surface roughness) to diagnose U,V
    elif numpy.size(heights_to_interp[mask_heights_to_interp_log_law]) > 0 and z_o is not None:
        speed_interp_log_law = speed[0] * \
                               numpy.log(heights_to_interp[mask_heights_to_interp_log_law] / z_o) / \
                               numpy.log(numpy.min(heights_above_ground) / z_o)
    else:
        logger.info('No eta-level heights were in the range of LOG-LAW interpolation.')
        speed_interp_log_law = []

    # For log-law interpolation, use the same wind direction as the bottom level where we have WRF data for the
    # direction. Assumes these heights are sorted from bottom to top, which is the WRF default.
    u_bottom = u_mass_column[0]
    v_bottom = v_mass_column[0]
    dir_interp_log_law = util.calc_dir_deg(u_bottom, v_bottom)
    u_mass_coord_interp_log_law = util.u_flow(speed_interp_log_law, dir_interp_log_law)
    v_mass_coord_interp_log_law = util.v_flow(speed_interp_log_law, dir_interp_log_law)

    return numpy.hstack((u_mass_coord_interp_log_law, u_mass_coord_interp_linear)), \
           numpy.hstack((v_mass_coord_interp_log_law, v_mass_coord_interp_linear))
