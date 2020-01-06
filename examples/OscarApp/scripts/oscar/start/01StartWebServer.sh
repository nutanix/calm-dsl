#!/bin/bash
set -ex

# Set up virtualenv
cd ~/Nutanix-Oscar/
virtualenv --python=python3 oscar
source ./oscar/bin/activate

# Start webserver via nohup
nohup python sandbox/manage.py runserver 0.0.0.0:8000 &

# Sleep so the process has a chance to start properly
sleep 5
