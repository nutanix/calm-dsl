#!/bin/bash
set -ex

sudo yum install -y https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-7-x86_64/pgdg-centos95-9.5-3.noarch.rpm
#sudo yum update -y
sudo yum install -y postgresql95 postgresql95-server postgresql95-contrib
sudo /usr/pgsql-9.5/bin/postgresql95-setup initdb
sudo systemctl enable postgresql-9.5
sudo systemctl start postgresql-9.5
sudo setenforce 0
systemctl stop firewalld


echo "listen_addresses = '*'" | sudo tee -a /var/lib/pgsql/9.5/data/postgresql.conf
echo -e "host \t all \t\t all \t\t 0.0.0.0/0 \t\t trust" | sudo tee -a /var/lib/pgsql/9.5/data/pg_hba.conf

sudo systemctl restart postgresql-9.5

sudo -i -u postgres psql -c "CREATE DATABASE @@{DISCOURSE_DB_NAME}@@; "
sudo -i -u postgres createuser -d -E -R -S @@{DISCOURSE_DB_USERNAME}@@
sudo -i -u postgres psql -c "alter user admin with encrypted password '@@{DISCOURSE_DB_PASSWORD}@@'; "
sudo -i -u postgres psql -c "grant all privileges on database discourse to @@{DISCOURSE_DB_USERNAME}@@;"


sudo -i -u postgres psql template1 -c "create extension if not exists hstore;"
sudo -i -u postgres psql template1 -c "create extension if not exists pg_trgm;"
sudo -i -u postgres psql discourse -c "create extension if not exists hstore;"
sudo -i -u postgres psql discourse -c "create extension if not exists pg_trgm;"

sudo systemctl restart postgresql-9.5

sleep 3