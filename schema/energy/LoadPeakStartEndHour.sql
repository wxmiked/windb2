CREATE TABLE LoadPeakStartEndHour ( 

  region varchar(10),
  year int,
  month int,
  day int,
  median_start time with time zone,
  median_end time with time zone,
  UNIQUE (region, year, month, day)
);
