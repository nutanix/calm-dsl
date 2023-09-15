import sys
import os
import json

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE
from calm.dsl.db.table_config import CacheTableBase, VersionTable
from peewee import OperationalError, IntegrityError
from calm.dsl.db import init_db_handle
from constants import MockConstants

LOG = get_logging_handle(__name__)


class BaseMockCache:
    __cache_type__ = None
    tables = {}

    def __init__(self, Model):
        self.model_obj = Model()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cache_type = cls.get_cache_type()
        if not cache_type:
            raise TypeError("Base table does not have a cache type attribute")

        cls.tables[cache_type] = cls

    @classmethod
    def get_cache_type(cls):
        """
        return cache type for the table
        """
        if not cls.__cache_type__:
            raise Exception("Cache type not implemented for given cache type")

        return cls.__cache_type__

    def update_cache_specific_attrs(self, data):
        """
        Subclasses to override this function if they need to update cache
        attributes that are specific to a given table
        """
        pass

    def read_cached_data(self, entity_type):
        """
        reads cache data from the file
        """
        cache_data_location = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), MockConstants.CACHE_FILE_NAME
        )
        with open(cache_data_location, "r") as file:
            cache_data = json.loads(file.read())

        entity_data = cache_data.get(entity_type, {})
        if not entity_data:
            LOG.warning("No data exists for {}".format(entity_type))

        return entity_data

    def create_test_data(self):
        """
        Inserts entries into mocked db table after fetching data from current db.
        """
        entity_data = self.read_cached_data(self.get_cache_type())
        try:
            for _, entity in entity_data.items():
                self.update_cache_specific_attrs(entity)
                self.model_obj.create(**entity)
        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


class MockAccountCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.ACCOUNT


class MockProviderCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.PROVIDER

    def update_cache_specific_attrs(self, data):
        data["_type"] = data.pop("type")


class MockResourceTypeCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.RESOURCE_TYPE


class MockAhvClustersCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.AHV_CLUSTER


class MockAhvVpcsCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.AHV_VPC


class MockAhvSubnetsCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.AHV_SUBNET

    def update_cache_specific_attrs(self, data):
        cluster_uuid = data.pop("cluster_uuid", "")
        vpc_uuid = data.pop("vpc_uuid", "")
        data["subnet_type"] = data.get("subnet_type", "-")
        if cluster_uuid:
            data["cluster"] = cluster_uuid
        elif vpc_uuid:
            data["vpc"] = vpc_uuid


class MockAhvImagesCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.AHV_DISK_IMAGE


class MockProjectCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.PROJECT


class MockEnvironmentCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.ENVIRONMENT


class MockUsersCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.USER


class MockRolesCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.ROLE


class MockDirectoryServiceCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.DIRECTORY_SERVICE


class MockUserGroupCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.USER_GROUP


class MockAhvNetworkFunctionChain(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN


class MockAppProtectionPolicyCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.APP_PROTECTION_POLICY


class MockPolicyEventCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.POLICY_EVENT


class MockPolicyAttributesCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.POLICY_ATTRIBUTES


class MockPolicyActionTypeCache(BaseMockCache):
    __cache_type__ = CACHE.ENTITY.POLICY_ACTION_TYPE


class MockNDB_DatabaseCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.DATABASE

    def update_cache_specific_attrs(self, data):
        data["_type"] = data.pop("type")


class MockNDB_ProfileCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE

    def update_cache_specific_attrs(self, data):
        data["_type"] = data.pop("type")


class MockNDB_SLACache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA


class MockNDB_ClusterCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.CLUSTER


class MockNDB_TimeMachineCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TIME_MACHINE


class MockNDB_SnapshotCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SNAPSHOT


class MockNDB_TagCache(BaseMockCache):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG


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
            self.model_obj.create(**entity_data)

        except (OperationalError, IntegrityError):
            LOG.error("Error inserting data into db.")


def create_mock_db(initialize=False):
    """
    Creates the mock data base.
    Args:
        initialize(bool): Pass True if need to initialize db or re-insert data to table.
    """

    if initialize:
        init_db_handle()

    for table_type, table in CacheTableBase.tables.items():
        if BaseMockCache.tables.get(table_type):
            mock_table_obj = BaseMockCache.tables[table_type](table)
            mock_table_obj.create_test_data()

    # Handle version table
    MockVersionTable(VersionTable).create_test_data()


if __name__ == "__main__":

    mock_db_initialised = True

    if len(sys.argv) > 1:
        mock_db_initialised = sys.argv[1]
        mock_db_initialised = True if mock_db_initialised == "True" else False

    create_mock_db(mock_db_initialised)
