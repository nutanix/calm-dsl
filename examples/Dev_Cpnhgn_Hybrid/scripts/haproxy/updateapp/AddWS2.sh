#!/bin/bash
set -ex

port=5000
echo "  server host-@@{WebServer2.address}@@ @@{WebServer2.address}@@:${port} weight 1 maxconn 100 check" | sudo tee -a /etc/haproxy/haproxy.cfg

sudo systemctl daemon-reload
sudo systemctl restart haproxy
