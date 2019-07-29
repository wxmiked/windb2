FROM postgres:11.4

RUN apt-get --no-cache-dir update && apt-get --no-cache-dir install -y wget python3 python3-psycopg2 python3-tz python3-numpy postgresql-9.5-postgis-2.3
WORKDIR /windb2
COPY * .
