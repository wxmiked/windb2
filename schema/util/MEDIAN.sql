CREATE OR REPLACE FUNCTION r_median(_float8) RETURNS float AS '
  median(arg1)
' LANGUAGE 'plr';

CREATE AGGREGATE median (
  sfunc = plr_array_accum,
  basetype = float8,
  stype = _float8,
  finalfunc = r_median
);   


CREATE OR REPLACE FUNCTION r_iqr(_float8) RETURNS float AS '
  IQR(arg1)
' LANGUAGE 'plr';

CREATE AGGREGATE iqr (
  sfunc = plr_array_accum,
  basetype = float8,
  stype = _float8,
  finalfunc = r_iqr
);   


