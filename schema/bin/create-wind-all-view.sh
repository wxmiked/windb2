#!/bin/bash -f
# IMPORTANT: Need to be run with the '-f' option 'to disable globbing/filename expansion altogether"
# http://stackoverflow.com/questions/2755795/how-do-i-pass-in-the-asterisk-character-in-bash-as-arguments-to-my-c-program
#
# This script joins together all wind domains so that only one table has
# to be listed to perform a query.

if [ $# != 3 ]; then
  echo "You need to privide a database name."
  echo "Usage: create-wind-db.sh <dbHost> <dbUser> <dbName>"
  exit -1
fi

# Set the DB name
dbhost=$1
dbuser=$2
dbname=$3

# Get rid of the old windspeed table
psql -h $dbhost -U $dbuser $dbname -c "DROP VIEW wind_all"

# Get a list of all the windspeed tables
command='CREATE VIEW wind_all AS SELECT * FROM '
let count=0
for i in `psql -h $dbhost -U $dbuser $dbname -c '\d' | cut -d '|' -f 2 | egrep 'wind_[0-9]+'`; do
  
   if [ $count -eq 0 ]; then
       command="$command $i"
       let count=$count+1
       echo $count
   else
       command=$command' UNION ALL SELECT * FROM '$i
   fi

done

echo Running the command: $command
echo $command > /tmp/runme-$PPID

psql -h $dbhost -U $dbuser $dbname -f /tmp/runme-$PPID

