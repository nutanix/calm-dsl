#!/bin/bash
set -ex

# Update to latest software, then install the required packages for Oscar
sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y update
sudo yum -y install git uuid gcc libpqxx-devel python36u python36u-libs python36u-devel python36u-pip

# Set up symlinks so the 'make' command later will work properly
sudo ln -s /usr/bin/python3.6 /usr/bin/python3
sudo ln -s /usr/bin/pip3.6 /usr/bin/pip

# Update pip, install virtualenv
sudo pip install -U pip
sudo pip install -U virtualenv
