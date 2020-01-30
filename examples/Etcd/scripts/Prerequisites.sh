#!/bin/bash
set -ex

# - * - Section 1 <---------- Just a representation of section, Don't use in actual script ---------->
# Script Variables & Constants
ETCD_IPS="@@{calm_array_address}@@"
MASTER_IPS=""
NODE_NAME="etcd@@{calm_array_index}@@"

# - * - Section 2 <---------- Just a representation of section, Don't use in actual script ---------->
# install lvm utils for creating lvm out of data disks.
sudo yum install -y lvm2 --quiet

# - * - Section 3 <---------- Just a representation of section, Don't use in actual script ---------->
# Set node hostname
# Update etcd, master names/ips in /etc/hosts.
sudo hostnamectl set-hostname --static ${NODE_NAME}

count=0
for ip in $(echo "${ETCD_IPS}" | tr "," "\n"); do
  echo "${ip} etcd${count}" | sudo tee -a /etc/hosts
  count=$((count+1))
done

count=0
for ip in $(echo "${MASTER_IPS}" | tr "," "\n"); do
  echo "${ip} master${count}" | sudo tee -a /etc/hosts
  count=$((count+1))
done

