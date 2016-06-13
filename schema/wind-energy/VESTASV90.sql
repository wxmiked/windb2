-- This was digitized from the Vestas V90 project brochure at http://www.ceoe.udel.edu/windpower/resources/ProductbrochureV90_3_0_UK.pdf
-- WebPlotDigitizer was used to digitize the plot: arohatgi.info/WebPlotDigitizer/app/
CREATE FUNCTION VESTASV90(speed real) RETURNS real AS $$
    BEGIN

	-- No power if wind is above or below cutin/out
        IF speed < 4.0 OR speed >= 25.0 THEN
	   RETURN 0.;

	ELSEIF speed >= 4.0 AND speed < 15. THEN
	   RETURN -45 + 263*speed - 62.8*speed^2 + 9.27*speed^3 - 0.349*speed^4;

	ELSEIF speed >= 15. AND speed < 25. THEN
	   RETURN 3000.;

	ELSE 
	   RETURN -999999.0;

        END IF;
    END;
$$ LANGUAGE plpgsql;

