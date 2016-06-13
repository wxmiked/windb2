-- This power curve was digitized by Mike Dvorak, 2008-12-10 
-- from the REpower 5M product brouchure downloaded from
-- http://www.repower.de/fileadmin/download/produkte/RE_PP_5M_uk.pdf
-- using the open source software Plot Digitizer and a Python
-- script contained in wind-bin-utils called calculate-polynomial-of-turbine-power-curve.py
-- Note: The actual image that was use for this was 
-- repower-5m-power-curve-dvorak-2008-12-10-r2.png
-- POWER output is in kW !!!
CREATE FUNCTION REPOWER5M(speed real) RETURNS real AS $$
    BEGIN

	-- No power if wind is above or below cutin/out
        IF speed < 3.5 OR speed >= 30.0 THEN
	   RETURN 0.;

	ELSEIF speed >= 3.5 AND speed < 9.14 THEN
	   RETURN -0.4441*speed^4 + 10.8240*speed^3. + -36.2389*speed^2. + 16.5411*speed + -9.7823;

	ELSEIF speed >= 9.14 AND speed < 13. THEN
	   RETURN 13.7987*speed^4 + -650.2977*speed^3. + 11312.5006*speed^2. + -85415.7097*speed + 238178.0412;

	ELSEIF speed >= 13. AND speed < 30. THEN
	   RETURN 5000.;

	ELSE 
	   RETURN NULL;

        END IF;
    END;
$$ LANGUAGE plpgsql;

