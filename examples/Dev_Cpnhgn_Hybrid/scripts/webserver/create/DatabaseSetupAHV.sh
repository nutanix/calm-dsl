#!/bin/bash
set -ex

cd ~/dev-traditional-app/
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
