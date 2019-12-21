#!/bin/bash
set -ex

# Install pip
sudo yum -y install epel-release
sudo yum -y install python-pip
sudo -H pip install --upgrade pip
pip --version

# Install locust
sudo -H pip install locustio --ignore-installed
