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


def get_cluster_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/clustermgmt/{}/config/clusters".format(
            PC_IP, PC_PORT, "@@{cluster_mgt_api_version}@@"
        ),
        name,
    )


def get_subnet_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/networking/{}/config/subnets".format(
            PC_IP, PC_PORT, "@@{networking_api_version}@@"
        ),
        name,
    )


def get_image_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/vmm/{}/content/images".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@"
        ),
        name,
    )


def get_storage_container_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/clustermgmt/{}/config/storage-containers".format(
            PC_IP, PC_PORT, "@@{cluster_mgt_api_version}@@"
        ),
        name,
        "containerExtId",
    )


def add_iso_image(iso_image):
    print("creating vm with iso image")
    payload["cd_roms"] = [
        {
            "backingInfo": {
                "dataSource": {
                    "reference": {
                        "$objectType": "vmm.v4.ahv.config.ImageReference",
                        "imageExtId": get_image_ext_id(iso_image),
                    }
                }
            }
        }
    ]


def add_disk_image(disk_image):
    print("creating vm with disk image")
    payload["disks"] = [
        {
            "backingInfo": {
                "$objectType": "vmm.v4.ahv.config.VmDisk",
                "dataSource": {
                    "reference": {
                        "$objectType": "vmm.v4.ahv.config.ImageReference",
                        "imageExtId": get_image_ext_id(disk_image),
                    }
                },
            }
        }
    ]


def add_disk(disk_size_in_bytes, storage_container):
    payload["disks"] = [
        {
            "backingInfo": {
                "$objectType": "vmm.v4.ahv.config.VmDisk",
                "diskSizeBytes": int(disk_size_in_bytes),
                "storageContainer": {
                    "extId": get_storage_container_ext_id(storage_container)
                },
            }
        }
    ]


def add_nic(subnet):
    payload["nics"] = [
        {"networkInfo": {"subnet": {"extId": get_subnet_ext_id(subnet)}}}
    ]


def add_cloud_init(cloud_init):
    payload["guestCustomization"] = {
        "config": {
            "$objectType": "vmm.v4.r0.b1.ahv.config.CloudInit",
            "cloudInitScript": {
                "$objectType": "vmm.v4.r0.b1.ahv.config.Userdata",
                "value": base64.b64encode(cloud_init.encode("ascii")).decode("ascii"),
            },
        }
    }


def add_sys_prep(sys_prep):
    payload["guestCustomization"] = {
        "config": {
            "$objectType": "vmm.v4.ahv.config.Sysprep",
            "sysprepScript": {
                "$objectType": "vmm.v4.ahv.config.Unattendxml",
                "value": base64.b64encode(sys_prep.encode("ascii")).decode("ascii"),
            },
        }
    }


def create_payload():
    if "@@{cluster}@@":
        cluster_uuid = get_cluster_ext_id("@@{cluster}@@")
        payload["cluster"] = {"extId": cluster_uuid}
    resource_values = {
        "numSockets": "@@{num_of_sockets}@@",
        "numCoresPerSocket": "@@{num_cores_per_socket}@@",
        "numThreadsPerCore": "@@{num_threads_per_core}@@",
        "memorySizeBytes": "@@{memory_size_bytes}@@",
    }
    for name, value in resource_values.items():
        if value.strip():
            payload[name] = int(value)
    if "@@{iso_image}@@".strip():
        add_iso_image("@@{iso_image}@@")
    if "@@{disk_image}@@".strip():
        add_disk_image("@@{disk_image}@@")
    if "@@{disk_size_in_bytes}@@".strip():
        if not "@@{storage_container}@@".strip():
            raise Exception("storage container is required when disk size is provided")
        add_disk("@@{disk_size_in_bytes}@@", "@@{storage_container}@@")
    if "@@{subnet}@@".strip():
        add_nic("@@{subnet}@@")
    if "@@{description}@@".strip():
        payload["description"] = "@@{description}@@"
    if """@@{cloud_init}@@""".strip():
        add_cloud_init("""@@{cloud_init}@@""")
    if """@@{sys_prep}@@""".strip():
        add_sys_prep("""@@{sys_prep}@@""")


def wait(task_uuid, timeout=1800):
    max_count = timeout / 10
    count = 0
    task_status_response = None
    while count <= 18:
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


def update(vm_ext_id):
    vm_details_response = session.get(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", vm_ext_id
        ),
    )
    print(f"vm details response: {vm_details_response.json()}")
    vm_details_response.raise_for_status()
    create_payload()
    print(f"payload = {payload}")
    update_vm_response = session.put(
        "https://{}:{}/api/vmm/{}/ahv/config/vms/{}".format(
            PC_IP, PC_PORT, "@@{vm_api_version}@@", vm_ext_id
        ),
        json=payload,
        headers={
            "Content-Type": "application/json",
            "If-Match": vm_details_response.headers["ETag"],
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
    )
    print(f"response = {update_vm_response.json()}")
    update_vm_response.raise_for_status()
    task_uuid = update_vm_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    if "@@{wait}@@" == "Yes":
        wait(task_uuid)


update("@@{vm_extId}@@")
