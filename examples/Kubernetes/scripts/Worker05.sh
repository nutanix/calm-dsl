#!/bin/bash
set -ex

MASTER_IP="@@{Master.address[0]}@@"
sshpass -p "@@{CENTOS.secret}@@" ssh -o stricthostkeychecking=no ${MASTER_IP} "kubectl drain 'worker@@{calm_array_index}@@' --ignore-daemonsets --delete-local-data --force"
sleep 10
sshpass -p "@@{CENTOS.secret}@@" ssh -o stricthostkeychecking=no ${MASTER_IP} "kubectl delete node 'worker@@{calm_array_index}@@'"
