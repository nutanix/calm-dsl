import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"


def get_vpc_name(extId):
    response = requests.get(
        "https://{}:{}/api/networking/{}/config/vpcs/{}".format(
            PC_IP, PC_PORT, "v4.0.b1", extId
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params={},
        verify=False,
    )
    name = response.json()["data"]["name"]
    return name


def list_policies(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/networking/{}/config/routing-policies".format(
            PC_IP, PC_PORT, "v4.0.b1"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    # print(f"response: {response.json()}")
    response.raise_for_status()
    tmp = []
    vpclist = {}

    if "data" in response.json():
        data = response.json()["data"]
        for d in data:
            name = d["name"]
            priority = d["priority"]
            if d["vpcExtId"] not in vpclist.keys():
                vpclist[d["vpcExtId"]] = get_vpc_name(d["vpcExtId"])
            protocolType = d["policies"][0]["policyMatch"]["protocolType"]
            actionType = d["policies"][0]["policyAction"]["actionType"]
            tmp.append(
                vpclist[d["vpcExtId"]]
                + ":"
                + name
                + ":"
                + str(priority)
                + ":"
                + actionType
            )

    print(f"{','.join(tmp)}")


params = {
    "$page": 0,
    "$limit": 50,
    "$orderby": "priority",
}
list_policies(params)
