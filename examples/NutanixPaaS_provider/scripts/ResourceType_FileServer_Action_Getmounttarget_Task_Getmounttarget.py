import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"

session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False


def get_file_server_extId(file_server_name):
    params = {
        "$page": 0,
        "$limit": 1,
        "$select": "extId, name",
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


def get_mount_target(name):
    get_mount_target_response = session.get(
        "https://{}:{}/api/files/{}/config/file-servers/{}/mount-targets/{}".format(
            PC_IP,
            PC_PORT,
            "@@{files_api_version}@@",
            get_file_server_extId("@@{file_server_name}@@"),
            get_mount_target_extId(name),
        )
    )
    print(f"get mount target response: {get_mount_target_response.json()}")
    get_mount_target_response.raise_for_status()
    print(
        "mount_target = "
        + json.dumps(json.dumps(get_mount_target_response.json()["data"]))
    )


get_mount_target("@@{mount_target_name}@@")
