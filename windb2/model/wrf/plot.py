#
# Mike Dvorak
# Stanford University
# dvorak@stanford.edu
#
# Created: 2010-10-14
# Modified: 2011-10-06
#
#
# Description: This library makes various plots for WRF output data
# using the NCAR PyNGL Python library.
#
import logging

import matplotlib

from windb2 import util
from windb2.util import none2NaN


def plotBuoyWRFWindSpeedPerMonth(yearNum, monthNum, timeDeltaMinutes, wrfDomain, wrfGeomKey, wrfHeight, buoyDomain, curs):
   """Creates a hourly wind speed average and power curve plot for a particular wind farm"""

   import matplotlib.pyplot as plt
   import numpy

   # Execute the statement to get the avg winds
   windBuoyDataSql = """SELECT t, m_u, m_v, b_u, b_v
                        FROM (SELECT t, U(speed,direction) as m_u, V(speed,direction) as m_v
                              FROM wind_""" + str(wrfDomain) + """
                              WHERE geomkey=""" + str(wrfGeomKey) + """ AND 
                                    height=""" + str(wrfHeight) + """ AND 
                                    date_part('month', t)=""" + str(monthNum) + """ AND 
                                    date_part('year', t)=""" + str(yearNum) + """) m
                        LEFT JOIN
                             (SELECT t, U(speed,direction) as b_u, V(speed,direction) as b_v
                              FROM wind_""" + str(buoyDomain) + """
                              WHERE date_part('month', t)=""" + str(monthNum) + """ AND 
                                    date_part('year', t)=""" + str(yearNum) + """) b 
                        USING (t) 
                        ORDER BY t;"""
   logging.debug("Executing the statement: {}".format(windBuoyDataSql))
   curs.execute(windBuoyDataSql)
   queryResult = curs.fetchall()
   queryResult = numpy.array(queryResult)

   # Divide up the data
   time = queryResult[:,0]
   wrfBuoyWind = numpy.array(queryResult[:,1:],dtype=numpy.float)
   
   # Get rid of the None because they cannot be used in masked arrays, convert to NaNs
   for i in range(wrfBuoyWind.shape[1]):
       wrfBuoyWind[:,i] = none2NaN(wrfBuoyWind[:, i])

   # Get the height of the buoy data (and assume they are all the same from this location)
   buoyHeightSql = "SELECT DISTINCT(height) FROM wind_" + str(buoyDomain)
   curs.execute(buoyHeightSql)
   buoyHeight = curs.fetchone()[0]
   
   # Debug
   print("wrfBuoyWind=", wrfBuoyWind)

   #
   # Set up the resources of the wind speed plots
   #
   fig = plt.figure()
   ax = fig.add_subplot(411)

   #
   # Get the name of the buoy
   #
   curs.execute("SELECT name FROM domain WHERE key=" + str(buoyDomain))
   buoyName = str(curs.fetchone()[0]).upper()
   plt.title(buoyName + ", " + str(yearNum) + "-" + str(monthNum))
   
   # Set the output filename
   filename = "wrf-wind-domain-" + str(wrfDomain) + "-buoy-" + buoyName + "-" + str(yearNum) + "-" + str(monthNum)


   # Data reduction on the plots in case we have a lot of data
   obsMarkEvery = int(60/timeDeltaMinutes)

   # MAKE THE PLOTS FOR THE U-DIRECTION
   ax.set_ylabel("u-wind (m/s)",size='small')
   xVals = numpy.arange(wrfBuoyWind.shape[0])
   ax.axhline(y=0,linewidth=0.5,linestyle='--',color='b')
   ax.plot_date(matplotlib.dates.date2num(time), wrfBuoyWind[:,0],
                linewidth=1,linestyle='-',marker=None,color='black',label='WRF(' + str(wrfHeight) + ' m)',
                markevery=2)
   ax.plot_date(matplotlib.dates.date2num(time)[numpy.isfinite(wrfBuoyWind[:,2])], wrfBuoyWind[:,2][numpy.isfinite(wrfBuoyWind[:,2])],
                linewidth=1,linestyle='-',marker=None,color='orange',label='Obs.(' + str(buoyHeight) + ' m)',
                markevery=obsMarkEvery)
   ax.set_ylim((-10,10))
   ax.legend(loc='upper left')
   ax.legend(loc=(0,0.5))

   # Set the legend font to small
   leg = plt.gca().get_legend()
   leg.draw_frame(False)
   ltext  = leg.get_texts()
   llines = leg.get_lines()
   plt.setp(ltext, fontsize='xx-small')
   plt.setp(llines, linewidth=2.0)

   # MAKE THE PLOTS FOR THE V-DIRECTION
   ax = fig.add_subplot(412,sharex=ax)
   ax.set_ylabel("v-wind (m/s)",size='small')
   ax.axhline(y=0,linewidth=0.5,linestyle='--',color='b')
   ax.plot_date(matplotlib.dates.date2num(time), wrfBuoyWind[:,1],
                linewidth=1,linestyle='-',marker=None,color='black',label='WRF(' + str(wrfHeight) + ' m)',
                markevery=2)
   ax.plot_date(matplotlib.dates.date2num(time)[numpy.isfinite(wrfBuoyWind[:,3])], wrfBuoyWind[:,3][numpy.isfinite(wrfBuoyWind[:,3])],
                linewidth=1,linestyle='-',marker=None,color='green',label='Obs.(' + str(buoyHeight) + ' m)',
                markevery=obsMarkEvery)
   ax.set_ylim((-10,10))
   ax.legend(loc='upper left')
   ax.legend(loc=(0,0.5))

   # Set the legend font to small
   leg = plt.gca().get_legend()
   leg.draw_frame(False)
   ltext  = leg.get_texts()
   llines = leg.get_lines()
   plt.setp(ltext, fontsize='xx-small')
   plt.setp(llines, linewidth=2.0)

   # MAKE THE PLOTS FOR THE SPEED
   speedWrf = util.speed(wrfBuoyWind[:,0], wrfBuoyWind[:,1])
   speedObs = util.speed(wrfBuoyWind[:,2], wrfBuoyWind[:,3])
   ax = fig.add_subplot(413,sharex=ax)
   ax.set_ylabel("wind (m/s)",size='small')
   ax.plot_date(matplotlib.dates.date2num(time),speedWrf,
                linewidth=1,linestyle='-',marker=None,color='black',label='WRF(' + str(wrfHeight) + ' m)')
   ax.plot_date(matplotlib.dates.date2num(time)[numpy.isfinite(speedObs)],speedObs[numpy.isfinite(speedObs)],
           linewidth=1,linestyle='-',marker=None,color='red',label='Obs.(' + str(buoyHeight) + ' m)',
           markevery=obsMarkEvery)
   ax.set_ylim((0,15))
   ax.legend(loc='upper left')
   ax.legend(loc=(0,0.5))

   # Set the legend font to small
   leg = plt.gca().get_legend()
   leg.draw_frame(False)
   ltext  = leg.get_texts()   # Set the location of the tick marks
   llines = leg.get_lines() 
   plt.setp(ltext, fontsize='xx-small')
   plt.setp(llines, linewidth=2.0)
   
   # MAKE THE PLOTS FOR ABS ERROR - masked where the obs are NaN
   ax = fig.add_subplot(414,sharex=ax)
   ax.set_ylabel("abs. err. (m/s)",size='small')
   ax.plot_date(matplotlib.dates.date2num(time)[numpy.isfinite(speedObs)],numpy.abs(speedWrf[numpy.isfinite(speedObs)] -
                                                                                    speedObs[numpy.isfinite(speedObs)]),
                linestyle='-',marker=None,color='red',label='speed-error',alpha=0.6)
   ax.set_ylim((0,12))
   ax.legend(loc='upper left')

   # Set the legend font to small
   leg = plt.gca().get_legend()
   leg.draw_frame(False)
   ltext  = leg.get_texts()
   llines = leg.get_lines()
   plt.setp(ltext, fontsize='xx-small')
   plt.setp(llines, linewidth=2.0)

   # # Add an x-axis to the bottom
   # xLabels = [0,7,14,21,28]
   # xLabelsMinor = numpy.arange(31)*24*60./timeDeltaMinutes
   # ax.set_xticks(numpy.array(xLabels)*24*60/timeDeltaMinutes)
   # ax.set_xticks(xLabelsMinor,minor=True)
   # ax.set_xlabel("day of month")
   # ax.set_xticklabels(xLabels)
   # ax.set_xlim(0,numpy.max(xVals))
   fig.autofmt_xdate()

   # Save the plot to a file
   plt.savefig(filename + '.png',bbox_inches='tight')
   plt.savefig(filename + '.eps',bbox_inches='tight')


#
# Creates histogram plots of any given time series.  Also plots the best fitting
# Rayleigh distribution to the data.
#
# timeSeriesData is a 1D array with values to plot
# nBins is the number of bins to be displayed
# title is a string for the graph title
def createHistogramForTimePeriod(timeSeriesData, nBins, barColor, title, fileName):

    import numpy as np
    import matplotlib.pyplot as plt

    # Some constants used through
    xMin, xMax = 0.0, 20
    xDelta = (xMax-xMin)/(nBins*4)

    ###mu, sigma = 100, 15
    ###x = mu + sigma*np.random.randn(10000)

    # Set up the resources of the wind speed plots
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel("day of month")
    ax.set_ylabel("wind speed (m/s)")
    

    # the histogram of the data
    n, bins, patches = plt.hist(timeSeriesData, bins=nBins, normed=1, facecolor=barColor, alpha=0.75)

    # Add Raleigh distribution line (from Masters, 2005, pp. 344-5)
    meanBuoy = np.mean(timeSeriesData)
    stdDevBuoy = np.std(timeSeriesData)
    print("buoyMean=", meanBuoy)
    k = (stdDevBuoy / meanBuoy)**-1.086 # k (from Jiang et al., 2008, pp. 4)
    c = 1.128 * meanBuoy
    x = np.arange(xMin, 1.25*xMax, xDelta)
    raleighPDF = np.pi * x / (2 * meanBuoy**2) * np.exp(-np.pi/4 * (x / meanBuoy)**2)

    # add a 'best fit' line
    l = plt.plot(x, raleighPDF, 'k--', linewidth=3)

    ax.set_xlabel('wind speed (m/s)')
    ax.set_label('probability')
    plt.title(title + ' $\mathrm{c=' + str(round(c,2)) + ", k=" + str(round(k,2)) + \
              ", \sigma=" + str(round(stdDevBuoy,2)) + \
              ", \\bar u=" + str(round(meanBuoy,2)) + "}$")
    ax.axis([0, xMax, None, None])
    ax.grid(True)

    # save the figure
    plt.savefig(fileName)
    plt.close()

    #plt.show()

