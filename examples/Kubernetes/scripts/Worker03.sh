#!/bin/bash
set -ex

sudo systemctl start docker kubelet
sudo systemctl enable docker kubelet
