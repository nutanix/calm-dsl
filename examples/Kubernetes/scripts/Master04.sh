#!/bin/bash
set -ex

MASTER_API_HTTPS=6443
INTERNAL_IP="@@{address}@@"
KUBE_CLUSTER_NAME="@@{KUBE_CLUSTER_NAME}@@"

sudo systemctl start etcd docker kubelet iscsid
sudo systemctl enable etcd docker kubelet iscsid
sudo systemctl restart rsyslog

export PATH=$PATH:/opt/bin

mkdir CA
mv admin*.pem ca*.pem etcd-*.pem kubernetes*.pem master* kube-*.kubeconfig encryption-config.yaml CA/
if [ @@{calm_array_index}@@ -ne 0 ];then
  exit
fi
cp /opt/kube-ssl/admin*.pem CA/
COUNT=0
while [[ $(curl --key CA/admin-key.pem --cert CA/admin.pem --cacert CA/ca.pem https://${INTERNAL_IP}:${MASTER_API_HTTPS}/healthz) != "ok" ]] ; do
    echo "sleep for 5 secs"
  sleep 5
  COUNT=$(($COUNT+1))
  if [[ $COUNT -eq 50 ]]; then
  	echo "Error: creating cluster"
    exit 1
  fi
done

kubectl config set-cluster ${KUBE_CLUSTER_NAME}  --certificate-authority=$HOME/CA/ca.pem  --embed-certs=true --server=https://${INTERNAL_IP}:${MASTER_API_HTTPS}
kubectl config set-credentials admin  --client-certificate=$HOME/CA/admin.pem  --client-key=$HOME/CA/admin-key.pem
kubectl config set-context ${KUBE_CLUSTER_NAME}  --cluster=${KUBE_CLUSTER_NAME}  --user=admin
kubectl config use-context ${KUBE_CLUSTER_NAME}

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:kube-apiserver-to-kubelet
rules:
  - apiGroups:
      - ""
    resources:
      - nodes/proxy
      - nodes/stats
      - nodes/log
      - nodes/spec
      - nodes/metrics
    verbs:
      - "*"
EOF

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: system:kube-apiserver
  namespace: ""
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:kube-apiserver-to-kubelet
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: kubernetes
EOF
