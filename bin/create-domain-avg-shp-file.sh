#!/bin/bash
#
#
# Mike Dvorak
# Stanford University
# dvorak@stanford.edu
#
# Created: 
# Modified: 
#
#
# Description: Averages wind speed, REpower 5M power, and power
# density over a given time period in the wind database.  UTC time is
# assumed.
#

if [[ $# != 5 && $# != 7 ]]; then
  echo "Useage: create-domain-avg-shp-file.sh <dbHost> <dbUser> <dbName> <domainNum> <height> <startDate e.g. 2005-08-01> <endDate (exclusive)> [<startTime> <endTime (inclusive)>]"
  exit -1
fi

dbhost=$1
dbuser=$2
dbname=$3
dom=$4
height=$5
start=$6
end=$7

if [ $# = 9 ]; then
startTime=$8
endTime=$9
fi


if [ $# = 7 ]; then

pgsql2shp -h $dbhost -u $dbuser -g geom -f domain-$dom-avg-$start-thru-$end $dbname "SELECT h.geom as geom, w.geomkey, avg(speed) as speed_avg, avg(repower5m(speed)) as rpr5m_avg, avg(0.5*1.225*pow(speed,3)) as pwrden_avg FROM wind_${dom} w, horizgeom h where h.key=w.geomkey and height=$height and w.domainkey=$dom and t>= timestamp'$start 00:00:00' and t<timestamp'$end 00:00:00' GROUP BY h.geom, w.geomkey"

elif [ $# = 9 ]; then 

pgsql2shp -h $dbhost -u $dbuser -g geom -f domain-$dom-avg-$start-thru-$end-peak-start-$startTime-end-$endTime $dbname "SELECT h.geom as geom, w.geomkey, avg(speed) as speed_avg, avg(repower5m(speed)) as rpr5m_avg, avg(0.5*1.225*pow(speed,3)) as pwrden_avg FROM wind_${dom} w, horizgeom h where h.key=w.geomkey and height=$height and w.domainkey=$dom and t>= timestamp'$start 00:00:00' and t<timestamp'$end 00:00:00' and date_part('hour',timezone('+05',w.t))>=$startTime and date_part('hour',timezone('+05',w.t))<=$endTime GROUP BY h.geom, w.geomkey"

fi
