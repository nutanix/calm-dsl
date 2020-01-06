#!/bin/bash
set -ex

# Nohup the locust load command and send output to log file
nohup locust --host=http://@@{Oscar.address}@@:8000 --no-web -c @@{load}@@ -r @@{load}@@ >> locust.log 2>&1 &
sleep 5
