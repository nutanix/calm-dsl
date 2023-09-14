import json
import os
import sys

from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from constants import (
    MockConstants,
    CONSTANT_ENTITIES,
    PROJECTS,
    PROVIDERS,
    SERIALISED_KEYS,
)
from calm.dsl.db.table_config import CacheTableBase
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

ROOT_DB_LOCATION = "calm/dsl/db"

cache_data_dict = {}
filtered_cache_data = {}
test_config_data = {}


def db_location(filename):
    file_path = os.path.join(ROOT_DB_LOCATION, filename)
    return file_path


def filter_project_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all project data
    Returns:
        filtered project data

    """
    project_data = {}
    key = 0

    for _, each_data in entity_data.items():
        project_name = each_data.get("name", None)
        project_uuid = each_data.get("uuid", None)
        if project_name in PROJECTS:
            kwargs.get("project_name_uuid_map")[project_name] = project_uuid

            kwargs.get("entities_connection")[project_uuid] = {}
            kwargs.get("entities_connection")[project_uuid]["NAME"] = project_name
            kwargs.get("entities_connection")[project_uuid]["ENVIRONMENTS"] = []
            kwargs.get("entities_connection")[project_uuid][
                "APP_PROTECTION_POLICY"
            ] = []
            kwargs.get("entities_connection")[project_uuid]["ACCOUNTS"] = []

            kwargs.get("project_uuids").append(project_uuid)
            project_data[key] = each_data
            key += 1

        accounts_data = each_data.get("accounts_data", {})
        if project_name in PROJECTS:
            for account_name, account_uuids in accounts_data.items():
                kwargs.get("all_account_uuids").extend(account_uuids)
                accounts_details = {
                    "NAME": account_name,
                    "ACCOUNT_UUIDS": account_uuids,
                }

                kwargs.get("entities_connection")[project_uuid]["ACCOUNTS"].append(
                    accounts_details
                )

    return project_data


def filter_environment_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all environment data
    Returns:
        filtered environment data

    """
    environment_data = {}
    key = 0

    for _, each_data in entity_data.items():
        project_uuid = each_data.get("project_uuid", None)
        if project_uuid in kwargs.get("project_uuids"):
            environment_name = each_data.get("name", None)
            environment_uuid = each_data.get("uuid", None)
            environment_details = {"NAME": environment_name, "UUID": environment_uuid}
            kwargs.get("entities_connection")[project_uuid]["ENVIRONMENTS"].append(
                environment_details
            )

            environment_data[key] = each_data
            key += 1

    return environment_data


def filter_app_protection_policy_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all app protection policy data data
    Returns:
        filtered app protection policy data

    """
    app_protection_policy_data = {}
    key = 0

    for _, each_data in entity_data.items():
        project_name = each_data.get("project_name", None)
        if project_name in PROJECTS:
            project_uuid = kwargs.get("project_name_uuid_map").get(project_name, None)
            policy_name = each_data.get("name", None)
            policy_uuid = each_data.get("uuid", None)
            rule_uuid = each_data.get("rule_uuid", None)
            protection_policy_details = {
                "NAME": policy_name,
                "UUID": policy_uuid,
                "RULE_UUID": rule_uuid,
            }
            kwargs.get("entities_connection")[project_uuid][
                "APP_PROTECTION_POLICY"
            ].append(protection_policy_details)
            app_protection_policy_data[key] = each_data
            key += 1

    return app_protection_policy_data


def filter_account_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all account data
    Returns:
        filtered account data

    """
    all_account_uuids_set = set(kwargs.get("all_account_uuids"))
    account_data = {}
    key = 0

    for _, each_data in entity_data.items():
        account_uuid = each_data.get("uuid", None)
        if account_uuid in all_account_uuids_set:
            account_name = each_data.get("name", None)
            kwargs.get("rev_account_name_uuid_map")[account_uuid] = account_name
            kwargs.get("account_connection")[account_uuid] = {}
            kwargs.get("account_connection")[account_uuid]["NAME"] = kwargs.get(
                "rev_account_name_uuid_map"
            ).get(account_uuid, None)
            kwargs.get("account_connection")[account_uuid]["AHV_CLUSTER"] = []
            kwargs.get("account_connection")[account_uuid]["AHV_DISK_IMAGE"] = []
            kwargs.get("account_connection")[account_uuid]["AHV_VPC"] = []
            kwargs.get("account_connection")[account_uuid]["AHV_SUBNET"] = []

            account_data[key] = each_data
            key += 1

    return account_data


def filter_ahv_cluster_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all ahv cluster data
    Returns:
        filtered ahv cluster data

    """
    all_account_uuids_set = set(kwargs.get("all_account_uuids"))
    ahv_cluster_data = {}
    key = 0

    for _, each_data in entity_data.items():
        account_uuid = each_data.get("account_uuid", None)
        if account_uuid in all_account_uuids_set:
            cluster_uuid = each_data.get("uuid", None)
            cluster_name = each_data.get("name", None)

            cluster_details = {"NAME": cluster_name, "UUID": cluster_uuid}

            kwargs.get("account_connection")[account_uuid]["AHV_CLUSTER"].append(
                cluster_details
            )

            ahv_cluster_data[key] = each_data
            key += 1

    return ahv_cluster_data


def filter_ahv_vpc_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all ahv vpc data
    Returns:
        filtered ahv vpc data

    """
    all_account_uuids_set = set(kwargs.get("all_account_uuids"))
    ahv_vpc_data = {}
    key = 0

    for _, each_data in entity_data.items():
        account_uuid = each_data.get("account_uuid", None)
        if account_uuid in all_account_uuids_set:
            vpc_uuid = each_data.get("uuid", None)
            vpc_name = each_data.get("name", None)

            vpc_details = {"NAME": vpc_name, "UUID": vpc_uuid}
            kwargs.get("account_connection")[account_uuid]["AHV_VPC"].append(
                vpc_details
            )

            ahv_vpc_data[key] = each_data
            key += 1

    return ahv_vpc_data


def filter_ahv_subnet_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all ahv subnet data
    Returns:
        filtered ahv subnet data

    """
    all_account_uuids_set = set(kwargs.get("all_account_uuids"))
    ahv_subnet_data = {}
    key = 0

    for _, each_data in entity_data.items():
        account_uuid = each_data.get("account_uuid", None)
        if account_uuid in all_account_uuids_set:
            subnet_details = {
                "NAME": each_data.get("name", None),
                "UUID": each_data.get("uuid", None),
                "CLUSTER_NAME": each_data.get("cluster_name", None),
                "CLUSTER_UUID": each_data.get("cluster_uuid", None),
                "VPC_NAME": each_data.get("vpc_name", None),
                "VPC_UUID": each_data.get("vpc_uuid", None),
            }

            kwargs.get("account_connection")[account_uuid]["AHV_SUBNET"].append(
                subnet_details
            )

            ahv_subnet_data[key] = each_data
            key += 1

    return ahv_subnet_data


def filter_ahv_disk_image_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all ahv disk image data
    Returns:
        filtered ahv disk image data

    """
    all_account_uuids_set = set(kwargs.get("all_account_uuids"))
    ahv_image_data = {}
    key = 0

    for _, each_data in entity_data.items():
        account_uuid = each_data.get("account_uuid", None)
        if account_uuid in all_account_uuids_set:
            image_uuid = each_data.get("uuid", None)
            image_name = each_data.get("name", None)

            disk_image_details = {"NAME": image_name, "UUID": image_uuid}

            kwargs.get("account_connection")[account_uuid]["AHV_DISK_IMAGE"].append(
                disk_image_details
            )

            ahv_image_data[key] = each_data
            key += 1

    return ahv_image_data


def filter_provider_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all provider data
    Returns:
        filtered provider data

    """
    provider_data = {}
    key = 0

    for _, each_data in entity_data.items():
        provider_name = each_data.get("name", None)
        if provider_name in PROVIDERS:
            provider_uuid = each_data.get("uuid", None)
            kwargs.get("provider_connection")[provider_uuid] = {}
            kwargs.get("provider_connection")[provider_uuid]["NAME"] = provider_name
            kwargs.get("provider_connection")[provider_uuid]["RESOURCE_TYPE"] = []

            provider_data[key] = each_data
            key += 1

    return provider_data


def filter_resource_type_data(entity_data, **kwargs):
    """

    Args:
        entity_data: dictionary of all resource type data
    Returns:
        filtered resource type data

    """
    resource_type_data = {}
    key = 0

    for _, each_data in entity_data.items():
        provider_name = each_data.get("provider_name", None)
        if provider_name in PROVIDERS:
            provider_uuid = each_data.get("provider_uuid", None)
            resource_name = each_data.get("name", None)
            resource_uuid = each_data.get("uuid", None)
            resource_type_details = {"NAME": resource_name, "UUID": resource_uuid}
            kwargs.get("provider_connection")[provider_uuid]["RESOURCE_TYPE"].append(
                resource_type_details
            )

            resource_type_data[key] = each_data
            key += 1

    return resource_type_data


def filter_data():
    """

    - Filters raw data of db to keep only those data that are necessary for test cases to run.
    - Filters project data initially and stores all accounts, environment, app protection policy required by these projects.
    - Filters resource type based on providers that are required.

    """
    global cache_data_dict, filtered_cache_data, test_config_data

    project_name_uuid_map = {}
    rev_account_name_uuid_map = {}
    entities_connection = {}
    account_connection = {}
    provider_connection = {}

    project_uuids = []
    all_account_uuids = []

    kwargs = {
        "project_name_uuid_map": project_name_uuid_map,
        "rev_account_name_uuid_map": rev_account_name_uuid_map,
        "entities_connection": entities_connection,
        "account_connection": account_connection,
        "provider_connection": provider_connection,
        "project_uuids": project_uuids,
        "all_account_uuids": all_account_uuids,
    }

    project_data = cache_data_dict[CACHE.ENTITY.PROJECT]
    filtered_cache_data[CACHE.ENTITY.PROJECT] = filter_project_data(
        project_data, **kwargs
    )

    environment_data = cache_data_dict[CACHE.ENTITY.ENVIRONMENT]
    filtered_cache_data[CACHE.ENTITY.ENVIRONMENT] = filter_environment_data(
        environment_data, **kwargs
    )

    protection_policy_data = cache_data_dict[CACHE.ENTITY.APP_PROTECTION_POLICY]
    filtered_cache_data[
        CACHE.ENTITY.APP_PROTECTION_POLICY
    ] = filter_app_protection_policy_data(protection_policy_data, **kwargs)

    account_data = cache_data_dict[CACHE.ENTITY.ACCOUNT]
    filtered_cache_data[CACHE.ENTITY.ACCOUNT] = filter_account_data(
        account_data, **kwargs
    )

    ahv_cluster_data = cache_data_dict[CACHE.ENTITY.AHV_CLUSTER]
    filtered_cache_data[CACHE.ENTITY.AHV_CLUSTER] = filter_ahv_cluster_data(
        ahv_cluster_data, **kwargs
    )

    ahv_vpc_data = cache_data_dict[CACHE.ENTITY.AHV_VPC]
    filtered_cache_data[CACHE.ENTITY.AHV_VPC] = filter_ahv_vpc_data(
        ahv_vpc_data, **kwargs
    )

    ahv_subnet_data = cache_data_dict[CACHE.ENTITY.AHV_SUBNET]
    filtered_cache_data[CACHE.ENTITY.AHV_SUBNET] = filter_ahv_subnet_data(
        ahv_subnet_data, **kwargs
    )

    ahv_disk_image_data = cache_data_dict[CACHE.ENTITY.AHV_DISK_IMAGE]
    filtered_cache_data[CACHE.ENTITY.AHV_DISK_IMAGE] = filter_ahv_disk_image_data(
        ahv_disk_image_data, **kwargs
    )

    provider_data = cache_data_dict[CACHE.ENTITY.PROVIDER]
    filtered_cache_data[CACHE.ENTITY.PROVIDER] = filter_provider_data(
        provider_data, **kwargs
    )

    resource_type_data = cache_data_dict[CACHE.ENTITY.RESOURCE_TYPE]
    filtered_cache_data[CACHE.ENTITY.RESOURCE_TYPE] = filter_resource_type_data(
        resource_type_data, **kwargs
    )

    for entity_type, entity_data in cache_data_dict.items():
        if entity_type in CONSTANT_ENTITIES:
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
    """
    Fetches raw data from current db and stores it in a dictionary.
    """
    global cache_data_dict

    model = Cache.get_entity_db_table_object(entity_type)
    cache_data_dict[entity_type] = {}
    key = 0

    for entity in model.select():
        entity_data = entity.get_detail_dict()
        cache_data_dict[entity_type][key] = entity_data
        key += 1


def load_data():
    """

    Writes final filtered data from db to cache_data.json and config_test.json.

    - cache_data.json contains filtered data
    - config_test.json contains filtered data attached to each entity they belong to.
      Data in test cases will be asserted against data in this file.

    """
    entity_types = list(CacheTableBase.tables.keys())
    for entity_type in entity_types:
        get_data(entity_type)

    filter_data()
    LOG.info("Filtered data successfully")
    with open(MockConstants.CACHE_FILE_NAME, "w") as outfile:
        outfile.write(json.dumps(filtered_cache_data, default=str, indent=4))

    with open(MockConstants.TEST_CONFIG_FILE_NAME, "w") as outfile:
        outfile.write(json.dumps(test_config_data, default=str, indent=4))


if __name__ == "__main__":
    is_data_loaded = False
    LOG.info("Started")
    if len(sys.argv) > 1:
        is_data_loaded = sys.argv[1]
        is_data_loaded = True if is_data_loaded == "True" else False
    LOG.info("ww")
    if not is_data_loaded:
        LOG.info("ww")
        load_data()
