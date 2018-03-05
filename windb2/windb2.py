import psycopg2
import sys
from datetime import datetime
import pytz
import numpy
import logging

class WinDB2:
    """Used to connect to a PostGIS WinDB. Contains all utility functions needed to interact with the WinDB."""
    
    def __init__(self, dbHost, dbName, dbUser="postgres", port=5432):
        self._dbHost = dbHost
        self._dbName = dbName
        self._dbUser = dbUser
        self._port = port

        # Logging
        self.logger = logging.getLogger('windb2')

    def connect(self):
        """ Connects to a WinDB database.
        
        dbHost, hostname of the PostGIS database
        dbName, name of the PostGIS database
        """
        
        ## Open the database
        DSN = 'dbname={} host={} user={} port={}'.format(self._dbName, self._dbHost, self._dbUser, self._port)
        print("Opening connection using dns:", DSN)
        self.conn = psycopg2.connect(DSN)
        print("Encoding for this connection is", self.conn.encoding)
        
        # Connect to the database
        self.curs = self.conn.cursor()

        # Always use UTC for the time zone
        self.curs.execute('SET TIME ZONE \'UTC\'')
        self.curs.execute('SHOW TIMEZONE')
        print('Time zone being used for this session: {}'.format(self.curs.fetchone()[0]))
        
        return
    
    def close(self):
        """Closes the connection."""
        
        self.conn.close()
    
    
    def createDomainkeyGeomkeyTimeHeightIndex(self, curs, conn, domainKey):
        """Creates an index in a windspeed table of 'UNIQUE, btree (domainkey, geomkey, t, height)'. Checks for the existence of the
        index and returns if it already exists.
        """
        
        # See if the index exists be querying the 'pg_class' table
        sql = "SELECT relname FROM pg_class WHERE relname='wind_3_domainkey_geomkey_t_height_key'"
        curs.execute(sql)
        if not curs.fetchone():
            # Add back in the index
            print('Creating the index ' + str(domainKey) + "_domainkey_geomkey_t_height_key ON wind_" + str(
                domainKey))
            sql = "CREATE UNIQUE INDEX wind_" + str(domainKey) + "_domainkey_geomkey_t_height_key ON wind_" + str(domainKey) + "(domainkey, geomkey, t, height)"
            curs.execute(sql)
        
        else:
            print('Index ' + str(domainKey) + "_domainkey_geomkey_t_height_key ON wind_" + str(
                domainKey) + ' already exists.')

        # Commit these changes
        conn.commit()
    
    
    def findDomainForDataName(self, dataName):
        """Checks for the existence of the 'data name' in the database. Returns None if that name is not found and or the domain key 
        otherwise."""
        
        # Make sure a 'dataName' table does not already exist, get the key if it does
        sql = "SELECT key FROM domain WHERE name='" + dataName + "'"
        try:
            self.curs.execute(sql)
        except psycopg2.InternalError as detail:
            print("Query to determine if domain exists failed: ", detail)

        # Return the domain, otherwise None if no domain existed
        domain_key = self.curs.fetchone()
        if domain_key is None:
            return None
        else:
            return domain_key[0]
    
    
    def dropWindspeedIndex(self, curs, domainKey):
        
        # See if the index exists be querying the 'pg_class' table
        sql = "SELECT relname FROM pg_class WHERE relname='wind_3_domainkey_geomkey_t_height_key'"
        curs.execute(sql)
        if curs.fetchone():
            # Drop the indicies for speed, only if we did not just create this domain
            try:
                sql = "DROP INDEX wind_" + str(domainKey) + "_domainkey_geomkey_t_height_key"
                curs.execute(sql)
            except psycopg2.ProgrammingError as detail:
                print(detail, 'Failed to drop the index ' + str(domainKey) + "_domainkey_geomkey_t_height_key")

    def table_exists(self, tablename):
        """Checks to see if a tablename already exists in the WinDB2"""

        self.curs.execute('SELECT * FROM information_schema.tables WHERE table_name=%s', (tablename,))
        try:
            return self.curs.fetchone()[0]
        except TypeError:
            return False
            

    def filterTimes(self, timesArray, timeFormat, sqlWhere='true'):
        """Uses the WinDB2 to filter out unwanted tide times. If sqlWhere is left blank, this function
        simply ends up converting the times into a datatime objects for easier manipulation.

        windb - WinDB2 object that has already been connected with windb2.connect()
        timesArray - Array of strings to timestamps to convert, which MUST BE IN UTC
        timeFormat - String of the timestamp format in Python datetime.datetime syntax e.g. '%Y-%m-%d %H:%M:%S'
        sqlWhere - SQL WHERE statement to be used as the filter (presumably referring to times with time zones),
                   returns everything if true

        Returns as array of datetimes
        """

        # Debug
        #print 'timesArray=', ''.join(timesArray[0])

        # Create a temp table to insert the data into
        sql = "CREATE TEMP TABLE time_filter ( t TIMESTAMP WITH TIME ZONE )"
        self.curs.execute(sql)

        # Insert the data
        for t in timesArray:

            # Debug
            #print 'time to convert=', ''.join(t)

            # Try and parse the datetime
            try:
                datetimeObj = datetime.strptime(b''.join(t).decode('utf-8'), timeFormat).replace(tzinfo=pytz.utc)

            except:
                print >> sys.stderr, "Unable to convert string: " + ''.join(t) + " to a date time using format " + timeFormat
                raise

            timePgsql = datetimeObj.strftime('%Y-%m-%d %H:%M:%S %Z')
            sql = "INSERT INTO time_filter (t) VALUES (timestamp with time zone'" + timePgsql + "')"
            self.curs.execute(sql)

        # Get only the times we want
        sql = "SELECT t FROM time_filter WHERE " + sqlWhere
        print(sql)
        self.curs.execute(sql)

        timeReturnArray = numpy.array(self.curs.fetchall())

        if timeReturnArray.shape[0] != 0:
            return list(timeReturnArray[:,0])
        else:
            return []

    def geomExists(self, domain, longitude, latitude):
        """Checks to see if the point exists. Returns the geomkey if true and false if not."""

        sql = "SELECT key FROM horizgeom WHERE ST_X(geom)=longitude AND ST_Y(geom)=latitude LIMIT 1"
        self.curs.execute(sql)
        result = self.curs.fetchone()
        if result is None:
            return False
        else:
            return result[0]

    def get_resolution(self, domain):
        """Returns the resolution of the domain and the units"""
        sql = "SELECT resolution, units FROM domain WHERE key={}".format(domain)
        self.curs.execute(sql)
        result = self.curs.fetchone()
        if result is None:
            return False
        else:
            return result[0], result[1]
