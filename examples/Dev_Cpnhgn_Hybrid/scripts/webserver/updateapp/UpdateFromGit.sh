#!/bin/bash
set -ex

cd ~/dev-traditional-app/
git fetch --all
git reset --hard origin/master
