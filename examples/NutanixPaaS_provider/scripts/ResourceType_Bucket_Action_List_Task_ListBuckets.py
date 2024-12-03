import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {
    "entity_type": "bucket",
    "group_member_sort_attribute": "name",
    "group_member_sort_order": "ASCENDING",
    "group_member_offset": 0,
    "filter_criteria": 'federation_name==""',
    "group_member_attributes": [
        {
            "attribute": "name",
        },
        {
            "attribute": "storage_usage_bytes",
        },
        {
            "attribute": "object_count",
        },
        {
            "attribute": "versioning",
        },
        {
            "attribute": "worm",
        },
        {
            "attribute": "outbound_replication_status",
        },
        {
            "attribute": "nfs",
        },
        {
            "attribute": "bucket_notification_state",
        },
        {
            "attribute": "website",
        },
        {
            "attribute": "owner_name",
        },
        {
            "attribute": "retention_start",
        },
        {
            "attribute": "retention_duration_days",
        },
        {
            "attribute": "inbound_replication_status",
        },
        {
            "attribute": "suspend_versioning",
        },
        {
            "attribute": "cors",
        },
    ],
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


def list_buckets(object_store_name):
    object_store_uuid = get_resource_ext_id(
        "https://{}:{}/api/objects/{}/operations/object-stores".format(
            PC_IP, PC_PORT, "@@{objects_api_version}@@"
        ),
        object_store_name,
    )
    response = session.post(
        f"https://{PC_IP}:{PC_PORT}/oss/api/nutanix/v3/objectstore_proxy/{object_store_uuid}/groups",
        json=payload,
    )
    response.raise_for_status()
    print(
        f"buckets = {json.dumps(response.json()['group_results'][0]['entity_results'])}"
    )
    print(response.json())


list_buckets("@@{object_store_name}@@")
