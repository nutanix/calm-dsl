#!/bin/bash
set -ex

ETCD_VERSION="v3.2.11"
KUBE_VERSION="@@{calm_array_VERSION[0]}@@"
INTERNAL_IP="@@{address}@@"
MASTER_IPS="@@{calm_array_address}@@"
NODE_NAME="master@@{calm_array_index}@@"
CLUSTER_SUBNET="@@{KUBE_CLUSTER_SUBNET}@@"
SERVICE_SUBNET="@@{KUBE_SERVICE_SUBNET}@@"
KUBE_CLUSTER_DNS="@@{KUBE_DNS_IP}@@"
DOCKER_VERSION="@@{DOCKER_VERSION}@@"
ETCD_CERT_PATH="/etc/ssl/certs/etcd"
KUBE_CERT_PATH="/etc/kubernetes/ssl"
KUBE_MANIFEST_PATH="/etc/kubernetes/manifests"
KUBE_CONFIG_PATH="/etc/kubernetes/config"
MASTER_API_HTTPS=6443
ETCD_SERVER_PORT=2379
CONTROLLER_COUNT=$(echo "@@{calm_array_address}@@" | tr ',' '\n' | wc -l)


count=0
for ip in $(echo "${MASTER_IPS}" | tr "," "\n"); do
  ETCD+="https://${ip}:${ETCD_SERVER_PORT}",
  count=$((count+1))
done
ETCD_SERVERS=$(echo $ETCD | sed  's/,$//')

curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubelet
chmod +x kubelet
sudo mv kubelet /usr/bin/kubelet

echo "apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
  labels:
    k8s-app: kube-apiserver
spec:
  hostNetwork: true
  containers:
  - name: kube-apiserver
    image: gcr.io/google-containers/hyperkube:${KUBE_VERSION}
    command:
    - /hyperkube
    - apiserver
    - --enable-admission-plugins=NamespaceLifecycle,NodeRestriction,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota,DenyEscalatingExec,EventRateLimit
    - --advertise-address=${INTERNAL_IP}
    - --allow-privileged=true
    - --anonymous-auth=false
    - --secure-port=${MASTER_API_HTTPS}
    - --profiling=false
    - --apiserver-count=${CONTROLLER_COUNT}
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
    - --audit-log-path=/var/lib/audit.log
    - --authorization-mode=Node,RBAC
    - --bind-address=0.0.0.0
    - --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP
    - --event-ttl=1h
    - --service-account-lookup=true
    - --storage-backend=etcd3
    - --etcd-cafile=${ETCD_CERT_PATH}/etcd-ca.pem
    - --etcd-certfile=${ETCD_CERT_PATH}/etcd-client.pem
    - --etcd-keyfile=${ETCD_CERT_PATH}/etcd-client-key.pem
    - --etcd-servers=${ETCD_SERVERS}
    - --experimental-encryption-provider-config=${KUBE_CERT_PATH}/encryption-config.yaml
    - --admission-control-config-file=${KUBE_CERT_PATH}/admission-control-config-file.yaml
    - --tls-cert-file=${KUBE_CERT_PATH}/kubernetes.pem
    - --tls-private-key-file=${KUBE_CERT_PATH}/kubernetes-key.pem
    - --kubelet-certificate-authority=${KUBE_CERT_PATH}/ca.pem
    - --kubelet-client-certificate=${KUBE_CERT_PATH}/kubernetes.pem
    - --kubelet-client-key=${KUBE_CERT_PATH}/kubernetes-key.pem
    - --kubelet-https=true
    - --runtime-config=api/all
    - --service-account-key-file=${KUBE_CERT_PATH}/kubernetes.pem
    - --service-cluster-ip-range=${SERVICE_SUBNET}
    - --service-node-port-range=30000-32767
    - --client-ca-file=${KUBE_CERT_PATH}/ca.pem
    - --v=2
    ports:
    - containerPort: ${MASTER_API_HTTPS}
      hostPort: ${MASTER_API_HTTPS}
      name: https
    - containerPort: 8080
      hostPort: 8080
      name: local
    volumeMounts:
    - mountPath: ${KUBE_CERT_PATH}
      name: ssl-certs-kubernetes
      readOnly: true
    - mountPath: /etc/ssl/certs
      name: ssl-certs-host
      readOnly: true
    - mountPath: /etc/pki
      name: ca-certs-etc-pki
      readOnly: true
  volumes:
  - hostPath:
      path: ${KUBE_CERT_PATH}
    name: ssl-certs-kubernetes
  - hostPath:
      path: /etc/ssl/certs
    name: ssl-certs-host
  - hostPath:
      path: /etc/pki
    name: ca-certs-etc-pki" | sudo tee ${KUBE_MANIFEST_PATH}/kube-apiserver.yaml

echo "apiVersion: v1
kind: Pod
metadata:
  name: kube-proxy
  namespace: kube-system
  labels:
    k8s-app: kube-proxy
spec:
  hostNetwork: true
  containers:
  - name: kube-proxy
    image: gcr.io/google-containers/hyperkube:${KUBE_VERSION}
    command:
    - /hyperkube
    - proxy
    - --config=${KUBE_CONFIG_PATH}/kube-proxy-config.yaml
    securityContext:
      privileged: true
    volumeMounts:
    - mountPath: ${KUBE_CERT_PATH}
      name: ssl-certs-kubernetes
      readOnly: true
    - mountPath: /etc/ssl/certs
      name: ssl-certs-host
      readOnly: true
    - mountPath: /lib/modules
      name: lib-modules-host
      readOnly: true
    - mountPath: ${KUBE_CONFIG_PATH}
      name: kube-config-path
      readOnly: true
  volumes:
  - hostPath:
      path: ${KUBE_CERT_PATH}
    name: ssl-certs-kubernetes
  - hostPath:
      path: /etc/ssl/certs
    name: ssl-certs-host
  - hostPath:
      path: /lib/modules
    name: lib-modules-host
  - hostPath:
      path: ${KUBE_CONFIG_PATH}
    name: kube-config-path" | sudo tee ${KUBE_MANIFEST_PATH}/kube-proxy.yaml

echo "apiVersion: v1
kind: Pod
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    k8s-app: kube-controller-manager
spec:
  hostNetwork: true
  containers:
  - name: kube-controller-manager
    image: gcr.io/google-containers/hyperkube:${KUBE_VERSION}
    command:
    - /hyperkube
    - controller-manager
    - --bind-address=0.0.0.0  
    - --allocate-node-cidrs=true  
    - --cluster-cidr=${CLUSTER_SUBNET}
    - --cluster-name=${KUBE_CLUSTER_NAME}
    - --leader-elect=true  
    - --kubeconfig=${KUBE_CERT_PATH}/kube-controller-manager.kubeconfig  
    - --service-account-private-key-file=${KUBE_CERT_PATH}/kubernetes-key.pem
    - --root-ca-file=${KUBE_CERT_PATH}/ca.pem
    - --service-cluster-ip-range=${SERVICE_SUBNET}
    - --terminated-pod-gc-threshold=100  
    - --profiling=false  
    - --use-service-account-credentials=true
    - --v=2
    livenessProbe:
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10252
      initialDelaySeconds: 15
      timeoutSeconds: 1
    volumeMounts:
    - mountPath: ${KUBE_CERT_PATH}
      name: ssl-certs-kubernetes
      readOnly: true
    - mountPath: /etc/ssl/certs
      name: ssl-certs-host
      readOnly: true
    - mountPath: /etc/pki
      name: ca-certs-etc-pki
      readOnly: true
  volumes:
  - hostPath:
      path: ${KUBE_CERT_PATH}
    name: ssl-certs-kubernetes
  - hostPath:
      path: /etc/ssl/certs
    name: ssl-certs-host
  - hostPath:
      path: /etc/pki
    name: ca-certs-etc-pki" | sudo tee ${KUBE_MANIFEST_PATH}/kube-controller-manager.yaml
   
echo "apiVersion: v1
kind: Pod
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    k8s-app: kube-scheduler
spec:
  hostNetwork: true
  containers:
  - name: kube-scheduler
    image: gcr.io/google-containers/hyperkube:${KUBE_VERSION}
    command:
    - /hyperkube
    - scheduler
    - --config=${KUBE_CONFIG_PATH}/kube-scheduler.yaml
    - --v=2
    livenessProbe:
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10251
      initialDelaySeconds: 15
      timeoutSeconds: 1
    volumeMounts:
    - mountPath: ${KUBE_CERT_PATH}
      name: ssl-certs-kubernetes
      readOnly: true
    - mountPath: ${KUBE_CONFIG_PATH}
      name: kube-config-path
      readOnly: true
  volumes:
  - hostPath:
      path: ${KUBE_CERT_PATH}
    name: ssl-certs-kubernetes
  - hostPath:
      path: ${KUBE_CONFIG_PATH}
    name: kube-config-path" | sudo tee ${KUBE_MANIFEST_PATH}/kube-scheduler.yaml
