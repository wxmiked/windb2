CREATE TABLE WindError (

  wrfDomain INT REFERENCES Domain(key),
  buoyDomain INT REFERENCES Domain(key),
  day DATE,
  wrfAvg REAL,
  wrfAvg_u REAL,
  wrfAvg_v REAL,
  wrfStddev REAL,
  wrfStddev_u REAL,
  wrfStddev_v REAL,
  buoyAvg REAL,
  buoyAvg_u REAL,
  buoyAvg_v REAL,
  buoyStddev REAL,
  buoyStddev_u REAL,
  buoyStddev_v REAL,
  nge REAL,
  nb REAL,
  rmse REAL,
  rmse_u REAL,
  rmse_v REAL,
  rmseub REAL,
  rmseub_u REAL,
  rmseub_v REAL,
  bias REAL,
  bias_u REAL,
  bias_v REAL,
  count INT,
  note VARCHAR(1000),
  created TIMESTAMP WITH TIME ZONE

);

