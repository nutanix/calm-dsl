#!/bin/bash
sudo service hadoop-hdfs-datanode restart
sudo service hadoop-hdfs-secondarynamenode restart
sudo service hadoop-yarn-nodemanager restart

echo "Service started"
