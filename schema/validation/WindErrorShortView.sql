CREATE VIEW WindErrorShort AS 

SELECT wrfDomain,
  buoyDomain,
  name,
  day,
  wrfAvg,
  buoyAvg,
  wrfStddev,
  buoyStddev,
  rmse,
  rmseub,
  wrfStddev/buoyStddev AS stddevRatio,
  bias,
  count,
  note
FROM winderror e, domain d
WHERE d.key=e.buoyDomain;

