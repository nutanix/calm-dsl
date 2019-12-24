#!/bin/bash
set -ex

# Kill WebServer Process
sudo kill `ps aux | grep -i oscar | grep -v grep | awk '{print $2}'`
