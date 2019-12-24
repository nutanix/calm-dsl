#!/bin/bash
set -ex

sudo sed -i "/@@{WebServer1.address}@@/d" /etc/haproxy/haproxy.cfg

sudo systemctl daemon-reload
sudo systemctl restart haproxy
