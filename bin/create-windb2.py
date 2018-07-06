#!/usr/bin/env python3
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2014-11-19
# Modified: 2016-06-16
#
#
# Description: Creates a new WinDB2 database with minimal functionality
#

import os
import sys
script_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(script_dir, '../'))
import argparse
from windb2 import windb2
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Set up logging level
logger = logging.getLogger('windb2')
logger.setLevel(logging.WARNING)
logging.basicConfig()

# Set all the relevant args
parser = argparse.ArgumentParser(description='Creates a new, empty WinDB2 in an existing PostgreSQL database')
parser.add_argument('dbhost', help='WinDB host')
parser.add_argument('dbuser', help='WinDB user')
parser.add_argument('dbname', help='WinDB name')
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
#TODO add no ask password option
args = parser.parse_args()

## Create a new user, which will fail if the user already exists
#createuser -h $dbHost $dbUser
#
## Create the database
#createdb -h $dbHost -U postgres --owner=$dbUser $dbName

# Change the password for postgres user
#read -s -p "Enter password for user $dbUser: " password
#psql -h $dbHost -U postgres $dbName -c "ALTER USER $dbUser WITH password '$password'";
#psql -h $dbHost -U postgres $dbName -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $dbUser";

# Try and authenticate, giving up if password-less auth has not been configured
try:
    windb = windb2.WinDB2(args.dbhost, args.dbname, dbUser=args.dbuser, port=args.port)
    windb.connect()

except psycopg2.OperationalError as e:

    # See if we can create the database
    if str(e).strip() == 'FATAL:  database "{}" does not exist'.format(args.dbname):

        # Create the database
        print('database "{}" does not exist... trying to create it'.format(args.dbname))
        try:
            conn = psycopg2.connect(user=args.dbuser, host=args.dbhost, database='postgres')
        except psycopg2.OperationalError as e:
            print('Unable to create a new database. You will have to do this manually outside of this script.')
            print('Run this command to create the database: % createdb --user={} {}'.format(args.dbuser, args.dbname))
            print('Reason for failure: ' + str(e))
            sys.exit(-1)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        conn.cursor().execute('CREATE DATABASE "{}"'.format(args.dbname))
        conn.close()
        print('successfully created database "{}"'.format(args.dbname))

        # Reconnect to it
        windb = windb2.WinDB2(args.dbhost, args.dbname, dbUser=args.dbuser, port=args.port)
        windb.connect()

    elif str(e).strip() == 'fe_sendauth: no password supplied':
        print('Failed to connect. You need to have a $HOME/.pgpass set up correctly with your password.', file=sys.stderr)
        print('Details here: https://wiki.postgresql.org/wiki/Pgpass', file=sys.stderr)
        sys.exit(-1)

    else:
        print('Failed to connect to your database.', file=sys.stderr)
        print('Failure reason:', file=sys.stderr)
        logger.error(e)
        sys.exit(-1)

# Make sure the supplied user is a PostgreSQL superuser
windb.curs.execute('SELECT usesuper FROM pg_user WHERE usename = \'{}\''.format(args.dbuser))
if not windb.curs.fetchone()[0]:
    print('Error: The database user must have superuser permissions to proceed.')
    print('To fix this, as another superuser (e.g. postgres) run this command:')
    print('psql# ALTER USER {} WITH SUPERUSER;'.format(args.dbuser))

# Enable PostGIS and change ownership of the necessary tables to the new user
try:
    windb.curs.execute('CREATE EXTENSION postgis')
except psycopg2.ProgrammingError as e:
    if str(e).strip() != 'extension "postgis" already exists':
        logger.error('Failure when trying to add create the "postgis" extension in the Postgres DB.')
        logger.error('You may need to be the DB superuser (usually "postgres" user) to create the extension.')
        logger.error(e)
        exit(-1)
    else:
        # Rollback from the 'extension "postgis" already exists or the following commands will fail
        windb.conn.rollback()
tables_to_change_owner = ['geography_columns', 'raster_columns', 'raster_overviews', 'spatial_ref_sys']
for table in tables_to_change_owner:
    windb.curs.execute('ALTER TABLE {} OWNER TO {}'.format(table, args.dbuser))

# Enable core
os.chdir(script_dir + '/../schema/core')
for sql in ['Domain.sql', 'HorizGeom.sql', 'GeoVariable.sql']:
    try:
        windb.curs.execute(open(sql, 'r').read())
    except psycopg2.ProgrammingError as e:
        if str(e).strip() == 'relation "domain" already exists':
            print('It looks like you have already initialzed a WinDB2 in the database.')
            sys.exit(-1)

# Enable utilities
os.chdir(script_dir + '/../schema/util')
for sql in ['Bias.sql', 'CALC_DIR_DEG.sql', 'DATE_ROUND.sql', 'MEDIAN.sql', 'MSE.sql', 'NB.sql', 'NGE.sql',
            'QUANTILE.sql', 'SPEED.sql', 'UTMZONE.sql', 'UV.sql', 'WINDDIR.sql']:
    try:
        windb.curs.execute(open(sql, 'r').read())
        windb.conn.commit()
    except psycopg2.ProgrammingError as e:
        print('Could not add SQL function from: {}'.format(sql))
        print(e)
        windb.conn.reset()
    except psycopg2.InternalError as e:
        print('Could not add SQL function from: {}'.format(sql))
        print(e)
        windb.conn.reset()

# Enable validation
os.chdir(script_dir + '/../schema/validation')
for sql in ['WindError.sql', 'WindErrorShortView.sql', 'ValidStation.sql', 'ValidError.sql']:
    windb.curs.execute(open(sql, 'r').read())

# Commit
windb.conn.commit()

# Info
print('Successfully created your WinDB2. Enjoy!')

# Add the tablefunc extension, which is useful for the crosstab functionality (rows as columns)
# http://www.postgresql.org/docs/9.1/static/tablefunc.html
#psql -h $dbHost -U postgres $dbName -c "CREATE EXTENSION tablefunc"
