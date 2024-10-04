import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"

session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {"protocol": "SMB", "smbProperties": {}}


def get_file_server_extId(file_server_name):
    params = {
        "$page": 0,
        "$limit": 1,
        "$select": "extId, name, sizeInGib",
        "$orderby": "name",
        "filter": f"name eq '{file_server_name}'",
    }
    response = session.get(
        "https://{}:{}/api/files/{}/config/file-servers".format(
            PC_IP, PC_PORT, "@@{files_api_version}@@"
        ),
        params=params,
    )
    print(f"list file server response: {response.json()}")
    response.raise_for_status()
    file_server_data = response.json()["data"]
    if (
        len(file_server_data) == 1
        and file_server_data[0]["name"] == "@@{file_server_name}@@"
    ):
        return file_server_data[0]["extId"]
    else:
        raise Exception("File server not found")


def add_description():
    payload["description"] = "@@{description}@@"


def add_type():
    payload["type"] = "@@{type}@@"


def add_access_based_enumeration_enabled():
    payload["smbProperties"]["isAccessBasedEnumerationEnabled"] = (
        True if "@@{access_based_enumeration_enabled}@@" == "Yes" else False
    )


def add_compression_enabled():
    payload["isCompressionEnabled"] = (
        True if "@@{compression_enabled}@@" == "Yes" else False
    )


def add_encryption_enabled():
    payload["smbProperties"]["isSmb3EncryptionEnabled"] = (
        True if "@@{encryption_enabled}@@" == "Yes" else False
    )


def add_ca_enaled():
    payload["smbProperties"]["isCaEnabled"] = (
        True if "@@{ca_enabled}@@" == "Yes" else False
    )


def add_share_acl():
    if "@@{share_acl}@@".strip():
        payload["smbProperties"]["shareACL"] = []
        for value in "@@{share_acl}@@".split(","):
            if value.strip():
                split_acl_data = value.split(":")
                payload["smbProperties"]["shareACL"].append(
                    {
                        "userOrGroupName": split_acl_data[0],
                        "permissionType": split_acl_data[1],
                        "smbAccessType": split_acl_data[2],
                    }
                )


def add_compression_enabled():
    payload["enableCompression"] = (
        True if "@@{compression_enabled}@@" == "Yes" else False
    )


def add_max_size_in_gb():
    payload["maxSizeGiBytes"] = int("@@{max_size_in_gb}@@")


def add_name():
    payload["name"] = "@@{file_server_name}@@"


def add_path():
    if "@@{path}@@".strip():
        payload["path"] = "@@{path}@@"


def create_payload():
    add_path()
    add_name()
    add_max_size_in_gb()
    add_compression_enabled()
    add_access_based_enumeration_enabled()
    add_encryption_enabled()
    add_ca_enaled()
    add_share_acl()
    add_description()
    add_type()


def wait(task_uuid, timeout=1800):
    max_count = timeout / 10
    count = 0
    task_status_response = None
    while count <= max_count:
        task_status_response = session.get(
            "https://{}:{}/api/nutanix/v3/tasks/{}".format(PC_IP, PC_PORT, task_uuid),
        )
        if task_status_response.status_code != 200:
            raise Exception(
                f"failed to get task, got response {task_status_response.json()}"
            )
        print(f"task status is {task_status_response.json()['status']}")
        if task_status_response.json()["status"] in {"QUEUED", "RUNNING"}:
            count += 1
            sleep(10)
        elif task_status_response.json()["status"] == "FAILED":
            raise Exception(
                f"Task status is failed, response {task_status_response.json()}"
            )
        else:
            count = 0
            break
    print(f"task_status = {task_status_response.json()['status']}")
    if count != 0:
        raise Exception("timed out waiting for task to complete")


def create():
    create_payload()
    print(f"payload: {payload}")
    create_file_server_response = session.post(
        "https://{}:{}/api/files/{}/config/file-servers/{}/mount-targets".format(
            PC_IP,
            PC_PORT,
            "@@{files_api_version}@@",
            get_file_server_extId("@@{file_server_name}@@"),
        ),
        json=payload,
    )
    print(f"create response: {create_file_server_response.json()}")
    create_file_server_response.raise_for_status()
    task_uuid = create_file_server_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")


create()
