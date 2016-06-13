CREATE FUNCTION windspeed_remove_duplicate_on_insert() RETURNS trigger AS $$
    DECLARE dup_record RECORD;
   	    domainNum integer;
    BEGIN
        -- See if the windspeed is a duplicate
        domainNum := TG_ARGV[0] AS integer;
	EXECUTE 'SELECT INTO dup_record * FROM WindSpeed_'||domainNum||' WHERE t=NEW.t';
        IF FOUND
	  THEN
	    INSERT INTO WindSpeed_Duplicate (domainkey, geomkey, t, windspeed, height)
                VALUES (NEW.domainkey, NEW.geomkey, NEW.t, NEW.windspeed, NEW.height);
	    RETURN NULL;
        ELSE RETURN NEW;
        END IF;
    END;
$$ LANGUAGE plpgsql;

-- CREATE TRIGGER windspeed_duplicate AFTER INSERT ON windspeed
--     FOR EACH ROW EXECUTE PROCEDURE windspeed_remove_duplicate();

