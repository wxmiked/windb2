from __future__ import print_function
import psycopg2
import sys
import numpy
import tempfile
import logging
import re

class Insert(object):
    """General functionality to be inherited by all WinDB for specific models and observations."""
     
    def __init__(self, windb2):
        
        self.windb2 = windb2
        self.srid = "unset"

        # Logging
        self.logger = logging.getLogger('windb2')
    
    def create_new_domain(self, domain_name, data_source, resolution, units, mask=None):
        """Creates a new empty domain with an associated unique domain ID.
        
        domain_name Name of simulation, configuration, or station name (e.g. SFO, East Coast r1, CWEX lidar)
        data_source Describes where the data came from e.g. "NDBC" or "WRF-ARWvX.X.X"
        resolution Resolution in the units of "units"
        units Units of the resolution e.g. degrees, m, km, etc...
        mask Name of a polygon mask that exists in the WinDB2
        
        return The key of the domain to use in future domain 
        """
        
        # Create a new domain
        sql = "INSERT INTO Domain(name, resolution, units, datasource, mask) VALUES ('{}', '{}', '{}', '{}', {}) " \
              "RETURNING key".format(domain_name, resolution, units, data_source, ("'" + mask + "'") if mask is not None else 'NULL')
        self.logger.debug("Running command to create new domain: " + sql);
        self.windb2.curs.execute(sql);
        
        # Get the unique key
        domain_key = self.windb2.curs.fetchone()[0];
        
        # Info
        print("Created domain number: {}".format(domain_key))

        return domain_key

    def mask_domain(self, domain_key, mask):
        """This method also creates a mask from a given spatial object in the database which uses a trigger to
        exclude the insertion of some points.

        :param:
        domain_key A 2D PostGIS object that overlays the domain points that will be kept
        """

        # Have to set autocommit to true so this doesn't run as a transaction or some parts will fail
        self.windb2.conn.autocommit = True

        # Get the SRID of the domain, assume they are all the same (because they are)
        sql = 'SELECT st_srid(geom) FROM horizgeom WHERE domainkey={} LIMIT 1'.format(domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        if self.windb2.curs.rowcount != 0:
            data_srid = self.windb2.curs.fetchone()[0]
        else:
            self.logger.error('No results were were returned for the new domain SRID. Exiting.')
            sys.exit(-1)

        # Get the horiz resolution, which was calculated before
        sql = "SELECT resolution FROM domain WHERE key=" + domain_key
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        res_m = self.windb2.curs.fetchone()[0]

        # Get the SRID of the mask object, assume they are all the same (because they are)
        sql = 'SELECT ST_SRID(geom) FROM {} LIMIT 1'.format(mask)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        mask_srid = self.windb2.curs.fetchone()[0]

        # Create a new index on the horizgeom table, that has the same SRID as the mask
        geomindex_name = 'horizgeom_gist_index_srid_{}_domain_{}'.format(data_srid, domain_key)
        sql = 'CREATE INDEX {} ON horizgeom ' \
              'USING GIST(ST_Transform(geom,{})) WHERE domainkey={}'.format(geomindex_name, mask_srid, domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Commit all previous commands so the following can run
        self.windb2.conn.commit()

        # Analyze the table so that the geometry index is actually used
        sql = 'VACUUM ANALYZE horizgeom(geom)'
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

		# Create a temporary table of the buffered mask object.  While this isn't wholly
		# necessary, it does allow you to see that progress is being made to making the mask.
		# Also, sometimes slight errors in projections cause points to be missed by using only
		# a buffer size of resMeters/2.0. Since the cost is only including a few more points in the
        # database and the risk is not building the database with the required info, the
		# buffer size has been increased to resMeters.
        self.logger.info('Creating the mask table for domain {} with the mask geometry {}'.format(domain_key, mask))
        sql = 'CREATE TABLE buffered_mask_{}(key SERIAL)'.format(domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        sql = "SELECT AddGeometryColumn('buffered_mask_{}', 'geom', {}, 'POLYGON', 2, false)".format(domain_key, 3857)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        # Do the following to allow both ST_Polygon and ST_MultiPolygon types to be inserted
        sql = 'ALTER TABLE buffered_mask_{} DROP CONSTRAINT enforce_geotype_geom'.format(domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)
        sql = 'INSERT INTO buffered_mask_{} (geom) ' \
              'SELECT ST_Buffer(ST_Transform(geom, {}), {}) AS geom FROM {}'.format(domain_key, 3857, res_m, mask)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Create an index for the buffered object
        sql = 'CREATE INDEX horizbuffer_gist_index_srid_{}_domain_{} ' \
              'ON buffered_mask_{} USING GIST(geom)'.format(data_srid, domain_key, domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Get rid of redundant points in the mask
        sql = 'DELETE FROM buffered_mask_{} WHERE key IN ' \
              '(SELECT b.key ' \
              ' FROM buffered_mask_{} a, buffered_mask_{} b ' \
              ' WHERE (ST_Contains(a.geom, b.geom) OR ' \
              '       ST_Area(b.geom)<pow({},2)) AND a.key<>b.key)' \
              ''.format(domain_key, domain_key, domain_key, float(res_m)*1.5)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Create a new table that is the spatial join of the maskTableName and the newly created geometry
        sql = 'CREATE TABLE geom_mask_{} AS ' \
              'SELECT DISTINCT h.key AS geomkey ' \
              'FROM horizgeom h, buffered_mask_{} b ' \
              'WHERE h.domainkey={} ' \
              'AND ST_Intersects(h.geom, ST_Transform(b.geom, {}))'.format(domain_key, domain_key, domain_key, data_srid)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Get rid of the mask geometry that we no longer need
        sql = 'DROP INDEX {}'.format(geomindex_name)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Delete all of the geomkeys that we no longer need
        sql = 'DELETE FROM horizgeom ' \
              '       WHERE domainkey={} AND ' \
              '             key NOT IN (SELECT geomkey FROM geom_mask_{})'.format(domain_key, domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Delete the buffered mask which we no longer need
        sql = 'DROP TABLE buffered_mask_{}'.format(domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

		# Create an index on the geomkey in the geom_mask for the domain
        sql = 'CREATE INDEX geom_mask_geomkey_index_{} ' \
              ' ON geom_mask_{}(geomkey)'.format(domain_key, domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Add a function that checks to see if a particular geomkey is in the particular mask
        sql = "CREATE OR REPLACE FUNCTION geomkey_in_{}_domain_{}() RETURNS trigger AS ' " \
              "DECLARE gid int; " \
              "BEGIN  " \
              "SELECT INTO gid geomkey FROM geom_mask_{} WHERE geomkey=new.geomkey; " \
              "IF gid IS NOT NULL THEN RETURN NEW; END IF; RETURN NULL; END ' LANGUAGE plpgsql;" \
              "".format(mask, domain_key, domain_key)
        self.logger.debug(sql)
        self.windb2.curs.execute(sql)

        # Turn autocommit back off
        self.windb2.conn.autocommit = False

    def insert_horiz_geom(self, domainKey, xCoordArray, yCoordArr, srid):
        """Inserts horizontal geometries into HorizGeom table. Assumes that the grid is not changing over time.
        
        domainKey The key of the domain you want to get the HorizWindGeom keys for
        xCoordArray 2D Numpy array of projected longitude values at a given position
        yCoordArr 2D Numpy array projected latitude values at a given position
        srid Corresponds to a Spatial Reference System Identifier (SRID)
     
        returns The key of the domain to use in future domain
        """
        
        # Set the SRID of the data
        self.srid = srid;

        # Create new grid points, using a temp file for the SQL copy command
        tempFile = tempfile.NamedTemporaryFile(mode='w');
        for y in range(xCoordArray.shape[1]):
            
            # Info that continually updates
            status_msg = "\rInserting new points: {:000.1%} done"
            sys.stdout.write(status_msg.format(float(y)/xCoordArray.shape[1]))
            sys.stdout.flush()

            for x in range(xCoordArray.shape[2]):
                
                # Create the grid point
                # You have to do it with this following syntax (ST_GeomFromText doesn't work with the COPY_FROM function)
                # See http://postgis.17.x6.nabble.com/Adding-postgis-column-in-COPY-command-td3520584.html
                geom = 'SRID=4326;POINT({} {})'.format(xCoordArray[0, y, x], yCoordArr[0, y, x])
                print('{}, {}, {}, {}'.format(geom, domainKey, x, y), file=tempFile)

        # Print the last update message
        sys.stdout.write((status_msg + '\n').format(1.))

        # Create a temporary table to import the native coordinate into
        self.windb2.curs.execute('CREATE TEMP TABLE horizgeom_import () INHERITS (horizgeom) ON COMMIT DROP')

        # Insert all of the grid points into the temp table
        tempFile.flush()
        try:
            self.windb2.curs.copy_from(open(tempFile.name, 'r'), "horizgeom_import", sep=',', columns=('geom', 'domainKey', 'x', 'y'))
        except psycopg2.IntegrityError as e:
            print >> sys.stderr, "ERROR ON INSERT: ", e.message
            raise e

        # Insert all of the points in the native WRF SRID
        try:
            count = self.windb2.curs.execute('INSERT INTO horizgeom SELECT key, domainkey, x, y, ST_Transform(geom, {}) FROM horizgeom_import WHERE domainkey={}'.format(self.srid, domainKey))
            self.logger.debug('Inserted {} new points'.format(self.windb2.curs.rowcount))
        except psycopg2.IntegrityError as e:
            print >> sys.stderr, "ERROR ON INSERT: ", e.message
            raise e
        
        # Commit the changes if successful
        self.windb2.conn.commit()
        
        return

    def create_new_table(self, domainKey, tableName, varList, varType, constraint=None, check=None):
        """Creates a new table for an already existing domain to store a geo variable.
        
        domainKey Domain key that the table is associated with
        tableName Name of the table usually associate with some geo field e.g. wind, theta
        varList Column names
        varType PostgreSQL data types
        constraint PostgreSQL constraint name e.g. "speed_positive"
        check PostgreSQL constraint check e.g. "speed >= 0"
        """
        
        # Make sure all of the extra columns to add match up in number
        #TODO these should be exceptions
        assert(len(varList) == len(varType))
        if constraint is not None:
            assert(len(constraint) <= len(varList))
        if check is not None:
            assert(len(check) == len(constraint))
        
        # Create a check on the table (for some reason we have to do almost the same thing twice
        self.windb2.curs.execute("CREATE TABLE " + tableName + "_" + str(domainKey) + " (CHECK (domainkey=" + str(domainKey) + ")) INHERITS (GeoVariable)")

        # Add a unique constraint to the table, so we don't get duplicates (this in theory
        # should be copied over from the inherited windspeed table, but it isn't in the
        # current postgres implementation
        sql = "ALTER TABLE " + tableName + "_" + str(domainKey) + " ADD UNIQUE(domainkey,geomkey,t,height)";
        self.windb2.curs.execute(sql)
        
        # Create indexes on these tables
        self.windb2.curs.execute("CREATE INDEX {}_geomkey_{} ON {}_{}(geomkey)".format(tableName, domainKey,
                                                                                                tableName, domainKey))
        self.windb2.curs.execute("CREATE INDEX {}_timestamp_{} ON {}_{}(t)".format(tableName, domainKey,
                                                                                            tableName, domainKey))
        
        # Add the extra columns and constraints required for this variable
        for i in range(len(varList)):
            
            # Add the column
            sql = "ALTER TABLE " + tableName + "_" + str(domainKey) + " ADD COLUMN " + varList[i] + " " + varType[i]
            if constraint is not None and check is not None:
                sql += " CONSTRAINT " + constraint[i] + " CHECK (" + check[i] + ")"
            self.logger.info("Running: " + sql)
            self.windb2.curs.execute(sql)

	    # Add a trigger that just ignores any wind speed insert where the geomkey isn't in the mask
        # try:
        self.windb2.curs.execute('SELECT mask FROM domain WHERE key={}'.format(domainKey))
        mask = self.windb2.curs.fetchone()[0]
        if mask is not None:
            sql = 'CREATE TRIGGER {}_geomkey_mask_domain_{} ' \
                  'BEFORE INSERT ' \
                  'ON {}_{} ' \
                  'FOR EACH ROW ' \
                  'EXECUTE PROCEDURE geomkey_in_{}_domain_{}()' \
                  ''.format(tableName, domainKey, tableName, domainKey, mask, domainKey)
            self.logger.debug(sql)
            self.windb2.curs.execute(sql)

        # Commit the changes
        self.windb2.conn.commit()

        return

    
    def calculateHorizWindGeomKeys(self, domainKey, xMax, yMax):
        """Given a domain it figures out which HorizWindGeom key corresponds to each x,y pair in a domain.
        This saves a lot of time by removing a sub-query that would normally be required to do this
        many times throughout the insert.
            
        domainKey The key of the domain you want to get the HorizWindGeom keys for.
        xMax max x dimension
        yMax max y dimension.
        
        Returns a 2D array [x][y] of the corresponding HorizWindGeom key for each (x,y) pair.
        Throws an SQLException"""
         
        # Create  a new 2D array to store the keys
        keyArray = numpy.zeros((xMax,yMax),numpy.int)
         
        # Info
        self.logger.info("Calculating the x,y pair geomkeys ({},{})...".format(xMax, yMax))

        # Get the matching key pairs
        sql = "SELECT sx.x, sy.y, key " + \
              "FROM (SELECT generate_series(0, " + str(xMax) + ") AS x) AS sx, " + \
              "     (SELECT generate_series(0, " + str(yMax) + ") AS y) AS sy, " + \
              "     horizgeom AS h WHERE domainkey=" + str(domainKey) + " AND h.x=sx.x AND h.y=sy.y ORDER BY x,y";
        self.windb2.curs.execute(sql)
         
        for row in self.windb2.curs.fetchall():
            
            # Debug
            #print("keyArray[{}, {}] = {}".format(row[0], row[1], row[2]))
            
            keyArray[row[0], row[1]] = row[2]
           
        # Info
        print("Finished calculating the x,y pair geomkeys.")

        return keyArray

    def insert_wind_data(self, data_name, data_creator, winddata, longitude=0, latitude=0, replace_data=False):
        """Inserts a WindData (2D) list into the given database.

        Args:
            inserter: WinDB2 InserterAbstract
            data_name: string like 'arps-ideal'
            data_creator: string like 'NCAR'
            winddata: list of WindData or WindData3D objects
            longitude: longitude of point, 0 by default
            latitude: latitude of a point, 0 by default
            replace_data: Delete and reinsert data that overlaps"""

        # See if this domain data name already exists
        domain_key = self.windb2.findDomainForDataName(data_name)

        # Try and get the domain key result. If no key was returned, we need to make new domain and windspeed tables
        newDomain = False
        if not domain_key:
            newDomain = True

        # Create a new table if we need to
        if domain_key is None:

            # Insert the name into the domain table which returns the new key
            sql = "INSERT INTO domain(name, resolution, units, datasource) VALUES ('" + data_name + "', 0, 'm', '" + data_creator + "') RETURNING key"
            try:
                self.windb2.curs.execute(sql)
            except psycopg2.ProgrammingError as detail:
                self.logger.error("Inserting a new domain domain failed. Exiting...")
                sys.exit(-1)

            # Get the domain key
            domain_key = self.windb2.curs.fetchone()[0]

            # Create a new windspeed table
            self.create_new_table(domain_key, 'wind', ('speed', 'direction'), ('real', 'smallint'),
                                      constraint=('speed_postive', 'direction_degrees'),
                                      check=('speed>=0', 'direction>=0 AND direction<=360'))

            # Add a 2D point for the made up location of the
            sql = "INSERT INTO horizgeom(domainkey, x, y, geom) \
                   VALUES (" + str(domain_key) + ",0,0, st_geomfromtext('POINT(" + str(longitude) + ' ' + str(latitude) + ")',4326)) RETURNING key"
            self.windb2.curs.execute(sql)
            geomkey = self.windb2.curs.fetchone()[0]

            # Commit all of these additions
            self.windb2.conn.commit()

        # Otherwise, check to see if there already exists a geomkey with the same coordinates
        elif longitude != 0 and latitude != 0:

            # Make sure there's only one geomkey for this domain
            sql = 'SELECT count(geom) FROM horizgeom WHERE domainkey={}'.format(domain_key)
            self.logger.debug(sql)
            self.windb2.curs.execute(sql)
            geomkey_count = self.windb2.curs.fetchone()[0]
            if geomkey_count != 1:
                raise ValueError('There should only be one geomkey for this domain, found {} geomkeys'.format(geomkey_count))

            # Get the geomkey for the location
            sql = 'SELECT key FROM horizgeom WHERE domainkey={} AND x=0 AND y=0'.format(domain_key)
            self.logger.debug(sql)
            self.windb2.curs.execute(sql)
            geomkey = self.windb2.curs.fetchone()[0]

            # Issue warning if this geomkey is far away based on the coordinates provide. Some of the NOAA NDBC have
            # significant "drift" over the years (on the order of several km).
            sql = "SELECT st_distance_sphere(geom, " \
                  "st_geomfromtext('POINT({} {})',4326)) FROM horizgeom " \
                  "WHERE key={}".format(longitude, latitude, geomkey)
            self.logger.debug(sql)
            self.windb2.curs.execute(sql)
            distance = self.windb2.curs.fetchone()[0]
            if distance > 100:
                self.logger.warning('Station {} was reported to be {} m away from its orignal location'.format(data_name,
                                                                                                           distance))

            # Make sure we actually found a geomkey
            if geomkey is None:
                self.logger.error('This query did not return a geomkey: {}'.format(sql))
                raise ValueError('No geomkey found to match the insert location.')

        # Otherwise, this is an ideal domain and there is not geom
        else:
            geomkey = 0


        # Open a temporary file to COPY from
        tempFile = tempfile.NamedTemporaryFile(mode='w')


        # Insert all of the data
        table_name = 'wind_{}'.format(domain_key)
        for data in winddata:

            # Add this row to be inserted into the database
            print('{}, {}, {}, {}, {}, {}'.format(domain_key, geomkey, data.time, data.speed, int(data.direction),
                                                           data.height), file=tempFile)

        # Insert the data
        tempFile.flush()
        insertColumns = ('domainkey', 'geomkey', 't', 'speed', 'direction', 'height')
        try:
            self.windb2.curs.copy_from(open(tempFile.name, 'r'), table_name, sep=',', columns=insertColumns)
        except psycopg2.IntegrityError as e:

            # Delete the duplicate data
            # TODO this doesn't exactly work as well as it does with WRF database because many different times need
            # TODO to be deleted for this to work
            errorTest = 'duplicate key value violates unique constraint "' + table_name + '_domainkey_geomkey_t_height_key"'
            if re.search(errorTest, str(e.pgerror)):

                # Delete the data and retry the insert if asked to replace data in the function call
                if replace_data:

                    # Rollback to the last commit (necessary to reset the database connection)
                    self.windb2.conn.rollback()

                    # Delete that timearr (assumes UTC timearr zone)
                    sql = 'DELETE FROM {} WHERE t = timestamp with time zone\'{}\''.format(table_name, data.time.strftime('%Y-%m-%d %H:%M:%S %Z'))
                    print("Deleting conflicting times: " + sql)
                    self.windb2.curs.execute(sql)
                    self.windb2.conn.commit()

                    # Reinsert that timearr
                    self.windb2.curs.copy_from(open(tempFile.name, 'r'), table_name, sep=',', columns=insertColumns)

                # Otherwise, just notify that the insert failed because of duplicate data. We do re-raise this error
                # because it's assumed that we want to suplement the WinDB with other data-heights if available.
                else:
                    self.logger.warning('ERROR ON INSERT: {}'.format(e.pgerror))
                    self.logger.warning('Use \'replace_data=True\' if you want the data to be reinserted.')
                    self.windb2.conn.rollback()

        # Commit the changes
        self.windb2.conn.commit()