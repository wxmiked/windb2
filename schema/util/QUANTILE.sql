--  2013-11-15: Code from http://iangow.wordpress.com/2012/12/05/using-plr-for-quantiles/
-- Use array_agg(double precision) to create a double precision[] field)

CREATE OR REPLACE FUNCTION r_quantile(double precision[], double precision) 
RETURNS double precision 
AS 'quantile(arg1, arg2, na.rm=TRUE)' 
LANGUAGE plr STRICT;