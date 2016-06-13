#!/bin/bash

# Make sure the dbName was included in the args
if [ $# != 3 ]; then
  echo "Usage: generate-schema-doc.sh <dbHost> <dbName> <dbPassword>"
  exit -1
fi

# Set the DB name
dbHost=$1
dbName=$2
dbPassword=$3

java -jar ../lib/schemaSpy_5.0.0.jar -hq -t pgsql -db sf-op-byc-12z-1 -host $dbHost= -u postgres -o ../doc -s public -u postgres -p $dbPassword -dp ../lib/postgresql-9.3-1100.jdbc41.jar