CREATE VIEW WindSpeedAvgView
AS
SELECT h.key as geomkey, h.geom, h.x, h.y, d.key as domain, w.height, w.windspeed
FROM domain d, windspeed w, horizwindgeom h, (SELECT geomkey, avg(windspeed) FROM windspeed GROUP BY geomkey) as avgwind
WHERE h.key=w.geomkey AND d.key=w.domainkey AND avgwind.geomkey=w.geomkey;

GROUP BY w.geomkey, h.key, d.key, w.domainkey, h.geom, h.x, h.y, w.height;

CREATE VIEW WindErrorGeom
AS
SELECT domainkey, buoydomain, buoygeomkey, h.geom AS buoygeom, buoyname, mm5avg, bouyavg, year, month, nge, nb, rmse, bias, count
FROM domain d, winderror w, horizwindgeom h
WHERE w.buoydomain=h.domainkey AND w.buoydomain=d.domainkey;

