#!/bin/bash
set -ex

MINION_IPS="@@{AHV_Worker.address}@@"
for ip in $(echo ${MINION_IPS} | tr "," "\n"); do
  if ! (( $(grep -c "${ip} worker${count}" /etc/hosts) )) ; then
  	echo "${ip} worker${count}" | sudo tee -a /etc/hosts
  fi
  count=$((count+1))
done
