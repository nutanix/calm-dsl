import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def list_security_policy(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/microseg/{}/config/policies".format(
            PC_IP, PC_PORT, "@@{flow_api_version}@@"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    data = response.json()
    if "data" in data:
        print("list_security_policies = " + json.dumps(json.dumps(data)))


params = {
    "$page": @@{page}@@,
    "$limit": @@{limit}@@,
}
if "@@{select}@@".strip():
    params["$select"] = "@@{select}@@"
if "@@{orderby}@@".strip():
    params["$orderby"] = "@@{orderby}@@"
if "@@{filter}@@":
    params["filter"] = "@@{filter}@@"


list_security_policy(params)
