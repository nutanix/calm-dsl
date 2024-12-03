import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {
    "api_version": "3.0",
    "metadata": {"kind": "bucket"},
    "spec": {"description": "", "name": "", "resources": {"features": []}},
}


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


def add_versioning():
    payload["spec"]["resources"]["features"].append("VERSIONING")
    if "@@{non_current_version_expiration_days}@@" or "@@{expiration_days}@@":
        payload["spec"]["resources"]["lifecycle_configuration"] = {
            "Rule": [
                {
                    "Filter": {},
                    "ID": "ntnx-frontend-emptyprefix-rule",
                    "Status": "Enabled",
                }
            ]
        }
        if "@@{non_current_version_expiration_days}@@":
            payload["spec"]["resources"]["lifecycle_configuration"]["Rule"][0][
                "NoncurrentVersionExpiration"
            ] = {"NoncurrentDays": int("@@{non_current_version_expiration_days}@@")}
        if "@@{expiration_days}@@":
            payload["spec"]["resources"]["lifecycle_configuration"]["Rule"][0][
                "Expiration"
            ] = {"Days": int("@@{expiration_days}@@")}


def get_creation_status(url):
    response = session.get(url)
    print(f"get bucket response = {response.json()}")
    response.raise_for_status()
    return response.json()["status"]["state"]


def create(bucket_name):
    payload["spec"]["name"] = bucket_name
    object_store_uuid = get_resource_ext_id(
        "https://{}:{}/api/objects/{}/operations/object-stores".format(
            PC_IP, PC_PORT, "@@{objects_api_version}@@"
        ),
        "frost",
    )
    if "@@{enable_versioning}@@" == "Yes":
        add_versioning()
    print(f"create payload: {payload}")
    response = session.post(
        f"https://{PC_IP}:{PC_PORT}/oss/api/nutanix/v3/objectstores/{object_store_uuid}/buckets",
        json=payload,
    )
    print(f"create response: {response.json()}")
    response.raise_for_status()

    status_path = f"https://{PC_IP}:{PC_PORT}/oss/api/nutanix/v3/objectstores/{object_store_uuid}/buckets/{bucket_name}"
    print(f"task_status = {get_creation_status(status_path)}")
    if "@@{wait}@@" == "Yes":
        while True:
            bucket_create_status = get_creation_status(status_path)
            if bucket_create_status == "COMPLETE":
                break
            sleep(30)


create("@@{bucket_name}@@")
