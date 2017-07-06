#!/usr/bin/python
#
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2014-05-26
# Modified: 2016-12-20
#
#
# Description: Interpolation utilities for the WinDB WRF grid to a regularly gridded long, lat grid
#


def getCoordsOfReguarGridInWrfCoords(curs, domainNum, outputLong, outputLat, nInputLong, nInputLat):
    """Calculates the WRF native coordinates of a regularly defined long, lat grid. The return values are meant
    to plug directly into the mpl_toolkits.basemap.interp function.
    
    @param curs: Psycopg2 cursor of the WinDB database
    @param domainNum: WinDB domain number
    @param outputLong: 1D Numpy array of longitudes in the regular grid
    @param outputLat: 1D Numpy array of latitudes in the regular grid
    
    @return: wrfX -> 1D WRF native longitudinal coordinate
             wrfY  -> 1D WRF native latitudinal coordinate
             regGridInWrfX -> 2D WRF native longitudinal coordinate of the regular grid longitudinal coordinates
             regGridInWrfY -> 2D WRF native latitudinal coordinate of the regular grid latitudinal coordinates
    """
    import numpy as np
    import mpl_toolkits.basemap.pyproj as pyproj
    
    # Get the coordinates of the WRF grid in the native WRF projection
    sql = """SELECT generate_series(x.min::int, x.max::int,(x.max::int - x.min::int)/({} - 1)) as x_coords
             FROM (SELECT min(st_x(geom)), max(st_x(geom)), resolution 
                   FROM horizgeom h, domain d
                   WHERE h.domainkey=d.key AND domainkey={}
                   GROUP BY d.resolution) x
             ORDER BY x_coords""".format(nInputLong, domainNum)
    curs.execute(sql)
    results = curs.fetchall()
    wrfX = np.array(results)[:,0]
    sql = """SELECT generate_series(y.min::int, y.max::int,(y.max::int - y.min::int)/({} - 1)) as y_coords
             FROM (SELECT min(st_y(geom)), max(st_y(geom)), resolution 
                   FROM horizgeom h, domain d
                   WHERE h.domainkey=d.key AND domainkey={}
                   GROUP BY d.resolution) y
             ORDER BY y_coords""".format(nInputLat, domainNum)
    curs.execute(sql)
    results = curs.fetchall()
    wrfY = np.array(results)[:,0]
    
    # Get the SRID of the WRF domain
    sql= """SELECT proj4text FROM spatial_ref_sys WHERE srid=(SELECT st_srid(geom) FROM horizgeom WHERE domainkey=""" + str(domainNum) + """ LIMIT 1)"""
    curs.execute(sql)
    wrfProj4Str = curs.fetchone()[0]
    
    # Change the WRF coordinates of the regular long, lat grid
    # Great tutorial on Basemap Proj4 transformations here: http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
    wrfProj4 = pyproj.Proj(wrfProj4Str)
    longGrid, latGrid = np.meshgrid(outputLong, outputLat)
    regGridInWrfX, regGridInWrfY = wrfProj4(longGrid, latGrid)
    
    return wrfX, wrfY, regGridInWrfX, regGridInWrfY

def transformWrfProj(curs, domainNum, wrfLong, wrfLat, proj='epsg_4326'):
    """Uses pyproj to transform from WRF Lambert Conformal Conic to a new projection.

    Args:
        curs: WinDB2 cursor
        domainNum: WinDB2 domain number
        wrfLong: 1D or 2D Numpy array of WRF longitudes
        wrfLat: 1D or 2D Numpy array of WRF longitudes
        proj: Defaults to WGS84, use a pyproj legal projection string to change e.g. proj='epsg:4326'

    Returns:
        Reprojected long and lat arrays in of the same dimension of the input data

    """
    import numpy as np
    import mpl_toolkits.basemap.pyproj as pyproj

    # Temporarily convert to 1D if we've been passed a grid
    if len(wrfLong.shape) == 2 and len(wrfLat.shape) == 2:
        twoDToOneD= True
        wrfLongShape = wrfLong.shape
        wrfLong = wrfLong.ravel()
        wrfLatShape = wrfLat.shape
        wrfLat = wrfLat.ravel()
    else:
        twoDToOneD = False

    # Get the SRID of the WRF domain
    sql = """SELECT proj4text FROM spatial_ref_sys WHERE srid=(SELECT st_srid(geom) FROM horizgeom WHERE domainkey=""" + str(
        domainNum) + """ LIMIT 1)"""
    curs.execute(sql)
    wrfProj4Str = curs.fetchone()[0]

    # Create the WRF projection
    wrfProj4 = pyproj.Proj(wrfProj4Str)

    # Transform from WRF to WGS84
    wrfWgs84Lon, wrfWgs84Lat = pyproj.transform(wrfProj4, pyproj.Proj(init='epsg:4326'), wrfLong, wrfLat)

    # Convert back to 2D if necessary
    if twoDToOneD:
        wrfWgs84Lon = np.reshape(wrfWgs84Lon, wrfLongShape)
        wrfWgs84Lat = np.reshape(wrfWgs84Lat, wrfLatShape)

    return wrfWgs84Lon, wrfWgs84Lat
