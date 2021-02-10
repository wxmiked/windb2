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
import xarray
from windb2.insert import Insert
from windb2 import util
import windb2.model.gfs.util

class InsertGFS(Insert):
    """Class for inserting GFS into WinDB2."""

    def __init__(self, windb2, config):
        if sys.version_info < (3,):
            super(Insert, self).__init__(windb2)
        else:
            super().__init__(windb2)

        self.config = config.config

        # Logging
        self.logger = logging.getLogger('windb2')

    def insert_variable(self, gfsfile, var_name, table_var_name, domain_key=None, replace_data=False, sql_where="true",
                        mask=None, zero_seconds=False):
        """Inserts a GFS GRIB into a WinDB2 database.
       *
       * windb2Conn - Connection to a WinDB2 database.
       * ncfile - Either an open file or a string name of a file to open.
       * var_name - Variable name in the GFS file
       * table_var_name - Name of the table, which can be different than the GFS variable name (e.g. a CF Convention compliant name)
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

        # Open the GFS GRIB file if it already isn't open
        if type(gfsfile) != xarray.Dataset:
            gfsfile = xarray.open_dataset(gfsfile, engine='cfgrib',
                                          backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround',
                                                                             'stepType': 'instant'}})
        nlong = gfsfile.longitude.shape[0]
        nlat = gfsfile.latitude.shape[0]
        x_coord_array = \
            numpy.tile(gfsfile.longitude.data[numpy.newaxis], (nlat, 1))[numpy.newaxis]  # insert_horiz_geom wants a 2D coordinate below
        x_coord_array = windb2.model.gfs.util.center_coords_on_prime_meridian(x_coord_array)  # make centered on zero instead of going 0 to 360 degrees
        y_coord_array = \
            numpy.tile(gfsfile.latitude.data[numpy.newaxis], (nlong, 1)).T[numpy.newaxis]  # insert_horiz_geom wants a 2D coordinate below
        init_t = \
            datetime.utcfromtimestamp(gfsfile.time.time.data.astype(datetime) / 1E9)  # convert datetime64 to datetime: https://stackoverflow.com/a/50625532
        valid_t = datetime.utcfromtimestamp(gfsfile.time.valid_time.data.astype(datetime) / 1E9)
        gfsvar = gfsfile[var_name].data

        # Create a new and/or domain if necessary
        resolution = abs(gfsfile.latitude.data[1] - gfsfile.latitude.data[0])
        if domain_key is None:
            domain_key = self.create_new_domain('Global Forecast System',
                                                gfsfile.attrs['GRIB_centreDescription'],
                                                resolution, 'deg', mask)
            self.insert_horiz_geom(domain_key, x_coord_array, y_coord_array, 4326, mask=mask)  # SRID=4326 is WGS84 for GFS

            # Mask the domain if necessary
            # TODO unclear why this is not done inside of create_new_domain
            if mask is not None:
                self.mask_domain(domain_key, mask)

        # Create a new table if necessary and add an initialization time column
        if not self.windb2.table_exists('{}_{}'.format(table_var_name, domain_key)):
            self.create_new_table(domain_key, table_var_name, ('value',), ('real',))
            self._create_initialization_time_column(table_var_name, domain_key)

        # Get the geomkeys associated with the coordinates
        horizgeomkey = self.calculateHorizWindGeomKeys(domain_key, nlong, nlat)

        # Create a counter to execute every so often
        startTime = datetime.now()
        counter = 0

        # Open a temporary file to COPY from
        temp_file = tempfile.NamedTemporaryFile(mode='w')

        # Iterate through the x,y, and timearr and insert the WRF variable
        for x in range(horizgeomkey.shape[0]):
            for y in range(horizgeomkey.shape[1]):

                # Make sure that this is actually a x,y point we want to insert
                # In order to create a mask of selective insert points, all
                # a horizGeomKey of zero means we don't want to insert this one
                if horizgeomkey[x, y] == 0:
                    continue

                # Add this row to be inserted into the database
                if self.config['vars'][var_name]['dims'] == 2:
                    val = gfsvar[y, x]

                if not numpy.isnan(val):
                    insert_val = '{}, {}, {}, {}, {}, {}'.format(domain_key, horizgeomkey[x, y],
                                                                 valid_t.strftime('%Y-%m-%d %H:%M:%S %Z'),
                                                                 val,
                                                                 0,  # TODO this should come from the config
                                                                 init_t.strftime('%Y-%m-%d %H:%M:%S %Z'))
                    print(insert_val, file=temp_file)
                    counter += 1

        # Insert the data
        temp_file.flush()
        insert_columns = ('domainkey', 'geomkey', 't', 'value', 'height', 'init')
        self.windb2.curs.copy_from(open(temp_file.name, 'r'), '{}_{}'.format(table_var_name, domain_key), sep=',',
                                   columns=insert_columns)
        # Commit the changes
        self.windb2.conn.commit()

        # Calaculate the insert rate
        elapsedTime = (datetime.now() - startTime).seconds
        try:
            print("Inserted {} x,y points into {}_{} at {} I/s".format(counter, table_var_name, domain_key, counter/elapsedTime))
        except ZeroDivisionError, UnboundLocalError:
            print("Inserted {counter} x,y points into {tableName}_{domainKey}".format(counter, table_var_name, domain_key))

        # Close the tempfile so it is deleted
        temp_file.close()

        return [valid_t.strftime('%Y-%m-%dT%H:%M:%S.000Z')], domain_key

    def _create_initialization_time_column(self, table_name, domain_key):
        """Adds the initialization time column to allow for multiple forecasts to coexist"""
        self.windb2.curs.execute('ALTER TABLE {}_{} ADD COLUMN init TIMESTAMP WITH TIME ZONE'
                                 .format(table_name, domain_key))
        self.windb2.curs.execute('ALTER TABLE {}_{} DROP CONSTRAINT {}_{}_domainkey_geomkey_t_height_key'
                                 .format(table_name, domain_key, table_name, domain_key))
        self.windb2.curs.execute('ALTER TABLE {}_{} ADD UNIQUE(domainkey, geomkey, t, height, init)'
                                 .format(table_name, domain_key))
