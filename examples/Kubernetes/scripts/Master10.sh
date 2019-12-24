#!/bin/bash
set -ex
sudo systemctl start etcd docker kubelet
sudo systemctl enable etcd docker kubelet

