import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def list_object_stores(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/objects/{}/operations/object-stores".format(
            PC_IP, PC_PORT, "@@{objects_api_version}@@"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    print("object_stores = " + json.dumps(json.dumps(response.json()["data"])))


params = {
    "$page": @@{page}@@,
    "$limit": @@{limit}@@,
    "$select": "@@{select}@@",
    "$orderby": "@@{orderby}@@",
}

if "@@{filter}@@".strip():
    params["$filter"] = "@@{filter}@@"

if "@@{expand}@@".strip():
    params["$expand"] = "@@{expand}@@"


list_object_stores(params)
