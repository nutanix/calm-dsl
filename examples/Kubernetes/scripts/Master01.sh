#!/bin/bash
set -ex
count=0
# Verify access to Centos mirror before yum update
check_mirror() {
curl -s mirrorlist.centos.org >/dev/null | true
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    if [ ${count} -lt 60 ]; then
        echo "Sleeping for 5 seconds before repeating the check" | sudo tee -a /var/log/messages
        sleep 5
        count=$((count+1))
        check_mirror
    else
        echo "DNS resolution failed after 5 minutes, exiting" | sudo tee -a /var/log/messages
        exit 1
    fi
fi
}
check_mirror

sudo easy_install netaddr

ETCD_VERSION="v3.3.12"
KUBE_VERSION="@@{calm_array_VERSION[0]}@@"
INTERNAL_IP="@@{address}@@"
MASTER_IPS="@@{calm_array_address}@@"
WORKER_IPS="@@{AHV_Worker.address}@@"
NODE_NAME="master@@{calm_array_index}@@"
CLUSTER_SUBNET="@@{KUBE_CLUSTER_SUBNET}@@"
SERVICE_SUBNET="@@{KUBE_SERVICE_SUBNET}@@"
KUBE_CLUSTER_DNS="@@{KUBE_DNS_IP}@@"
DOCKER_VERSION="@@{DOCKER_VERSION}@@"
ETCD_CERT_PATH="/etc/ssl/certs/etcd"
KUBE_CERT_PATH="/etc/kubernetes/ssl"
KUBE_CONFIG_PATH="/etc/kubernetes/config"
KUBE_MANIFEST_PATH="/etc/kubernetes/manifests"
KUBE_CNI_BIN_PATH="/opt/cni/bin"
KUBE_CNI_CONF_PATH="/etc/cni/net.d"
MASTER_API_HTTPS=6443
ETCD_SERVER_PORT=2379
ETCD_CLIENT_PORT=2380
MASTER_API_PORT=8080
FIRST_IP_SERVICE_SUBNET=$(python -c "from netaddr import * ; print IPNetwork('${SERVICE_SUBNET}')[1]")

sudo mkdir -p /opt/kube-ssl ${KUBE_CERT_PATH} ${KUBE_CNI_BIN_PATH} ${ETCD_CERT_PATH} ${KUBE_MANIFEST_PATH} ${KUBE_CNI_CONF_PATH} ${KUBE_CONFIG_PATH}

sudo hostnamectl set-hostname --static ${NODE_NAME}
sudo yum update -y --quiet
sudo yum install -y iscsi-initiator-utils socat sshpass --quiet

count=0
for ip in $(echo "${MASTER_IPS}" | tr "," "\n"); do
  echo "${ip} master${count}" | sudo tee -a /etc/hosts
  CON+="master${count}=https://${ip}:${ETCD_CLIENT_PORT}",
  ETCD+="https://${ip}:${ETCD_SERVER_PORT}",
  count=$((count+1))
done
ETCD_ALL_CONTROLLERS=$(echo $CON | sed  's/,$//')
ETCD_SERVERS=$(echo $ETCD | sed  's/,$//')
  
count=0
for ip in $(echo ${WORKER_IPS} | tr "," "\n"); do
  echo "${ip} worker${count}" | sudo tee -a /etc/hosts
  count=$((count+1))
done  
    
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error "https://github.com/coreos/etcd/releases/download/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-amd64.tar.gz"
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://github.com/containernetworking/plugins/releases/download/v0.7.5/cni-plugins-amd64-v0.7.5.tgz
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubelet
chmod +x kubelet
sudo mv kubelet /usr/bin/kubelet

# -*- Bootstrapping a H/A etcd cluster.
tar -xvf etcd-${ETCD_VERSION}-linux-amd64.tar.gz
sudo mv etcd-${ETCD_VERSION}-linux-amd64/etcd* /usr/bin/
rm -rf etcd-${ETCD_VERSION}-linux-amd64*

echo "[Unit]
Description=etcd
Documentation=https://github.com/coreos

[Service]
ExecStart=/usr/bin/etcd \\
  --name ${NODE_NAME} \\
  --cert-file=${ETCD_CERT_PATH}/etcd-server.pem \\
  --key-file=${ETCD_CERT_PATH}/etcd-server-key.pem \\
  --peer-cert-file=${ETCD_CERT_PATH}/etcd-peer.pem \\
  --peer-key-file=${ETCD_CERT_PATH}/etcd-peer-key.pem \\
  --trusted-ca-file=${ETCD_CERT_PATH}/etcd-ca.pem \\
  --peer-trusted-ca-file=${ETCD_CERT_PATH}/etcd-ca.pem \\
  --peer-client-cert-auth \\
  --client-cert-auth \\
  --initial-advertise-peer-urls https://${INTERNAL_IP}:${ETCD_CLIENT_PORT} \\
  --listen-peer-urls https://${INTERNAL_IP}:${ETCD_CLIENT_PORT} \\
  --listen-client-urls https://${INTERNAL_IP}:${ETCD_SERVER_PORT},http://127.0.0.1:${ETCD_SERVER_PORT} \\
  --advertise-client-urls https://${INTERNAL_IP}:${ETCD_SERVER_PORT} \\
  --initial-cluster-token etcd-cluster-0 \\
  --initial-cluster ${ETCD_ALL_CONTROLLERS} \\
  --initial-cluster-state new \\
  --data-dir=/var/lib/etcd \\
  --wal-dir=/var/lib/etcd/wal \\
  --max-wals=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/etcd.service

echo "if \$programname == 'etcd' then /var/log/etcd.log
& stop" | sudo tee /etc/rsyslog.d/etcd.conf

sudo yum install -y --quiet yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
if [[ "${DOCKER_VERSION}" == "17.03.3.ce" ]]; then
  sudo yum install -y --quiet --setopt=obsoletes=0 docker-ce-${DOCKER_VERSION} docker-ce-selinux-${DOCKER_VERSION}
else
  sudo yum install -y --quiet docker-ce-${DOCKER_VERSION} docker-ce-selinux-${DOCKER_VERSION}
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
  --node-labels 'node-role.kubernetes.io/master=true' \\
  --node-labels 'node-role.kubernetes.io/etcd=true' \\
  --register-with-taints=node-role.kubernetes.io/master=true:NoSchedule \\
  --node-labels 'beta.kubernetes.io/fluentd-ds-ready=true' \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/kubelet.service

echo "if \$programname == 'kubelet' then /var/log/kubelet.log
& stop" | sudo tee /etc/rsyslog.d/kubelet.conf

sudo mkdir -p /var/lib/docker /var/lib/etcd/wal

sudo yum install -y lvm2 --quiet
sudo pvcreate /dev/sd{b,c,d}
sudo vgcreate etcd /dev/sd{b,c,d}
sleep 3
sudo lvcreate -l 100%VG -n etcd_lvm etcd
sudo mkfs.xfs /dev/etcd/etcd_lvm

sudo pvcreate /dev/sd{e,f,g}
sudo vgcreate docker /dev/sd{e,f,g}
sleep 3
sudo lvcreate -l 100%VG -n docker_lvm docker
sudo mkfs.xfs /dev/docker/docker_lvm

echo -e "/dev/etcd/etcd_lvm \t /var/lib/etcd \t xfs \t defaults \t 0 0" | sudo tee -a /etc/fstab
echo -e "/dev/docker/docker_lvm \t /var/lib/docker \t xfs \t defaults \t 0 0" | sudo tee -a /etc/fstab
sudo mount -a

echo "InitiatorName=iqn.1994-05.com.nutanix:k8s-worker" | sudo tee /etc/iscsi/initiatorname.iscsi
echo 'exclude=docker*' | sudo tee -a /etc/yum.conf

curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubectl
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error "https://storage.googleapis.com/kubernetes-helm/helm-v2.8.2-linux-amd64.tar.gz"

tar -zxvf helm-v2.8.2-linux-amd64.tar.gz
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64 kubectl linux-amd64/helm
sudo mv cfssl_linux-amd64 /usr/local/bin/cfssl
sudo mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
sudo mv kubectl linux-amd64/helm /usr/local/bin/
rm -rf helm-v2.8.2-linux-amd64.tar.gz linux-amd64
