-- Used to go from <=v3.1.9 to 3.2.0+ schemas
-- Adds and populates obs_domain to ValidError tables

-- Rename the column
ALTER TABLE ValidError RENAME COLUMN obs_geomkey TO obs_stationkey;

-- Add the foreign key
ALTER TABLE ValidError ADD FOREIGN KEY (obs_stationkey) REFERENCES ValidStation(key);
