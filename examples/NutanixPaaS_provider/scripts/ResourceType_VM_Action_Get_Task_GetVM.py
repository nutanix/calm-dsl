import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


def get(vm_ext_id):
    headers = {
        "accept": "application/json",
    }
    response = requests.get(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", vm_ext_id
        ),
        auth=(PC_USERNAME, PC_PASSWORD),
        headers=headers,
        verify=False,
    )
    print(f"response = {response.json()}")
    response.raise_for_status()
    print("vm = " + json.dumps(json.dumps(response.json()["data"])))


get("@@{vm_extId}@@")
