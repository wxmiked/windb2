CREATE TABLE HorizGeom ( 

  key SERIAL PRIMARY KEY ,
  domainKey int ,
  x smallint ,
  y smallint

);

--Add the geometry column, setting the SRID to zero to allow for mixed SRIDs
SELECT AddGeometryColumn('', 'horizgeom', 'geom', 0, 'POINT', 2);

CREATE INDEX horizgeom_index on horizgeom(x,y);

