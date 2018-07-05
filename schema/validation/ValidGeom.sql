CREATE TABLE ValidGeom (

  key SERIAL PRIMARY KEY,
  station VARCHAR(40) UNIQUE

);

--Add the geometry column, setting the SRID to zero to allow for mixed SRIDs
SELECT AddGeometryColumn('', 'validgeom', 'geom', 0, 'POINT', 2);
