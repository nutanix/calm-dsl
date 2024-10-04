import requests
import uuid

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


def update_description():
    if "@@{description}@@".strip():
        payload["description"] = "@@{description}@@"


def update_type():
    if "@@{type}@@" != "-":
        payload["type"] = "@@{type}@@"


def update_access_based_enumeration_enabled():
    if "@@{access_based_enumeration_enabled}@@" != "-":
        payload["smbProperties"]["isAccessBasedEnumerationEnabled"] = (
            True if "@@{access_based_enumeration_enabled}@@" == "Yes" else False
        )


def update_compression_enabled():
    if "@@{compression_enabled}@@" != "-":
        payload["isCompressionEnabled"] = (
            True if "@@{compression_enabled}@@" == "Yes" else False
        )


def update_encryption_enabled():
    if "@@{encryption_enabled}@@" != "-":
        payload["smbProperties"]["isSmb3EncryptionEnabled"] = (
            True if "@@{encryption_enabled}@@" == "Yes" else False
        )


def update_ca_enaled():
    if "@@{ca_enabled}@@" != "-":
        payload["smbProperties"]["isCaEnabled"] = (
            True if "@@{ca_enabled}@@" == "Yes" else False
        )


def update_share_acl():
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


def update_compression_enabled():
    if "@@{compression_enabled}@@" != "-":
        payload["enableCompression"] = (
            True if "@@{compression_enabled}@@" == "Yes" else False
        )


def update_max_size_in_gb():
    if "@@{max_size_in_gb}@@".strip() and int("@@{max_size_in_gb}@@") != 0:
        payload["maxSizeGiBytes"] = int("@@{max_size_in_gb}@@")


def update_path():
    if "@@{path}@@".strip():
        payload["path"] = "@@{path}@@"


def create_payload():
    update_path()
    update_max_size_in_gb()
    update_compression_enabled()
    update_access_based_enumeration_enabled()
    update_encryption_enabled()
    update_ca_enaled()
    update_share_acl()
    update_description()
    update_type()


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


def get_mount_target_extId(name):
    params = {
        "$page": 0,
        "$limit": 1,
        "$select": "extId, name",
        "$orderby": "name",
        "filter": f"name eq '{name}'",
    }
    response = session.get(
        "https://{}:{}/api/files/{}/config/file-servers/{}/mount-targets".format(
            PC_IP,
            PC_PORT,
            "@@{files_api_version}@@",
            get_file_server_extId("@@{file_server_name}@@"),
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
    )
    print(f"list mount target response: {response.json()}")
    response.raise_for_status()
    mount_target_response_data = response.json()["data"]
    if len(mount_target_response_data) == 1:
        return mount_target_response_data[0]["extId"]
    else:
        raise Exception("Mount target not found")


def update(name):
    payload["name"] = name
    create_payload()
    print(f"payload: {payload}")
    mount_target_extId = get_mount_target_extId(name)
    filer_server_extId = get_file_server_extId("@@{file_server_name}@@")
    mount_target = session.get(
        "https://{}:{}/api/files/{}/config/file-servers/{}/mount-targets/{}".format(
            PC_IP,
            PC_PORT,
            "@@{files_api_version}@@",
            filer_server_extId,
            mount_target_extId,
        )
    )
    print(f"get mount target response: {mount_target.json()}")
    mount_target.raise_for_status()
    update_mount_target_response = session.put(
        "https://{}:{}/api/files/{}/config/file-servers/{}/mount-targets/{}".format(
            PC_IP,
            PC_PORT,
            "@@{files_api_version}@@",
            filer_server_extId,
            mount_target_extId,
        ),
        headers={
            "Content-Type": "application/json",
            "If-Match": mount_target.headers["ETag"],
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
        json=payload,
    )
    print(f"update response: {update_mount_target_response.json()}")
    update_mount_target_response.raise_for_status()
    task_uuid = update_mount_target_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")


update("@@{mount_target_name}@@")
