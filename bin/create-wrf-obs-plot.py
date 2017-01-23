#!/usr/bin/env python3
#
#
# Mike Dvorak
# Postdoc
# UC Berkeley
# Civil and Environmental Engineering
# dvorak@berkeley.edu
#
# Created: 2013-05-13
# Modified: 2016-11-14
#
#
# Description: Plots out wind speed at a height on the same x-axis, including wind direction. 
#

import os
import sys
try:
    sys.path.append(os.environ['WINDB2_HOME'])
except KeyError:
    print('You must define WINDB2_HOME in your environment.')
    exit(-1)

# Next two lines required to get MPL to plot in a non-DISPLAY environment http://stackoverflow.com/questions/4931376/generating-matplotlib-graphs-without-a-running-x-server
import matplotlib as mpl
mpl.use('Agg')
import psycopg2
import numpy
import datetime
from datetime import timedelta, tzinfo
import matplotlib.pyplot as plt
import matplotlib.dates
from pylab import specgram, detrend_linear
import pytz
import numpy.ma as ma
import numpy.fft
import re
from windb2 import windb2
from windb2.model.wrf import error, plot
import matplotlib.dates as mdates
import matplotlib.dates as mdates
import argparse

# Get the command line opts
knotConversion = 1.0
parser = argparse.ArgumentParser()
parser.add_argument("dbHost", type=str, help="Database hostname")
parser.add_argument("dbUser", type=str, help="Database username")
parser.add_argument("dbName", type=str, help="Database name")
parser.add_argument("obsName", type=str, help="Name of observation (e.g. BYC or ppxc1)")
parser.add_argument("obsPeriodSec", type=str, help="Averaging length of obvservations (e.g. 360 or 0.2 seconds)")
parser.add_argument("obsHeight", type=str, help="Height of the WRF and observation in meters")
parser.add_argument("wrfDomainKey", type=int, help="Domain number of the WRF run in the WinDB")
parser.add_argument("wrfHeight", type=str, help="Height of the WRF and observation in meters")
parser.add_argument("startDateIncl", type=str, help="Start date in ISO format: YYYY-MM-DD (UTC)")
parser.add_argument("startTimeIncl", type=str, help="Start time in 24-hr format: HH:MM (UTC)")
parser.add_argument("endDateIncl", type=str, help="End date format in ISO format: YYYY-MM-DD (UTC")
parser.add_argument("endTimeIncl", type=str, help="End time in 24-hr format: HH:MM (UTC)")
parser.add_argument("-t","--plotTimeZone", action="store", default='UTC',
                    help="Optional conversion to a different time zone FOR THE PLOT ONLY (other times are still UTC)")
parser.add_argument("-k", "--knots", help="convert from m/s to knots", action="store_true")
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
print("<plotTimeZone> converts the final plot to the desired time zone e.g. 'UTC' or 'US/Pacific'")
args = parser.parse_args()
if args.knots:
  print("Using knots instead of m/s")
  knotConversion = 1.94384

# Connect to the WinDB
# Connect to the WinDB2
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()


# Try make datetimes out of the command line start and end times
try:
    startDateTime = datetime.datetime.strptime(args.startDateIncl + ' ' + args.startTimeIncl, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone('UTC'))
    print('startDateTime={}'.format(startDateTime))
    startDateInclStr = startDateTime.strftime("%Y-%m-%d %H:%M:%S %Z")
    endDateTime = datetime.datetime.strptime(args.endDateIncl + ' ' + args.endTimeIncl, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone('UTC'))
    print('endDateTime={}'.format(endDateTime))
    endDateInclStr = (endDateTime).strftime("%Y-%m-%d %H:%M:%S %Z")

except ValueError as detail:
    print("Error trying to parse the start or end date: ", detail)
    sys.exit(-1)

# Get the obs domain number
print(args.obsName)
obsDomainKey = windb2.findDomainForDataName(args.obsName)

# Get the resolution of the domain to make sure there is really WRF coverage at this area
sql = "SELECT resolution FROM domain WHERE key=" + str(args.wrfDomainKey)
windb2.curs.execute(sql)
wrfResolutionM = windb2.curs.fetchone()[0]

# Get the geomkey of the closest WRF point
distanceToObsM = -999.
domainKeyToPlot = -999.
wrfKeyNearObsSql = ""
geomKeyToPlot, distanceToObsM = error.findWRFPointInProximityToBuoy(obsDomainKey,args.wrfDomainKey,windb2.curs)
wrfKeyNearObsSql = " AND geomkey=" + str(geomKeyToPlot)

# Abort if the distance to the observation is more than the resolution
if distanceToObsM > wrfResolutionM:
    print("ERROR: WRF data too far away from observation point. Resolutions: WRF=" + str(wrfResolutionM) + "m Obs=" + str(distanceToObsM) + " m")
    sys.exit(-1)

# Create a temp table of the times that should be in the observation dataset
sql = """CREATE TEMP TABLE times AS SELECT generate_series(timestamp'""" + startDateInclStr + """', \
                                                           timestamp'""" + endDateInclStr + "', '" + str(args.obsPeriodSec) + " seconds') as t"""
print(sql)
windb2.curs.execute(sql)
                                                           
# Get the obs data at the frequency of the obs data, rounding to the nearest observation period
sql = """SELECT times.t at time zone 'UTC' at time zone '""" + args.plotTimeZone + """' as t_plot_tz, times.t as t,
                speed*""" + str(knotConversion) + """, winddir(direction)
         FROM times LEFT JOIN 
             (SELECT date_round(t at time zone 'UTC','""" + str(args.obsPeriodSec) + """ second') as t_round, * 
              FROM wind_""" + str(obsDomainKey) + """
              WHERE t at time zone 'UTC'>=timestamp'""" + startDateInclStr + """' AND
                    t at time zone 'UTC'<=timestamp'""" + endDateInclStr + """' AND
                    height=""" + str(args.obsHeight) + """) as obs ON times.t=obs.t_round"""
print(sql)
windb2.curs.execute(sql)
obsData = numpy.array(windb2.curs.fetchall())

# Get the WRF data at the frequency of the obs data
# Convert the UTC TIME ZONE to the desired TIME ZONE
sql = """SELECT times.t at time zone 'UTC' at time zone '""" + args.plotTimeZone + """' as t_plot_tz, times.t as t,
                speed*""" + str(knotConversion) + """, winddir(direction)
         FROM times LEFT JOIN
             (SELECT *
              FROM wind_""" + str(args.wrfDomainKey) + """
              WHERE t at time zone 'UTC'>=timestamp'""" + startDateInclStr + """' AND 
                    t at time zone 'UTC'<=timestamp'""" + endDateInclStr + """' AND 
                    height=""" + args.wrfHeight + wrfKeyNearObsSql + """) as w
              ON times.t=w.t"""
print(sql)
windb2.curs.execute(sql)
wrfData = numpy.array(windb2.curs.fetchall())

# Make sure there were some results to plot
if obsData.size == 0 or wrfData.size == 0:
    print("No data to plot.  Exiting...")
    sys.exit(-1)

# Create the plot
fig1 = plt.figure(figsize=(12,3))
fig1.canvas.set_window_title('Obs: ' + str(args.obsHeight) + ' m, ' + 'WRF: ' + str(args.wrfHeight) + ' m,' + startDateInclStr + ' ' + endDateInclStr)
ax1 = fig1.add_subplot(111)
ax1.set_title("Forecast vs Obs at " + args.obsName.upper() + ", z={" + 'WRF: ' + str(args.wrfHeight) + ' m, ' + 'Obs: ' + str(args.obsHeight) + ' m} AGL')
ax1.set_xlabel('Time: ' + args.plotTimeZone, fontsize='medium')
if knotConversion == 1:
  ax1.set_ylim((0,10))
  ax1.set_ylabel('wind speed [$\mathrm{ms^{-1}}$]', fontsize='medium')
else:
  ax1.set_ylim((0,35))
  ax1.set_ylabel('wind speed [knots]', fontsize='medium')
fig1.autofmt_xdate()
heightCount = 1
        
# Create the moving average
if int(args.obsPeriodSec) < 360:
  movingAvg = movingAverageFromMovingWindow(numpy.array(plot.none2NaN(obsData[:,2]),dtype=numpy.float), 360, 0.05)
else:
  # No moving average required if the obsPeriodSec is >= 360 s
  movingAvg = numpy.array(plot.none2NaN(obsData[:,2]))
  movingAvg = ma.masked_where(numpy.isnan(movingAvg), movingAvg)

# Masks for the directions annotations, where the data are above 2.5 knots (above "calm and variable")
wrfMask = numpy.array(wrfData[:,2], dtype=numpy.float)>=2.5/1.94384
obsMask = numpy.logical_and(wrfMask, numpy.array(obsData[:,2], dtype=numpy.float)>=2.5/1.94384)

# Plot the obs data and moving average
if int(args.obsPeriodSec) < 360:
    ax1.plot_date(obsData[:,0],[obsMask],
                  obsData[:,2][obsMask],'-',alpha=0.2)
    ax1.plot_date(obsData[:,0],movingAvg,'-', color='green')
else:
    ax1.plot_date(obsData[:,0][obsMask],obsData[:,2][obsMask],'-', color='green')

# Plot the WRF data
ax1.plot_date(wrfData[:,0][wrfMask],
              wrfData[:,2][wrfMask],
              '-.', linewidth=3.0, color='red')

# Annotate the WRF and obs time series if a outputLong-term average
if int(args.obsPeriodSec) >= 360:
  
  # Get rid of the first directions because the obscure the y-axis text
  wrfData[0,3] = ''
  obsData[0,3] = ''

  # Label WRF data
  for x, y, label in zip(mdates.date2num(wrfData[:,0][wrfMask]),
                       wrfData[:,2][wrfMask],
                       wrfData[:,3][wrfMask]):
      ax1.annotate(label, xy=(x,y), color='red', ha='center')
  
  # Label obs data
  for x, y, label in zip(mdates.date2num(obsData[:,0][obsMask]),
                       obsData[:,2][obsMask],
                       obsData[:,3][obsMask]):
      ax1.annotate(label, xy=(x,y), color='black', ha='center')

# Show only hour and minute on the x-axis
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Save the figure to file
# plt.show()
outputName = 'wind-speed-at-' + args.obsName + '-windb-' + args.dbName + '-wrf-dom-' + str(args.wrfDomainKey) + '-wrf-height-' + args.wrfHeight + 'm-' + \
              re.sub(' ','-',startDateInclStr) + '-thru-' + re.sub(' ','-',endDateInclStr)
plt.savefig(outputName + '.svg',dpi=150,bbox_inches='tight')

# Calculate error statistic and write out to file
statsFile = open(outputName + '.tex','w')
commonDataPoints = numpy.logical_and(numpy.array(wrfData[:,2],dtype=numpy.bool),movingAvg>=0)
wrfMinusMovingAvg = numpy.array(wrfData[:,2][commonDataPoints] - movingAvg[commonDataPoints],dtype=numpy.double)
rmse = numpy.sqrt(numpy.sum(numpy.power(wrfMinusMovingAvg,2)/wrfMinusMovingAvg.shape[-1]))
print('Start time: ', startDateInclStr, '\\newline', file=statsFile)
print('End time: ', endDateInclStr, '\\newline', file=statsFile)
print('RMSE computed with ', wrfData[:,2][commonDataPoints].shape[-1], ' points.\\newline', file=statsFile)
print('RMSE=', format(rmse, '.2f'), '$ms^{-1}$', '\\newline', file=statsFile)
print('STDDEV\_OBS HIGH FREQ=', format(numpy.std(numpy.array(obsData[:,2],dtype=numpy.float)), '.2f'), '$ms^{-1}$\\newline', file=statsFile)
if float(args.obsPeriodSec) < 360:
  print('STDDEV\_OBS MOV AVG=', format(numpy.std(movingAvg[movingAvg>=0]), '.2f'), '$ms^{-1}$\\newline', file=statsFile)
print('STDDEV\_WRF=', format(numpy.std(wrfData[:,2][numpy.array(wrfData[:,2],dtype=numpy.bool)]), '.2f'), '$ms^{-1}$\\newline', file=statsFile)
print('STDDEV COMMON POINTS=', format(numpy.std(wrfData[:,2][commonDataPoints]), '.2f'), '$ms^{-1}$\\newline', file=statsFile)
print('MEAN\_OBS HIGH FREQ=', format(numpy.mean(numpy.array(obsData[:,2],dtype=float)), '.2f'), '$ms^{-1}$\\newline', file=statsFile)
print('MEAN\_WRF=', format(numpy.mean(wrfData[:,2][numpy.array(wrfData[:,2],dtype=numpy.bool)]), '.2f'), '$ms^{-1}$', file=statsFile)
statsFile.close()
