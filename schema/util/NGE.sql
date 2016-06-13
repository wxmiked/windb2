CREATE FUNCTION NGE(predicted real, observed real) RETURNS real 
  AS 'SELECT abs($1 - $2) / $2;'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;
