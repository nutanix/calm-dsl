import requests

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


def get_vpc_ext_id(name):
    return get_resource_ext_id(
        "https://{}:{}/api/networking/{}/config/vpcs".format(
            PC_IP, PC_PORT, "@@{flow_virtual_network_api_version}@@"
        ),
        name,
    )


def get_policy_extid():
    vpc_name = "@@{delete_policy}@@".split(":")[0]
    policy_name = "@@{delete_policy}@@".split(":")[1]
    priority = "@@{delete_policy}@@".split(":")[2]
    headers = {"Content-Type": "application/json"}
    response = session.get(
        "https://{}:{}/api/networking/{}/config/routing-policies".format(
            PC_IP, PC_PORT, "v4.0.b1"
        ),
        headers=headers,
        verify=False,
    )
    extID = [
        d["extId"]
        for d in response.json()["data"]
        if d["name"] == policy_name
        and d["vpcExtId"] == get_vpc_ext_id(vpc_name)
        and d["priority"] == int(priority)
    ]
    return extID[0]


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


def delete():
    response = session.delete(
        "https://{}:{}/api/networking/{}/config/routing-policies/{}".format(
            PC_IP, PC_PORT, "@@{flow_virtual_network_api_version}@@", get_policy_extid()
        ),
        headers={
            "Content-Type": "application/json",
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
        timeout=120,
    )
    print(f"delete response: {response.text}")
    response.raise_for_status()
    task_uuid = response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


delete()
