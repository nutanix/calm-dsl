import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False


def get_resource_ext_id(url, name, id_key="extId"):
    response = session.get(
        url,
        headers={
            "accept": "application/json",
        },
        params={"$page": 0, "$limit": 1, "$filter": f"name eq '{name}'"},
    )
    print(f"get {name} response: {response.json()}")
    response.raise_for_status()
    data = response.json().get("data")
    if data:
        if isinstance(data, list):
            if id_key in data[0] and data[0]["name"] == name:
                return data[0][id_key]
        else:
            if id_key in data:
                return data[id_key]
    raise Exception(f"failed to get extId for {name}")


def modify_access(bucket_name):
    object_store_uuid = get_resource_ext_id(
        "https://{}:{}/api/objects/{}/operations/object-stores".format(
            PC_IP, PC_PORT, "@@{objects_api_version}@@"
        ),
        "@@{object_store_name}@@",
    )
    permissions = [x for x in "@@{permissions}@@".split(",") if x != "NONE"]
    payload = {
        "name": bucket_name,
        "bucket_permissions": [
            {"username": "@@{username}@@", "permissions": permissions}
        ],
    }
    response = session.post(
        f"https://localhost:9440/oss/api/nutanix/v3/objectstores/{object_store_uuid}/buckets/{bucket_name}/share"
    )
    print(f"got response : {response.json()}")
    response.raise_for_status()


modify_access("@@{bucket_name}@@")
