import json
import pdb
import os
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE

ENTITIES = [
    CACHE.ENTITY.PROJECT,
    CACHE.ENTITY.ACCOUNT,
    CACHE.ENTITY.AHV_CLUSTER,
    CACHE.ENTITY.AHV_VPC,
    CACHE.ENTITY.AHV_SUBNET,
    CACHE.ENTITY.AHV_DISK_IMAGE,
    CACHE.ENTITY.PROVIDER,
    CACHE.ENTITY.RESOURCE_TYPE,
    CACHE.ENTITY.USER,
    CACHE.ENTITY.ROLE,
    CACHE.ENTITY.DIRECTORY_SERVICE,
    CACHE.ENTITY.USER_GROUP,
    CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN,
    CACHE.ENTITY.ENVIRONMENT,
    CACHE.ENTITY.POLICY_EVENT,
    CACHE.ENTITY.POLICY_ACTION_TYPE,
    CACHE.ENTITY.POLICY_ATTRIBUTES,
    CACHE.ENTITY.APP_PROTECTION_POLICY,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.DATABASE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.CLUSTER,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TIME_MACHINE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SNAPSHOT,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG,
]

PROJECTS = [
    "default",
    "test_snapshot_policy_project",
    "test_vmw_snapshot_policy_project",
    "rbac_bp_test_project",
    "test_approval_policy",
    "test_approval_policy_rbac",
    "test_quota_project",
    "test_dyn_cred_project",
    "test_vpc_project",
]

PROVIDERS = ["AzureVault_Cred_Provider", "HashiCorpVault_Cred_Provider", "NDB"]

CACHE_FILE_NAME = "cache_data.json"
TEST_CONFIG_FILE_NAME = "config_test.json"

SERIALISED_KEYS = [
    "data",
    "auth_schema_list",
    "tags",
    "action_list",
    "accounts_data",
    "whitelisted_subnets",
    "whitelisted_clusters",
    "whitelisted_vpcs",
    "platform_data",
    "slas",
]

ROOT_DB_LOCATION = "calm/dsl/db"

cache_data_dict = {}
filtered_cache_data = {}
test_config_data = {}


def db_location(filename):
    file_path = os.path.join(ROOT_DB_LOCATION, filename)
    return file_path


def filter_data():
    global cache_data_dict, filtered_cache_data, test_config_data

    project_name_uuid_map = {}
    rev_account_name_uuid_map = {}
    entities_connection = {}
    account_connection = {}
    provider_connection = {}

    project_uuids = []
    all_account_uuids = []

    for entity_type, entity_data in cache_data_dict.items():
        if entity_type == CACHE.ENTITY.PROJECT:
            project_data = {}
            key = 0

            for _, each_data in entity_data.items():
                project_name = each_data.get("name", None)
                project_uuid = each_data.get("uuid", None)
                if project_name in PROJECTS:
                    project_name_uuid_map[project_name] = project_uuid

                    entities_connection[project_uuid] = {}
                    entities_connection[project_uuid]["NAME"] = project_name
                    entities_connection[project_uuid]["ENVIRONMENTS"] = []
                    entities_connection[project_uuid]["APP_PROTECTION_POLICY"] = []
                    entities_connection[project_uuid]["ACCOUNTS"] = []

                    project_uuids.append(project_uuid)
                    project_data[key] = each_data
                    key += 1

                accounts_data = each_data.get("accounts_data", {})
                if project_name in PROJECTS:
                    for account_name, account_uuids in accounts_data.items():
                        all_account_uuids.extend(account_uuids)
                        kwargs = {"NAME": account_name, "ACCOUNT_UUIDS": account_uuids}

                        entities_connection[project_uuid]["ACCOUNTS"].append(kwargs)

            filtered_cache_data[entity_type] = project_data

        elif entity_type == CACHE.ENTITY.ENVIRONMENT:
            environment_data = {}
            key = 0

            for _, each_data in entity_data.items():
                project_uuid = each_data.get("project_uuid", None)
                if project_uuid in project_uuids:
                    environment_name = each_data.get("name", None)
                    environment_uuid = each_data.get("uuid", None)
                    kwargs = {"NAME": environment_name, "UUID": environment_uuid}
                    entities_connection[project_uuid]["ENVIRONMENTS"].append(kwargs)

                    environment_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = environment_data

        elif entity_type == CACHE.ENTITY.APP_PROTECTION_POLICY:
            app_protection_policy_data = {}
            key = 0

            for _, each_data in entity_data.items():
                project_name = each_data.get("project_name", None)
                if project_name in PROJECTS:
                    project_uuid = project_name_uuid_map.get(project_name, None)
                    policy_name = each_data.get("name", None)
                    policy_uuid = each_data.get("uuid", None)
                    rule_uuid = each_data.get("rule_uuid", None)
                    kwargs = {
                        "NAME": policy_name,
                        "UUID": policy_uuid,
                        "RULE_UUID": rule_uuid,
                    }
                    entities_connection[project_uuid]["APP_PROTECTION_POLICY"].append(
                        kwargs
                    )
                    app_protection_policy_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = app_protection_policy_data

        elif entity_type == CACHE.ENTITY.ACCOUNT:
            all_account_uuids_set = set(all_account_uuids)
            account_data = {}
            key = 0

            for _, each_data in entity_data.items():
                account_uuid = each_data.get("uuid", None)
                if account_uuid in all_account_uuids_set:
                    account_name = each_data.get("name", None)
                    rev_account_name_uuid_map[account_uuid] = account_name
                    account_connection[account_uuid] = {}
                    account_connection[account_uuid][
                        "NAME"
                    ] = rev_account_name_uuid_map.get(account_uuid, None)
                    account_connection[account_uuid]["AHV_CLUSTER"] = []
                    account_connection[account_uuid]["AHV_DISK_IMAGE"] = []
                    account_connection[account_uuid]["AHV_VPC"] = []
                    account_connection[account_uuid]["AHV_SUBNET"] = []

                    account_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = account_data

        elif entity_type == CACHE.ENTITY.AHV_CLUSTER:
            all_account_uuids_set = set(all_account_uuids)
            ahv_cluster_data = {}
            key = 0

            for _, each_data in entity_data.items():
                account_uuid = each_data.get("account_uuid", None)
                if account_uuid in all_account_uuids_set:
                    cluster_uuid = each_data.get("uuid", None)
                    cluster_name = each_data.get("name", None)

                    kwargs = {"NAME": cluster_name, "UUID": cluster_uuid}

                    account_connection[account_uuid]["AHV_CLUSTER"].append(kwargs)

                    ahv_cluster_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = ahv_cluster_data

        elif entity_type == CACHE.ENTITY.AHV_VPC:
            all_account_uuids_set = set(all_account_uuids)
            ahv_vpc_data = {}
            key = 0

            for _, each_data in entity_data.items():
                account_uuid = each_data.get("account_uuid", None)
                if account_uuid in all_account_uuids_set:
                    vpc_uuid = each_data.get("uuid", None)
                    vpc_name = each_data.get("name", None)

                    kwargs = {"NAME": vpc_name, "UUID": vpc_uuid}
                    account_connection[account_uuid]["AHV_VPC"].append(kwargs)

                    ahv_vpc_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = ahv_vpc_data

        elif entity_type == CACHE.ENTITY.AHV_SUBNET:
            all_account_uuids_set = set(all_account_uuids)
            ahv_subnet_data = {}
            key = 0

            for _, each_data in entity_data.items():
                account_uuid = each_data.get("account_uuid", None)
                if account_uuid in all_account_uuids_set:
                    kwargs = {
                        "NAME": each_data.get("name", None),
                        "UUID": each_data.get("uuid", None),
                        "CLUSTER_NAME": each_data.get("cluster_name", None),
                        "CLUSTER_UUID": each_data.get("cluster_uuid", None),
                        "VPC_NAME": each_data.get("vpc_name", None),
                        "VPC_UUID": each_data.get("vpc_uuid", None),
                    }

                    account_connection[account_uuid]["AHV_SUBNET"].append(kwargs)

                    ahv_subnet_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = ahv_subnet_data

        elif entity_type == CACHE.ENTITY.AHV_DISK_IMAGE:
            all_account_uuids_set = set(all_account_uuids)
            ahv_image_data = {}
            key = 0

            for _, each_data in entity_data.items():
                account_uuid = each_data.get("account_uuid", None)
                if account_uuid in all_account_uuids_set:
                    image_uuid = each_data.get("uuid", None)
                    image_name = each_data.get("name", None)

                    kwargs = {"NAME": image_name, "UUID": image_uuid}

                    account_connection[account_uuid]["AHV_DISK_IMAGE"].append(kwargs)

                    ahv_image_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = ahv_image_data

        elif entity_type == CACHE.ENTITY.PROVIDER:
            provider_data = {}
            key = 0

            for _, each_data in entity_data.items():
                provider_name = each_data.get("name", None)
                if provider_name in PROVIDERS:
                    provider_uuid = each_data.get("uuid", None)
                    provider_connection[provider_uuid] = {}
                    provider_connection[provider_uuid]["NAME"] = provider_name
                    provider_connection[provider_uuid]["RESOURCE_TYPE"] = []

                    provider_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = provider_data

        elif entity_type == CACHE.ENTITY.RESOURCE_TYPE:
            resource_type_data = {}
            key = 0

            for _, each_data in entity_data.items():
                provider_name = each_data.get("provider_name", None)
                if provider_name in PROVIDERS:
                    provider_uuid = each_data.get("provider_uuid", None)
                    resource_name = each_data.get("name", None)
                    resource_uuid = each_data.get("uuid", None)
                    kwargs = {"NAME": resource_name, "UUID": resource_uuid}
                    provider_connection[provider_uuid]["RESOURCE_TYPE"].append(kwargs)

                    resource_type_data[key] = each_data
                    key += 1

            filtered_cache_data[entity_type] = resource_type_data

        else:
            filtered_cache_data[entity_type] = entity_data

    for entity_type, entity_data in filtered_cache_data.items():
        for index, each_data in entity_data.items():
            for each_key in SERIALISED_KEYS:
                if each_key in each_data:
                    entity_data[index][each_key] = json.dumps(each_data[each_key])

    test_config_data = {
        "PROJECTS": entities_connection,
        "ACCOUNTS": account_connection,
        "PROVIDERS": provider_connection,
        "METADATA": {
            "PROJECT": project_name_uuid_map,
            "ACCOUNT": {v: k for k, v in rev_account_name_uuid_map.items()},
        },
    }


def get_data(entity_type):
    global cache_data_dict

    model = Cache.get_entity_db_table_object(entity_type)
    cache_data_dict[entity_type] = {}
    key = 0

    for entity in model.select():
        entity_data = entity.get_detail_dict()
        cache_data_dict[entity_type][key] = entity_data
        key += 1


def load_data():
    for entity_type in ENTITIES:
        get_data(entity_type)

    filter_data()

    with open(CACHE_FILE_NAME, "w") as outfile:
        outfile.write(json.dumps(filtered_cache_data, default=str, indent=4))

    with open(TEST_CONFIG_FILE_NAME, "w") as outfile:
        outfile.write(json.dumps(test_config_data, default=str, indent=4))


load_data()
