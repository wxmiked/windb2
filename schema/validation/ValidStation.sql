CREATE TABLE ValidStation (

  key SERIAL PRIMARY KEY,
  station VARCHAR(40) UNIQUE,
  source VARCHAR(40)

);

--Add the geometry column, setting the SRID to zero to allow for mixed SRIDs
SELECT AddGeometryColumn('', 'validstation', 'geom', 0, 'POINT', 2);
