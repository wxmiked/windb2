FROM postgres:11.4

RUN apt update && apt install -y wget python3 python3-psycopg2 python3-tz python3-numpy postgresql-9.5-postgis-2.3
WORKDIR /windb2
COPY * /windb2/
COPY docker/create-windb2-in-docker.sh /docker-entrypoint-initdb.d

