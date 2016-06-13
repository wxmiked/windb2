CREATE VIEW winderrordomain AS SELECT d.name, w.*  FROM winderror w, domain d WHERE d.key=w.buoydomain;
