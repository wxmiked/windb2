CREATE TABLE Bathymetry ( 

  key SERIAL PRIMARY KEY ,
  name VARCHAR(50) ,
  resolution int ,
  resUnits varchar(10),
  datasource VARCHAR(50),
  locationDesc varchar(50)

);
