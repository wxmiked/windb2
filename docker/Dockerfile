FROM postgres:9.5

ARG WINDB2_VERSION

RUN apt-get update
RUN apt-get install -y wget python3 python3-psycopg2 python3-tz python3-numpy postgresql-9.5-postgis-2.3
RUN wget https://github.com/sailorsenergy/windb2/archive/v$WINDB2_VERSION.tar.gz
RUN tar xvzf v$WINDB2_VERSION.tar.gz
RUN mv windb2-$WINDB2_VERSION /windb2

COPY ./create-windb2.sh /docker-entrypoint-initdb.d
