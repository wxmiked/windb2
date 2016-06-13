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
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


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
            """'PROJCS["SPHERICAL WRF", GEOGCS["GCS_Sphere_WRF",
            DATUM["Sphere_WRF",
            SPHEROID["Sphere_WRF",6370000.0,0.0]],
            PRIMEM["Greenwich",0.0],
            AUTHORITY["EPSG","8901"]]',""" + \
            "'+proj=longlat +a=6370000 +b=6370000 +no_defs') RETURNING srid"

    # Info
    print("Creating a new SRID for this domain:", srid_sql)

    # Get the next unique SRID number in the database
    windb2_instance.curs.execute(srid_sql)
    srid = windb2_instance.curs.fetchone()[0]
    print("Newly created SRID: ", srid)
    return srid


