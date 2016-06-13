-- Returns the associated wind direction as a string
CREATE FUNCTION WINDDIR(dir int) RETURNS varchar(2) AS $$
    BEGIN
    IF dir >= 337.5 AND dir < 360 OR dir < 22.5	THEN
       RETURN 'N';
    ELSEIF dir >= 22.5  AND dir < 67.5	THEN
        RETURN 'NE';
    ELSEIF dir >= 67.5  AND dir < 112.5	THEN
    	   RETURN 'E';
    ELSEIF dir >= 112.5 AND dir < 157.5	THEN
        RETURN 'SE';
    ELSEIF dir >= 157.5 AND dir < 202.5	THEN
    	   RETURN 'S';
    ELSEIF dir >= 202.5 AND dir < 247.5	THEN
        RETURN 'SW';
    ELSEIF dir >= 247.5 AND dir < 292.5	THEN
    	   RETURN 'W';
    ELSEIF dir >= 292.5 AND dir < 337.5	THEN
        RETURN 'NW';
    ELSEIF dir IS NULL THEN
    	RETURN '';
    ELSE RETURN '';

    END IF;



    END;
$$ LANGUAGE plpgsql;

