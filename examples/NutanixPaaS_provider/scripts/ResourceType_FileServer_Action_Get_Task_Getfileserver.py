import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def get_file_server(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/files/{}/config/file-servers".format(
            PC_IP, PC_PORT, "@@{files_api_version}@@"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    file_server_data = response.json()["data"]
    if (
        len(file_server_data) == 1
        and file_server_data[0]["name"] == "@@{file_server_name}@@"
    ):
        print("file_server = " + json.dumps(json.dumps(file_server_data[0])))
    else:
        raise Exception("File server not found")


params = {
    "$page": 0,
    "$limit": 1,
    "$select": "extId, name, sizeInGib",
    "$orderby": "name",
    "filter": "name eq '@@{file_server_name}@@'",
}

get_file_server(params)
