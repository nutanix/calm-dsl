#!/bin/bash
set -ex

#Update yum and install Java
sudo yum update -y
sudo yum install -y java-1.8.0-openjdk
