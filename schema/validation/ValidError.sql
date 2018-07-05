-- This is meant to be an abstract schema and inherited by specific variable types (e.g. wind direction, speed, RH, etc...)
CREATE TABLE ValidError (
  fcst_domain INT REFERENCES Domain(key),
  fcst_time TIMESTAMP WITH TIME ZONE,
  fcst_age_hr FLOAT,
  fcst_height FLOAT,
  obs_station VARCHAR(40),
  obs_geomkey INT REFERENCES ValidGeom(key),
  obs_var_name VARCHAR(10),
  obs_height FLOAT,
  obs_source VARCHAR(40),
  obs_time TIMESTAMP WITH TIME ZONE,
  diff FLOAT,
  diff_squared FLOAT,
  created TIMESTAMP WITH TIME ZONE DEFAULT now()
);
