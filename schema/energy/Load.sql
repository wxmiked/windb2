CREATE TABLE Load ( 

  t TIMESTAMP WITH TIME ZONE,
  region varchar(10),
  load_mw real,
  UNIQUE (region, t)
);
