import json
import os

from calm.dsl.api import get_api_client, get_resource_api


dsl_config_file_location = os.path.expanduser("~/.calm/.local/.tests/config.json")


def add_account_details(config):
    """add account details to config"""

    # Get api client
    client = get_api_client()

    # Add accounts details
    payload = {"length": 250, "filter": "state==VERIFIED;type!=nutanix"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    a_entities = response.get("entities", None)

    accounts = {}
    for a_entity in a_entities:
        account_type = a_entity["status"]["resources"]["type"].upper()
        if account_type not in accounts:
            accounts[account_type] = []

        account_data = {
            "NAME": a_entity["status"]["name"],
            "UUID": a_entity["metadata"]["uuid"],
        }

        if account_type == "NUTANIX_PC":
            account_data["SUBNETS"] = []
            Obj = get_resource_api("nutanix/v1/subnets", client.connection)
            payload = {"filter": "account_uuid=={}".format(account_data["UUID"])}
            result, er = Obj.list(payload)
            if er:
                pass
            else:
                result = result.json()
                for entity in result["entities"]:
                    cluster_ref = entity["status"]["cluster_reference"]
                    cluster_name = cluster_ref.get("name", "")

                    account_data["SUBNETS"].append(
                        {
                            "NAME": entity["status"]["name"],
                            "CLUSTER": cluster_name,
                            "UUID": entity["metadata"]["uuid"],
                        }
                    )

            # If it is local nutanix account, assign it to local nutanix ACCOUNT
            if a_entity["status"]["resources"]["data"].get("host_pc", False):
                accounts["NTNX_LOCAL_AZ"] = account_data

        accounts[account_type].append(account_data)

    # fill accounts data
    config["ACCOUNTS"] = accounts


def add_directory_service_users(config):

    # Get api client
    client = get_api_client()

    # Add user details
    payload = {"length": 250}
    res, err = client.user.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    # Add user details to config
    ds_users = []

    res = res.json()
    for entity in res["entities"]:
        if entity["status"]["state"] != "COMPLETE":
            continue
        e_resources = entity["status"]["resources"]
        if e_resources.get("user_type", "") == "DIRECTORY_SERVICE":
            ds_users.append(
                {
                    "DISPLAY_NAME": e_resources["display_name"],
                    "DIRECTORY": e_resources["directory_service_user"]
                    .get("directory_service_reference", {})
                    .get("name", ""),
                    "NAME": e_resources["directory_service_user"].get(
                        "user_principal_name", ""
                    ),
                    "UUID": entity["metadata"]["uuid"],
                }
            )

    config["USERS"] = ds_users


def add_directory_service_user_groups(config):

    # Get api client
    client = get_api_client()

    # Add user details
    payload = {"length": 250}
    res, err = client.group.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    # Add user_group details to config
    ds_groups = []

    res = res.json()
    for entity in res["entities"]:
        if entity["status"]["state"] != "COMPLETE":
            continue
        e_resources = entity["status"]["resources"]
        directory_service_user_group = (
            e_resources.get("directory_service_user_group") or dict()
        )
        distinguished_name = directory_service_user_group.get("distinguished_name")
        directory_service_ref = (
            directory_service_user_group.get("directory_service_reference") or dict()
        )
        directory_service_name = directory_service_ref.get("name", "")
        if directory_service_name and distinguished_name:
            ds_groups.append(
                {
                    "DISPLAY_NAME": e_resources["display_name"],
                    "DIRECTORY": directory_service_name,
                    "NAME": distinguished_name,
                    "UUID": entity["metadata"]["uuid"],
                }
            )

    config["USER_GROUPS"] = ds_groups


def add_project_details(config):

    client = get_api_client()

    for _, project_config in config["PROJECTS"].items():
        project_name = project_config["NAME"]

        payload = {
            "length": 200,
            "offset": 0,
            "filter": "name=={}".format(project_name),
        }
        project_name_uuid_map = client.project.get_name_uuid_map(payload)

        if not project_name_uuid_map:
            print("Project {} not found".format(project_name))
            continue

        project_uuid = project_name_uuid_map[project_name]
        project_config["UUID"] = project_uuid

        res, _ = client.project.read(project_uuid)
        project_data = res.json()

        # Attach project accounts here
        project_config["ACCOUNTS"] = {}

        payload = {"length": 250, "offset": 0}
        account_uuid_name_map = client.account.get_uuid_name_map(payload)
        account_uuid_type_map = client.account.get_uuid_type_map(payload)

        for _account in project_data["status"]["resources"].get(
            "account_reference_list", []
        ):
            _account_uuid = _account["uuid"]
            _account_type = account_uuid_type_map[_account_uuid].upper()
            _account_name = account_uuid_name_map[_account_uuid]
            if _account_type not in project_config["ACCOUNTS"]:
                project_config["ACCOUNTS"][_account_type] = []

            project_config["ACCOUNTS"][_account_type].append(
                {"NAME": _account_name, "UUID": _account_uuid}
            )

        payload = {
            "length": 200,
            "offset": 0,
            "filter": "project_reference=={}".format(project_uuid),
        }
        env_name_uuid_map = client.environment.get_name_uuid_map(payload) or dict()

        # From 3.2, it is envs are required for testing
        project_config["ENVIRONMENTS"] = []
        for e_k, e_v in env_name_uuid_map.items():
            project_config["ENVIRONMENTS"].append({"NAME": e_k, "UUID": e_v})


f = open(dsl_config_file_location, "r")
config = json.loads(f.read())
f.close()

add_account_details(config)
add_directory_service_users(config)
add_directory_service_user_groups(config)
add_project_details(config)

f = open(dsl_config_file_location, "w")
f.write(json.dumps(config, indent=4))
f.close()
