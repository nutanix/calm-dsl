import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {}


def pool_list_payload(plist):
    plist = plist.strip().split(",")
    ip_pool_list = []
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


def create_payload():
    payload["spec"] = {"name": "@@{subnet_name}@@".strip()}
    if "@@{description}@@" != "":
        payload["spec"].update({"description": "@@{description}@@"})

    payload["spec"]["resources"] = {"subnet_type": "OVERLAY"}
    payload["spec"]["resources"]["vpc_reference"] = {
        "kind": "vpc",
        "uuid": "@@{vpc_uuid}@@".strip().split(":")[1],
    }
    payload["spec"]["resources"]["ip_config"] = {
        "default_gateway_ip": "@@{default_gateway_ip}@@".strip()
    }
    payload["spec"]["resources"]["ip_config"].update(
        {
            "prefix_length": int("@@{subnet_ip}@@".strip().split("/")[1]),
            "subnet_ip": "@@{subnet_ip}@@".strip().split("/")[0],
        }
    )
    pool_list_payload("@@{pool_list}@@")
    dhcp_payload()
    payload["spec"]["resources"].update(
        {
            "virtual_network_reference": {
                "kind": "virtual_network",
                "uuid": "@@{vpc_uuid}@@".strip().split(":")[1],
            }
        }
    )
    payload["metadata"] = {"kind": "subnet"}


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


def create_overlay_subnet():
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


create_overlay_subnet()
