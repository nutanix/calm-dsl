import requests

pc_user = "@@{account.username}@@"
pc_pass = "@@{account.password}@@"
api = (
    "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/subnets/list"
)
payload = {
    "kind": "subnet",
    "offset": @@{offset}@@,
    "sort_attribute": "@@{sort_attribute}@@",
    "sort_order": "@@{sort_order}@@",
    "length": @@{length}@@
}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r.raise_for_status()
r = json.loads(r.content)
tmp = []
for sname in r["entities"]:
    tmp1 = sname["status"]["name"]
    tmp1 = tmp1 + ":" + sname["status"]["resources"]["subnet_type"]
    if "vlan_id" in sname["status"]["resources"]:
        tmp1 = tmp1 + ":" + str(sname["status"]["resources"]["vlan_id"])
    tmp1 = tmp1 + ":" + sname["metadata"]["uuid"]
    tmp.append(tmp1)

print("subnet_list=" + ",".join(tmp))
