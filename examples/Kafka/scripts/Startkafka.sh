#!/bin/bash
set -ex
sudo systemctl start kafka-zookeeper
sudo systemctl start kafka
