import numpy as np

_merra2_long_res = 0.625
_merra2_lat_res = 0.5

def get_surrounding_merra2_nodes(long, lat, grid=False):
    """
    Calculates four surrounding MERRA2 nodes for the given coordinate.

    Returns a string of long for ncks, string of long for ncks
    """

    # MERRA2 specs
    deltaLong = 0.625
    deltaLat = 0.5

    # Closest points
    leftLong = long - ((long*1000)%(deltaLong*1000))/1000
    rightLong = leftLong + deltaLong
    bottonLat = lat - ((lat*100)%(deltaLat*100))/100
    topLat = bottonLat + deltaLat

    longGrid, latGrid = np.meshgrid([leftLong, rightLong], [bottonLat, topLat])

    if (leftLong*1000)%(deltaLong*1000) == 0 and (lat*100)%(deltaLat*100) == 0:
        return '{}'.format(long), '{}'.format(lat)
    else:
        return '{},{}'.format(leftLong, rightLong), '{},{}'.format(bottonLat, topLat)


def download_all_merra2(windb2, long, lat, variables, dryrun=False, download_missing=False):
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

    # Get the domain key
    domainkey = windb2.findDomainForDataName('MERRA2')
    if domainkey is None:
        raise ValueError('You have to run this for existing MERRA2 domains.')
        sys.exit(-3)

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
        start_t_incl = merra2_start_incl
        chunk_size_days = 200
        while start_t_incl < merra2_end_excl:

            # Convert start index to hours
            index_start = (start_t_incl - merra2_start_incl).days * 24
            if start_t_incl + timedelta(days=chunk_size_days) < merra2_end_excl:
                index_stop = (start_t_incl + timedelta(days=chunk_size_days) - merra2_start_incl).days * 24 - 1
            else:
                index_stop = (merra2_end_excl - merra2_start_incl).days * 24 - 1
            end_t_incl = merra2_start_incl + timedelta(hours=index_stop)

            # Debug
            # if dryrun:
            #     print('var={} index_start={}, index_stop={}'.format(var, index_start, index_stop))
            #     print('start_t_incl={} end_t_incl={}'.format(start_t_incl, end_t_incl))

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

def insert_merra2_file(windb2conn, ncfile, vars):
    """Inserts a MERRA2 file downloaded using ncks

    ncfile: netCDF file downloaded with ncks
    vars: CSV list of MERRA2 variables (e.g. u50m,v50m,ps)
    """
    from netCDF4 import Dataset, num2date
    import re
    from windb2.struct import geovariable, insert

    # Open the netCDF file
    ncfile = Dataset(ncfile, 'r')
    # Get the times
    timevar = ncfile.variables['time']
    timearr = num2date(timevar[:], units=timevar.units)
    # Get the coordinates
    longitudearr = ncfile.variables['lon'][:]
    latitudearr = ncfile.variables['lat'][:]
    # For each variable...
    for var in vars.split(','):

        # Break up the variable name
        var_re = re.match(r'([a-z]+)([0-9]*)([a-z]*)[,]*', var)

        # For each long
        longcount = 0
        longarr = ncfile.variables['lon']
        for long in longarr:

            # For each lat
            latcount = 0
            latarr = ncfile.variables['lat']
            for lat in latarr:

                # For each time in the variable
                tcount = 0
                varstoinsert = []
                for t in timearr:

                    # Clean up the seconds because every other time has a residual
                    t = t.replace(microsecond=0)

                    # Figure out the height
                    if var_re.group(2) is not None:
                        height = var_re.group(2)
                    else:
                        height = -9999

                    v = geovariable.GeoVariable(var, t, height,
                                                ncfile.variables[var_re.group(0)][tcount, latcount, longcount])
                    varstoinsert.append(v)

                    # Increment t
                    tcount += 1

                # Insert the data
                insert.insertGeoVariable(windb2conn, "MERRA2", "NASA", varstoinsert, longitude=long, latitude=lat)

            # Increment lat
            latcount += 1

        # Increment long
        longcount += 1



