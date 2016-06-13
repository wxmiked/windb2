CREATE FUNCTION MSE(predicted double precision, observed double precision) RETURNS double precision
  AS 'SELECT power($1 - $2,2.0);'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;
