#!/bin/bash
set -ex

sudo yum install epel-release -y
sudo yum update -y
sudo yum install redis -y


sudo sed -i 's/tcp-keepalive 0/tcp-keepalive 60/' /etc/redis.conf
sudo sed -i 's/bind 127.0.0.1/#bind 127.0.0.1/' /etc/redis.conf
echo "requirepass @@{REDIS_CONFIG_PASSWORD}@@" | sudo tee -a /etc/redis.conf
echo "maxmemory-policy noeviction" | sudo tee -a /etc/redis.conf
sudo sed -i 's/appendonly no/appendonly yes/' /etc/redis.conf
sudo sed -i 's/appendfilename "appendonly.aof"/appendfilename redis-staging-ao.aof/' /etc/redis.conf

sudo systemctl restart redis.service
