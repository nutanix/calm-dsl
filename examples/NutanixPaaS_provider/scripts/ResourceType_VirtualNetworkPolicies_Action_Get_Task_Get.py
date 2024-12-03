import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def get_policies(extId):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/networking/{}/config/routing-policies/{}".format(
            PC_IP, PC_PORT, "@@{flow_virtual_network_api_version}@@", extId
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    print("get_policies = " + json.dumps(json.dumps(response.json()["data"])))


extId = "@@{extId}@@".strip()
get_policies(extId)
