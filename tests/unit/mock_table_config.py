import sys
import os
import click
import json


from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE
from calm.dsl.db.table_config import *
from peewee import OperationalError, IntegrityError
from calm.dsl.db import get_db_handle, init_db_handle

ROOT_DB_LOCATION = ""
CACHE_FILE_NAME = "cache_data.json"

LOG = get_logging_handle(__name__)


def read_cached_data(filename, entity_type):
    entity_data = {}
    cache_data_location = os.path.join(ROOT_DB_LOCATION, filename)

    with open(cache_data_location, "r") as file:
        cache_data = json.loads(file.read())

    try:
        entity_data = cache_data[entity_type]
    except:
        LOG.warning("No data exists for {}".format(entity_type))

    return entity_data


class MockAccountCache:
    __cache_type__ = CACHE.ENTITY.ACCOUNT

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    provider_type=entity["provider_type"],
                    state=entity["state"],
                    data=entity["data"],
                    last_update_time=entity["last_update_time"],
                )
        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockProviderCache:
    __cache_type__ = CACHE.ENTITY.PROVIDER

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    _type=entity["type"],
                    use_parent_auth=entity["use_parent_auth"],
                    parent_uuid=entity["parent_uuid"],
                    infra_type=entity["infra_type"],
                    state=entity["state"],
                    auth_schema_list=entity["auth_schema_list"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockResourceTypeCache:
    __cache_type__ = CACHE.ENTITY.RESOURCE_TYPE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    _type=entity["_type"],
                    tags=entity["tags"],
                    provider_uuid=entity["provider_uuid"],
                    provider_name=entity["provider_name"],
                    state=entity["state"],
                    action_list=entity["action_list"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAhvClustersCache:
    __cache_type__ = CACHE.ENTITY.AHV_CLUSTER

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    pe_account_uuid=entity["pe_account_uuid"],
                    account_uuid=entity["account_uuid"],
                    last_update_time=entity["last_update_time"],
                )
        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAhvVpcsCache:
    __cache_type__ = CACHE.ENTITY.AHV_VPC

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_uuid=entity["account_uuid"],
                    tunnel_name=entity["tunnel_name"],
                    tunnel_uuid=entity["tunnel_uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAhvSubnetsCache:
    __cache_type__ = CACHE.ENTITY.AHV_SUBNET

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                cluster_uuid = entity.get("cluster_uuid", "")
                vpc_uuid = entity.get("vpc_uuid", "")
                kwargs = {
                    "name": entity["name"],
                    "uuid": entity["uuid"],
                    "account_uuid": entity["account_uuid"],
                    "subnet_type": entity.get("subnet_type", "-"),
                    "last_update_time": entity["last_update_time"],
                }
                if cluster_uuid:
                    kwargs["cluster"] = cluster_uuid
                elif vpc_uuid:
                    kwargs["vpc"] = vpc_uuid
                self.model_obj.create(**kwargs)

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAhvImagesCache:
    __cache_type__ = CACHE.ENTITY.AHV_DISK_IMAGE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    image_type=entity["image_type"],
                    account_uuid=entity["account_uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockProjectCache:
    __cache_type__ = CACHE.ENTITY.PROJECT

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    accounts_data=entity["accounts_data"],
                    whitelisted_subnets=entity["whitelisted_subnets"],
                    whitelisted_clusters=entity["whitelisted_clusters"],
                    whitelisted_vpcs=entity["whitelisted_vpcs"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockEnvironmentCache:
    __cache_type__ = CACHE.ENTITY.ENVIRONMENT

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    project_uuid=entity["project_uuid"],
                    accounts_data=entity["accounts_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockUsersCache:
    __cache_type__ = CACHE.ENTITY.USER

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    display_name=entity["display_name"],
                    directory=entity["directory"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockRolesCache:
    __cache_type__ = CACHE.ENTITY.ROLE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockDirectoryServiceCache:
    __cache_type__ = CACHE.ENTITY.DIRECTORY_SERVICE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockUserGroupCache:
    __cache_type__ = CACHE.ENTITY.USER_GROUP

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    display_name=entity["display_name"],
                    directory=entity["directory"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAhvNetworkFunctionChain:
    __cache_type__ = CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAppProtectionPolicyCache:
    __cache_type__ = CACHE.ENTITY.APP_PROTECTION_POLICY

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    rule_name=entity["rule_name"],
                    rule_uuid=entity["rule_uuid"],
                    rule_expiry=entity["rule_expiry"],
                    rule_type=entity["rule_type"],
                    project_name=entity["project_name"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockPolicyEventCache:
    __cache_type__ = CACHE.ENTITY.POLICY_EVENT

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    entity_type=entity["entity_type"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockPolicyAttributesCache:
    __cache_type__ = CACHE.ENTITY.POLICY_ATTRIBUTES

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    event_name=entity["event_name"],
                    type=entity["type"],
                    operators=entity["operators"],
                    jsonpath=entity["jsonpath"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockPolicyActionTypeCache:
    __cache_type__ = CACHE.ENTITY.POLICY_ACTION_TYPE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_DatabaseCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.DATABASE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    _type=entity["type"],
                    status=entity["status"],
                    clone=entity["clone"],
                    clustered=entity["clustered"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_ProfileCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    _type=entity["type"],
                    status=entity["status"],
                    engine_type=entity["engine_type"],
                    system_profile=entity["system_profile"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_SLACache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    continuous_retention=entity["continuous_retention"],
                    daily_retention=entity["daily_retention"],
                    weekly_retention=entity["weekly_retention"],
                    monthly_retention=entity["monthly_retention"],
                    quartely_retention=entity["quartely_retention"],
                    yearly_retention=entity["yearly_retention"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_ClusterCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.CLUSTER

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    status=entity["status"],
                    healthy=entity["healthy"],
                    hypervisor_type=entity["hypervisor_type"],
                    nx_cluster_uuid=entity["nx_cluster_uuid"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_TimeMachineCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TIME_MACHINE

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    status=entity["status"],
                    _type=entity["_type"],
                    clustered=entity["clustered"],
                    slas=entity["slas"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_SnapshotCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SNAPSHOT

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    status=entity["status"],
                    _type=entity["_type"],
                    time_machine_id=entity["time_machine_id"],
                    snapshot_timestamp=entity["snapshot_timestamp"],
                    timezone=entity["timezone"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockNDB_TagCache:
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG

    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = read_cached_data(CACHE_FILE_NAME, self.__cache_type__)
        try:
            for _, entity in entity_data.items():
                self.model_obj.create(
                    name=entity["name"],
                    uuid=entity["uuid"],
                    account_name=entity["account_name"],
                    status=entity["status"],
                    entity_type=entity["entity_type"],
                    values=entity["values"],
                    platform_data=entity["platform_data"],
                    last_update_time=entity["last_update_time"],
                )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockVersionTable:
    def __init__(self, Model):
        self.model_obj = Model()

    def create_test_data(self):
        entity_data = {
            "name": "Calm",
            "version": "3.7.0",
            "last_update_time": "2023-09-07 06:58:27.061793",
        }

        try:
            self.model_obj.create(
                name=entity_data["name"],
                version=entity_data["version"],
                last_update_time=entity_data["last_update_time"],
            )

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


def create_mock_db(initialize=False):
    if initialize:
        init_db_handle()
    db_handler = get_db_handle()
    db_tables = db_handler.registered_tables
    cache_tables = {}

    for table in db_tables:
        if hasattr(table, "__cache_type__"):
            cache_tables[table.__cache_type__] = table
        elif table.__name__ == "VersionTable":
            cache_tables["version_table"] = table

    for _, entity in cache_tables.items():
        class_name = getattr(sys.modules[__name__], "Mock" + entity.__name__)
        md = class_name(entity)

        if not len(md.model_obj.select()):
            md.create_test_data()


create_mock_db(True)
