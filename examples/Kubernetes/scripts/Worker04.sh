#!/bin/bash
set -ex

KUBE_VERSION="@@{calm_array_VERSION[0]}@@"
INTERNAL_IP="@@{address}@@"
NODE_NAME="worker@@{calm_array_index}@@"
CLUSTER_SUBNET="@@{KUBE_CLUSTER_SUBNET}@@"
KUBE_CLUSTER_DNS="@@{KUBE_DNS_IP}@@"
DOCKER_VERSION="@@{DOCKER_VERSION}@@"
KUBE_CERT_PATH="/etc/kubernetes/ssl"
KUBE_MANIFEST_PATH="/etc/kubernetes/manifests"
KUBE_CONFIG_PATH="/etc/kubernetes/config"

curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubelet
chmod +x kubelet
sudo mv kubelet /usr/bin/kubelet

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
