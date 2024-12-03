import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def list_policies(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/networking/{}/config/routing-policies".format(
            PC_IP, PC_PORT, "@@{flow_virtual_network_api_version}@@"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    print("list_policies = " + json.dumps(json.dumps(response.json()["data"])))


params = {
    "$page": @@{page}@@,
    "$limit": @@{limit}@@,
}
if "@@{filter}@@":
    params["filter"] = "@@{filter}@@"
if "@@{select}@@":
    params["select"] = "@@{select}@@"
if "@@{orderby}@@":
    params["orderby"] = "@@{orderby}@@"

list_policies(params)
