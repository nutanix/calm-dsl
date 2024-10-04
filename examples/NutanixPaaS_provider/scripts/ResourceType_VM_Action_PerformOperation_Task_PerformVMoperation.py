import requests
import uuid

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


def wait(task_uuid, timeout=1800):
    max_count = timeout / 10
    count = 0
    task_status_response = None
    while count <= max_count:
        task_status_response = session.get(
            "https://{}:{}/api/prism/{}/config/tasks/{}".format(
                PC_IP, PC_PORT, "@@{prism_api_version}@@", task_uuid
            ),
        )
        if task_status_response.status_code != 200:
            raise Exception(
                f"failed to get task, got response {task_status_response.json()}"
            )
        print(f"task status is {task_status_response.json()['data']['status']}")
        if task_status_response.json()["data"]["status"] in {"QUEUED", "RUNNING"}:
            count += 1
            sleep(10)
        else:
            count = 0
            break
    print(f"task_status = {task_status_response.json()['data']['status']}")
    if count != 0:
        raise Exception("timed out waiting for task to complete")


def peform_action(vm_ext_id, action):
    vm_details_response = session.get(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", vm_ext_id
        ),
        verify=False,
    )
    print(f"vm details response: {vm_details_response.json()}")
    vm_details_response.raise_for_status()
    print(f"performing {action} on {vm_ext_id}".format(action))
    vm_action_response = session.post(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}/$actions/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", vm_ext_id, action
        ),
        headers={
            "accept": "application/json",
            "If-Match": vm_details_response.headers["ETag"],
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
    )
    print(f"vm action response: {vm_action_response.json()}")
    vm_action_response.raise_for_status()
    task_uuid = vm_action_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    if "@@{wait}@@" == "Yes":
        wait(task_uuid)


peform_action("@@{vm_extId}@@", "@@{action}@@")
