CREATE TABLE GeoVariable ( 

  domainkey INT REFERENCES Domain(key),
  geomkey INT REFERENCES HorizGeom(key) ,
  t TIMESTAMP WITH TIME ZONE,
  height real,
  UNIQUE (domainkey, geomkey, t, height)
);

CREATE INDEX geomkey_index ON GeoVariable(geomkey);

CREATE INDEX timestamp_index ON GeoVariable(t);

CREATE INDEX geomkey_t_height_index ON GeoVariable(geomkey, t, height);

