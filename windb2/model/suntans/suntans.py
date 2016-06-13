#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-12-26
# Modified:
#
#
# Description: Manages SUNTANS tide forecast netCDF data in a WindDB2.
#
#
import numpy
import scipy.io.netcdf as nc
import argparse
from windb2 import insert, util
import os
import tempfile
from datetime import datetime
import math
import psycopg2
import sys
import logging
import re
import logging
import pytz

# Set up logging for this package
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()

"""Inserts a netCDF file with SUNTANS tidal current output into a WinDB2 database.
   *
   * windb2Conn - Connection to a WinDB2 database.
   * ncFile - Either an open file or a string name of a file to open.
   * domainKey - Existing domain key in the database. If left blank, a new domain will be created.
   * replaceData - Deletes data for the same time in the database if True. Useful for freshening data.
   *
   * returns timesInsertedList, domainKey - A list of times inserted in ISO time format, and the
     domainKey where the data was inserted.
"""
def insertNcFile(windb2_conn, ncFile, domainKey=None, tableName="current", replaceData=False, sqlWhere="true"):

    # Connect to the WinDB
    inserter = insert.Insert(windb2_conn)

    # Open the tide netCDF file
    print('netCDF file type passed to suntans.insertNcFile=', type(ncFile))
    if type(ncFile) != nc.netcdf_file:
        ncFile = nc.netcdf_file(ncFile, 'r')

    # Get the grid dimensions and coordinates
    nLong = ncFile.dimensions['west_east']
    nLat = ncFile.dimensions['south_north']
    nTime = ncFile.variables['Times'].shape[0] # 'Time' dim is UNLIMITED
    lonArr = ncFile.variables['utm_easting']
    latArr = ncFile.variables['utm_northing']
    timeArr = ncFile.variables['Times']
    u = ncFile.variables['u_top1m']
    v = ncFile.variables['v_top1m']

    # Create a new domain if necessary
    if domainKey == None:
        domainKey = str(inserter.create_new_domain("SF Bay currents ", "SUNTANS", 200, 'm'))
        inserter.insert_horiz_geom(domainKey, lonArr, latArr, 26910) # EPSG:26910: NAD83 / UTM zone 10N
        inserter.create_new_table(domainKey, tableName, ("speed", "direction"), ("real", "smallint"),
                                  ("speed_positive","direction_degree"), ("speed >= 0","direction >= 0 AND direction < 360"))
    else:
        # Make sure it's a string so that we don't have concatenation problems later
        domainKey = str(domainKey)

    # Get the geomkeys associated with the WRF coordinates
    horizGeomKey = inserter.calculateHorizWindGeomKeys(domainKey, nLong, nLat)

    # Create a counter to execute every so often
    counter = 0
    startTime = datetime.now()

    # Pass the timeArr through the timeArr filter, even if no filter is set to return Postres
    # compliant timestamps. See Python datetime.datetime for datetime format details
    timesToInsert = windb2_conn.filterTimes(timeArr, '%Y-%m-%d_%H:%M:%S', sqlWhere=sqlWhere)

    # Info
    print('Reduced the number of times to insert by ',
          round((1 - float(len(timesToInsert)) / timeArr.shape[0]) * 100, 1), '%')

    # Iterate through the times that we want to insert
    ttiCount = 0
    tncfCount = 0
    timeValuesToReturn = []
    while ttiCount < len(timesToInsert) and tncfCount < nTime:

        # Only insert if this is a time we want to insert
        tncf = datetime.strptime(timeArr[tncfCount].tostring().decode('UTF-8'), '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.utc)
        tti = timesToInsert[ttiCount]
        if tti != tncf:
            tncfCount += 1
            continue

        # Open a temporary file to COPY from
        temp_file = tempfile.NamedTemporaryFile(mode='w+b')

        # Create the time in GeoServer/GeoWebCache format
        timeValuesToReturn.append(tncf.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

        # Info
        print('Processing time: ', timeValuesToReturn[-1])

        # Iterate through the x,y, and timeArr and insert the tidal current data
        for x in range(horizGeomKey.shape[0]):
            for y in range(horizGeomKey.shape[1]):

                # Make sure that this is actually a x,y point we want to insert
                # In order to create a mask of selective insert points, all
                # a horizGeomKey of zero means we don't want to insert this one
                if horizGeomKey[x,y]==0:
                    continue;

                # Write the data string to the temp file
                if not numpy.isnan(u[tncfCount,y,x]):

                    # Calculate speed
                    speed = math.sqrt(math.pow(u[tncfCount,y,x],2) + math.pow(v[tncfCount,y,x],2))

                    # Calculate direction (using the 'flow' convention for tides)
                    dir = int(util.calc_dir_deg(u[tncfCount,y,x], v[tncfCount,y,x]))

                    # Add this row to be inserted into the database
                    str_to_write = '{},{},{},{},{},{}\n'.format(domainKey, horizGeomKey[x,y],
                                                                   tncf.strftime('%Y-%m-%d %H:%M:%S %Z'), speed, dir, 0)
                    temp_file.write(bytes(str_to_write, 'UTF-8'))
                    counter += 1


        # Insert the data at height 0 for tidal current
        temp_file.flush()
        insertColumns = ('domainkey', 'geomkey', 't', 'speed', 'direction', 'height')
        try:
            windb2_conn.curs.copy_from(open(temp_file.name, 'rb'), tableName + '_' + domainKey, sep=',', columns=insertColumns)
        except psycopg2.IntegrityError as e:

            # Delete the duplicate data
            errorTest = 'duplicate key value violates unique constraint "' + tableName + "_" + domainKey + '_domainkey_geomkey_t_height_key"'
            if re.search(errorTest, str(e)):

                # Delete the data and retry the insert if asked to replace data in the function call
                if replaceData:

                    # Rollback to the last commit (necessary to reset the database connection)
                    windb2_conn.conn.rollback()

                    # Delete that timeArr (assumes UTC timeArr zone)
                    sql = 'DELETE FROM ' +  tableName + '_' + domainKey + ' WHERE t = timestamp with time zone\'' +  tti.strftime('%Y-%m-%d %H:%M:%S %Z') + '\''
                    print("Deleting conflicting times: " + sql)
                    windb2_conn.curs.execute(sql)
                    windb2_conn.conn.commit()

                    # Reinsert that timeArr
                    windb2_conn.curs.copy_from(open(temp_file.name, 'r'), tableName + '_' + domainKey, sep=',', columns=insertColumns)

                # Otherwise, just notify that the insert failed because of duplicate data
                else:
                    logging.error("ERROR ON INSERT: ", e.message)
                    logging.error("Use 'replaceData=True' if you want the data to be reinserted.")
                    raise

        # Commit the changes
        windb2_conn.conn.commit()

        # Calaculate the insert rate
        elapsedTime = (datetime.now() - startTime).seconds
        if elapsedTime > 0:
            insertRate = counter / elapsedTime
            print("Inserted ", counter, " x,y wind points at ", insertRate, " I/s")

        # Close the tempfile so it is deleted
        temp_file.close()

        # Increment the time
        ttiCount += 1

    return timeValuesToReturn
