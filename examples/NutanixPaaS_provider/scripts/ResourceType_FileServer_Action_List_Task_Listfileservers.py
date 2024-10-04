import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def list_file_servers(params):
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
    print("file_servers = " + json.dumps(json.dumps(response.json()["data"])))


params = {
    "$page": @@{page}@@,
    "$limit": @@{limit}@@,
    "$select": "@@{select}@@",
    "$orderby": "@@{order_by}@@",
}
if "@@{filter}@@":
    params["filter"] = "@@{filter}@@"

list_file_servers(params)
