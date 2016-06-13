CREATE FUNCTION SPEED(u double precision, v double precision) RETURNS double precision
  AS 'SELECT sqrt(pow($1,2.0) + pow($2,2.0));'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;
