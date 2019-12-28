#!/bin/bash

set -ex

NODE_NAME="@@{calm_application_name}@@"
sudo hostnamectl set-hostname --static ${NODE_NAME}
sudo yum install epel-release -y
sudo yum update -y
