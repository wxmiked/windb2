#
#
# Mike Dvorak
# Stanford University
# dvorak@stanford.edu
#
# Created: 2010-11-22
# Modified: 2012-04-30
#
#
# Description: This library has several utility functions that are
# useful for doing error calculations with WRF and offshore buoys.
#

import datetime
import sys

def findBuoysInProximityToWRFPoints(wrfDomainNum, curs):
  """
  findBuoysInProximityToWRFPoints returns a 2D array with WRF point 
  geomkey, buoy point geomkey, buoy domain num, and distance from that
  point.
  """

  # Create a empty list to return with the wrfkey, buoydomain, buoykey, distmeters
  closestWRFPointsToBuoys = []

  # Get all the buoys keys in the database
  buoyKeySql = "SELECT h.key AS buoykey, h.domainkey AS buoydomain FROM horizgeom h, domain d WHERE h.domainkey=d.key AND (d.datasource='National Data Buoy Center' OR d.datasource='National Climatic Data Center')"
  curs.execute(buoyKeySql)
  buoykeys = curs.fetchall()

  # Get the resolution of the WRF domian to use as a distance cutoff
  sql = "SELECT resolution FROM domain WHERE key=" + str(wrfDomainNum)
  curs.execute(sql)
  wrfDomainResolution = curs.fetchone()[0]

  # Find the closest wrfgeom to the buoygeom, putting a limit of twice the resolution
  for buoykey in buoykeys:
    closestWRFKeySql = "SELECT m.key AS wrfkey, st_distance_sphere(st_transform(m.geom,4326), st_transform(b.geom,4326)) AS dist \
                        FROM (SELECT * FROM horizgeom WHERE key=" + str(buoykey[0]) + ") b, \
                             (SELECT * FROM horizgeom WHERE domainkey=" + str(wrfDomainNum) + ") m \
                             WHERE st_distance_sphere(st_transform(m.geom,4326), st_transform(b.geom,4326))<=" + str(wrfDomainResolution) + " \
                            ORDER BY dist LIMIT 1"
    curs.execute(closestWRFKeySql)
    temp = curs.fetchone()

    # Make sure we got a result
    if not(temp):
      continue

    # print 

    # Add the results to the array to return
    closestWRFPointsToBuoys.append([temp[0], buoykey[1], buoykey[0], temp[1]])

  return closestWRFPointsToBuoys
   
def findWRFPointInProximityToBuoy(buoyDomainKey, wrfDomainNum, curs):
  """
  findBuoysInProximityToWRFPoints returns a WRF point geomkey and distance [m] from that point.
  """

  # Create a empty list to return with the wrfkey, buoydomain, buoykey, distmeters
  closestBuoyPointToBuoys = []

  # Find the closest wrfgeom to the buoygeom, putting a limit of twice the resolution
  sql = "SELECT m.key AS wrfkey, st_distance_sphere(st_transform(m.geom,4326), st_transform(b.geom,4326)) AS dist \
                    FROM (SELECT * FROM horizgeom WHERE domainkey=" + str(buoyDomainKey) + ") b, \
                         (SELECT * FROM horizgeom WHERE domainkey=" + str(wrfDomainNum) + ") m \
                        ORDER BY dist LIMIT 1"
  curs.execute(sql)
  temp = curs.fetchone()
  
  # Debug
  print(sql)

  # Make sure we got a result
  if temp == None:
      sys.stderr.write("ERROR: No buoys returned.")
      sys.exit(-1)
  elif temp[1] > 10000:
      sys.stderr.write("WARNING WARNING: distance to WRF point is exceptionally large.  Closest WRF point is " + str(temp[1]) + " m away.")

  return temp[0],temp[1]


def findObservationalDomainsInLatitudinalBand(minLatitude, maxLatitude, curs):
  """
  Returns all observational data in the database that are within the
  longitudinal band specified.  Also asserts that mix < max.
  """
    
  # Make sure the min lat is less than the max
  assert minLatitude < maxLatitude;

  # Create a empty list to return with the wrfkey, buoydomain, buoykey, distmeters
  buoysInLatBand = []

  # Get all the buoys keys in the database
  buoyKeySql = "SELECT h.domainkey AS buoydomain \
                FROM horizgeom h, domain d \
                WHERE h.domainkey=d.key \
                    AND (d.datasource='National Data Buoy Center' OR d.datasource='National Climatic Data Center') \
                    AND st_y(h.geom) >= " + str(minLatitude) + " AND st_y(h.geom) <= " + str(maxLatitude);
  curs.execute(buoyKeySql)
  buoyKeys = curs.fetchall()

  # Make sure we at least got one key
  if len(buoyKeys) > 1:
    return buoyKeys
  else:
    print("ERROR: No buoy keys were found in that region.")
    return None



def calculateBuoyErrorForPeriod(conn, wrfDomain, wrfKey, wrfHeight, buoyDomain, buoyRangeLowHeight, buoyRangeHighHeight, startDateIncl, endDateExcl, noteForRecord):
    # Get the cursor for the connection
    curs = conn.cursor()
        
    # Get the number of WRF data available at this same time period
    checkwrfDataExists = "SELECT count(*) FROM wind_" + str(wrfDomain) + " m WHERE m.height=" + str(wrfHeight) + " AND m.geomkey=" + str(wrfKey) + \
                                 " AND date_part('month',m.t)=" + str(startDateIncl.month) + " AND date_part('year',m.t)=" + str(startDateIncl.year)
    curs.execute(checkwrfDataExists)
    print("Ran this query: ", curs.query)
    countOfWrfData = curs.fetchone()[0]
    print("fetchone()[0]=", countOfWrfData)
    if countOfWrfData == 0:
        print("WARNING: There were no WRF data in ", str(startDateIncl.year), "-", str(startDateIncl.month), " wrf domain ", str(wrfDomain), " that matched")
        return 0
    
    # Make sure there is at least some data for this buoy during this particular month
    # Otherwise you get a division by zero
    checkBuoyDataExists = "SELECT count(*) FROM wind_" + str(buoyDomain) + " m WHERE m.height>=" + str(buoyRangeLowHeight) + " AND m.height<=" + str(buoyRangeHighHeight) + \
                                 " AND date_part('month',m.t)=" + str(startDateIncl.month) + " AND date_part('year',m.t)=" + str(startDateIncl.year)
    curs.execute(checkBuoyDataExists)
    print("Ran this query: ", curs.query)
    countOfBuoyData = curs.fetchone()[0]
    print("fetchone()[0]=", countOfBuoyData)
    if countOfBuoyData == 0:
        print("WARNING: There were no buoy data in ", str(startDateIncl.year), "-", str(startDateIncl.month), " buoy domain ", str(buoyDomain), " that matched")
        return 0
    
    # Create the error query
    errorQuery = """INSERT INTO winderror (wrfdomain, buoydomain, year, month, 
                                           wrfAvg, wrfAvg_u, wrfAvg_v,
                                           wrfStddev, wrfStddev_u, wrfStddev_v, 
                                           buoyAvg, buoyAvg_u, buoyAvg_v,
                                           buoyStddev, buoyStddev_u, buoyStddev_v,  
                                           nge, nb, 
                                           rmse, rmse_u, rmse_v, 
                                           bias, bias_u, bias_v, 
                                           count, note, created) """ + \
                          "SELECT " +  str(wrfDomain) + ", " + str(buoyDomain) + ", " + \
                          str(startDateIncl.year) + ", " + str(startDateIncl.month) + ", " + \
                          """avg(m.speed) AS wrfAvg, 
                          avg(U(m.speed,m.direction)) AS wrfAvg_u, 
                          avg(V(m.speed,m.direction)) AS wrfAvg_v,
                          stddev(m.speed) AS wrfStddev,
                          stddev(U(m.speed,m.direction)) AS wrfStddev_u,
                          stddev(V(m.speed,m.direction)) AS wrfStddev_v,
                          avg(b.speed) AS buoyAvg, 
                          avg(U(b.speed,b.direction)) AS buoyAvg_u, 
                          avg(V(b.speed,b.direction)) AS buoyAvg_v,
                          stddev(b.speed) AS buoyStddev,
                          stddev(U(b.speed,b.direction)) AS buoyStddev_u,
                          stddev(V(b.speed,b.direction)) AS buoyStddev_v,
                          sum(nge(m.speed, b.speed::real))/count(*) AS nge,\
                          sum(nb(m.speed, b.speed::real))/count(*) AS nb,
                          sqrt(sum(mse(m.speed, b.speed::real))/count(*)) AS rmse,\
                          sqrt(sum(mse(U(m.speed,m.direction)::real, U(b.speed,b.direction)::real))/count(*)) AS rmse_u,
                          sqrt(sum(mse(V(m.speed,m.direction)::real, V(b.speed,b.direction)::real))/count(*)) AS rmse_v,
                          sum(bias(m.speed, b.speed::real))/count(*) AS bias,
                          sum(bias(U(m.speed,m.direction)::real, U(b.speed,b.direction)::real))/count(*) AS bias_u,
                          sum(bias(V(m.speed,m.direction)::real, V(b.speed,b.direction)::real))/count(*) AS bias_v, 
                          count(*) AS COUNT,""" + \
                          "'" + noteForRecord + "', " + \
                          "now() \
                      FROM wind_" + str(wrfDomain) + " m,wind_" + str(buoyDomain) + " b WHERE m.geomkey=" + str(wrfKey) + " AND \
                      b.height>=" + str(buoyRangeLowHeight) + " AND b.height<=" + str(buoyRangeHighHeight) + " AND m.height=" + str(wrfHeight) + " AND \
                      date_part('month',m.t)=" + str(startDateIncl.month) + " AND date_part('year',m.t)=" + str(startDateIncl.year) + " \
                      AND b.speed > 1.0 AND b.t=m.t RETURNING count, bias, bias_u, bias_v"

    # Execute the query
    print("Running this query:", errorQuery)
    curs.execute(errorQuery)
    
    # DebugfindWRFPointNearLongLat
    #print "Ran this query: ", curs.query
    print("Got this status msg: ", curs.statusmessage)

    # Get the count and biases to calculate the unbiased RMSE
    result = curs.fetchall()
    count = result[0][0]
    bias = str(result[0][1])
    bias_u = str(result[0][2])
    bias_v = str(result[0][3])

    # Exit if there were no matches found
    # WARNING: Check and see if the NDBC STDMET output times are at 50 minutes past the hour, instead of the
    # expect 00 minutes. Used CWIND data for the Principle Power project to avoid this problem.
    if count == 0:
        return 0 

    # Commit all of the changes for that month
    conn.commit()

    # Calculate the unbiased RMSE for the buoy
    # Note: We could hypothetically do this in one query but PostgreSQL does not currently
    # have this functionality implemented.
    unbiasedQuery = "SELECT sqrt(sum(mse(m.speed, b.speed::real+" + bias + "::real))/count(*)) AS rmseub, \
                         sqrt(sum(mse(U(m.speed,m.direction)::real+" + bias_u + "::real, \
                              U(b.speed,b.direction)::real))/count(*)) AS rmseub_u, \
                         sqrt(sum(mse(V(m.speed,m.direction)::real+" + bias_v + "::real, \
                              V(b.speed,b.direction)::real))/count(*)) AS rmseub_v \
                  FROM wind_" + str(wrfDomain) + " m,wind_" + str(buoyDomain) + " b WHERE m.geomkey=" + str(wrfKey) + " AND \
                              b.height>=" + str(buoyRangeLowHeight) + " AND b.height<=" + str(buoyRangeHighHeight) + " AND m.height=" + str(wrfHeight) + " AND \
                              date_part('month',m.t)=" + str(startDateIncl.month) + " AND date_part('year',m.t)=" + str(startDateIncl.year) + " \
                              AND b.speed > 1.0 AND b.t=m.t"
    
    # Debug
    print(unbiasedQuery)

    # Get the unbiased results
    # Execute the query
    curs.execute(unbiasedQuery)
    
    # Debug
    print("Ran this query: ", curs.query)
    print("Got this status msg: ", curs.statusmessage)

    # Get the count and biases to calculate the unbiased RMSE
    result = curs.fetchall()
    rmseub = str(result[0][0])
    rmseub_u = str(result[0][1])
    rmseub_v = str(result[0][2])
    updateUnbiasedQuery = "UPDATE winderror SET (rmseub, rmseub_u, rmseub_v) = \
                           (" + rmseub + "," + rmseub_u + "," + rmseub_v + ") \
                  WHERE wrfdomain=" + str(wrfDomain) + " AND buoydomain=" + str(buoyDomain) + " AND \
                           year=" + str(startDateIncl.year) + " AND month=" + str(startDateIncl.month) + " AND \
                           note='" + noteForRecord + "' \
                  RETURNING count"

    # Execute the query
    curs.execute(updateUnbiasedQuery)
    
    # Debug
    #print "Ran this query: ", curs.query
    print("Got this status msg: ", curs.statusmessage)

    # Commit all of the changes for that month
    conn.commit()

    # Return percent complete
    return float(count)/float(countOfWrfData)*100

# NOTE: This is nearly identical to the original "calculateBuoyErrorForPeriod" function, just tweaked to calculate the day of the run.
def calculateBuoyErrorForDayOfRun(conn, wrfDomain, wrfKey, wrfHeight, buoyDomain, buoyRangeLowHeight, buoyRangeHighHeight, dayForCalc, dayOfRun, noteForRecord):
    # Get the cursor for the connection
    curs = conn.cursor()
    
    # Make sure there is at least some data for this buoy during this particular month
    # Otherwise you get a division by zero
    checkBuoyDataExists = "SELECT count(*) FROM wind_" + str(buoyDomain) + " m WHERE m.height>=" + buoyRangeLowHeight + " AND m.height<=" + buoyRangeHighHeight + \
                                " AND m.t::date = date'" + dayForCalc.isoformat() + "'"
    curs.execute(checkBuoyDataExists)
    #print "Ran this query: ", curs.query
    countOfBuoyData = curs.fetchone()[0]
    print("fetchone()[0]=", countOfBuoyData)
    if countOfBuoyData == 0:
        print("WARNING: There were no buoy data in ", dayForCalc.isoformat(), "-", " buoy domain ", str(buoyDomain), " that matched")
        return 0
    
# Create the error query
    errorQuery = """INSERT INTO winderrorbyday (wrfdomain, buoydomain, day, runDay, 
                                           wrfAvg, wrfAvg_u, wrfAvg_v,
                                           wrfStddev, wrfStddev_u, wrfStddev_v, 
                                           buoyAvg, buoyAvg_u, buoyAvg_v,
                                           buoyStddev, buoyStddev_u, buoyStddev_v,  
                                           nge, nb, 
                                           rmse, rmse_u, rmse_v, 
                                           bias, bias_u, bias_v, 
                                           count, note, created) """ + \
                          "SELECT " +  str(wrfDomain) + ", " + str(buoyDomain) + ", " + \
                          "date '" + dayForCalc.strftime("%Y-%m-%d") + "', " + str(dayOfRun) + ", " + \
                          """avg(m.speed) AS wrfAvg, 
                          avg(U(m.speed,m.direction)) AS wrfAvg_u, 
                          avg(V(m.speed,m.direction)) AS wrfAvg_v,
                          stddev(m.speed) AS wrfStddev,
                          stddev(U(m.speed,m.direction)) AS wrfStddev_u,
                          stddev(V(m.speed,m.direction)) AS wrfStddev_v,
                          avg(b.speed) AS buoyAvg, 
                          avg(U(b.speed,b.direction)) AS buoyAvg_u, 
                          avg(V(b.speed,b.direction)) AS buoyAvg_v,
                          stddev(b.speed) AS buoyStddev,
                          stddev(U(b.speed,b.direction)) AS buoyStddev_u,
                          stddev(V(b.speed,b.direction)) AS buoyStddev_v,
                          sum(nge(m.speed, b.speed::real))/count(*) AS nge,\
                          sum(nb(m.speed, b.speed::real))/count(*) AS nb,
                          sqrt(sum(mse(m.speed, b.speed::real))/count(*)) AS rmse,\
                          sqrt(sum(mse(U(m.speed,m.direction)::real, U(b.speed,b.direction)::real))/count(*)) AS rmse_u,
                          sqrt(sum(mse(V(m.speed,m.direction)::real, V(b.speed,b.direction)::real))/count(*)) AS rmse_v,
                          sum(bias(m.speed, b.speed::real))/count(*) AS bias,
                          sum(bias(U(m.speed,m.direction)::real, U(b.speed,b.direction)::real))/count(*) AS bias_u,
                          sum(bias(V(m.speed,m.direction)::real, V(b.speed,b.direction)::real))/count(*) AS bias_v, 
                          count(*) AS COUNT,""" + \
                          "'" + noteForRecord + "', " + \
                          "now() \
                      FROM wind_" + str(wrfDomain) + " m,wind_" + str(buoyDomain) + " b WHERE m.geomkey=" + str(wrfKey) + " AND \
                      b.height>=" + buoyRangeLowHeight + " AND b.height<=" + buoyRangeHighHeight + " AND m.height=" + wrfHeight + " AND \
                      m.t::date = date'" + dayForCalc.isoformat() + "' \
                      b.speed > 1.0 RETURNING count"

    # Execute the query
    curs.execute(errorQuery)
    
    # Debug
    #print "Ran this query: ", curs.query
    print("Got this status msg: ", curs.statusmessage)

    # Get the results
    count = curs.fetchone()[0]

    # Commit all of the changes for that month
    conn.commit()
    return count

def findWRFPointNearLongLat(wrfDomainNum, longitude, latitude, curs):
  """
  Finds WRF domain points near WRF geometries, returning a geomkey and distance [m] from that point.

  Return distance from nearest point and the units
  """

  # Find the closest wrfgeom to the buoygeom, putting a limit of twice the resolution
  sql = "SELECT m.key AS wrfkey, st_distancesphere(st_transform(m.geom,4326), st_geomfromtext('POINT(" + str(longitude) + " " + str(latitude) + ")',4326)) AS dist \
                    FROM (SELECT * FROM horizgeom WHERE domainkey=" + str(wrfDomainNum) + ") m \
                        ORDER BY dist LIMIT 1"
  curs.execute(sql)
  temp = curs.fetchone()
  
  # Make sure we got a result
  if temp == None:
      print("ERROR: No WRF points returned.", file=sys.stderr)
      sys.exit(-1)
  elif temp[1] > 10000:
      print("WARNING WARNING: distance to WRF point is exceptionally large.  Closest WRF point is {} m away.".format(temp[1]), file=sys.stderr)

  return temp[0], temp[1]
  
