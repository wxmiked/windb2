#!/usr/bin/env python3
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2014-11-19
# Modified: 2016-03-02
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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
        conn = psycopg2.connect(user=args.dbuser, host=args.dbhost)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        conn.cursor().execute('CREATE DATABASE "{}"'.format(args.dbname))
        conn.close()
        print('successfully created database "{}"'.format(args.dbname))

        # Reconnect to it
        windb = windb2.WinDB2(args.dbhost, args.dbname, dbUser=args.dbuser, port=args.port)
        windb.connect()

    else:
        logger.error(e)
        sys.exit(-1)

# Enable PostGIS and change ownership of the necessary tables to teh new user
windb.curs.execute('CREATE EXTENSION postgis')
tables_to_change_owner = ['geography_columns', 'raster_columns', 'raster_overviews', 'spatial_ref_sys']
for table in tables_to_change_owner:
    windb.curs.execute('ALTER TABLE {} OWNER TO {}'.format(table, args.dbuser))

# Enable core
os.chdir(script_dir + '/../schema/core')
for sql in ['Domain.sql', 'HorizGeom.sql', 'GeoVariable.sql']:
    windb.curs.execute(open(sql, 'r').read())

# Enable utilities
os.chdir(script_dir + '/../schema/util')
for sql in ['UV.sql', 'NGE.sql', 'MSE.sql', 'NB.sql', 'Bias.sql']:
    windb.curs.execute(open(sql, 'r').read())

# Enable validation
os.chdir(script_dir + '/../schema/validation')
for sql in ['WindError.sql', 'WindErrorShortView.sql']:
    windb.curs.execute(open(sql, 'r').read())

# Commit
windb.conn.commit()

# Add the tablefunc extension, which is useful for the crosstab functionality (rows as columns)
# http://www.postgresql.org/docs/9.1/static/tablefunc.html
#psql -h $dbHost -U postgres $dbName -c "CREATE EXTENSION tablefunc"
