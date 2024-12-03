import requests
import uuid

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"


session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False

payload = {}


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


def update_resources():
    resource_values = {
        "numSockets": "@@{num_of_sockets}@@",
        "numCoresPerSocket": "@@{num_cores_per_socket}@@",
        "numThreadsPerCore": "@@{num_threads_per_core}@@",
        "memorySizeBytes": "@@{memory_size_bytes}@@",
    }
    for name, value in resource_values.items():
        if value.strip():
            payload[name] = int(value)


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


def clone(clone_from_ext_id, cloned_vm_name):
    payload["name"] = cloned_vm_name
    update_resources()
    vm_details_response = session.get(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", clone_from_ext_id
        ),
        headers={
            "accept": "application/json",
        },
    )
    print(f"vm details response: {vm_details_response.json()}")
    vm_details_response.raise_for_status()
    clone_vm_response = session.post(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}/$actions/clone".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", clone_from_ext_id
        ),
        headers={
            "accept": "application/json",
            "If-Match": vm_details_response.headers["ETag"],
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
        json=payload,
    )
    print(f"vm clone response: {clone_vm_response.json()}")
    clone_vm_response.raise_for_status()
    task_uuid = clone_vm_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    if "@@{wait}@@" == "Yes":
        wait(task_uuid)


clone("@@{clone_from_extId}@@", "@@{cloned_vm_name}@@")
