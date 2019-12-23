#!/bin/bash
set -ex

# Install necessary yum software and update to latest
sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y update
sudo yum -y install git vim wget gcc libpqxx-devel python-pip python-devel postgresql-server postgresql-devel postgresql-contrib

# Install necessary pip software
sudo pip install -U pip
sudo pip install -U psycopg2 Flask-Script Flask-SQLAlchemy Flask-Migrate
