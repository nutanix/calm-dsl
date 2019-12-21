#!/bin/bash

# Handle special characters in the password
password='@@{db_password}@@'
escaped_pass="${password//\//\\/}"

# Modify config parameters
cd ~/dev-traditional-app/
sed -i "s/password/`echo $escaped_pass`/g" app.py
sed -i "s/my_database/@@{Postgres.DB_NAME}@@/g" app.py
sed -i "s/localhost/@@{Postgres.DB_SERVER_IP}@@/g" app.py
