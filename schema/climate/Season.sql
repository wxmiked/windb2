CREATE TABLE Season ( 
  season varchar(30),
  month int,
  UNIQUE (season, month)
);

INSERT INTO season(season, month)  VALUES ('Winter',1);
INSERT INTO season(season, month)  VALUES ('Winter',2);
INSERT INTO season(season, month)  VALUES ('Winter',3);
		  
INSERT INTO season(season, month)  VALUES ('Spring',4);
INSERT INTO season(season, month)  VALUES ('Spring',5);
INSERT INTO season(season, month)  VALUES ('Spring',6);
		  
INSERT INTO season(season, month)  VALUES ('Summer',7);
INSERT INTO season(season, month)  VALUES ('Summer',8);
INSERT INTO season(season, month)  VALUES ('Summer',9);
		  
INSERT INTO season(season, month)  VALUES ('Fall',10);
INSERT INTO season(season, month)  VALUES ('Fall',11);
INSERT INTO season(season, month)  VALUES ('Fall',12);

