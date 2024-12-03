import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def list_vm(params):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/vmm/{}/ahv/config/vms".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@"
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        params=params,
        headers=headers,
        verify=False,
    )
    print(f"response: {response.json()}")
    response.raise_for_status()
    if not response.json().get("data"):
        print(response.json())
        raise Exception("unable to list vms, please check the parameters")
    print("vms = " + json.dumps(json.dumps(response.json()["data"])))


params = {
    "$page": @@{page}@@,
    "$limit": @@{limit}@@,
    "$select": "@@{select}@@",
    "$orderby": "@@{orderby}@@",
    "$filter": "@@{filter}@@",
}

list_vm(params)
