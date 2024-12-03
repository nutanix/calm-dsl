import requests
import re
import uuid

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {
    "platform": {
        "$objectType": "files.v4.config.OnPrem",
    }
}


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


def add_file_server_storage():
    if "@@{file_server_size_in_gb}@@".strip():
        payload["sizeGiBytes"] = int("@@{file_server_size_in_gb}@@")


def add_rebalance_enabled():
    if "@@{rebalance_enabled}@@" != "-":
        payload["isRebalanceEnabled"] = (
            True if "@@{rebalance_enabled}@@" == "Yes" else False
        )


def add_compression_enabled():
    if "@@{compression_enabled}@@" != "-":
        payload["isCompressionEnabled"] = (
            True if "@@{compression_enabled}@@" == "Yes" else False
        )


def add_file_blocking_extensions():
    if "@@{file_blocking_extensions}@@".strip():
        payload["fileBlockingExtensions"] = "@@{file_blocking_extensions}@@"


def add_dns_domain():
    if "@@{dns_domain_name}@@".strip():
        payload["dnsDomainName"] = "@@{dns_domain_name}@@"


def add_dns_servers():
    if "@@{dns_servers}@@".strip():
        payload["dnsServers"] = []
        for dns_server_ip in "@@{dns_servers}@@".split(","):
            payload["dnsServers"].append({"value": dns_server_ip})


def add_ntp_servers():
    if "@@{ntp_servers}@@".strip():
        payload["ntpServers"] = []
        for ntp_server_ip in "@@{ntp_servers}@@".split(","):
            if re.search(r"\w+", ntp_server_ip):
                payload["ntpServers"].append({"fqdn": {"value": ntp_server_ip}})
            else:
                payload["ntpServers"].append({"ipv4": {"value": ntp_server_ip}})


def add_vm():
    if "@@{vm_count}@@".strip() and int("@@{vm_count}@@") != 0:
        payload["nvmsCount"] = int("@@{vm_count}@@")


def add_vm_vcpu():
    if "@@{vm_vcpu}@@".strip() and int("@@{vm_vcpu}@@") != 0:
        payload["platform"]["vcpus"] = int("@@{vm_vcpu}@@")


def add_vm_memory():
    if "@@{vm_memory_gib}@@".strip() and int("@@{vm_memory_gib}@@") != 0:
        payload["platform"]["memoryGib"] = int("@@{vm_memory_gib}@@")


def create_payload():
    add_file_server_storage()
    add_rebalance_enabled()
    add_compression_enabled()
    add_file_blocking_extensions()
    add_dns_domain()
    add_dns_servers()
    add_ntp_servers()
    add_vm()
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


def get_file_server_response(params):
    response = session.get(
        "https://{}:{}/api/files/{}/config/file-servers".format(
            PC_IP, PC_PORT, "@@{files_api_version}@@"
        ),
        params=params,
    )
    print(f"list file server response: {response.json()}")
    response.raise_for_status()
    file_server_data = response.json()["data"]
    if (
        len(file_server_data) == 1
        and file_server_data[0]["name"] == "@@{file_server_name}@@"
    ):
        file_server_get_response = session.get(
            "https://{}:{}/api/files/{}/config/file-servers/{}".format(
                PC_IP,
                PC_PORT,
                "@@{files_api_version}@@",
                file_server_data[0]["extId"],
            )
        )
        print(f"get file server response: {response.json()}")
        file_server_get_response.raise_for_status()
        return file_server_get_response
    else:
        raise Exception("File server not found")


def update(name):
    payload["name"] = name
    create_payload()
    print(f"payload: {payload}")
    file_server_get_response = get_file_server_response(
        params={
            "$page": 0,
            "$limit": 1,
            "$select": "extId, name, sizeInGib",
            "$orderby": "name",
            "filter": f"name eq '{name}'",
        }
    )
    update_file_server_response = session.put(
        "https://{}:{}/api/files/{}/config/file-servers".format(
            PC_IP, PC_PORT, "@@{files_api_version}@@"
        ),
        headers={
            "Content-Type": "application/json",
            "If-Match": file_server_get_response.headers["ETag"],
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
        json=payload,
    )
    print(f"update response: {update_file_server_response.json()}")
    update_file_server_response.raise_for_status()
    task_uuid = update_file_server_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    if "@@{wait}@@" == "Yes":
        wait(task_uuid)


update("@@{file_server_name}@@")
