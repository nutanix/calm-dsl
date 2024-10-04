import requests

pc_user = "@@{username}@@"
pc_pass = "@@{password}@@"
# pc_user = 'admin'
# pc_pass = 'Nutanix.123'
api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/subnets/list"
payload = {"kind": "subnet", "offset": 0}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r = json.loads(r.content)

# for sname in r['entities']:
#  print(sname['status']['name'])

slist = [
    sname["status"]["name"] + ":" + sname["metadata"]["uuid"] for sname in r["entities"]
]

print(",".join(slist))
