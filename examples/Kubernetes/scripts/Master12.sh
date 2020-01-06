et -ex

if [ @@{calm_array_index}@@ -ne 0 ];then
  exit
fi

INTERNAL_IP="@@{address}@@"
MASTER_IPS="@@{calm_array_address}@@"
WORKER_IPS="@@{AHV_Worker.address}@@"
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'
KUBE_VERSION_NEW="@@{KUBE_VERSION_NEW}@@"
MASTER_API_HTTPS=6443
curl -C - -L -O --retry 6 --retry-max-time 60 --retry-delay 60 --silent --show-error https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION_NEW}/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl

count=0
while [[ $(curl --key CA/admin-key.pem --cert CA/admin.pem --cacert CA/ca.pem https://${INTERNAL_IP}:${MASTER_API_HTTPS}/healthz) != "ok" ]] ; do
  echo "Trying to reach master server https://${INTERNAL_IP}:${MASTER_API_HTTPS} : sleep for 5 secs"
  sleep 10
  if [[ $count -eq 10 ]]; then
    echo "Unable to reach master server: https://${INTERNAL_IP}:${MASTER_API_HTTPS}"
    exit 1
  fi
  count=$((count+1))
done

count=0
for ip in $(echo "${WORKER_IPS}" | tr "," "\n"); do
  #kubectl drain "worker${count}" --ignore-daemonsets --delete-local-data --force
  #sleep 20
  sshpass -p "@@{CENTOS.secret}@@" ssh -o stricthostkeychecking=no $ip "sudo yum update -y --quiet && sudo systemctl daemon-reload && sudo systemctl restart kubelet"
  sleep 10
  while [[ `kubectl get nodes -l kubernetes.io/hostname=worker${count} -o jsonpath="$JSONPATH" | grep "Ready=Unknown" 2>/dev/null` ]]; do sleep 10 ; done
  #kubectl uncordon worker${count}
  count=$((count+1))
done


if [[ `kubectl get nodes -o jsonpath="$JSONPATH" | grep "Ready=Unknown"` ]]; then 
  echo "Upgrade failed on worker nodes"
    exit 1
fi

count=0
for ip in $(echo "${MASTER_IPS}" | tr "," "\n"); do
  #kubectl drain "master${count}" --ignore-daemonsets --delete-local-data --force
  #sleep 20
  sshpass -p "@@{CENTOS.secret}@@" ssh -o stricthostkeychecking=no $ip "sudo yum update -y --quiet && sudo systemctl daemon-reload && sudo systemctl restart kubelet"
  sleep 10
  while [[ `kubectl get nodes -l kubernetes.io/hostname=master${count} -o jsonpath="$JSONPATH" | grep "Ready=Unknown" 2>/dev/null` ]]; do sleep 10 ; done
  #kubectl uncordon master${count}
  count=$((count+1))
done


if [[ `kubectl get nodes -o jsonpath="$JSONPATH" | grep "Ready=Unknown"` ]]; then 
  echo "Upgrade failed on nodes: $(kubectl get nodes -o jsonpath='$JSONPATH' | grep 'Ready=Unknown')"
    exit 1
fi
