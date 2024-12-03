import requests
import re

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {"platform": {"$objectType": "files.v4.config.OnPrem"}}


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


def get_subnet_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/networking/{}/config/subnets".format(
            PC_IP, PC_PORT, "@@{networking_api_version}@@"
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


def get_cluster_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/clustermgmt/{}/config/clusters".format(
            PC_IP, PC_PORT, "@@{cluster_mgt_api_version}@@"
        ),
        name,
    )


def add_storage_container():
    payload["storageContainerId"] = get_storage_container_ext_id(
        "@@{storage_container}@@"
    )


def add_file_server_storage():
    payload["sizeGiBytes"] = int("@@{file_server_size_in_gb}@@")


def add_server_version():
    payload["version"] = "@@{file_server_version}@@"


def add_rebalance_enabled():
    payload["isRebalanceEnabled"] = (
        True if "@@{rebalance_enabled}@@" == "Yes" else False
    )


def add_compression_enabled():
    payload["isCompressionEnabled"] = (
        True if "@@{compression_enabled}@@" == "Yes" else False
    )


def add_file_blocking_extensions():
    if "@@{file_blocking_extensions}@@":
        payload["fileBlockingExtensions"] = "@@{file_blocking_extensions}@@"


def add_dns_domain():
    payload["dnsDomainName"] = "@@{dns_domain_name}@@"


def add_dns_servers():
    payload["dnsServers"] = []
    for dns_server_ip in "@@{dns_servers}@@".split(","):
        payload["dnsServers"].append({"value": dns_server_ip})


def add_ntp_servers():
    payload["ntpServers"] = []
    for ntp_server_ip in "@@{ntp_servers}@@".split(","):
        if re.search(r"\w+", ntp_server_ip):
            payload["ntpServers"].append({"fqdn": {"value": ntp_server_ip}})
        else:
            payload["ntpServers"].append({"ipv4": {"value": ntp_server_ip}})


def add_deployment_type():
    payload["deploymentType"] = "@@{type_of_deployment}@@"


def add_platform_type():
    payload["platformType"] = "ON_PREM"


def add_internal_network_reference():
    payload["platform"]["internalNetworks"] = [
        {
            "isManaged": (
                True if "@@{internal_network_is_managed}@@" == "Yes" else False
            ),
            "networkExtId": get_subnet_ext_id("@@{internal_network_vlan}@@"),
            "subnetMask": {"ipv4": {"value": "@@{internal_network_subnet_mask}@@"}},
            "defaultGateway": {
                "ipv4": {"value": "@@{internal_network_default_gateway}@@"}
            },
            "ipAddresses": [
                {"ipv4": {"value": ip}}
                for ip in "@@{internal_network_ip_address}@@".split(",")
            ],
        }
    ]


def add_external_network_reference():
    payload["platform"]["externalNetworks"] = [
        {
            "isManaged": (
                True if "@@{external_network_is_managed}@@" == "Yes" else False
            ),
            "networkExtId": get_subnet_ext_id("@@{external_network_vlan}@@"),
            "subnetMask": {"ipv4": {"value": "@@{external_network_subnet_mask}@@"}},
            "defaultGateway": {
                "ipv4": {"value": "@@{external_network_default_gateway}@@"}
            },
            "ipAddresses": [
                {"ipv4": {"value": ip}}
                for ip in "@@{external_network_ip_address}@@".split(",")
            ],
        }
    ]


def add_vm():
    payload["nvmsCount"] = int("@@{vm_count}@@")


def add_cluster():
    payload["platform"]["clusterExtId"] = get_cluster_ext_id("@@{cluster_name}@@")


def add_vm_vcpu():
    payload["platform"]["vcpus"] = int("@@{vm_vcpu}@@")


def add_vm_memory():
    payload["platform"]["memoryGib"] = int("@@{vm_memory_gib}@@")


def create_payload():
    add_storage_container()
    add_file_server_storage()
    add_server_version()
    add_rebalance_enabled()
    add_compression_enabled()
    add_file_blocking_extensions()
    add_dns_domain()
    add_dns_servers()
    add_ntp_servers()
    add_deployment_type()
    add_platform_type()
    add_internal_network_reference()
    add_external_network_reference()
    add_vm()
    add_cluster()
    add_vm_vcpu()
    add_vm_memory()


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


def create(name):
    payload["name"] = name
    create_payload()
    print(f"payload: {payload}")
    create_file_server_response = session.post(
        "https://{}:{}/api/files/{}/config/file-servers".format(
            PC_IP, PC_PORT, "@@{files_api_version}@@"
        ),
        json=payload,
    )
    print(f"create response: {create_file_server_response.json()}")
    create_file_server_response.raise_for_status()
    task_uuid = create_file_server_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")


create("@@{file_server_name}@@")
