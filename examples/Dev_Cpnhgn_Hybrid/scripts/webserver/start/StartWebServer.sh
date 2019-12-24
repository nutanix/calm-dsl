#!/bin/bash
set -ex

nohup python ~/dev-traditional-app/app.py flask run &
sleep 5
