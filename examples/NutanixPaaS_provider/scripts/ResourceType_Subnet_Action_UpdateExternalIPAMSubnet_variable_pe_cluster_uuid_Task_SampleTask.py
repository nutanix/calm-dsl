import requests


def apiCall(url):
    pc_user = "@@{username}@@"
    pc_pass = "@@{password}@@"
    r = requests.post(url, json=payload, auth=(pc_user, pc_pass), verify=False)
    r = json.loads(r.content)
    return r


# get pe cluster uuid
api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/clusters/list"
payload = {"kind": "cluster"}
r = apiCall(api)

tmp = []
pe_cluster_uuid = [
    cname["metadata"]["uuid"]
    for cname in r["entities"]
    if cname["spec"]["name"] != "Unnamed"
]
for cname in r["entities"]:
    if cname["spec"]["name"] == "Unnamed":
        continue
    clustername = cname["spec"]["name"]
    clusteruuid = cname["metadata"]["uuid"]
    tmp.append(clustername + ":" + clusteruuid)

# print("pe_cluster_uuid={}".format(pe_cluster_uuid[0]))
print(",".join(tmp))
