import requests


def apiCall(url):
    pc_user = "@@{username}@@"
    pc_pass = "@@{password}@@"
    r = requests.post(url, json=payload, auth=(pc_user, pc_pass), verify=False)
    r = json.loads(r.content)
    return r


# get vpc uuid
api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/vpcs/list"
payload = {"kind": "vpc", "offset": 0}
r = apiCall(api)

tmp = []
for cname in r["entities"]:
    vpcname = cname["status"]["name"]
    vpcuuid = cname["metadata"]["uuid"]
    vpctype = cname["status"]["resources"]["vpc_type"]
    specid = cname["metadata"]["spec_version"]
    tmp.append(vpcname + ":" + vpcuuid + ":" + vpctype + ":" + str(specid))
print(",".join(tmp))
