import requests
import re
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

ipv4 = r"^(?:\d{1,3}\.){3}\d{1,3}$"
ipv6 = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"


def find(Ip):
    if re.search(ipv4, Ip):
        return "ipv4"
    elif re.search(ipv6, Ip):
        return "ipv6"
    else:
        print("Not a valid ip address")


# ---------------------------------------------------------------------------
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


# -------------------------------------------------------------------------------------------
def add_subnet(address_Type, subnet_ip):
    # addressType = EXTERNAL or ANY or Custom(SUBNET)
    tmp1 = {}
    tmp1["addressType"] = address_Type.strip()
    if address_Type.strip() == "SUBNET":
        subnet_ipaddr = subnet_ip.split("/")[0]
        subnet_prefix = subnet_ip.split("/")[1]
        tmp1["subnetPrefix"] = {
            find(subnet_ipaddr): {
                "ip": {"value": subnet_ipaddr, "prefixLength": int(subnet_prefix)},
                "prefixLength": int(subnet_prefix),
            }
        }
    return tmp1


def add_PortRanges(port_list):
    tmp2 = []
    for port in port_list:
        if "-" in port:
            startPort = int(port.split("-")[0])
            endPort = int(port.split("-")[1])
        else:
            startPort = int(port)
            endPort = int(port)
        tmp2.append({"startPort": startPort, "endPort": endPort})
    return tmp2


def add_protocolParameters():
    # variables ::
    # protocolType = ANY | PROTOCOL_NUMBER | TCP |  UDP | ICMP
    # TCP_UDP_DATA = ANY | < startPort,startPort:endPort,endPort >
    # ICMP_DATA = ANY | < icmptype_no:[ANY|icmpcode_no] >,
    #   if ICMP_TYPE = ANY then ICMP_CODE = ANY
    #   if ICMP_TYPE = no then ICMP_CODE either ANY or No.

    if (
        "@@{protocolType}@@" in ["TCP", "UDP"]
        and "@@{TCP_UDP_DATA}@@".strip() != "ANY:ANY"
    ):
        payload["policies"][0]["policyMatch"]["protocolParameters"] = {
            "$objectType": "networking.v4.config.LayerFourProtocolObject"
        }

    if "@@{protocolType}@@" in ["TCP", "UDP"]:
        if "@@{TCP_UDP_DATA}@@" == "":
            raise Exception("TCP_UDP_DATA values are not entered.")
        source_port_list = "@@{TCP_UDP_DATA}@@".split(":")[0].split(",")
        if "ANY" not in source_port_list:
            payload["policies"][0]["policyMatch"]["protocolParameters"][
                "sourcePortRanges"
            ] = add_PortRanges(source_port_list)

    if "@@{protocolType}@@" in ["TCP", "UDP"]:
        destination_port_list = "@@{TCP_UDP_DATA}@@".split(":")[1].split(",")
        if "ANY" not in destination_port_list:
            payload["policies"][0]["policyMatch"]["protocolParameters"][
                "destinationPortRanges"
            ] = add_PortRanges(destination_port_list)

    if "@@{protocolType}@@" == "PROTOCOL_NUMBER":
        if "@@{protocolNumber}@@" == "":
            raise Exception("protocolNumber value is not entered.")
        payload["policies"][0]["policyMatch"]["protocolParameters"] = {
            "$objectType": "networking.v4.config.ProtocolNumberObject"
        }
        payload["policies"][0]["policyMatch"]["protocolParameters"][
            "protocolNumber"
        ] = int("@@{protocolNumber}@@")

    if "@@{protocolType}@@" == "ICMP":
        if "@@{ICMP_DATA}@@" == "":
            raise Exception("ICMP_DATA values are not entered.")
        if "@@{ICMP_DATA}@@".strip() != "ANY:ANY":
            payload["policies"][0]["policyMatch"]["protocolParameters"] = {
                "$objectType": "networking.v4.config.ICMPObject"
            }
        if "@@{ICMP_DATA}@@".split(":")[0] != "ANY":
            payload["policies"][0]["policyMatch"]["protocolParameters"][
                "icmpType"
            ] = int("@@{ICMP_DATA}@@".split(":")[0])
        if "@@{ICMP_DATA}@@".split(":")[1] != "ANY":
            payload["policies"][0]["policyMatch"]["protocolParameters"][
                "icmpCode"
            ] = int("@@{ICMP_DATA}@@".split(":")[1])


def add_rerouteParams():
    # Variables:
    # separate_reroute = YES | NO
    # rerouteFallbackAction = PASSTHROUGH | NO_ACTION | ALLOW | DROP
    # "serviceIp": { "ipv4": { "value": "string", "prefixLength": 32 }, "ipv6": { "value": "string", "prefixLength": 128} },
    # "ingressServiceIp": { "ipv4": { "value": "string", "prefixLength": 32 }, "ipv6": { "value": "string", "prefixLength": 128 } },
    # "egressServiceIp": { "ipv4": { "value": "string", "prefixLength": 32 }, "ipv6": { "value": "string", "prefixLength": 128 } }
    payload["policies"][0]["policyAction"]["rerouteParams"] = [{}]
    payload["policies"][0]["policyAction"]["rerouteParams"][0][
        "rerouteFallbackAction"
    ] = "@@{rerouteFallbackAction}@@".strip()

    if "@@{separate_reroute}@@" == "Yes":
        ingressPrefix = 32
        if find("@@{ingressServiceIp}@@") == "ipv6":
            ingressPrefix = 128
        egressPrefix = 32
        if find("@@{egressServiceIp}@@") == "ipv6":
            egressPrefix = 128

        payload["policies"][0]["policyAction"]["rerouteParams"][0][
            "ingressServiceIp"
        ] = {
            find("@@{ingressServiceIp}@@"): {
                "value": "@@{ingressServiceIp}@@",
                "prefixLength": ingressPrefix,
            }
        }
        payload["policies"][0]["policyAction"]["rerouteParams"][0][
            "egressServiceIp"
        ] = {
            find("@@{egressServiceIp}@@"): {
                "value": "@@{egressServiceIp}@@",
                "prefixLength": egressPrefix,
            }
        }
    else:
        prefix = 32
        if find("@@{serviceIp}@@") == "ipv6":
            prefix = 128
        payload["policies"][0]["policyAction"]["rerouteParams"][0]["serviceIp"] = {
            find("@@{serviceIp}@@"): {
                "value": "@@{serviceIp}@@",
                "prefixLength": prefix,
            }
        }


def add_forwardParams():
    prefix = 32
    if find("@@{forwardIp}@@") == "ipv6":
        prefix = 128
    payload["policies"][0]["policyAction"]["nexthopIpAddress"] = {
        find("@@{forwardIp}@@"): {"value": "@@{forwardIp}@@", "prefixLength": prefix}
    }


def add_policy():
    # Variables:
    # source_addressType = ANY, EXTERNAL, SUBNET(custom)
    # destination_addressType = ANY, EXTERNAL, SUBNET(custom)
    # actionType = PERMIT, DENY, REROUTE, FORWARD
    # source_subnet_ip / destination_subnet_ip = <ip>
    # isBidirectional = YES/NO
    # protocolType = ANY | PROTOCOL_NUMBER | TCP |  UDP | ICMP
    source_addressType = "@@{source_addressType}@@"
    if source_addressType == "CUSTOM":
        source_addressType = "SUBNET"
    destination_addressType = "@@{destination_addressType}@@"
    if destination_addressType == "CUSTOM":
        destination_addressType = "SUBNET"
    payload["policies"] = [{}]
    payload["policies"][0]["policyMatch"] = {
        "source": add_subnet(source_addressType, "@@{source_subnet_ip}@@"),
        "destination": add_subnet(
            destination_addressType, "@@{destination_subnet_ip}@@"
        ),
        "protocolType": "@@{protocolType}@@",
    }

    if "@@{protocolType}@@" != "ANY":
        add_protocolParameters()

    payload["policies"][0]["policyAction"] = {"actionType": "@@{actionType}@@"}

    if "@@{actionType}@@" in ["REROUTE"]:
        add_rerouteParams()

    if "@@{actionType}@@" in ["FORWARD"]:
        add_forwardParams()

    if "@@{actionType}@@" != "FORWARD" and "@@{isBidirectional}@@".strip() == "Yes":
        payload["policies"][0]["isBidirectional"] = True
    else:
        payload["policies"][0]["isBidirectional"] = False


def add_basic_details():
    payload["name"] = "@@{policy_name}@@".strip()
    payload["priority"] = int("@@{priority}@@".strip())
    payload["vpcExtId"] = "@@{vpcExtId}@@".strip().split(":")[1]
    if "@@{description}@@" != "":
        payload["description"] = "@@{description}@@"
    # payload['extId'] = get_vpc_ext_id("@@{vpcExtId}@@".strip().split(':')[0])


def create_payload():
    add_basic_details()
    add_policy()


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
    create_routing_policy_response = session.post(
        "https://{}:{}/api/networking/{}/config/routing-policies".format(
            PC_IP, PC_PORT, "@@{flow_virtual_network_api_version}@@"
        ),
        json=payload,
        headers={
            "Content-Type": "application/json",
            "NTNX-Request-Id": str(uuid.uuid4()),
        },
    )
    print(f"create response: {create_routing_policy_response.json()}")
    create_routing_policy_response.raise_for_status()
    task_uuid = create_routing_policy_response.json()["data"]["extId"]
    print(f"task_uuid = {task_uuid}")
    wait(task_uuid)


create()
