import sys
from windb2 import windb2
from windb2.struct.winddata import WindData
from windb2.struct.winddata3d import WindData3D
import psycopg2

def insertWindData(windb2, dataName, dataCreator, windData, longitude=0, latitude=0):
    """Inserts a WindData (2D) or WindData3D list into the given database.

    windb2, WinDB2 instantiation
    dataName, string like 'arps-ideal'
    dataCreator, string like 'NCAR'
    windData, list of WindData or WindData3D objects
    longitude, longitude of point, 0 by default
    latitude, latitude of a point, 0 by default"""

    # Check to see if the data is 3D
    data3D = False
    if isinstance(windData[0], WindData3D):
        data3D = True

        # Info
        print
        'WindData is 3D.'

    # See if this domain data name already exists
    domainKey = windb2.findDomainForDataName(dataName)

    # Try and get the domain key result. If no key was returned, we need to make new domain and windspeed tables
    newDomain = False
    if not domainKey:
        newDomain = True

    # Create a new table if we need to
    if domainKey == None:

        # Insert the name into the domain table which returns the new key
        sql = "INSERT INTO domain(name, resolution, units, datasource) VALUES ('" + dataName + "', 0, 'm', '" + dataCreator + "') RETURNING key"
        try:
            windb2.curs.execute(sql)
        except psycopg2.ProgrammingError as detail:
            print
            "Inserting a new domain domain failed. Exiting..."
            print
            detail
            sys.exit(-1)

        # Get the domain key
        domainKey = windb2.curs.fetchone()[0]

        # Create a new wind table
        sql = "CREATE TABLE wind_" + str(domainKey) + " () INHERITS(GeoVariable)"
        try:
            windb2.curs.execute(sql)
        except Exception as detail:
            print
            detail

        # Add in the unique constraint because this is not inherited from parent
        sql = "ALTER TABLE wind_" + str(domainKey) + " ADD CONSTRAINT wind_" + str(
            domainKey) + "_domainkey_geomkey_t_height_key UNIQUE (domainkey, geomkey, t, height)"
        try:
            windb2.curs.execute(sql)
        except Exception as detail:
            print
            detail

        # Add in the unique constraint because this is not inherited from parent
        sql = "ALTER TABLE wind_" + str(domainKey) + " ADD COLUMN speed float, ADD COLUMN direction smallint"
        try:
            windb2.curs.execute(sql)
        except Exception as detail:
            print
            detail

        # Add a geometry column to store the observation point
        if data3D:
            sql = "ALTER TABLE wind_" + str(domainKey) + " ADD COLUMN w real"
            windb2.curs.execute(sql)

        # Add a 2D point for the made up location of the
        sql = "INSERT INTO horizgeom(domainkey, x, y, geom) \
               VALUES (" + str(domainKey) + ",0,0, st_geomfromtext('POINT(" + str(longitude) + ' ' + str(
            latitude) + ")',4326)) RETURNING key"
        print(sql)
        windb2.curs.execute(sql)
        geomKey = windb2.curs.fetchone()

        # Commit all of these addtions
        windb2.conn.commit()

    # Otherwise, check to see if there already exists a geomkey with the same coordinates
    elif longitude != 0 and latitude != 0 and moving is False:

        # Get the geomkey for the location
        sql = "SELECT key FROM horizgeom \
               WHERE st_distance_sphere(st_transform(geom, 4326), st_geomfromtext('POINT(" + str(longitude) + ' ' + str(latitude) + ")',4326)) = 0 AND \
                     domainkey = " + str(domainKey) + " LIMIT 1"
        windb2.curs.execute(sql)
        geomKey = windb2.curs.fetchone()[0]

    # Otherwise, this is an ideal domain and there is not geom
    else:
        geomKey = 0

    # Insert all of the data
    execList = []
    sql3D = ["", ""]
    if data3D:
        sql3D = [",w", ", %(w)s"]
    sql = "INSERT INTO wind_" + str(domainKey) + """(domainkey, geomkey, t, speed, direction, height""" + sql3D[
        0] + """)
           VALUES (%(domainkey)s, %(geomkey)s, %(t)s, %(speed)s, %(direction)s, %(height)s""" + sql3D[1] + ")"
    for data in windData:

        # Data to append
        dataToAppend = {'domainkey': domainKey, 'geomkey': geomKey, 't': data.time, 'speed': data.speed,
                        'direction': data.direction, 'height': data.height}
        if data3D:
            dataToAppend['w'] = data.wSpeed
        execList.append(dataToAppend)

    try:
        windb2.curs.executemany(sql, execList)
    except psycopg2.DataError as detail:
        print("DataError while inserting the large list wind speed: ", detail)
        "Exiting..."
        sys.exit(-1)

    # Commit these changes
    windb2.conn.commit()

def insertGeoVariable(windb2, dataName, dataCreator, dataToInsert, table_name_override=None, x=0, y=0, longitude=0, latitude=0, resolution=0, reinsert=False, moving=False):
    """Inserts a list of Variables into the given database.

    windb2, WinDB2 instantiation
    dataName, string like 'MERRA2'
    dataCreator, string like 'NASA'
    dataToInsert, list of struct.Variable objects
    table_name_override, name of table that overrides the default naming (useful for combined variables like wind = [speed, dir])
    longitude, longitude of point, 0 by default
    latitude, latitude of a point, 0 by default"""

    # See if this domain data name already exists
    domainKey = windb2.findDomainForDataName(dataName)

    # Try and get the domain key result. If no key was returned, we need to make new domain and wind tables
    newDomain = False
    if domainKey is None:
        newDomain = True

    # Create a new table if we need to
    if domainKey is None:

        # Insert the name into the domain table which returns the new key
        sql = "INSERT INTO domain(name, resolution, units, datasource) VALUES ('{}', '{}', '{}', '{}') RETURNING key"\
            .format(dataName, resolution, dataToInsert[0].units, dataCreator)
        try:
            windb2.curs.execute(sql)
        except psycopg2.ProgrammingError as detail:
            print("Inserting a new domain domain failed. Exiting...")
            print(detail)
            sys.exit(-1)

        # Get the domain key
        domainKey = windb2.curs.fetchone()[0]

        # Commit all of these additions
        windb2.conn.commit()

    # Otherwise, check to see if there already exists a geomkey with the same coordinates
    elif longitude != 0 and latitude != 0 and moving is False:

        # Get the geomkey for the location
        sql = "SELECT key FROM horizgeom \
               WHERE st_distance_sphere(st_transform(geom, 4326), st_geomfromtext('POINT({} {})',4326))=0 AND \
                     domainkey={} LIMIT 1".format(longitude, latitude, domainKey)
        windb2.curs.execute(sql)
        geomKey = windb2.curs.fetchone()

    # Otherwise, this is an ideal domain and there is not geom
    else:
        geomKey = 0

    # Set the table name, overriding it if necessary
    if table_name_override is not None:
        table_name = '{}_{}'.format(table_name_override, domainKey)
    else:
        table_name = '{}_{}'.format(dataToInsert[0].name, domainKey)

    # Create a new geovariable table if it doesn't exist
    sql = "SELECT to_regclass('public.{}');".format(table_name)
    windb2.curs.execute(sql)
    if not windb2.curs.fetchone()[0]:
        sql = "CREATE TABLE {} () INHERITS(geovariable)".format(table_name)
        try:
            windb2.curs.execute(sql)
        except Exception as detail:
            print(detail)
            sys.exit(-1)

        # Add a geometry column to the geovariable table if a moving station and make the geomkey a serial column
        if moving is True:
            try:
                seq_name = '{}_geomkey_seq'.format(table_name)
                windb2.curs.execute("SELECT AddGeometryColumn('{}', 'geom', 4326, 'POINT', 2)".format(table_name))
                windb2.curs.execute('CREATE SEQUENCE {}'.format(seq_name))
                windb2.curs.execute("ALTER TABLE {} ALTER COLUMN geomkey SET DEFAULT nextval('{}')".format(table_name, seq_name))
            except Exception as detail:
                print(detail)
                raise
                sys.exit(-1)

        # Add a column for the value
        sql = "ALTER TABLE {} ADD COLUMN value real".format(table_name)
        try:
            windb2.curs.execute(sql)
        except Exception as detail:
            print(detail)
            sys.exit(-1)

        # Add in the unique constraint because this is not inherited from parent
        if moving is False:
            sql = "ALTER TABLE {} " \
                  "ADD UNIQUE (domainkey, geomkey, t, height)"\
                .format(table_name)
            try:
                windb2.curs.execute(sql)
            except Exception as detail:
                print(detail)
        elif moving is True:
            sql = "ALTER TABLE {} " \
                  "ADD UNIQUE (domainkey, geom, t, height)"\
                .format(table_name)
            try:
                windb2.curs.execute(sql)
            except Exception as detail:
                print(detail)

    # Add a 2D point if necessary
    if moving is False:
        sql = "SELECT key FROM horizgeom WHERE domainkey={} AND st_transform(geom,4326)=st_geomfromtext('POINT({} {})',4326)"\
            .format(domainKey, longitude, latitude)
        windb2.curs.execute(sql)
        geomKey = windb2.curs.fetchone()
        if geomKey is None:
            sql = "INSERT INTO horizgeom(domainkey, x, y, geom) \
                   VALUES ({},{},{}, st_geomfromtext('POINT({} {})',4326)) RETURNING key"\
                .format(domainKey, x, y, longitude, latitude)
            windb2.curs.execute(sql)
            geomKey = windb2.curs.fetchone()[0]
        else:
            geomKey = geomKey[0]

    # Insert all of the data
    execList = []
    t_min = None
    t_max = None
    if moving is False:
        sql = """INSERT INTO {} (domainkey, geomkey, t, height, value)
               VALUES (%(domainkey)s, %(geomkey)s, %(t)s, %(height)s, %(value)s)""" \
            .format(table_name)
    elif moving is True:
        sql = """INSERT INTO {} (domainkey, geom, t, height, value)
               VALUES (%(domainkey)s, ST_GeomFromText(%(geom)s, 4326), %(t)s, %(height)s, %(value)s)""" \
            .format(table_name)
    for data in dataToInsert:

        # Store the min and max dates for the reinsert functionality
        if reinsert:
            if t_min is None:
                t_min = data.time
            elif data.time < t_min:
                t_min = data.time

            if t_max is None:
                t_max = data.time
            elif data.time > t_max:
                t_max = data.time

        # Data to append
        if moving is False:
            dataToAppend = {'domainkey': domainKey, 'geomkey': geomKey, 't': data.time, 'height': data.height, 'value': data.val}
        elif moving is True:
            dataToAppend = {'domainkey': domainKey, 'geom': "POINT({} {})".format(longitude, latitude), 't': data.time, 'height': data.height, 'value': data.val}
        execList.append(dataToAppend)

    try:

        # Clean out the table before insert if reinsert is true
        if reinsert:
            print('DELETING all data between {} and {} from: {}_{}'
                  .format(t_min, t_max, table_name, geomKey))
            if moving is False:
                sql = "DELETE FROM {} " \
                      "WHERE geomkey={} AND t>=timestamp with time zone'{}' AND t<=timestamp with time zone'{}'"\
                    .format(table_name, geomKey, t_min, t_max)
            elif moving is True:
                sql = "DELETE FROM {} " \
                      "WHERE ST_Equals(geom, ST_GeomFromText('POINT({} {})')) AND t>=timestamp with time zone'{}' AND t<=timestamp with time zone'{}'" \
                    .format(table_name, longitude, latitude, geomKey, t_min, t_max)
            print('Reinsert delete: {}'.format(sql))
            windb2.curs.execute(sql)

        # Insert the list of geovariables
        windb2.curs.executemany(sql, execList)
    except psycopg2.DataError as detail:
        print("DataError while inserting the large list wind speed: ", detail)
        "Exiting..."
        sys.exit(-1)

    # Commit these changes
    windb2.conn.commit()

