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
    policy_list = []
    vpclist = {}

    if "data" in response.json():
        data = response.json()["data"]
        for d in data:
            name = d["name"]
            priority = d["priority"]
            if d["vpcExtId"] not in vpclist.keys():
                vpclist[d["vpcExtId"]] = get_vpc_name(d["vpcExtId"])
            actionType = d["policies"][0]["policyAction"]["actionType"]
            policy_list.append(
                vpclist[d["vpcExtId"]]
                + ":"
                + name
                + ":"
                + str(priority)
                + ":"
                + actionType
            )
        if "@@{select_all_policies}@@" == "No":
            print(f"{','.join(policy_list)}")
        else:
            policy_list1 = [t1.split(":")[0] for t1 in policy_list]
            policy_list1 = sorted(set(policy_list1))
            print(f"{','.join(policy_list1)}")


params = {
    "$page": 0,
    "$limit": 50,
    "$orderby": "priority",
}
list_policies(params)
