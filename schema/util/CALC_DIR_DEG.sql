CREATE OR REPLACE FUNCTION calc_dir_deg(u FLOAT, v FLOAT)
  RETURNS INT AS 'SELECT (degrees(atan2(u, v))::int + 360) % 360;'
  LANGUAGE SQL
  IMMUTABLE
  RETURNS NULL ON NULL INPUT;