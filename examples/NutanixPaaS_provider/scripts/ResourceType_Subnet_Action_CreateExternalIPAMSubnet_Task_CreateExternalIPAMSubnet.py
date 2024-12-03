import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {}


def create_payload():
    pe_cluster_uuid = "@@{pe_cluster_uuid}@@".strip().split(":")[1]
    virtual_switch_uuid = "@@{virtual_switch_uuid}@@".strip().split(":")[1]
    description = "@@{description}@@"
    vlan_id = int("@@{vlan_id}@@".strip())
    subnet_name = "@@{subnet_name}@@".strip()
    subnet_ip = "@@{subnet_ip}@@".strip().split("/")[0]
    prefix_length = int("@@{subnet_ip}@@".strip().split("/")[1])
    default_gateway_ip = "@@{default_gateway_ip}@@".strip()
    ip_pool_list = []
    plist = "@@{pool_list}@@".strip().split(",")
    if len(plist[0]) != 0:
        for p in "@@{pool_list}@@".strip().split(","):
            p = p.replace('"', "")
            val = {"range": p}
            ip_pool_list.append(val)
    else:
        raise Exception("IP Pool list is not provided.")

    enable_nat = @@{enable_nat}@@

    payload1 = {
        "spec": {
            "name": subnet_name,
            "description": description,
            "resources": {
                "subnet_type": "VLAN",
                "virtual_switch_uuid": virtual_switch_uuid,
                "is_external": True,
                "ip_config": {
                    "default_gateway_ip": default_gateway_ip,
                    "pool_list": ip_pool_list,
                    "prefix_length": prefix_length,
                    "subnet_ip": subnet_ip,
                },
                "enable_nat": enable_nat,
                "external_connectivity_state": "DISABLED",
                "vlan_id": vlan_id,
            },
            "cluster_reference": {"kind": "cluster", "uuid": pe_cluster_uuid},
        },
        "metadata": {"kind": "subnet"},
    }
    payload.update(payload1)


def wait(task_uuid, timeout=1800):
    max_count = timeout / 10
    count = 0
    task_status_response = None
    while count <= 18:
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


def create_ext_subnet_ipam():
    create_payload()
    print(f"payload = {payload}")
    create = session.post(
        "https://{}:{}/api/nutanix/v3/subnets".format(PC_IP, PC_PORT),
        json=payload,
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    print(f"response = {create.json()}")
    create.raise_for_status()
    task_uuid = create.json()["status"]["execution_context"]["task_uuid"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


create_ext_subnet_ipam()
