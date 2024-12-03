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


def get_servicesAndAddr_extId(url, c_name, id_key="extId"):
    response = session.get(
        url,
        headers={"accept": "application/json"},
        params={"$page": 0, "$limit": 1, "$filter": f"name eq '{c_name}'"},
    )
    # print(f"response: {response.json()}")
    response.raise_for_status()
    data = response.json().get("data")
    if data:
        if isinstance(data, list):
            if id_key in data[0] and data[0]["name"] == c_name:
                return data[0][id_key]
        else:
            if id_key in data:
                return data[id_key]
    raise Exception(f"failed to get extId for {c_name}")


def get_serviesGroup_extId(names):
    # value - ServiceName:<startPort>, ServiceName:<startPort> - <endPort>, ...
    url = "https://{}:{}/api/microseg/{}/config/service-groups".format(
        PC_IP, PC_PORT, "v4.0.b1"
    )
    extId = get_servicesAndAddr_extId(url, names)
    return extId


def get_addressGroup_extID(names):
    group_names = names.split(",")
    extId_list = []
    url = "https://{}:{}/api/microseg/{}/config/address-groups".format(
        PC_IP, PC_PORT, "v4.0.b1"
    )
    for group_name in group_names:
        extId_list.append(get_servicesAndAddr_extId(url, group_name))
    return extId_list


# ------------------------------------------------------------------------------------------


def add_tcpudpports(proto_value):
    tcpports = proto_value.split(",")
    tmp = []
    for ports in tcpports:
        if "-" in ports:
            startport = ports.split("-")[0]
            endport = ports.split("-")[1]
        else:
            startport = ports
            endport = ports
        tmp.append({"startPort": int(startport), "endPort": int(endport)})
    return tmp


def add_icmpports(proto_value):
    # format : ANY,ANY or ANY,port or port,ANY or port,port
    icmp_data = proto_value.split(",")
    icmpService_data = []
    tmp1 = {}
    if proto_value == "ANY,ANY":
        tmp1["isAllAllowed"] = True
    elif icmp_data[0] != "ANY":
        tmp1["type"] = int(icmp_data[0])
    elif icmp_data[1] != "ANY":
        tmp1["code"] = int(icmp_data[1])
    icmpService_data.append(tmp1)
    return icmpService_data


def check_protocol(proto):
    # default will be ALL
    if "ALL" in proto or proto == "":
        proto_type = "ALL"
    else:
        proto_type = proto.split(":")[0]
        proto_value = proto.split(":")[1]
    if proto_type == "ALL":
        key1 = "isAllProtocolAllowed"
        value1 = True
    elif proto_type == "TCP" or proto_type == "UDP":
        key1 = "tcpServices"
        value1 = add_tcpudpports(proto_value)
    elif proto_type == "ICMP":
        key1 = "icmpServices"
        value1 = add_icmpports(proto_value)
    elif proto_type == "SERVICE":
        proto_value = proto.split(":", 1)[1]
        s_tmp = []
        for p in proto_value.split(","):
            service_name = p.split(":")[0]
            s_tmp.append(get_serviesGroup_extId(service_name))
        key1 = "serviceGroupReferences"
        value1 = s_tmp
    return key1, value1


def add_common(type, dictkey, dictvalue, proto_key, proto_val):
    basic = {
        "type": type,
        "spec": {
            "$objectType": "microseg.v4.config.ApplicationRuleSpec",
            "securedGroupCategoryReferences": get_categorygroup_extId(
                "@@{securedGroup}@@"
            ),
            dictkey: dictvalue,
        },
    }
    if proto_key != "":
        basic["spec"][proto_key] = proto_val
    return basic


def add_application_rule(
    endpoint, CategoryRef, SubnetRef, AddressGroupRef, AllGroupType
):
    # variables :
    # repeate 16. securedGroup = securedGroupCategoryReferences
    # 19. srcCategoryReferences -> src_catProtocolType (drop down list [ALL|TCP|UDP|ICMP|SERVICE])
    # 21. srcSubnet -> src_subnetProtocolType (drop down list [ALL|TCP|UDP|ICMP|SERVICE])
    # 23. srcAddressGroupReferences -> src_addrProtocolType (drop down list [ALL|TCP|UDP|ICMP|SERVICE])
    # 25. srcAllGroupType = ALL or None -> src_allProtocolType (drop down list [ALL|TCP|UDP|ICMP|SERVICE])
    # 27. serviceGroupReferences
    # add_proto == src_ProtocolType|dest_ProtocolType ==> ALL; TCP:22,22-25; UDP:22,22-25; ICMP:ANY,ANY or ANY,PORT or PORT,ANY or PORT,PORT
    # And servicesGroupReference
    add_proto = ""

    if endpoint == "src":
        if "@@{src_serviceGroupReferences}@@" != "":
            add_proto = "SERVICE:@@{src_serviceGroupReferences}@@"
        category_add_proto = add_proto + ";" + "@@{src_CategoryProtocolType}@@"
        subnet_add_proto = add_proto + ";" + "@@{src_SubnetProtocolType}@@"
        address_add_proto = add_proto + ";" + "@@{src_AddressProtocolType}@@"
        allgroup_add_proto = add_proto + ";" + "@@{src_AllGroupProtocolType}@@"
    elif endpoint == "dest":
        if "@@{dest_serviceGroupReferences}@@" != "":
            add_proto = "SERVICE:@@{dest_serviceGroupReferences}@@"
        category_add_proto = add_proto + ";" + "@@{dest_CategoryProtocolType}@@"
        subnet_add_proto = add_proto + ";" + "@@{dest_SubnetProtocolType}@@"
        address_add_proto = add_proto + ";" + "@@{dest_AddressProtocolType}@@"
        allgroup_add_proto = add_proto + ";" + "@@{dest_AllGroupProtocolType}@@"

    # if no protocol defined then default willbe ALL
    if category_add_proto == ";":
        category_add_proto = "ALL"
    if subnet_add_proto == ";":
        subnet_add_proto = "ALL"
    if address_add_proto == ";":
        address_add_proto = "ALL"
    if allgroup_add_proto == ";":
        allgroup_add_proto = "ALL"

    if AllGroupType == "ALL":
        for each_proto in filter(None, allgroup_add_proto.split(";")):
            print(f"AllGroupType : checking protocol: {each_proto}")
            all_protocol = check_protocol(each_proto)
            payload["rules"].append(
                add_common(
                    "APPLICATION",
                    endpoint + "AllowSpec",
                    "ALL",
                    all_protocol[0],
                    all_protocol[1],
                )
            )
    if CategoryRef != "":
        for each_proto in filter(None, category_add_proto.split(";")):
            print(f"CategoryRef : checking protocol: {each_proto}")
            cat_protocol = check_protocol(each_proto)
            payload["rules"].append(
                add_common(
                    "APPLICATION",
                    endpoint + "CategoryReferences",
                    get_categorygroup_extId(CategoryRef),
                    cat_protocol[0],
                    cat_protocol[1],
                )
            )
    if SubnetRef != "":
        for each_proto in filter(None, subnet_add_proto.split(";")):
            print(f"SubnetRef : checking protocol: {each_proto}")
            sub_protocol = check_protocol(each_proto)
            subnet = SubnetRef.split("/")
            payload["rules"].append(
                add_common(
                    "APPLICATION",
                    endpoint + "Subnet",
                    {"value": subnet[0], "prefixLength": int(subnet[1])},
                    sub_protocol[0],
                    sub_protocol[1],
                )
            )
    if AddressGroupRef != "":
        for each_proto in filter(None, address_add_proto.split(";")):
            print(f"AddressGroupRef : checking protocol: {each_proto}")
            addr_protocol = check_protocol(each_proto)
            payload["rules"].append(
                add_common(
                    "APPLICATION",
                    endpoint + "AddressGroupReferences",
                    get_addressGroup_extID(AddressGroupRef),
                    addr_protocol[0],
                    addr_protocol[1],
                )
            )
    print(f"Added {endpoint} rule: {payload['rules']} \n")


def add_intra_group_rule():
    # variables
    # 16. app_securedGroup 17. intra_groupAction = DENY / ALLOW
    intra_spec = {
        "spec": {
            "$objectType": "microseg.v4.config.IntraEntityGroupRuleSpec",
            "securedGroupCategoryReferences": get_categorygroup_extId(
                "@@{securedGroup}@@"
            ),
            "securedGroupAction": "@@{intra_groupAction}@@",
        },
        "type": "INTRA_GROUP",
    }
    return intra_spec


def create_payload():
    # Variables ::
    # 1. name, 2. description :
    # 3. type : ISOLATION / [QUARANTINE/APPLICATION] APPLICATION -> 3.1. Generic 3.2. VDI
    # 4. state : SAVE, MONITOR(Apply), ENFORCE(Apply Enforce)
    # 5. isIpv6TrafficAllowed : True/False 6. isHitlogEnabled : True/False
    # 7. scope : ALL_VLAN / VPC_LIST 8. vpcReferences [if no vpcRef then def scope is all_vlan]
    # 9. rule_type : QUARANTINE(QUARANTINE) / [INTRA_GROUP | APPLICATION] (APPLICATION/VDI) / TWO_ENV_ISOLATION (ISOLATION)
    payload["name"] = "@@{policy_name}@@".strip()
    payload["type"] = "APPLICATION".strip()
    payload["$objectType"] = "microseg.v4.config.NetworkSecurityPolicy"
    payload["state"] = "@@{policy_state}@@"
    payload["scope"] = "ALL_VLAN"
    if "@@{vpcReferences}@@" != "":
        payload["scope"] = "VPC_LIST"
        vpcextid = [x.split(":")[1] for x in "@@{vpcReferences}@@".split(",")]
        payload["vpcReferences"] = vpcextid
    if "@@{description}@@" != "":
        payload["description"] = "@@{description}@@"
    if "@@{isIpv6TrafficAllowed}@@" == "False":
        payload["isIpv6TrafficAllowed"] = False
    else:
        payload["isIpv6TrafficAllowed"] = True
    if "@@{isHitlogEnabled}@@" == "False":
        payload["isHitlogEnabled"] = False
    else:
        payload["isHitlogEnabled"] = True

    payload["rules"] = []
    payload["rules"].append(add_intra_group_rule())
    print("Adding source references")
    add_application_rule(
        "src",
        "@@{srcCategoryReferences}@@",
        "@@{srcSubnet}@@",
        "@@{srcAddressGroupReferences}@@",
        "@@{srcAllGroupType}@@",
    )
    print("Adding destination references")
    add_application_rule(
        "dest",
        "@@{destCategoryReferences}@@",
        "@@{destSubnet}@@",
        "@@{destAddressGroupReferences}@@",
        "@@{destAllGroupType}@@",
    )


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
    if task_status_response.json()["data"]["status"] == "FAILED":
        raise Exception(f"Task failed, got response {task_status_response.json()}")


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
