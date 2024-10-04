import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def get(object_store):
    params = {"$filter": f"name eq '{object_store}'", "$page": 0, "$limit": 1}
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
    print(f"response = {response.json()}")
    response.raise_for_status()
    data = response.json().get("data")
    print(data[0]["name"], len(data), object_store)
    if data:
        if len(data) == 1 and data[0]["name"] == object_store:
            print(
                "object_store = " + json.dumps(json.dumps(response.json()["data"][0]))
            )
            return
    raise Exception(f"failed to get object store with name {object_store}")


get("@@{object_store_name}@@")
