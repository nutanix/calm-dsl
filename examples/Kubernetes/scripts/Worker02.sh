#!/bin/bash
set -ex

KUBE_CLUSTER_NAME="@@{KUBE_CLUSTER_NAME}@@"
MASTER_IP="@@{AHV_Master.address[0]}@@"
INSTANCE_IP="@@{address}@@"
instance="worker@@{calm_array_index}@@"
KUBE_CERT_PATH="/etc/kubernetes/ssl"
MASTER_API_HTTPS=6443

sudo systemctl start iscsid
sudo systemctl restart rsyslog

while [ ! $(sshpass -p "@@{CENTOS.secret}@@" ssh -o stricthostkeychecking=no $MASTER_IP "ls /opt/kube-ssl/encryption-config.yaml 2>/dev/null") ] ; do  echo "waiting for certs sleeping 5" && sleep 5; if [[ $count -eq 600 ]]; then echo "failed to download certs" && exit 1; fi; count=$(($count+5)) ; done

sshpass -p "@@{CENTOS.secret}@@" scp -o stricthostkeychecking=no "${MASTER_IP}:/opt/kube-ssl/ca*.pem" .
sshpass -p "@@{CENTOS.secret}@@" scp -o stricthostkeychecking=no "${MASTER_IP}:/opt/kube-ssl/kubernetes*.pem" .
sshpass -p "@@{CENTOS.secret}@@" scp -o stricthostkeychecking=no "${MASTER_IP}:/opt/kube-ssl/kube-proxy.kubeconfig" .
sshpass -p "@@{CENTOS.secret}@@" scp -o stricthostkeychecking=no "${MASTER_IP}:/opt/kube-ssl/ca-config.json" .

echo "{
  \"CN\": \"system:node:${instance}\",
  \"key\": {
    \"algo\": \"rsa\",
    \"size\": 2048
  },
  \"names\": [
    {
      \"C\": \"US\",
      \"L\": \"San Jose\",
      \"O\": \"system:nodes\",
      \"OU\": \"Kubernetes The Hard Way\",
      \"ST\": \"California\"
    }
  ]
}" | tee ${instance}-csr.json
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -hostname=${instance},${INSTANCE_IP} -profile=client-server ${instance}-csr.json | cfssljson -bare ${instance}

kubectl config set-cluster ${KUBE_CLUSTER_NAME} --certificate-authority=ca.pem --embed-certs=true --server=https://${MASTER_IP}:${MASTER_API_HTTPS} --kubeconfig=${instance}.kubeconfig
kubectl config set-credentials system:node:${instance} --client-certificate=${instance}.pem --client-key=${instance}-key.pem --embed-certs=true --kubeconfig=${instance}.kubeconfig
kubectl config set-context default --cluster=${KUBE_CLUSTER_NAME} --user=system:node:${instance} --kubeconfig=${instance}.kubeconfig
kubectl config use-context default --kubeconfig=${instance}.kubeconfig

sudo cp *.pem *.kubeconfig ${KUBE_CERT_PATH}/
sudo chmod +r ${KUBE_CERT_PATH}/*

rm -rf ${instance}-csr.json
