#!/bin/bash
set -ex

INTERNAL_IP="@@{address}@@"
MASTER_IPS="@@{calm_array_address}@@"
WORKER_IPS="@@{AHV_Worker.address}@@"
MASTER_API_HTTPS=6443
SERVICE_SUBNET="@@{KUBE_SERVICE_SUBNET}@@"
KUBE_CLUSTER_NAME="@@{KUBE_CLUSTER_NAME}@@"
FIRST_IP_SERVICE_SUBNET=$(python -c "from netaddr import * ; print IPNetwork('${SERVICE_SUBNET}')[1]")

count=0
for ip in $(echo "${MASTER_IPS}" | tr "," "\n"); do
  CONS_NAMES+="master${count}",
  count=$((count+1))
done

CONTROLLER_NAMES=$(echo $CONS_NAMES | sed  's/,$//')
  
count=0
for ip in $(echo ${WORKER_IPS} | tr "," "\n"); do
  MIN_NAMES+="worker${count}",
  count=$((count+1))
done
MINION_NAMES=$(echo $MIN_NAMES | sed  's/,$//')  

if [ @@{calm_array_index}@@ -ne 0 ];then
  exit
fi
sudo chown -R $USER:$USER /opt/kube-ssl && cd /opt/kube-ssl
echo '{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "server": {
        "expiry": "8760h",
        "usages": [ "signing", "key encipherment", "server auth", "client auth" ]
      },
      "client": {
        "expiry": "8760h",
        "usages": [ "key encipherment", "client auth" ]
      },
      "client-server": {
        "expiry": "8760h",
        "usages": [ "key encipherment", "server auth", "client auth" ]
      }
    }
  }
}' | tee ca-config.json

echo '{
  "CN": "etcd-ca",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "etcd",
      "OU": "CA",
      "ST": "California"
    }
  ]
}' | tee etcd-ca-csr.json

cfssl gencert -initca etcd-ca-csr.json | cfssljson -bare etcd-ca

echo '{
  "CN": "etcd",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "etcd",
      "OU": "CA",
      "ST": "California"
    }
  ]
}' | tee etcd-csr.json

cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem -config=ca-config.json -hostname=${MASTER_IPS} -profile=server etcd-csr.json | cfssljson -bare etcd-server
cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem -config=ca-config.json -hostname=${MASTER_IPS} -profile=client-server etcd-csr.json | cfssljson -bare etcd-peer
cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem -config=ca-config.json -hostname=${MASTER_IPS} -profile=client etcd-csr.json | cfssljson -bare etcd-client

echo '{
  "CN": "kube-ca",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "kube",
      "OU": "CA",
      "ST": "California"
    }
  ]
}' | tee kube-ca-csr.json

cfssl gencert -initca kube-ca-csr.json | cfssljson -bare ca

echo '{
  "CN": "kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "kube",
      "OU": "Cluster",
      "ST": "California"
    }
  ]
}' | tee kubernetes-csr.json

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -hostname=${CONTROLLER_NAMES},${MASTER_IPS},${MINION_NAMES},${WORKER_IPS},${FIRST_IP_SERVICE_SUBNET},127.0.0.1,kubernetes.default,kubernetes,kubernetes.default.svc,kubernetes.default.svc.cluster.local -profile=server kubernetes-csr.json | cfssljson -bare kubernetes

echo '{
  "CN": "system:kube-controller-manager",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "system:kube-controller-manager",
      "OU": "Cluster",
      "ST": "California"
    }
  ]
}' | tee kube-controller-manager-csr.json

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=server kube-controller-manager-csr.json | cfssljson -bare kube-controller-manager

echo '{
  "CN": "system:kube-scheduler",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "system:kube-scheduler",
      "OU": "Cluster",
      "ST": "California"
    }
  ]
}' | tee kube-scheduler-csr.json

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=server kube-scheduler-csr.json | cfssljson -bare kube-scheduler

count=0
for ip in $(echo ${MASTER_IPS} | tr "," "\n"); do
instance="master${count}"
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
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -hostname=${instance},${ip} -profile=client-server ${instance}-csr.json | cfssljson -bare ${instance}
count=$((count+1))
done 

# -*- Creating kube-proxy certificates
echo '{
  "CN": "system:kube-proxy",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "system:node-proxier",
      "OU": "Cluster",
      "ST": "California"
    }
  ]
}' | tee kube-proxy-csr.json

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=client kube-proxy-csr.json | cfssljson -bare kube-proxy

echo '{
  "CN": "admin",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "San Jose",
      "O": "system:masters",
      "OU": "Cluster",
      "ST": "California"
    }
  ]
}' | tee admin-csr.json

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=client admin-csr.json | cfssljson -bare admin

count=0
for ip in $(echo ${MASTER_IPS} | tr "," "\n"); do
kubectl config set-cluster ${KUBE_CLUSTER_NAME} --certificate-authority=ca.pem --embed-certs=true --server=https://${INTERNAL_IP}:${MASTER_API_HTTPS} --kubeconfig=master${count}.kubeconfig
kubectl config set-credentials system:node:master${count} --client-certificate=master${count}.pem --client-key=master${count}-key.pem --embed-certs=true --kubeconfig=master${count}.kubeconfig
kubectl config set-context default --cluster=${KUBE_CLUSTER_NAME} --user=system:node:master${count} --kubeconfig=master${count}.kubeconfig
kubectl config use-context default --kubeconfig=master${count}.kubeconfig
count=$((count+1))
done

kubectl config set-cluster ${KUBE_CLUSTER_NAME} --certificate-authority=ca.pem --embed-certs=true --server=https://${INTERNAL_IP}:${MASTER_API_HTTPS} --kubeconfig=kube-controller-manager.kubeconfig
kubectl config set-credentials kube-controller-manager --client-certificate=kube-controller-manager.pem --client-key=kube-controller-manager-key.pem --embed-certs=true --kubeconfig=kube-controller-manager.kubeconfig
kubectl config set-context default --cluster=${KUBE_CLUSTER_NAME} --user=kube-controller-manager --kubeconfig=kube-controller-manager.kubeconfig
kubectl config use-context default --kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-cluster ${KUBE_CLUSTER_NAME} --certificate-authority=ca.pem --embed-certs=true --server=https://${INTERNAL_IP}:${MASTER_API_HTTPS} --kubeconfig=kube-scheduler.kubeconfig
kubectl config set-credentials kube-scheduler --client-certificate=kube-scheduler.pem --client-key=kube-scheduler-key.pem --embed-certs=true --kubeconfig=kube-scheduler.kubeconfig
kubectl config set-context default --cluster=${KUBE_CLUSTER_NAME} --user=kube-scheduler --kubeconfig=kube-scheduler.kubeconfig
kubectl config use-context default --kubeconfig=kube-scheduler.kubeconfig

kubectl config set-cluster ${KUBE_CLUSTER_NAME} --certificate-authority=ca.pem --embed-certs=true --server=https://${INTERNAL_IP}:${MASTER_API_HTTPS} --kubeconfig=kube-proxy.kubeconfig
kubectl config set-credentials kube-proxy --client-certificate=kube-proxy.pem --client-key=kube-proxy-key.pem --embed-certs=true --kubeconfig=kube-proxy.kubeconfig
kubectl config set-context default --cluster=${KUBE_CLUSTER_NAME} --user=kube-proxy --kubeconfig=kube-proxy.kubeconfig
kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig

ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
echo "kind: EncryptionConfig
apiVersion: v1
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}" | tee encryption-config.yaml

#echo "@@{CENTOS.secret}@@" | tee ~/.ssh/id_rsa
#chmod 400 ~/.ssh/id_rsa

count=0
for ip in $(echo ${MASTER_IPS} | tr "," "\n"); do
  instance="master${count}"
  sshpass -p "@@{CENTOS.secret}@@" scp -o stricthostkeychecking=no admin*.pem ca*.pem etcd*.pem kubernetes*.pem ${instance}* kube-proxy.kubeconfig kube-controller-manager.kubeconfig kube-scheduler.kubeconfig encryption-config.yaml ${instance}:
count=$((count+1))
done
