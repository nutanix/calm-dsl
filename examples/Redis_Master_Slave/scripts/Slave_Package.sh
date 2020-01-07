#!/bin/bash
set -ex

sudo yum install epel-release -y
sudo yum update -y
sudo yum install redis -y

sudo sed -i 's/bind 127.0.0.1/#bind 127.0.0.1/' /etc/redis.conf
echo "requirepass @@{REDIS_CONFIG_PASSWORD}@@" | sudo tee -a /etc/redis.conf
echo "masterauth @@{REDIS_CONFIG_PASSWORD}@@" | sudo tee -a /etc/redis.conf
echo "slaveof @@{RedisMaster.address}@@ 6379" | sudo tee -a /etc/redis.conf

sudo systemctl restart redis.service
