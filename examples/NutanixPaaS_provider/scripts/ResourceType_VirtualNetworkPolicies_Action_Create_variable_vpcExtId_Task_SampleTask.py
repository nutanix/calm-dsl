import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"
# ----------------------------------


def list_policies(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/networking/{}/config/vpcs".format(PC_IP, PC_PORT, "v4.0.b1"),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    # print(f"response: {response.json()}")
    response.raise_for_status()
    # print("object_stores = " + json.dumps(json.dumps(response.json()["data"])))
    tmp = []
    if "data" in response.json():
        for data in response.json()["data"]:
            vpcname = data["name"]
            vpcextId = data["extId"]
            tmp.append(vpcname + ":" + vpcextId)
        print(",".join(tmp))


params = {}

list_policies(params)
