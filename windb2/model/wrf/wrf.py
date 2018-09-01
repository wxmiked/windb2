#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-12-26
# Modified: 2016-03-06
#
#
# Description: Manages WRF netCDF data in a WindDB2.
# 
#
import logging

# Set up logging for InsertAbstract
logger = logging.getLogger('windb2')


def create_wrf_srid(windb2_instance, ncfile):
    """Create a new SRID for this domain based on a spherical earth.

    windb2_instance - Initialized WinDB2 instance.
    ncfile - NetcdfFile that must contain the relevant WRF attributes that correspond to the Lambert Conformal Conic
           Projection parameters.

    Returns the SRID of the newly created SRID.
    """

    # Get the next SRID key value
    sql = 'SELECT max(srid) FROM spatial_ref_sys'
    windb2_instance.curs.execute(sql)
    new_srid = int(windb2_instance.curs.fetchone()[0]) + 1

    # Create the SRID insert string.  Some nice person documented this for WRF here:
    # http://spatialreference.org/ref/sr-org/wrf-sphere/
    srid_sql = "INSERT INTO \"spatial_ref_sys\" (srid, auth_name, auth_srid, srtext, proj4text) VALUES (" + str(new_srid) + \
               ", 'WRF '," + str(new_srid) + "," + \
               """'PROJCS["WRF Lambert",
                    GEOGCS["unnamed ellipse",
                        DATUM["unknown",
                            SPHEROID["unnamed",6370000,0]],
                        PRIMEM["Greenwich",0],
                        UNIT["degree",0.0174532925199433]],
                    PROJECTION["Lambert_Conformal_Conic_2SP"],
                    PARAMETER["standard_parallel_1",{}],
                    PARAMETER["standard_parallel_2",{}],
                    PARAMETER["latitude_of_origin",{}],
                    PARAMETER["central_meridian",{}],
                    PARAMETER["false_easting",0],
                    PARAMETER["false_northing",0],
                    UNIT["Meter",1]]',""".format(ncfile['WRF'].TRUELAT1, ncfile['WRF'].TRUELAT2, ncfile['WRF'].CEN_LAT, ncfile['WRF'].STAND_LON) + \
               "'+proj=lcc +lat_1={} +lat_2={} +lat_0={} +lon_0={} +x_0=0 +y_0=0 +a=6370000 +b=6370000 +units=m +no_defs') RETURNING srid"\
                .format(ncfile['WRF'].TRUELAT1, ncfile['WRF'].TRUELAT2, ncfile['WRF'].CEN_LAT, ncfile['WRF'].STAND_LON)

    # Info
    logger.debug("Creating a new WRF SRID for this domain: {}".format(srid_sql))

    # Get the next unique SRID number in the database
    windb2_instance.curs.execute(srid_sql)
    srid = windb2_instance.curs.fetchone()[0]
    print("Newly created SRID: ", srid)
    return srid
