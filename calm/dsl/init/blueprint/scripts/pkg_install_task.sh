#!/bin/bash

set -ex

echo "@@{sample_pkg_var}@@"

sudo yum install epel-release -y
sudo yum update -y

echo "Package installation steps go here ..."
