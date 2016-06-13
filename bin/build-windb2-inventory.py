#!/usr/bin/env python3
#
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2008-10-28
# Modified: 2015-12-24
#
#
# Description:  Creates an inventory to check the integrity of the WinDB2.
#
#

import os
import sys
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))
import argparse
from windb2 import windb2
import csv
from datetime import date

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('dbHost', help='Database hostname')
parser.add_argument('dbUser', help='Database user')
parser.add_argument('dbName', help='Database name')
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
parser.add_argument('-d', '--dir', type=str, default='domain-inventory', help='Directory name to store the inventory in.')
args = parser.parse_args()

# Connect to the WinDB
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()

# Get all of the domains
sql = 'SELECT key FROM domain'
windb2.curs.execute(sql)
domains = windb2.curs.fetchall()

# Make sure the directory for the results exists
try:
    os.chdir(args.dir)
except FileNotFoundError:
    os.mkdir(args.dir)
    os.chdir(args.dir)

# Create the inventory
# TODO currently this only works for wind
for domain in domains:

    # Create the inventory
    print('Calculating for domain: {}'.format(domain[0]))
    sql="""SELECT date_part('year', t), date_part('month', t), date_part('day', t) AS t_utc, count(*)
           FROM wind_{}
           GROUP BY date_part('year', t), date_part('month', t), date_part('day', t)
           ORDER BY date_part('year', t), date_part('month', t), date_part('day', t)
           """.format(domain[0])
    windb2.curs.execute(sql)

    # Write the rows out to CSV
    fieldnames = ('year', 'month', 'day', 'count')
    with open('{}-{}-domain-{}-{}.csv'
              .format(args.dbHost, args.dbName, domain[0], date.today().isoformat()), 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(fieldnames)
        for row in windb2.curs.fetchall():
            writer.writerow(row)


