import requests

pc_user = "@@{username}@@"
pc_pass = "@@{password}@@"

cluster_uuid = "@@{pe_cluster_uuid}@@".split(":")[1]

api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/subnets/list"
payload = {"kind": "subnet", "filter": "subnet_type==OVERLAY", "offset": 0}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r = json.loads(r.content)

# for sname in r['entities']:
#  print(sname['status']['name'])

slist = [
    sname["status"]["name"] + ":" + str(sname["metadata"]["spec_version"])
    for sname in r["entities"]
]

print(",".join(slist))