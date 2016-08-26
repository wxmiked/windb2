#!/bin/bash

# Set up WinDB2
/windb2/bin/create-windb2.py localhost $POSTGRES_USER windb2
apt-get remove -y python3 python3 python3-psycopg2 python3-tz python3-numpy
apt-get autoremove -y
rm -fr /windb2
