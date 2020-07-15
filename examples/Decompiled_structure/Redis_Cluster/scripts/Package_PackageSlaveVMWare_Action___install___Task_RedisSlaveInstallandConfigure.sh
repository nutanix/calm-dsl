#!/bin/bash
set -ex

REDIS_MASTER_ADDRESS="@@{Redis_Master.address}@@"
REDIS_CONFIG_PASSWORD="@@{REDIS_CONFIG_PASSWORD}@@"

#Update yum repo and install redis
sudo yum install epel-release -y
sudo yum update -y
sudo yum install redis -y

#Configure the redis in /etc/redis.conf
sudo sed -i 's/bind 127.0.0.1/#bind 127.0.0.1/' /etc/redis.conf
echo "requirepass ${REDIS_CONFIG_PASSWORD}" | sudo tee -a /etc/redis.conf
echo "masterauth ${REDIS_CONFIG_PASSWORD}" | sudo tee -a /etc/redis.conf
echo "slaveof ${REDIS_MASTER_ADDRESS} 6379" | sudo tee -a /etc/redis.conf

#Restart the redis service
sudo systemctl restart redis.service