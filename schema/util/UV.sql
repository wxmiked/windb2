-- Returns the u and v orthogonal components of the wind. Direction is in degrees.
CREATE FUNCTION u(speed real, direction smallint) RETURNS double precision
  AS 'SELECT $1*sin(radians($2))'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;

CREATE FUNCTION v(speed real, direction smallint) RETURNS double precision
  AS 'SELECT $1*cos(radians($2))'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;
