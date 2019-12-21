et -ex

if [ @@{calm_array_index}@@ -ne 0 ];then
	exit
fi
export PATH=$PATH:/opt/bin
sudo mkdir /etc/kubernetes/addons/helm
echo "#helm init --service-account helm
apiVersion: v1
kind: ServiceAccount
metadata:
  name: helm
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: helm
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: helm
  namespace: kube-system" | sudo tee /etc/kubernetes/addons/helm/helm.yaml

kubectl create -f /etc/kubernetes/addons/helm/helm.yaml
helm init --service-account helm

