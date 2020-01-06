#!/bin/bash
set -ex

count=0
# Verify access to Centos mirror before yum update
check_mirror() {
curl -s mirrorlist.centos.org >/dev/null | true
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    if [ ${count} -lt 60 ]; then
        echo "Sleeping for 5 seconds before repeating the check"
        sleep 5
        count=$((count+1))
        check_mirror
    else
        echo "DNS resolution failed after 5 minutes, exiting"
        exit 1
    fi
fi
}
check_mirror

KUBE_VERSION="@@{calm_array_VERSION[0]}@@"
INTERNAL_IP="@@{address}@@"
MASTER_IPS="@@{AHV_Master.address}@@"
NODE_NAME="worker@@{calm_array_index}@@"
CLUSTER_SUBNET="@@{KUBE_CLUSTER_SUBNET}@@"
SERVICE_SUBNET="@@{KUBE_SERVICE_SUBNET}@@"
KUBE_CLUSTER_DNS="@@{KUBE_DNS_IP}@@"
DOCKER_VERSION="@@{DOCKER_VERSION}@@"
KUBE_CERT_PATH="/etc/kubernetes/ssl"
KUBE_MANIFEST_PATH="/etc/kubernetes/manifests"
KUBE_CONFIG_PATH="/etc/kubernetes/config"
KUBE_CNI_BIN_PATH="/opt/cni/bin"
KUBE_CNI_CONF_PATH="/etc/cni/net.d"
ETCD_SERVER_PORT=2379

sudo mkdir -p ${KUBE_CERT_PATH} ${KUBE_MANIFEST_PATH} ${KUBE_CNI_CONF_PATH} ${KUBE_CNI_BIN_PATH} ${KUBE_CONFIG_PATH}
sudo hostnamectl set-hostname --static ${NODE_NAME}

sudo yum update -y --quiet
sudo yum install -y iscsi-initiator-utils socat sshpass --quiet

curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://github.com/containernetworking/plugins/releases/download/v0.7.5/cni-plugins-amd64-v0.7.5.tgz
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubelet
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubectl
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
chmod +x kubelet kubectl cfssl_linux-amd64 cfssljson_linux-amd64
sudo mv kubelet kubectl /usr/bin/
sudo mv cfssl_linux-amd64 /usr/local/bin/cfssl
sudo mv cfssljson_linux-amd64 /usr/local/bin/cfssljson

sudo yum install -y --quiet yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
if [[ "${DOCKER_VERSION}" == "17.03.3.ce" ]]; then
  sudo yum install -y --quiet --setopt=obsoletes=0 docker-ce-${DOCKER_VERSION} docker-ce-selinux-${DOCKER_VERSION}
else
  sudo yum install -y --quiet docker-ce-${DOCKER_VERSION}
fi

sudo sed -i '/ExecStart=/c\\ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock' /usr/lib/systemd/system/docker.service
sudo systemctl enable docker
sudo usermod -a -G docker $USER

sudo mkdir -p /etc/docker
echo '{
  "storage-driver": "overlay"
}' | sudo tee /etc/docker/daemon.json

echo '{
  "name": "cbr0",
  "type": "flannel",
  "delegate": {
    "isDefaultGateway": true
  }
}' | sudo tee ${KUBE_CNI_CONF_PATH}/10-flannel.conf

sudo tar -zxvf cni-plugins-amd64-*.tgz -C ${KUBE_CNI_BIN_PATH}
rm -rf cni-plugins-amd64-*.tgz

cat <<EOF | sudo tee ${KUBE_CONFIG_PATH}/kubelet-config.yaml
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: "${KUBE_CERT_PATH}/ca.pem"
authorization:
  mode: Webhook
clusterDomain: "cluster.local"
clusterDNS:
  - "${KUBE_CLUSTER_DNS}"
staticPodPath: "${KUBE_MANIFEST_PATH}"
podCIDR: "${CLUSTER_SUBNET}"
runtimeRequestTimeout: "10m"
tlsCertFile: "${KUBE_CERT_PATH}/${NODE_NAME}.pem"
tlsPrivateKeyFile: "${KUBE_CERT_PATH}/${NODE_NAME}-key.pem"
readOnlyPort: 0
protectKernelDefaults: false
makeIPTablesUtilChains: true
eventRecordQPS: 0
kubeletCgroups: "/systemd/system.slice"
evictionHard:
  memory.available: "200Mi"
  nodefs.available:  "10%"
  nodefs.inodesFree: "5%"
EOF

echo "[Unit]
Description=Kubernetes Kubelet
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=docker.service
Requires=docker.service

[Service]
ExecStart=/usr/bin/kubelet \\
  --config=${KUBE_CONFIG_PATH}/kubelet-config.yaml \\
  --container-runtime=docker \\
  --kubeconfig=${KUBE_CERT_PATH}/${NODE_NAME}.kubeconfig \\
  --network-plugin=cni \\
  --register-node=true \\
  --runtime-cgroups=/systemd/system.slice \\
  --node-labels 'node-role.kubernetes.io/worker=true' \\
  --node-labels 'beta.kubernetes.io/fluentd-ds-ready=true' \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/kubelet.service

echo "if \$programname == 'kubelet' then /var/log/kubelet.log
& stop" | sudo tee /etc/rsyslog.d/kubelet.conf

cat <<EOF | sudo tee ${KUBE_CONFIG_PATH}/kube-proxy-config.yaml
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
clientConnection:
  kubeconfig: "${KUBE_CERT_PATH}/kube-proxy.kubeconfig"
mode: "iptables"
clusterCIDR: "${CLUSTER_SUBNET}"
iptables:
  masqueradeAll: true
EOF

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
    
if [ "@@{KUBE_CNI_PLUGIN}@@" == "canal" ] ||  [ "@@{KUBE_CNI_PLUGIN}@@" == "calico" ]; then
	sudo sed -i '/masqueradeAll/d' ${KUBE_CONFIG_PATH}/kube-proxy-config.yaml
fi 

echo "InitiatorName=iqn.1994-05.com.nutanix:k8s-worker" | sudo tee /etc/iscsi/initiatorname.iscsi

sudo mkdir -p /var/lib/docker
sudo yum install -y lvm2 --quiet
sudo pvcreate /dev/sd{b,c,d}
sudo vgcreate docker /dev/sd{b,c,d}
sleep 3
sudo lvcreate -l 100%VG -n docker_lvm docker
sudo mkfs.xfs /dev/docker/docker_lvm

echo -e "/dev/docker/docker_lvm \t /var/lib/docker \t xfs \t defaults \t 0 0" | sudo tee -a /etc/fstab
sudo mount -a

echo 'exclude=docker*' | sudo tee -a /etc/yum.conf

#echo "@@{CENTOS.secret}@@" | tee ~/.ssh/id_rsa
#chmod 400 ~/.ssh/id_rsa
