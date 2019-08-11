#!/bin/bash

# Set up WinDB2
psql -l
/windb2/bin/create-windb2.py localhost $POSTGRES_USER windb2
