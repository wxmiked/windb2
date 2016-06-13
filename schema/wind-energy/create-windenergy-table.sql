CREATE TABLE windenergy AS (
SELECT w.domainkey as domain, date_part('year',w.t) as year, date_part('month',w.t) as month, count(speed), geomkey, avg(speed) AS speed_avg, 
       sum(GE36SL(speed)) AS GE36SL_KWH, 
       (0.087*avg(speed)-3600/111^2)*count(speed)*3600 AS GE36SL_CF_KWH, 
       sum(REPOWER5M(speed)) AS REPOWER5M_KWH, 
       (0.087*avg(speed)-5000/126^2)*count(speed)*5000 AS REPOWER5M_CF_KWH
FROM windspeed_all w, horizwindgeom h 
WHERE h.key=w.geomkey AND w.height=80 
GROUP BY geomkey, w.domainkey, date_part('year',w.t), date_part('month',w.t));

