CREATE VIEW WindErrorShort AS 

SELECT wrfDomain,
  buoyDomain,
  name,
  year,
  month,
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

