--
-- Found at https://wiki.postgresql.org/wiki/Round_time on 2013-07-10.
--
CREATE FUNCTION date_round(base_date timestamptz, round_interval INTERVAL) RETURNS timestamptz AS $BODY$
SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (EXTRACT(epoch FROM $1)::INTEGER + EXTRACT(epoch FROM $2)::INTEGER / 2)
                / EXTRACT(epoch FROM $2)::INTEGER * EXTRACT(epoch FROM $2)::INTEGER * INTERVAL '1 second';
$BODY$ LANGUAGE SQL STABLE;
