import requests

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False


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


def delete(extId):
    response = session.delete(
        "https://{}:{}/api/microseg/{}/config/policies/{}".format(
            PC_IP, PC_PORT, "@@{flow_api_version}@@", extId
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


policy_extId = "@@{policy_name}@@".split(":")[1]
delete(policy_extId)
