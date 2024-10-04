import requests


def apiCall(url):
    pc_user = "@@{username}@@"
    pc_pass = "@@{password}@@"
    r = requests.get(url, headers=headers, auth=(pc_user, pc_pass), verify=False)
    r = json.loads(r.content)
    return r


# get virtual switch uuid
api = "https://@@{pc_server}@@:@@{pc_port}@@/api/networking/v4.0.b1/config/virtual-switches"
headers = {
    "x-cluster-id": "@@{pe_cluster_uuid}@@".strip().split(":")[1],
    "accept": "application/json",
}

r = apiCall(api)

name = r["data"][0]["name"]
uuid = r["data"][0]["extId"]
# print("virtual_switch={}".format(name+':'+uuid))
print(name + ":" + uuid)
