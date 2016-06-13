CREATE TABLE WindSpeedNaN ( 

  domainkey INT REFERENCES Domain(key),
  geomkey INT REFERENCES HorizWindGeom(key) ,
  t timestamp ,
  height int 
);

