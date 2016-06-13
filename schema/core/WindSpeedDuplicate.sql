CREATE TABLE WindSpeed_Duplicate ( 

  domainkey INT REFERENCES Domain(key),
  geomkey INT REFERENCES HorizWindGeom(key) ,
  t timestamp ,
  windspeed float ,
  height int 
);

