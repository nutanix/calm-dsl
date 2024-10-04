import requests

pc_user = "@@{username}@@"
pc_pass = "@@{password}@@"

api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/subnets/list"
payload = {"kind": "subnet", "offset": 0}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r = json.loads(r.content)

# slist = [ sname['status']['name'] + ':' + sname['metadata']['uuid'] for sname in r['entities'] ]
slist = [
    sname["status"]["name"]
    + ":"
    + sname["status"]["resources"]["subnet_type"]
    + ":"
    + sname["metadata"]["uuid"]
    for sname in r["entities"]
    if "is_external" in sname["status"]["resources"].keys()
    if sname["status"]["resources"]["is_external"]
]

print(",".join(slist))
