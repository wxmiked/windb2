import numpy as np

_merra2_long_res = 0.625
_merra2_lat_res = 0.5

def get_surrounding_merra2_nodes(long, lat, grid=False):
    """
    Calculates four surrounding MERRA2 nodes for the given coordinate.

    Returns a string of long for ncks, string of long for ncks
    """

    # Round to the appropriate resolution
    long = round(long, 3)
    lat = round(lat, 2)

    # Closest points
    leftLong = long - ((long*1000)%(_merra2_long_res*1000))/1000
    rightLong = leftLong + _merra2_long_res
    bottonLat = lat - ((lat*100)%(_merra2_lat_res*100))/100
    topLat = bottonLat + _merra2_lat_res

    # Return a single coordinate if an exact MERRA node location has been requested, surrounding points otherwise
    if (leftLong*1000)%(_merra2_long_res*1000) == 0 and (lat*100)%(_merra2_lat_res*100) == 0:
        if grid:
            long_grid, lat_grid = np.meshgrid([long], [lat])
            return long_grid, lat_grid
        else:
            return '{}'.format(long), '{}'.format(lat)
    else:
        if grid:
            long_grid, lat_grid = np.meshgrid([leftLong, rightLong], [bottonLat, topLat])
        else:
            return '{},{}'.format(leftLong, rightLong), '{},{}'.format(bottonLat, topLat)


def download_all_merra2(windb2, long, lat, variables, dryrun=False, download_missing=False, startyear=1980):
    """Checks the inventory and downloads all MERRA2 for a given coordinate"""
    from datetime import datetime, timedelta
    import pytz
    import subprocess
    import os.path

    # Get the surrounding nodes
    longSurround, latSurround = get_surrounding_merra2_nodes(long, lat)

    # MERRA2 data is updated around the 15th of the month
    merra2_start_incl = datetime(1980, 1, 1, 0, 0, 0).replace(tzinfo=pytz.utc)
    merra2_end_excl = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
    if datetime.utcnow().day < 15:
        merra2_end_excl = merra2_end_excl - timedelta(days=15)
    merra2_end_excl = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    # If there's nothing in the database, then we need to get everything
    missing_data = False
    # TODO this needs to be implemented in a smart way, just downloading everything for now
    missing_data = True
    # for var in variables.split(','):
    #     sql = """SELECT min(t), max(t)
    #              FROM {}_{}
    #              WHERE domainkey=(SELECT key FROM horizgeom WHERE st_transform(geom,4326)=st_geomfromtext('POINT({} {})',4326))"""\
    #         .format(var, domainkey, long, lat)
    #     windb2.curs.execute(sql)
    #     existing_t_range = windb2.curs.fetchone()
    #     if existing_t_range[0] is None and existing_t_range[1] is None:
    #         missing_data = True
    #         break

    # Get everything is nothing is here
    if missing_data:

        # Download the data in chunks
        start_t_incl = datetime(startyear, 1, 1, 0, 0, 0).replace(tzinfo=pytz.utc)
        chunk_size_days = 200
        while start_t_incl < merra2_end_excl:

            # Convert start index to hours
            index_start = (start_t_incl - merra2_start_incl).days * 24
            if start_t_incl + timedelta(days=chunk_size_days) < merra2_end_excl:
                index_stop = (start_t_incl + timedelta(days=chunk_size_days) - merra2_start_incl).days * 24 - 1
            else:
                index_stop = (merra2_end_excl - merra2_start_incl).days * 24 - 1
            end_t_incl = merra2_start_incl + timedelta(hours=index_stop)

            # Generatet the ncks command to run
            url = 'http://goldsmr4.gesdisc.eosdis.nasa.gov/dods/M2T1NXSLV'
            cmd = '/usr/bin/ncks'
            filename = 'merra2_{}_{}_{:06}-{:06}.nc'.format(longSurround, latSurround, index_start, index_stop)
            args = '-O -v {} -d time,{},{} -d lon,{} -d lat,{} {} {}' \
                .format(variables, index_start, index_stop, longSurround, latSurround, url, filename)

            # Only download what's missing
            if download_missing:
                if os.path.isfile(filename):
                    print('Skipping file: {}'.format(filename))
                    start_t_incl += timedelta(days=chunk_size_days)
                    continue

            if dryrun:
                print(cmd, ' ', args)
            else:
                print('Running: {} {}'.format(cmd, args))
                subprocess.call(cmd + ' ' + args, shell=True)

            start_t_incl += timedelta(days=chunk_size_days)

def insert_merra2_file(windb2conn, ncfile, vars, reinsert=False):
    """Inserts a MERRA2 file downloaded using ncks

    ncfile: netCDF file downloaded with ncks
    vars: CSV list of MERRA2 variables (e.g. u50m,v50m,ps)
    """
    from netCDF4 import Dataset, num2date
    import re
    from windb2.struct import geovariable, insert
    import pytz

    # Info
    print('Inserting: {}'.format(ncfile))

    # Open the netCDF file
    ncfile = Dataset(ncfile, 'r')

    # Get the times
    timevar = ncfile.variables['time']
    timearr = num2date(timevar[:], units=timevar.units)

    # For each variable...
    for var in vars.split(','):

        # Break up the variable name
        var_re = re.match(r'([a-z]+)([0-9]*)([a-z]*)[,]*', var)

        # For each lat
        latcount = 0
        latarr = ncfile.variables['lat'][:]
        for lat in latarr:

            # For each long
            longcount = 0
            longarr = ncfile.variables['lon'][:]
            for long in longarr:

                # For each time in the variable
                tcount = 0
                varstoinsert = []
                for t in timearr:

                    # Clean up the seconds because every other time has a residual
                    t = t.replace(microsecond=0).replace(tzinfo=pytz.utc)

                    # Figure out the height
                    if var_re.group(2) is not None:
                        height = var_re.group(2)
                    else:
                        height = -9999

                    # Append the data to insert
                    v = geovariable.GeoVariable(var, t, height,
                        ncfile.variables[var][tcount, latcount, longcount])
                    varstoinsert.append(v)
                    if var == 'u50m':
                        print(v)

                    # Increment t
                    tcount += 1

                # Insert the data
                insert.insertGeoVariable(windb2conn, "MERRA2", "NASA", varstoinsert,
                                         longitude=long, latitude=lat, reinsert=reinsert)
                # Increment long
                longcount += 1

            # Increment lat
            latcount += 1



def export_to_csv(windb2conn, long, lat, variables, startyear=1980):
    import numpy as np
    import re

    # Split the variables
    variables = variables.split(',')

    # Get the gridded coordinates
    long_grid, lat_grid = get_surrounding_merra2_nodes(long, lat, grid=True)

    # Write out a CSV file for each MERRA node, labeled A through D
    labels = np.array([['C', 'D'], ['A', 'B']])
    it = np.nditer(long_grid, flags=['multi_index'])
    while not it.finished:

        # Get the geomkey for this node
        sql = "SELECT key, domainkey " \
              "FROM horizgeom " \
              "WHERE st_transform(geom,4326)=st_geomfromtext('POINT({} {})',4326) LIMIT 1"\
            .format(long_grid[it.multi_index], lat_grid[it.multi_index])
        windb2conn.curs.execute(sql)
        geomkey, domainkey = windb2conn.curs.fetchone()

        # Get the max time
        sql = 'SELECT max(t) FROM {}_{} WHERE geomkey={}'.format(variables[0], domainkey, geomkey)
        windb2conn.curs.execute(sql)
        tmax = windb2conn.curs.fetchone()[0].date()

        # Create the view
        names_re = [re.match(r'([a-z]+)([0-9]*)([a-z]*)[,]*', var) for var in variables]
        selects = '{}.t as t, '.format(names_re[0].group(0)) + \
                  '%s ' % str(['{varname}.value as {varname} '
                              .format(varname=var.group(0)) for var in names_re])\
                      .replace("'", '').replace('[', '').replace(',$', '').replace(']', '')
        froms = '{varname}_{domainkey} as {varname}'.format(varname=variables[0], domainkey=domainkey)
        leftjoins = '%s ' % str(['LEFT JOIN {varname}_{domainkey} as {varname} ON {varname1}.t={varname}.t '
                                 'AND {varname1}.geomkey={varname}.geomkey AND {varname}.geomkey={geomkey}' \
                                .format(varname1=variables[0], varname=var, domainkey=domainkey, geomkey=geomkey) for var in variables[1:-1]]) \
                            .replace("'", '').replace('[', '').replace(',$', '').replace(']', '').replace(',', '')
        leftjoins += 'LEFT JOIN {varname}_{domainkey} as {varname} ON {varname1}.t={varname}.t ' \
                     'AND {varname1}.geomkey={varname}.geomkey AND {varname}.geomkey={geomkey}' \
                     .format(varname1=variables[0], varname=variables[-1], domainkey=domainkey, geomkey=geomkey)
        wheres = '%s ' % str(['{varname}.geomkey={geomkey} AND '
                             .format(varname=var, geomkey=geomkey) for var in variables[:-1]])\
                             .replace("'", '').replace('[', '').replace(',$', '').replace(']', '').replace(',', '')
        wheres += '{varname}.geomkey={geomkey}'.format(varname=variables[-1], geomkey=geomkey)

        # Convert u,v pairs into speed "ws" and "wd" direction fields
        # Negate the wind direction to get the meteorogical wind direction
        selects = re.sub(r'u([0-9]+)m\.value as u[0-9]+m , v([0-9]+)m\.value as v[0-9]+m ([,]*) ',
                         'speed(u\g<1>m.value, v\g<2>m.value) as ws\g<1>m, calc_dir_deg(-u\g<1>m.value, -v\g<2>m.value)::int as wd\g<1>m\g<3> ',
                         selects)

        # sql = """CREATE TEMP VIEW csv_out_node_A AS
        #          SELECT u50m.t as t, u50m.value as u50m , v50m.value as v50m , t2m.value as t2m
        #          FROM u50m_1 as u50m
        #             LEFT JOIN  v50m_1  as v50m ON u50m.t=v50m.t
        #             LEFT JOIN  t2m_1 as t2m ON  u50m.t=t2m.t
        #          WHERE u50m.geomkey=1 AND  v50m.geomkey=1 AND  t2m.geomkey=1
        #          ORDER BY t"""

        # Final query to create the view
        sql = """CREATE TEMP VIEW csv_out_node_{} AS
                 SELECT {}
                 FROM {}
                    {}
                 WHERE {}
                 ORDER BY t""".format(labels[it.multi_index], selects, froms, leftjoins, wheres)
        windb2conn.curs.execute(sql)

        # Make the filename
        filename='MERRA2_Node_{node}_{long:.{prec}f}_{lat:.{prec}f}_{startyear}_thru_{tmax}.csv'\
            .format(node=labels[it.multi_index], long=long_grid[it.multi_index], lat=lat_grid[it.multi_index],
                    prec=3, startyear=startyear, tmax=tmax)

        # Write out the CSV file
        sql = 'COPY (SELECT * FROM csv_out_node_{}) TO STDOUT WITH CSV HEADER'.format(labels[it.multi_index])
        with open(filename, 'w') as file:
            print('Writing out Node {}: {}'.format(labels[it.multi_index], filename))
            windb2conn.curs.copy_expert(sql, file)

        it.iternext()

def _convert_long_to_index(long_surround, lat_surround):

    if isinstance(long_surround, list):
        long_surround = np.array(long_surround)
        lat_surround = np.array(lat_surround)

    if np.all((long_surround*1000)%(_merra2_long_res*1000)) or np.all((lat_surround*100)%(_merra2_lat_res*100)):
        raise ValueError('Illegal long or at value')

    return (long_surround + 179.375)/_merra2_long_res, (lat_surround + 90)/_merra2_lat_res




