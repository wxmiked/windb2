-- This is meant to be an abstract schema and inherited by specific variable types (e.g. wind direction, speed, RH, etc...)
CREATE TABLE ValidError (
  fcst_domain INT REFERENCES Domain(key),
  fcst_time TIMESTAMP WITH TIME ZONE,
  fcst_age_hr FLOAT,
  fcst_height FLOAT,
  fcst_val FLOAT,
  obs_stationkey INT REFERENCES ValidStation(key),
  obs_time TIMESTAMP WITH TIME ZONE,
  obs_height FLOAT,
  obs_val FLOAT,
  created TIMESTAMP WITH TIME ZONE DEFAULT now()
);
