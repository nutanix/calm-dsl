import requests

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


def add_total_capacity():
    if "@@{total_capacity_gib}@@".strip():
        payload["totalCapacityGiB"] = int("@@{total_capacity_gib}@@")


def add_public_network_ips():
    if "@@{public_network_ips}@@":
        payload["publicNetworkIps"] = [
            {"ipv4": {"value": ip, "prefixLength": 32}}
            for ip in "@@{public_network_ips}@@".split(",")
        ]


def add_public_network_reference():
    if "@@{public_network}@@":
        ## get the public network reference extId
        payload["publicNetworkReference"] = get_resource_ext_id(
            "https://{}:{}/api/networking/{}/config/subnets".format(
                PC_IP, PC_PORT, "@@{networking_api_version}@@"
            ),
            "@@{public_network}@@",
        )


def add_storage_network_dns_ip():
    if "@@{storage_network_dns_ip}@@":
        payload["storageNetworkDnsIp"] = {
            "ipv4": {"value": "@@{storage_network_dns_ip}@@", "prefixLength": 32}
        }


def add_storage_network_vip():
    if "@@{storage_network_vip}@@":
        payload["storageNetworkVip"] = {
            "ipv4": {"value": "@@{storage_network_vip}@@", "prefixLength": 32}
        }


def add_storage_network_reference():
    if "@@{storage_network}@@":
        ## get the storage network reference extId
        payload["storageNetworkReference"] = get_resource_ext_id(
            "https://{}:{}/api/networking/{}/config/subnets".format(
                PC_IP, PC_PORT, "@@{networking_api_version}@@"
            ),
            "@@{storage_network}@@",
        )


def add_cluster_reference():
    if "@@{cluster}@@":
        ## get the cluster reference extId
        payload["clusterReference"] = get_resource_ext_id(
            "https://{}:{}/api/clustermgmt/{}/config/clusters".format(
                PC_IP, PC_PORT, "@@{cluster_mgt_api_version}@@"
            ),
            "@@{cluster}@@",
        )


def add_worker_nodes():
    if "@@{number_of_worker_nodes}@@".strip():
        payload["numWorkerNodes"] = int("@@{number_of_worker_nodes}@@")


def add_region():
    if "@@{region}@@":
        payload["region"] = "@@{region}@@"


def add_domain():
    if "@@{domain}@@":
        payload["domain"] = "@@{domain}@@"


def add_deployment_version():
    if "@@{deployment_version}@@":
        payload["deployment_version"] = "@@{deployment_version}@@"


def add_description():
    if "@@{description}@@":
        payload["description"] = "@@{description}@@"


def create_payload():
    add_total_capacity()
    add_public_network_ips()
    add_public_network_reference()
    add_storage_network_dns_ip()
    add_storage_network_vip()
    sleep(2)
    add_storage_network_reference()
    add_cluster_reference()
    add_worker_nodes()
    add_region()
    add_domain()
    add_deployment_version()
    add_description()


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


def create(name):
    payload["name"] = name
    create_payload()
    print(f"payload: {payload}")
    create_object_storage_response = session.post(
        "https://{}:{}/api/objects/{}/operations/object-stores".format(
            PC_IP, PC_PORT, "@@{objects_api_version}@@"
        ),
        json=payload,
    )
    print(f"create response: {create_object_storage_response.json()}")
    create_object_storage_response.raise_for_status()
    task_uuid = create_object_storage_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    if "@@{wait}@@" == "Yes":
        wait(task_uuid)


create("@@{object_store_name}@@")
