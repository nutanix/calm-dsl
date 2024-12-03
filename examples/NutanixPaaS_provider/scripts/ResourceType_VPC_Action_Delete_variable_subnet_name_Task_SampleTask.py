import requests

vpc_name = "@@{vpc_name}@@".split(",")


def apiCall(url):
    pc_user = "@@{username}@@"
    pc_pass = "@@{password}@@"
    r = requests.post(url, json=payload, auth=(pc_user, pc_pass), verify=False)
    r = json.loads(r.content)
    return r


# get vpc uuid
api = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/subnets/list"
payload = {"kind": "subnet", "offset": 0}
r = apiCall(api)

tmp = []
for v in vpc_name:
    vname = v.split(":")[0]
    vuuid = v.split(":")[1]
    for i in r["entities"]:
        name = i["status"]["name"]
        if i["spec"]["resources"]["subnet_type"] == "OVERLAY":
            if i["spec"]["resources"]["vpc_reference"]["uuid"] == vuuid:
                suuid = i["metadata"]["uuid"]
                tmp.append(vname + ":" + name + ":" + suuid)
print("|".join(tmp))
