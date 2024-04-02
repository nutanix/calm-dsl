if @@{calm_array_index}@@ == 0:

  url     = "https://@@{kubemaster_ip}@@:443/apis/apps/v1/namespaces/default/deployments/dev-docker-app-@@{calm_application_uuid}@@"
  headers = {'Content-Type': 'application/merge-patch+json', 'Accept': 'application/json'}

  payload = {
    "spec": {
      "template": {
        "spec": {
          "containers": [
            {
              "name": "dev-docker-app",
              "image":"michaelatnutanix/dev-docker-app:@@{label}@@"
            }
          ]
        }
      }
    }
  }


  kube_user = '@@{karbon.username}@@'
  kube_pass = '@@{karbon.secret}@@'

  resp = urlreq(url, verb='PATCH', auth='BASIC', user=kube_user, passwd=kube_pass, params=json.dumps(payload), headers=headers)

  if resp.ok:
    print (json.dumps(json.loads(resp.content), indent=4))
  else:
    print ("Patch K8S Deployment request failed", json.dumps(json.loads(resp.content), indent=4))
    exit(1)

else:
  print ("calm_array_index is not 0, skipping.")
