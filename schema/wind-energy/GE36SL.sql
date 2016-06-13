-- This is from the suplemental that was originially provided for the
-- following paper: Kempton, et al., 2007 Large CO2 reductions via
-- offshore wind power..., Geophysical Research Letters
CREATE FUNCTION GE36SL(speed real) RETURNS real AS $$
    BEGIN

	-- No power if wind is above or below cutin/out
        IF speed < 3.5 OR speed >= 27.0 THEN
	   RETURN 0.;

	ELSEIF speed >= 3.5 AND speed < 9. THEN
	   RETURN 3.43*speed^3. + -26.14*speed^2. + 190.07*speed + -492.02;

	ELSEIF speed >= 9. AND speed < 14. THEN
	   RETURN -2.78*speed^3. + 50.00*speed^2. + 369.56*speed + -3750.5;

	ELSEIF speed >= 14. AND speed < 27. THEN
	   RETURN 3600.;

	ELSE 
	   RETURN -999999.0;

        END IF;
    END;
$$ LANGUAGE plpgsql;

