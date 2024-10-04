import requests
import uuid
import base64

PC_USERNAME = "@@{account.username}@@"
PC_PASSWORD = "@@{account.password}@@"
PC_IP = "@@{account.pc_server}@@"
PC_PORT = "@@{account.pc_port}@@"
session = requests.Session()
session.auth = (PC_USERNAME, PC_PASSWORD)
session.verify = False
payload = {}


def get_resource_ext_id(url, name, id_key="extId"):
    keyname = name.split(":")[0]
    keyvalue = name.split(":")[1]
    response = session.get(
        url,
        headers={
            "accept": "application/json",
        },
        params={
            "$page": 0,
            "$limit": 1,
            "$filter": f"key eq '{keyname}' and value eq '{keyvalue}'",
        },
    )
    # print(f"get {name} response: {response.json()}")
    response.raise_for_status()
    data = response.json().get("data")
    if data:
        if isinstance(data, list):
            if (
                id_key in data[0]
                and data[0]["key"] == keyname
                and data[0]["value"] == keyvalue
            ):
                return data[0][id_key]
        else:
            if id_key in data:
                return data[id_key]
    raise Exception(f"failed to get extId for {name}")


def get_category_extID(category_name):
    return get_resource_ext_id(
        "https://{}:{}/api/prism/{}/config/categories".format(
            PC_IP, PC_PORT, "@@{prism_api_version}@@"
        ),
        category_name,
    )


def get_categorygroup_extId(names):
    group_names = names.split(",")
    extId_list = []
    for category_name in group_names:
        extId_list.append(get_category_extID(category_name))
    return extId_list


def add_two_env_isolation_rule():
    # Variables :
    # 10. firstIsolationGroup
    # 11. secondIsolationGroup #both comma separated list
    payload["rules"][0].update(
        {
            "spec": {
                "firstIsolationGroup": get_categorygroup_extId(
                    "@@{firstIsolationGroup}@@"
                ),
                "secondIsolationGroup": get_categorygroup_extId(
                    "@@{secondIsolationGroup}@@"
                ),
                "$objectType": "microseg.v4.config.TwoEnvIsolationRuleSpec",
            }
        }
    )


def create_payload():
    # Variables ::
    # 1. name, 2. description :
    # 3. type : ISOLATION / [QUARANTINE/APPLICATION] APPLICATION -> 3.1. Generic 3.2. VDI
    # 4. state : SAVE, MONITOR(Apply), ENFORCE(Apply Enforce)
    # 5. isIpv6TrafficAllowed : True/False 6. isHitlogEnabled : True/False
    # 7. scope : ALL_VLAN / VPC_LIST 8. vpcReferences [if no vpcRef then def scope is all_vlan]
    # 9. rule_type : QUARANTINE / INTRA_GROUP / APPLICATION / TWO_ENV_ISOLATION
    payload["name"] = "@@{policy_name}@@".strip()
    payload["type"] = "ISOLATION"
    payload["$objectType"] = "microseg.v4.config.NetworkSecurityPolicy"
    payload["state"] = "@@{policy_state}@@"

    if "@@{scope}@@" != "":
        payload["scope"] = "@@{scope}@@"
    elif "@@{vpcReferences}@@" != "":
        payload["scope"] = "VPC_LIST"
        vpclist = [vpc.split(":")[1] for vpc in "@@{vpcReferences}@@".split(",")]
        payload["vpcReferences"] = vpclist
    else:
        payload["scope"] = "ALL_VLAN"

    if "@@{description}@@" != "":
        payload["description"] = "@@{description}@@"

    payload["isIpv6TrafficAllowed"] = False
    if "@@{isIpv6TrafficAllowed}@@" == "True":
        payload["isIpv6TrafficAllowed"] = True
    payload["isHitlogEnabled"] = False
    if "@@{isHitlogEnabled}@@" == "True":
        payload["isHitlogEnabled"] = True

    payload["rules"] = [{"type": "TWO_ENV_ISOLATION"}]
    add_two_env_isolation_rule()


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


def create():
    create_payload()
    print(f"payload: {payload}")
    create_security_policy_response = session.post(
        "https://{}:{}/api/microseg/{}/config/policies".format(
            PC_IP, PC_PORT, "@@{flow_api_version}@@"
        ),
        json=payload,
        headers={
            "Content-Type": "application/json",
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
    )
    print(f"create response: {create_security_policy_response.json()}")
    create_security_policy_response.raise_for_status()
    task_uuid = create_security_policy_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


create()
