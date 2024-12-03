import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"


def apiCall(url):
    r = requests.post(url, json=payload, auth=(PC_USERNAME, PC_PASSWORD), verify=False)
    r = json.loads(r.content)
    return r


# get vpc uuid
api = "https://{}:{}/api/nutanix/v3/vpcs/list".format(PC_IP, PC_PORT)
payload = {"kind": "vpc", "offset": 0}
r = apiCall(api)

tmp = []
for cname in r["entities"]:
    vpcname = cname["status"]["name"]
    vpcuuid = cname["metadata"]["uuid"]
    vpctype = cname["status"]["resources"]["vpc_type"]
    specid = cname["metadata"]["spec_version"]
    tmp.append(vpcname + ":" + vpcuuid + ":" + vpctype)
print(",".join(tmp))
