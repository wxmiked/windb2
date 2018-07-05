CREATE TABLE Domain ( 

  key SERIAL PRIMARY KEY ,
  name VARCHAR(50) ,
  resolution float ,
  units VARCHAR(50) ,
  datasource VARCHAR(50),
  mask VARCHAR(200)

);
ALTER TABLE domain ADD UNIQUE (key);