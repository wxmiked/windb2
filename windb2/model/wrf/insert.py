from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import logging
import re
import sys
import tempfile
from datetime import datetime
import pytz

import psycopg2
import numpy
from netCDF4._netCDF4 import Dataset, chartostring
from windb2.insert import Insert

from windb2 import insert, util
from windb2.model.wrf.wrf import logger, create_wrf_srid


class InsertWRF(Insert):
    """Class for inserting WRF specific WinDB2 objects."""

    def __init__(self, windb2, config):
        if sys.version_info < (3,):
            super(Insert, self).__init__(windb2)
        else:
            super().__init__(windb2)

        self.config = config.config

        # Logging
        self.loggerSQL = logging.getLogger('windb2')

    def insert_variable(self, ncfile, var_name, domain_key=None, replace_data=False, sql_where="true",
                        file_type='windb2', mask=None, zero_seconds=False):
        """Inserts a netCDF file with WinDB2 or WRF output into a WinDB2 database.
       *
       * windb2Conn - Connection to a WinDB2 database.
       * ncfile - Either an open file or a string name of a file to open.
       * var_name - Name of WinDB2 supported variable or a WRF 3D variable (currently WIND, THETA, RHO).
       * domain_key - Existing domain key in the database. If left blank, a new domain will be created.
       * replace_data - Deletes data for the same time in the database if True. Useful for freshening data.
       * file_type - Type of netCDF file to insert: {'windb2' (default), or 'wrf'}
       * mask - String name of a mask in the WinDB2 database. Only relevant when creating a new domain (the mask is
       *        applied automatically thereafter).
       *
       * returns timesInsertedList, domain_key - A list of times inserted in ISO time format, and the
         domain_key where the data was inserted.
         :param file_type:
       """

        # Make sure this the file_type of file is support
        if file_type != 'windb2' and file_type != 'wrf':
            raise TypeError('Unsupported file file_type: {}'.format(file_type))

        # Open the WinDB netCDF file
        logger.debug('netCDF file file_type passed to wrf.insertNcFile={}'.format(type(ncfile)))
        if type(ncfile) != Dataset:
            ncfile = Dataset(ncfile, 'r')

        # Get the grid dimensions and coordinates
        if file_type== 'windb2':
            nlong = len(ncfile.dimensions['x'])
            nlat = len(ncfile.dimensions['y'])
            x_coord_array = ncfile.groups['WRF']['XLONG'][:]
            y_coord_array = ncfile.groups['WRF']['XLAT'][:]
            if self.config['vars'][var_name]['dims'] == 3:
                height_array = ncfile.variables['height'][:]
            elif self.config['vars'][var_name]['dims'] == 2:
                height_array = [self.config['vars'][var_name]['insert'][0]]
            else:
                raise Exception('Number of dimensions must either be 2 or 3')
            init_t = datetime.strptime(ncfile.groups['WRF'].SIMULATION_START_DATE, '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.utc)
        elif file_type== 'wrf':
            nlong = len(ncfile.dimensions['west_east'])
            nlat = len(ncfile.dimensions['south_north'])
            x_coord_array = ncfile['XLONG'][:]
            y_coord_array = ncfile['XLAT'][:]
            height_array = [self.config[var_name]['insert'][0]]
            init_t = datetime.strptime(ncfile.SIMULATION_START_DATE, '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.utc)

        # Read in the vars to insert
        wrf_copied_var = False
        if file_type == 'windb2' and var_name.lower() == 'WIND'.lower():
            u = ncfile.variables['eastward_wind'][:]
            v = ncfile.variables['northward_wind'][:]
        elif file_type == 'windb2' and var_name.lower() == 'DPT'.lower():
            ncVariable = ncfile.variables['dew_point_temperature'][:]
        # Otherwise try find the WinDB2 interp or WRF var
        else:
            try:
                ncVariable = ncfile.variables[var_name][:]
            except KeyError as e:
                wrf_copied_var = True
                ncVariable = ncfile.groups['WRF'][var_name][:]

        # Create a new and/or domain if necessary
        if domain_key is None:
            if file_type== 'windb2':
                domain_key = str(self.create_new_domain(ncfile.groups['WRF'].TITLE, "WRF", ncfile.groups['WRF'].DX, 'm', mask))
            elif file_type== 'wrf':
                domain_key = str(self.create_new_domain(ncfile.TITLE, "WRF", ncfile.DX, 'm', mask))
            self.insert_horiz_geom(domain_key, x_coord_array, y_coord_array, create_wrf_srid(self.windb2, ncfile))

            # Mask the domain if necessary
            if mask is not None:
                self.mask_domain(domain_key, mask)

        # Create a new table if necessary and add an initialization time column
        if file_type == 'windb2' and var_name.lower() == 'wind'.lower():
            if not self.windb2.table_exists('wind' + '_' + domain_key):
                self.create_new_table(domain_key, var_name, ('speed', 'direction'), ('real', 'smallint'))
                self._create_initialization_time_column(var_name, domain_key)
        else:
            if not self.windb2.table_exists('{}_{}'.format(var_name.lower(), domain_key)):
                self.create_new_table(domain_key, var_name, ('value',), ('real',))
                self._create_initialization_time_column(var_name.lower(), domain_key)

        # Make sure it's a string so that we don't have concatenation problems later
        domain_key = str(domain_key)

        # Get the geomkeys associated with the WRF coordinates
        horizGeomKey = self.calculateHorizWindGeomKeys(domain_key, nlong, nlat)

        # Create a counter to execute every so often
        counter = 0
        startTime = datetime.now()

        # Get the time array to iterate through
        if file_type == 'windb2':
            time_char_array = chartostring(ncfile.variables['Time'][:])
        elif file_type == 'wrf':
            time_char_array = chartostring(ncfile.variables['Times'][:])

        # Create a statement to use
        tCount = 0
        timeValuesToReturn = []
        for t in time_char_array:

            # Create a datetime from the WRF string
            t = datetime.strptime(t, '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.utc)

            # Zero the seconds if asked to
            if zero_seconds:
                t = t.replace(second=0)

            # Create the time in GeoServer/GeoWebCache format
            timeValuesToReturn.append(t.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

            # Info
            print('Processing time for {}: {}'.format(var_name, timeValuesToReturn[-1]))

            # Iterate through the x,y, and timearr and insert the WRF variable
            for h in height_array:

                # We actually need the index of the height, not the actual height itself
                height = None
                if file_type == 'windb2' and wrf_copied_var is False:
                    try:
                        z = numpy.argwhere(ncfile.variables['height'][:] == h)[0, 0]
                        height = height_array[z]
                    except IndexError:
                        logger.error('Height {} to insert does not exist in WinDB2 file'.format(h))
                        sys.exit(-1)
                elif wrf_copied_var is True:
                    height = height_array[0]
                else:
                    height = 0

                counter = 0

                # Open a temporary file to COPY from
                tempFile = tempfile.NamedTemporaryFile(mode='w')

                for x in range(horizGeomKey.shape[0]):
                    for y in range(horizGeomKey.shape[1]):

                        # Make sure that this is actually a x,y point we want to insert
                        # In order to create a mask of selective insert points, all
                        # a horizGeomKey of zero means we don't want to insert this one
                        if horizGeomKey[x, y] == 0:
                            continue

                        # Write the data string to the temp file
                        if file_type == 'windb2' and var_name.lower() == 'wind'.lower():
                            if not (numpy.isnan(u[tCount, z, y, x]) or numpy.isnan(v[tCount, z, y, x])):

                                # Add this row to be inserted into the database
                                # Note that we negate U and V so they exist in WinDB2 as the vernacular "coming from" wind direction
                                print('{}, {}, {}, {}, {}, {}, {}'.format(domain_key, horizGeomKey[x, y],
                                                                      t.strftime('%Y-%m-%d %H:%M:%S %Z'),
                                                                      util.speed(u[tCount, z, y, x], v[tCount, z, y, x]),
                                                                      int(util.calc_dir_deg(-u[tCount, z, y, x],
                                                                      -v[tCount, z, y, x])),
                                                                      height,
                                                                      init_t.strftime('%Y-%m-%d %H:%M:%S %Z')), file=tempFile)
                                counter += 1

                        elif file_type == 'windb2':
                            # Add this row to be inserted into the database
                            if self.config['vars'][var_name]['dims'] == 2:
                                val = ncVariable[tCount, y, x]
                            elif self.config['vars'][var_name]['dims'] == 3:
                                val = ncVariable[tCount, z, y, x]

                            if not numpy.isnan(val):
                                print('{}, {}, {}, {}, {}, {}'.format(domain_key, horizGeomKey[x, y],
                                                                      t.strftime('%Y-%m-%d %H:%M:%S %Z'),
                                                                      val,
                                                                      height,
                                                                      init_t.strftime('%Y-%m-%d %H:%M:%S %Z')), file=tempFile)
                                counter += 1

                        elif file_type == 'wrf':
                            if not numpy.isnan(ncVariable[tCount, y, x]):

                                # Add this row to be inserted into the database
                                print('{}, {}, {}, {}, {}'.format(domain_key, horizGeomKey[x, y], t.strftime('%Y-%m-%d %H:%M:%S %Z'),
                                      ncVariable[tCount, y, x], init_t.strftime('%Y-%m-%d %H:%M:%S %Z')), file=tempFile)
                                counter += 1

                # Insert the data
                tempFile.flush()
                if file_type == 'windb2' and var_name.lower() == 'wind'.lower():
                    insertColumns = columns=('domainkey', 'geomkey', 't', 'speed', 'direction', 'height', 'init')
                else:
                    insertColumns = columns=('domainkey', 'geomkey', 't', 'value', 'height', 'init')
                try:
                    self.windb2.curs.copy_from(open(tempFile.name, 'r'), var_name + '_' + domain_key, sep=',', columns=insertColumns)
                except psycopg2.IntegrityError as e:

                    # Delete the duplicate data
                    errorTest = 'duplicate key value violates unique constraint "' + var_name.lower() + "_" + domain_key + '_domainkey_geomkey_t_height_init_key"'
                    if re.search(errorTest, str(e.pgerror)):

                        # Delete the data and retry the insert if asked to replace data in the function call
                        if replace_data:

                            # Rollback to the last commit (necessary to reset the database connection)
                            self.windb2.conn.rollback()

                            # Delete that timearr (assumes UTC timearr zone)
                            sql = 'DELETE FROM ' +  var_name + '_' + domain_key + \
                                  ' WHERE t = timestamp with time zone\'' + t.strftime('%Y-%m-%d %H:%M:%S %Z') + '\' ' + \
                                  'AND height=' + str(h)
                            print("Deleting conflicting times: " + sql)
                            self.windb2.curs.execute(sql)
                            self.windb2.conn.commit()

                            # Reinsert that timearr
                            self.windb2.curs.copy_from(open(tempFile.name, 'r'), var_name + '_' + domain_key, sep=',', columns=insertColumns)

                            # No need to commit again, go on to the next height
                            self.windb2.conn.commit()
                            continue

                        # Otherwise, just notify that the insert failed because of duplicate data. We do re-raise this error
                        # because it's assumed that we want to suplement the WinDB with other data-heights if available.
                        else:
                            logging.warning('ERROR ON INSERT: {}'.format(e.pgerror))
                            logging.warning('Use \'replace_data=True\' if you want the data to be reinserted.')
                            self.windb2.conn.rollback()
                            continue

                # Commit the changes
                self.windb2.conn.commit()

                # Calaculate the insert rate
                elapsedTime = (datetime.now() - startTime).seconds
                try:
                    print('Inserted {}, {}-m height x,y wind points at {} I/s'.format(counter, height_array[z], counter / elapsedTime))
                except ZeroDivisionError:
                    print('Inserted {}, {}-m height x,y wind points'.format(counter, height_array[z]))
                except UnboundLocalError:
                    print('Inserted {}, {}-m height x,y wind points'.format(counter, height_array[0]))

                # Close the tempfile so it is deleted
                tempFile.close()

            # Increment the time
            tCount += 1

        return timeValuesToReturn, domain_key

    def _create_initialization_time_column(self, table_name, domain_key):
        """Adds the initialization time column to allow for multiple forecasts to coexist"""
        self.windb2.curs.execute('ALTER TABLE {}_{} ADD COLUMN init TIMESTAMP WITH TIME ZONE'.format(table_name, domain_key))
        self.windb2.curs.execute('ALTER TABLE {}_{} DROP CONSTRAINT {}_{}_domainkey_geomkey_t_height_key'
                                 .format(table_name, domain_key, table_name, domain_key))
        self.windb2.curs.execute('ALTER TABLE {}_{} ADD UNIQUE(domainkey, geomkey, t, height, init)'.format(table_name, domain_key))

