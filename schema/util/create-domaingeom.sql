-- Used for making location maps of the buoys

CREATE VIEW domaingeom AS 
SELECT h.key, d.key AS domainkey, 
       name, geom 
FROM horizwindgeom h, domain d WHERE h.domainkey=d.key;