#!/bin/bash
set -ex

# Kill the locust process
sudo kill `ps aux | grep locust | grep -v grep | awk '{print $2}'`
