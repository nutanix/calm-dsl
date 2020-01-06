#!/bin/bash
set -ex

# Clone the Nutanix Customized Oscar Software
git clone https://github.com/MichaelHaigh/Nutanix-Oscar.git
cd Nutanix-Oscar/

# Handle special characters in the password
password='@@{db_password}@@'
escaped_pass="${password//\//\\/}"

# Customize the sandbox/settings.py file for this particular deployment
sed -i 's/oscar_django_201902060613/@@{Postgres.DB_ENTITY_NAME}@@/g' sandbox/settings.py
sed -i "s/ThisIsAVeryLongAndStrongPasswordOK/`echo $escaped_pass`/g" sandbox/settings.py
sed -i 's/10.45.100.118/@@{Postgres.DB_SERVER_IP}@@/g' sandbox/settings.py
sed -i 's/poseidon_access/@@{objects_creds.username}@@/g' sandbox/settings.py
sed -i 's/poseidon_secret/@@{objects_creds.secret}@@/g' sandbox/settings.py
sed -i 's/oscarstatic/@@{bucket_name}@@/g' sandbox/settings.py
sed -i 's/10.45.5.41/@@{objects_ip}@@/g' sandbox/settings.py

