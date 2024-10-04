import requests

pc_user = "@@{username}@@"
pc_pass = "@@{password}@@"

api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/subnets/list"
payload = {"kind": "subnet", "filter": "is_external==true"}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r = json.loads(r.content)

slist = [
    sname["status"]["name"] + ":" + sname["metadata"]["uuid"] for sname in r["entities"]
]
print(",".join(slist))
