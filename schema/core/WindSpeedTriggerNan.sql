CREATE FUNCTION windspeed_remove_nan() RETURNS trigger AS $windspeed_remove_nan$
    BEGIN
        -- See if the windspeed is NaN
        IF NEW.windspeed='NaN' THEN
            INSERT INTO WindSpeedNaN (domainkey, geomkey, t, height) 
		VALUES (NEW.domainkey, NEW.geomkey, NEW.t, NEW.height);
 	    DELETE FROM WindSpeed WHERE domainkey=NEW.domainkey AND geomkey=NEW.geomkey 
		AND t=NEW.t AND height=NEW.height;
	    RETURN NULL;
        ELSE RETURN NEW;
        END IF;
    END;
$windspeed_remove_nan$ LANGUAGE plpgsql;

CREATE TRIGGER windspeed_nan AFTER INSERT ON windspeed
    FOR EACH ROW EXECUTE PROCEDURE windspeed_remove_nan();

