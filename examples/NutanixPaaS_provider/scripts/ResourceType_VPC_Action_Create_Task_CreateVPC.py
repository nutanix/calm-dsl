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
    vpc_name = "@@{vpc_name}@@".strip()
    vpc_type = "REGULAR"
    external_subnet_reference = "@@{external_subnet_reference}@@".strip().split(":")[1]

    dnsip_list = "@@{common_domain_name_server_ip_list}@@".strip().split(",")
    dns_ip_list = []
    if len(dnsip_list[0]) != 0:
        for p in dnsip_list:
            p = p.strip().replace('"', "")
            val = {"ip": p}
            dns_ip_list.append(val)

    extrouteip_list = "@@{externally_routable_prefix_list}@@".strip().split(",")
    ext_route_prefix_list = []
    if len(extrouteip_list[0]) != 0:
        for p in extrouteip_list:
            p = p.strip().replace('"', "")
            p_ip = p.split("/")[0]
            p_prefix = p.split("/")[1]
            val = {"ip": p_ip, "prefix_length": int(p_prefix)}
            ext_route_prefix_list.append(val)

    payload["spec"] = {"name": vpc_name}
    payload["spec"]["resources"] = {"vpc_type": vpc_type}
    payload["spec"]["resources"]["external_subnet_list"] = [
        {
            "external_subnet_reference": {
                "kind": "subnet",
                "uuid": external_subnet_reference,
            }
        }
    ]
    if dns_ip_list:
        payload["spec"]["resources"]["common_domain_name_server_ip_list"] = dns_ip_list
    if ext_route_prefix_list:
        payload["spec"]["resources"][
            "externally_routable_prefix_list"
        ] = ext_route_prefix_list
    if "@@{Description}@@".strip() != "":
        payload["spec"]["description"] = "@@{Description}@@".strip()
    payload["metadata"] = {"kind": "vpc"}


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


def create_vpc():
    create_payload()
    print(f"payload = {payload}")
    create_vpc = session.post(
        "https://{}:{}/api/nutanix/v3/vpcs".format(PC_IP, PC_PORT),
        json=payload,
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    print(f"response = {create_vpc.json()}")
    create_vpc.raise_for_status()
    task_uuid = create_vpc.json()["status"]["execution_context"]["task_uuid"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


create_vpc()
