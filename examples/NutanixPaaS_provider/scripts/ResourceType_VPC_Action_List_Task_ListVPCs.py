import requests

pc_user = "@@{account.username}@@"
pc_pass = "@@{account.password}@@"
api = "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/vpcs/list"
payload = {
    "kind": "vpc",
    "offset": 0,
    "sort_attribute": "@@{sort_attribute}@@",
    "sort_order": "@@{sort_order}@@",
    "length": 50,
}

r = requests.post(api, json=payload, auth=(pc_user, pc_pass), verify=False)
r.raise_for_status()
r = json.loads(r.content)
tmp = []
for sname in r["entities"]:
    tmp1 = sname["status"]["name"]
    tmp1 = tmp1 + ":" + sname["status"]["resources"]["vpc_type"]
    tmp1 = tmp1 + ":" + sname["metadata"]["uuid"]
    tmp.append(tmp1)

print("vpc_list=" + ",".join(tmp))
