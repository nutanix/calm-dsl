# update_normal_subnet
import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {}


def get_data(url, name, payload):
    response = session.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    print(f"get {url} response: {response.json()}")
    response.raise_for_status()

    r = json.loads(response.content)
    for sname in r["entities"]:
        if sname["status"]["name"] == name:
            uuid = sname["metadata"]["uuid"]
            spec_v = sname["metadata"]["spec_version"]
            return uuid, int(spec_v)

    raise Exception(f"failed to get extId for {name}")


def get_other_details(name):
    payload = {"kind": "subnet", "length": 50, "offset": 0}
    response = session.post(
        "https://{}:{}/api/nutanix/v3/subnets/list".format(PC_IP, PC_PORT),
        json=payload,
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    print(f"get immutable_data response: {response.json()}")
    response.raise_for_status()

    r = json.loads(response.content)
    for sname in r["entities"]:
        if sname["status"]["name"] == name:
            virtual_network_reference_uuid = sname["status"]["resources"][
                "virtual_network_reference"
            ]["uuid"]
            external_connectivity_state = sname["status"]["resources"][
                "external_connectivity_state"
            ]
            vpc_reference_uuid = sname["status"]["resources"]["vpc_reference"]["uuid"]
            subnet_ip = sname["status"]["resources"]["ip_config"]["subnet_ip"]
            prefix_length = sname["status"]["resources"]["ip_config"]["prefix_length"]
            default_gateway_ip = sname["status"]["resources"]["ip_config"][
                "default_gateway_ip"
            ]
            return (
                virtual_network_reference_uuid,
                subnet_ip,
                prefix_length,
                vpc_reference_uuid,
                external_connectivity_state,
                default_gateway_ip,
            )

    raise Exception(f"failed to get extId for {name}")


def get_uuid(name):
    return get_data(
        "https://{}:{}/api/nutanix/v3/subnets/list".format(PC_IP, PC_PORT),
        name,
        {"kind": "subnet", "length": 50, "offset": 0},
    )


def get_ip_pool():
    subnetnm = "@@{subnet_name}@@".strip().split(":")[0]
    api = "https://{}:{}/api/nutanix/v3/subnets/list".format(PC_IP, PC_PORT)
    payload = {
        "kind": "subnet",
        "filter": f"name=={subnetnm}",
        "offset": 0,
        "length": 50,
    }
    r = session.post(api, json=payload)
    r.raise_for_status()
    r = json.loads(r.content)
    tmp_pool = []
    if "ip_config" in r["entities"][0]["spec"]["resources"]:
        if "pool_list" in r["entities"][0]["spec"]["resources"]["ip_config"]:
            for pools in r["entities"][0]["spec"]["resources"]["ip_config"][
                "pool_list"
            ]:
                tmp_pool.append(pools)
    print("Existing pool_list:", tmp_pool)
    return tmp_pool


def pool_list_payload(plist):
    plist = plist.strip().split(",")
    ip_pool_list = get_ip_pool()
    if len(plist[0]) != 0:
        for p in plist:
            p = p.replace('"', "")
            val = {"range": p}
            ip_pool_list.append(val)
        payload["spec"]["resources"]["ip_config"].update({"pool_list": ip_pool_list})


def dhcp_payload():
    if (
        "@@{domain_name_server_list}@@" != ""
        or "@@{boot_file_name}@@" != ""
        or "@@{domain_name}@@" != ""
        or "@@{tftp_server_name}@@" != ""
        or "@@{domain_search_list}@@" != ""
    ):
        payload["spec"]["resources"]["ip_config"]["dhcp_options"] = {}
    dnsip_list = "@@{domain_name_server_list}@@".strip().split(",")
    dns_ip_list = []
    if len(dnsip_list[0]) != 0:
        for p in dnsip_list:
            p = p.strip().replace('"', "")
            val = p
            dns_ip_list.append(val)
        payload["spec"]["resources"]["ip_config"]["dhcp_options"].update(
            {"domain_name_server_list": dns_ip_list}
        )
    if "@@{boot_file_name}@@" != "":
        payload["spec"]["resources"]["ip_config"]["dhcp_options"].update(
            {"boot_file_name": "@@{boot_file_name}@@"}
        )
    if "@@{domain_name}@@" != "":
        payload["spec"]["resources"]["ip_config"]["dhcp_options"].update(
            {"domain_name": "@@{domain_name}@@"}
        )
    if "@@{tftp_server_name}@@" != "":
        payload["spec"]["resources"]["ip_config"]["dhcp_options"].update(
            {"tftp_server_name": "@@{tftp_server_name}@@"}
        )

    ds_list = "@@{domain_search_list}@@".strip().split(",")
    ds_ip_list = []
    if len(ds_list[0]) != 0:
        for p in ds_list:
            p = p.strip().replace('"', "")
            val = p
            ds_ip_list.append(val)
        payload["spec"]["resources"]["ip_config"]["dhcp_options"].update(
            {"domain_search_list": ds_ip_list}
        )


def create_payload(spec_version):
    payload["spec"] = {"name": "@@{subnet_name}@@".strip().split(":")[0]}
    # payload['spec']['cluster_reference'] = { "kind": "cluster","uuid":'@@{pe_cluster_uuid}@@'.strip().split(':')[1] }
    if "@@{description}@@" != "":
        payload["spec"].update({"description": "@@{description}@@"})
    # hard code immutable values
    payload["spec"]["resources"] = {"subnet_type": "OVERLAY"}
    (
        virtual_network_reference_uuid,
        subnet_ip,
        prefix_length,
        vpc_reference_uuid,
        external_connectivity_state,
        default_gateway_ip,
    ) = get_other_details("@@{subnet_name}@@".strip().split(":")[0])
    payload["spec"]["resources"].update(
        {"vpc_reference": {"kind": "vpc", "uuid": vpc_reference_uuid}}
    )
    payload["spec"]["resources"].update(
        {
            "virtual_network_reference": {
                "kind": "virtual_network",
                "uuid": virtual_network_reference_uuid,
            }
        }
    )
    payload["spec"]["resources"]["ip_config"] = {
        "default_gateway_ip": default_gateway_ip,
        "subnet_ip": subnet_ip,
        "prefix_length": prefix_length,
    }
    pool_list_payload("@@{pool_list}@@")
    dhcp_payload()
    payload["metadata"] = {"kind": "subnet", "spec_version": spec_version}


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


def update_subnet():
    UUID, spec_version = get_uuid("@@{subnet_name}@@".strip().split(":")[0])
    create_payload(spec_version)
    print(f"payload = {payload}")
    update = session.put(
        "https://{}:{}/api/nutanix/v3/subnets/{}".format(PC_IP, PC_PORT, UUID),
        json=payload,
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    print(f"response = {update.json()}")
    update.raise_for_status()
    task_uuid = update.json()["status"]["execution_context"]["task_uuid"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


update_subnet()
