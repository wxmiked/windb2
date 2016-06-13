CREATE VIEW WindErrorGeom AS
SELECT w.wrfdomain, buoydomain, h.key AS buoygeomkey, h.geom AS buoygeom, 
       d.name AS buoyname, wrfavg, buoyavg, year, month, nge, nb, rmse, bias, count
FROM domain d, winderror w, horizwindgeom h
WHERE w.buoydomain=h.domainkey AND w.buoydomain=d.key;

