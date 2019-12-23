#!/bin/bash
set -ex

# Set up virtualenv
cd ~/Nutanix-Oscar/
virtualenv --python=python3 oscar
source ./oscar/bin/activate

# Initialize site
make sandbox
