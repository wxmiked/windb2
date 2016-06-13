CREATE FUNCTION windspeed_remove_duplicate() RETURNS trigger AS $windspeed_remove_duplicate$
    DECLARE dup_record RECORD;
    BEGIN
        -- See if the windspeed is a duplicate
	SELECT INTO dup_record * FROM WindSpeed WHERE domainkey=NEW.domainkey AND geomkey=NEW.geomkey AND t=NEW.t AND height=NEW.height;
        IF FOUND
	  THEN
	    INSERT INTO WindSpeed_Duplicate (domainkey, geomkey, t, windspeed, height)
                VALUES (NEW.domainkey, NEW.geomkey, NEW.t, NEW.windspeed, NEW.height);
 	    DELETE FROM WindSpeed WHERE domainkey=NEW.domainkey AND geomkey=NEW.geomkey 
		AND t=NEW.t AND height=NEW.height;
	    RETURN NULL;
        ELSE RETURN NEW;
        END IF;
    END;
$windspeed_remove_duplicate$ LANGUAGE plpgsql;

CREATE TRIGGER windspeed_duplicate AFTER INSERT ON windspeed
    FOR EACH ROW EXECUTE PROCEDURE windspeed_remove_duplicate();

