#!/bin/bash

sudo setenforce 0
sudo sed -i 's/permissive/disabled/' /etc/sysconfig/selinux

#Create wordpress DB
mysql -u root -p@@{MYSQL_PASSWORD}@@<<EOF
CREATE DATABASE wordpress;
CREATE USER '@@{WP_DB_USER}@@'@'%' IDENTIFIED WITH mysql_native_password BY '@@{WP_DB_PASSWORD}@@';
GRANT ALL PRIVILEGES ON wordpress.* TO '@@{WP_DB_USER}@@'@'%';
FLUSH PRIVILEGES;
EOF