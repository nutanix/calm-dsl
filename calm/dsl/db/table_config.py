from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    BlobField,
    DateTimeField,
    ForeignKeyField,
    BooleanField,
    CompositeKey,
    DoesNotExist,
    IntegerField,
)
import datetime
import click
import arrow
import json
import sys
import re
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE, TUNNEL, GLOBAL_VARIABLE, VARIABLE
from calm.dsl.api.util import is_policy_check_required


LOG = get_logging_handle(__name__)
NON_ALPHA_NUMERIC_CHARACTER = "[^0-9a-zA-Z]+"
REPLACED_CLUSTER_NAME_CHARACTER = "_"
# Proxy database
dsl_database = SqliteDatabase(None)

context = get_context()
ncm_server_config = context.get_ncm_server_config()
NCM_ENABLED = ncm_server_config.get("ncm_enabled", False)


class BaseModel(Model):
    class Meta:
        database = dsl_database


class SecretTable(BaseModel):
    name = CharField(primary_key=True)
    uuid = CharField()
    creation_time = DateTimeField(default=datetime.datetime.now())
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "creation_time": self.creation_time,
            "last_update_time": self.last_update_time,
        }


class DataTable(BaseModel):
    secret_ref = ForeignKeyField(SecretTable, backref="data")
    kdf_salt = BlobField()
    ciphertext = BlobField()
    iv = BlobField()
    auth_tag = BlobField()
    pass_phrase = BlobField()

    def generate_enc_msg(self):
        return (self.kdf_salt, self.ciphertext, self.iv, self.auth_tag)


class CacheTableBase(BaseModel):
    tables = {}
    is_approval_policy_required = False
    is_policy_required = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cache_type = cls.get_cache_type()
        if not cache_type:
            raise TypeError("Base table does not have a cache type attribute")

        cls.tables[cache_type] = cls

    def get_detail_dict(self):
        raise NotImplementedError(
            "get_detail_dict helper not implemented for {} table".format(
                self.get_cache_type()
            )
        )

    @classmethod
    def get_detail_dict_list(cls, qeury_obj):
        """
        This helper returns multiple matching instance for a given query
        Args:
            query_obj (pewee.ModelSelect object): containing multiple matching instance
            object for a query
        Returns:
            entity_details (list): list of dict containing each entity data fetched from database
        """
        raise NotImplementedError(
            "'get_detail_dict_list' helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def get_provider_plugin(self, provider_type="AHV_VM"):
        """returns the provider plugin"""

        # Not a top-level import because of : https://github.com/ideadevice/calm-dsl/issues/33
        from calm.dsl.providers import get_provider

        return get_provider(provider_type)

    @classmethod
    def get_cache_tables(cls):
        return cls.tables

    @classmethod
    def get_cache_type(cls):
        """return cache type for the table"""

        return getattr(cls, "__cache_type__", None)

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        raise NotImplementedError(
            "clear helper not implemented for {} table".format(cls.get_cache_type())
        )

    @classmethod
    def show_data(cls):
        raise NotImplementedError(
            "show_data helper not implemented for {} table".format(cls.get_cache_type())
        )

    @classmethod
    def sync(cls):
        raise NotImplementedError(
            "sync helper not implemented for {} table".format(cls.get_cache_type())
        )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        raise NotImplementedError(
            "create_entry helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        raise NotImplementedError(
            "get_entity_data helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        raise NotImplementedError(
            "get_entity_data_using_uuid helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def fetch_one(cls, uuid):
        raise NotImplementedError(
            "fetch one helper not implemented for {} table".format(cls.get_cache_type())
        )

    @classmethod
    def add_one(cls, uuid, **kwargs):
        raise NotImplementedError(
            "add_one helper not implemented for {} table".format(cls.get_cache_type())
        )

    @classmethod
    def add_one_by_entity_dict(cls, entity):
        raise NotImplementedError(
            "add_one_by_entity_dict method not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        raise NotImplementedError(
            "delete_one helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )

    @classmethod
    def update_one(cls, uuid, **kwargs):
        raise NotImplementedError(
            "update_one helper not implemented for {} table".format(
                cls.get_cache_type()
            )
        )


class AccountCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.ACCOUNT
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    provider_type = CharField()
    state = CharField()
    is_host = BooleanField(default=False)  # Used for Ntnx accounts only
    data = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "provider_type": self.provider_type,
            "state": self.state,
            "is_host": self.is_host,
            "data": json.loads(self.data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "PROVIDER_TYPE", "UUID", "STATE", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["provider_type"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["state"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        provider_type = kwargs.get("provider_type", "")
        if not provider_type:
            LOG.error("Provider type not supplied for fetching user {}".format(name))
            sys.exit(-1)

        is_host = kwargs.get("is_host", False)
        data = kwargs.get("data", "{}")
        state = kwargs.get("state", "")

        super().create(
            name=name,
            uuid=uuid,
            provider_type=provider_type,
            is_host=is_host,
            data=data,
            state=state,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {
            "length": 250,
            "filter": "(state==ACTIVE,state==VERIFIED)",
        }

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if stratos_config.get("stratos_status", False):
            payload["filter"] += ";child_account==true"

        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):
            provider_type = entity["status"]["resources"]["type"]
            data = {}
            query_obj = {
                "name": entity["status"]["name"],
                "uuid": entity["metadata"]["uuid"],
                "provider_type": entity["status"]["resources"]["type"],
                "state": entity["status"]["resources"]["state"],
            }

            if provider_type == "nutanix_pc":
                query_obj["is_host"] = entity["status"]["resources"]["data"]["host_pc"]

                # store cluster accounts for PC account (Note it will store account name)
                for pe_acc in (
                    entity["status"]["resources"]
                    .get("data", {})
                    .get("cluster_account_reference_list", [])
                ):
                    group = data.setdefault("clusters", {})
                    group[pe_acc["uuid"]] = (
                        pe_acc.get("resources", {})
                        .get("data", {})
                        .get("cluster_name", "")  # This is  the account_name itself
                    )

            elif provider_type == "nutanix":
                data["pc_account_uuid"] = entity["status"]["resources"]["data"][
                    "pc_account_uuid"
                ]

            query_obj["data"] = json.dumps(data)
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        provider_type = kwargs.get("provider_type", "")
        if provider_type:
            query_obj["provider_type"] = provider_type

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """returns project data for project uuid"""

        # update by latest data
        client = get_api_client()

        res, err = client.account.read(uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity = res.json()
        provider_type = entity["status"]["resources"]["type"]
        data = {}
        query_obj = {
            "name": entity["status"]["name"],
            "uuid": entity["metadata"]["uuid"],
            "provider_type": entity["status"]["resources"]["type"],
            "state": entity["status"]["resources"]["state"],
        }

        if provider_type == "nutanix_pc":
            query_obj["is_host"] = entity["status"]["resources"]["data"]["host_pc"]

            # store cluster accounts for PC account (Note it will store cluster name not account name)
            for pe_acc in (
                entity["status"]["resources"]
                .get("data", {})
                .get("cluster_account_reference_list", [])
            ):
                group = data.setdefault("clusters", {})
                group[pe_acc["uuid"]] = (
                    pe_acc.get("resources", {}).get("data", {}).get("cluster_name", "")
                )

        elif provider_type == "nutanix":
            data["pc_account_uuid"] = entity["status"]["resources"]["data"][
                "pc_account_uuid"
            ]

        query_obj["data"] = json.dumps(data)
        return query_obj

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to project table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from project"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to project table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        q = cls.update(
            {
                cls.name: db_data["name"],
                cls.provider_type: db_data["provider_type"],
                cls.state: db_data["state"],
                cls.data: db_data["data"],
            }
        ).where(cls.uuid == uuid)
        q.execute()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class ProviderCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.PROVIDER
    feature_min_version = "3.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    _type = CharField()
    use_parent_auth = BooleanField(default=False)
    parent_uuid = CharField()
    infra_type = CharField()
    state = CharField()
    auth_schema_list = BlobField()
    variable_list = BlobField()
    endpoint_schema = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "type": self._type,
            "state": self.state,
            "infra_type": self.infra_type,
            "parent_uuid": self.parent_uuid,
            "use_parent_auth": self.use_parent_auth,
            "auth_schema_list": json.loads(self.auth_schema_list),
            "variable_list": json.loads(self.variable_list),
            "endpoint_schema": json.loads(self.endpoint_schema),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def _get_dict_for_db_upsert(cls, entity):
        return {
            "name": entity["status"]["name"],
            "uuid": entity["metadata"]["uuid"],
            "_type": entity["status"]["resources"].get("type", ""),
            "infra_type": entity["status"]["resources"].get("infra_type", ""),
            "parent_uuid": entity["status"]["resources"]
            .get("parent_reference", {})
            .get("uuid", ""),
            "use_parent_auth": entity["status"]["resources"].get(
                "use_parent_auth", False
            ),
            "auth_schema_list": json.dumps(
                entity["status"]["resources"].get("auth_schema_list", {})
            ),
            "variable_list": json.dumps(
                entity["status"]["resources"].get("variable_list", {})
            ),
            "endpoint_schema": json.dumps(
                entity["status"]["resources"].get("endpoint_schema", {})
            ),
            "state": entity["status"]["state"],
        }

    @classmethod
    def add_one_by_entity_dict(cls, entity):
        """adds one entry to provider table"""
        db_data = cls._get_dict_for_db_upsert(entity)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one provider entity from cache"""
        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "INFRA TYPE", "UUID", "STATE", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["infra_type"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["state"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        _type = kwargs.get("type", "")
        infra_type = kwargs.get("infra_type", "cloud")
        parent_uuid = kwargs.get("parent_uuid", "")
        use_parent_auth = kwargs.get("use_parent_auth", False)
        state = kwargs.get("state", "")
        auth_schema_list = kwargs.get("auth_schema_list", "[]")
        variable_list = kwargs.get("variable_list", "[]")
        endpoint_schema = kwargs.get("endpoint_schema", "{}")

        super().create(
            name=name,
            uuid=uuid,
            _type=_type,
            infra_type=infra_type,
            parent_uuid=parent_uuid,
            state=state,
            use_parent_auth=use_parent_auth,
            auth_schema_list=auth_schema_list,
            variable_list=variable_list,
            endpoint_schema=endpoint_schema,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": ""}

        ContextObj = get_context()
        stratos_status = ContextObj.get_stratos_config().get("stratos_status", False)
        cp_status = ContextObj.get_cp_config().get("cp_status", False)
        if cp_status:
            additional_fltr = "type==SYS_CUSTOM|CUSTOM|CREDENTIAL|SYS_CREDENTIAL"
            if not stratos_status:  # Exclude NDB provider if stratos is not enabled
                additional_fltr += ";name!=NDB"
            payload["filter"] = additional_fltr
        elif stratos_status:
            payload["filter"] = "type==SYS_CUSTOM|CUSTOM|CREDENTIAL|SYS_CREDENTIAL"

        res, err = client.provider.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):
            query_obj = cls._get_dict_for_db_upsert(entity)
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class ResourceTypeCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.RESOURCE_TYPE
    feature_min_version = "3.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    _type = CharField()
    state = CharField()
    tags = CharField()
    provider_uuid = CharField()
    provider_name = CharField()
    action_list = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def _get_dict_for_db_upsert(cls, entity):
        return {
            "name": entity["status"]["name"],
            "uuid": entity["metadata"]["uuid"],
            "state": entity["status"]["state"],
            "_type": entity["status"]["resources"].get("type", ""),
            "tags": json.dumps(entity["status"]["resources"].get("tags", [])),
            "provider_uuid": entity["status"]["resources"]
            .get("provider_reference", {})
            .get("uuid", ""),
            "provider_name": entity["status"]["resources"]
            .get("provider_reference", {})
            .get("name", ""),
            "action_list": json.dumps(
                entity["status"]["resources"].get("action_list", [])
            ),
        }

    @classmethod
    def add_one_by_entity_dict(cls, entity):
        """adds one entry to provider table"""
        db_data = cls._get_dict_for_db_upsert(entity)
        cls.create_entry(**db_data)

    @classmethod
    def delete_by_provider(cls, provider_name):
        query = cls.delete().where(cls.provider_name == provider_name)
        return query.execute()

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "_type": self._type,
            "state": self.state,
            "tags": json.loads(self.tags),
            "provider_uuid": self.provider_uuid,
            "provider_name": self.provider_name,
            "action_list": json.loads(self.action_list),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "TAGs",
            "PROVIDER NAME",
            "UUID",
            "STATE",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["tags"]),
                    highlight_text(entity_data["provider_name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["state"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        provider_name = kwargs.get("provider_name", "")
        if not provider_name:
            LOG.error(
                "provider_name not supplied for fetching resource_type {}".format(name)
            )
            sys.exit(-1)

        _type = kwargs.get("_type", "")
        tags = kwargs.get("tags", "[]")
        state = kwargs.get("state", "")
        provider_uuid = kwargs.get("provider_uuid", "")
        action_list = kwargs.get("action_list", "[]")

        super().create(
            name=name,
            uuid=uuid,
            provider_uuid=provider_uuid,
            _type=_type,
            tags=tags,
            state=state,
            provider_name=provider_name,
            action_list=action_list,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {
            "length": 250,
            "filter": "",
        }

        ContextObj = get_context()
        stratos_status = ContextObj.get_stratos_config().get("stratos_status", False)
        cp_status = ContextObj.get_cp_config().get("cp_status", False)
        if cp_status:
            additional_fltr = (
                "provider_type==SYS_CUSTOM|CUSTOM|CREDENTIAL|SYS_CREDENTIAL"
            )
            if not stratos_status:  # Exclude NDB provider if stratos is not enabled
                additional_fltr += ";provider_name!=NDB"
            payload["filter"] = additional_fltr

        elif stratos_status:
            payload[
                "filter"
            ] = "provider_type==SYS_CUSTOM|CUSTOM|CREDENTIAL|SYS_CREDENTIAL"

        res, err = client.resource_types.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):
            query_obj = cls._get_dict_for_db_upsert(entity)
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        provider_name = kwargs.get("provider_name", "")
        if provider_name:
            query_obj["provider_name"] = provider_name

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "provider_uuid")


class AhvClustersCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_CLUSTER
    feature_min_version = "3.5.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    pe_account_uuid = CharField(default="")
    account_uuid = CharField(default="")
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "pe_account_uuid": self.pe_account_uuid,
            "account_uuid": self.account_uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "PE_ACCOUNT_UUID",
            "ACCOUNT_UUID",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["pe_account_uuid"]),
                    highlight_text(entity_data["account_uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = cls.get_provider_plugin("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for pc_acc_name, pc_acc_uuid in account_name_uuid_map.items():

            # Get pe-accoun-uuid to cluster-uuid map
            res, err = client.account.read(pc_acc_uuid)
            if err:
                LOG.error("[{}] - {}".format(err["code"], err["error"]))
                continue

            pc_acc_data = res.json()
            cluster_uuid_pe_account_uuid_map = {}
            for _cluster_data in pc_acc_data["status"]["resources"]["data"].get(
                "cluster_account_reference_list", []
            ):
                _cluster_uuid = _cluster_data["resources"]["data"].get(
                    "cluster_uuid", ""
                )
                cluster_uuid_pe_account_uuid_map[_cluster_uuid] = _cluster_data["uuid"]

            try:
                res = AhvObj.clusters(account_uuid=pc_acc_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch clusters for Nutanix_PC Account(uuid={})".format(
                        pc_acc_name
                    )
                )
                continue

            for entity in res.get("entities", []):
                cluster_name = entity["status"]["name"]
                cluster_uuid = entity["metadata"]["uuid"]

                if not cluster_uuid_pe_account_uuid_map.get(cluster_uuid, ""):
                    LOG.debug(
                        "Ignoring cluster '{}' with uuid '{}', as it doesn't have any pe account".format(
                            cluster_name, cluster_uuid
                        )
                    )
                    continue

                cls.create_entry(
                    name=cluster_name,
                    uuid=cluster_uuid,
                    pe_account_uuid=cluster_uuid_pe_account_uuid_map[cluster_uuid],
                    account_uuid=pc_acc_uuid,
                )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        """
        Creates an entry for an AHV PE Cluster.

        Args:
            name: Name of the AHV PE cluster.
            uuid: UUID of the AHV PE cluster.
        """
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for AHV PE Cluster {}".format(name))
            sys.exit(-1)

        pe_account_uuid = kwargs.get("pe_account_uuid", "")
        if not pe_account_uuid:
            LOG.error("PE Cluster UUID not supplied for AHV PE Cluster {}".format(name))
            sys.exit(-1)

        # store data in table
        super().create(
            name=name,
            uuid=uuid,
            pe_account_uuid=pe_account_uuid,
            account_uuid=account_uuid,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}
        pe_account_uuid = kwargs.get("pe_account_uuid", "")
        if pe_account_uuid:
            query_obj["pe_account_uuid"] = pe_account_uuid

        account_uuid = kwargs.get("account_uuid", "")
        if account_uuid:
            query_obj["account_uuid"] = account_uuid

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        pe_account_uuid = kwargs.get("pe_account", "")

        try:
            if pe_account_uuid:
                entity = super().get(
                    cls.uuid == uuid, cls.pe_account == pe_account_uuid
                )
            else:
                entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_uuid")


class AhvVpcsCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_VPC
    feature_min_version = "3.5.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    account_uuid = CharField(default="")
    tunnel_name = CharField(default="")
    tunnel_uuid = CharField(default="")
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_uuid": self.account_uuid,
            "tunnel_name": self.tunnel_name,
            "tunnel_uuid": self.tunnel_uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "TUNNEL_NAME",
            "TUNNEL_UUID",
            "ACCOUNT_UUID",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(
                        entity_data["tunnel_name"]
                        if entity_data["tunnel_name"] != ""
                        else "-"
                    ),
                    highlight_text(
                        entity_data["tunnel_uuid"]
                        if entity_data["tunnel_uuid"] != ""
                        else "-"
                    ),
                    highlight_text(entity_data["account_uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)
        AhvVmProvider = cls.get_provider_plugin("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        # Get all Calm vpcs and Tunnels
        calm_vpc_entities = client.network_group.list_all()
        for pc_acc_name, pc_acc_uuid in account_name_uuid_map.items():
            try:
                res = AhvObj.vpcs(account_uuid=pc_acc_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch vpcs for Nutanix_PC Account(uuid={})".format(
                        pc_acc_name
                    )
                )
                continue

            for entity in res.get("entities", []):
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]

                # TODO improve this, it shouldn't iterate over these entities every time
                tunnel_reference = next(
                    (
                        calm_vpc["status"]["resources"].get("tunnel_reference", {})
                        for calm_vpc in calm_vpc_entities
                        if uuid
                        in calm_vpc["status"]["resources"].get(
                            "platform_vpc_uuid_list", []
                        )
                    ),
                    {},
                )

                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    account_uuid=pc_acc_uuid,
                    tunnel_reference=tunnel_reference,
                )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        """
        Creates an entry for an AHV PE Cluster.

        Args:
            name: Name of the AHV PE cluster.
            uuid: UUID of the AHV PE cluster.
        """
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for VPC {}".format(name))
            sys.exit(-1)
        tunnel_reference = kwargs.get("tunnel_reference", {})
        kwargs = {"name": name, "uuid": uuid, "account_uuid": account_uuid}
        if tunnel_reference:
            kwargs["tunnel_name"] = tunnel_reference.get("name", "")
            kwargs["tunnel_uuid"] = tunnel_reference.get("uuid", "")

        # store data in table
        super().create(**kwargs)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {}
        if name:
            query_obj = {"name": name}

        account_uuid = kwargs.get("account_uuid", "")
        if account_uuid:
            query_obj["account_uuid"] = account_uuid

        tunnel_name = kwargs.get("tunnel_name", "")
        if tunnel_name:
            query_obj["tunnel_name"] = tunnel_name

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):

        query_obj = {}
        if uuid:
            query_obj["uuid"] = uuid

        if kwargs.get("tunnel_uuid", ""):
            query_obj["tunnel_uuid"] = kwargs.get("tunnel_uuid")

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_uuid")


class AhvSubnetsCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_SUBNET
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    account_uuid = CharField(default="")
    last_update_time = DateTimeField(default=datetime.datetime.now())
    subnet_type = CharField()
    cluster = ForeignKeyField(AhvClustersCache, to_field="uuid", null=True)
    vpc = ForeignKeyField(AhvVpcsCache, to_field="uuid", null=True)

    def get_detail_dict(self, *args, **kwargs):
        details = {
            "name": self.name,
            "uuid": self.uuid,
            "subnet_type": self.subnet_type,
            "account_uuid": self.account_uuid,
            "last_update_time": self.last_update_time,
        }
        if self.cluster:
            details["cluster_name"] = self.cluster.name
            details["cluster_uuid"] = self.cluster.uuid
        elif self.vpc:
            details["vpc_name"] = self.vpc.name
            details["vpc_uuid"] = self.vpc.uuid
        return details

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "TYPE",
            "CLUSTER_NAME",
            "CLUSTER_UUID",
            "VPC_NAME",
            "VPC_UUID",
            "ACCOUNT_UUID",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["subnet_type"]),
                    highlight_text(entity_data.get("cluster_name", "-")),
                    highlight_text(entity_data.get("cluster_uuid", "-")),
                    highlight_text(entity_data.get("vpc_name", "-")),
                    highlight_text(entity_data.get("vpc_uuid", "-")),
                    highlight_text(entity_data["account_uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = cls.get_provider_plugin("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for _, e_uuid in account_name_uuid_map.items():
            try:
                res = AhvObj.subnets(account_uuid=e_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                        e_uuid
                    )
                )
                continue

            for entity in res.get("entities", []):
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]
                subnet_type = (
                    entity["status"].get("resources", {}).get("subnet_type", "-")
                )
                cluster_uuid = (
                    entity["status"].get("cluster_reference", {}).get("uuid", "")
                )
                vpc_uuid = (
                    entity["status"]
                    .get("resources")
                    .get("vpc_reference", {})
                    .get("uuid", "")
                )
                LOG.debug(
                    "Cluster: {}, VPC: {} for account: {}, subnet: {}".format(
                        cluster_uuid, vpc_uuid, e_uuid, uuid
                    )
                )
                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    subnet_type=subnet_type,
                    account_uuid=e_uuid,
                    cluster_uuid=cluster_uuid,
                    vpc_uuid=vpc_uuid,
                )

        # For older version < 2.9.0
        # Add working for older versions too

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for subnet {}".format(name))
            sys.exit(-1)

        cluster_uuid = kwargs.get("cluster_uuid", "")
        vpc_uuid = kwargs.get("vpc_uuid", "")
        subnet_type = kwargs.get("subnet_type", "-")
        kwargs = {
            "name": name,
            "uuid": uuid,
            "account_uuid": account_uuid,
            "subnet_type": subnet_type,
        }
        if cluster_uuid:
            kwargs["cluster"] = cluster_uuid
        elif vpc_uuid:
            kwargs["vpc"] = vpc_uuid

        # store data in table
        super().create(**kwargs)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}
        account_uuid = kwargs.get("account_uuid", "")
        if account_uuid:
            query_obj["account_uuid"] = account_uuid

        cluster_name = kwargs.get("cluster", "")
        vpc_name = kwargs.get("vpc", "")
        if cluster_name:
            cluster_query_obj = {"name": cluster_name}
            if account_uuid:
                cluster_query_obj["account_uuid"] = account_uuid
            cluster = AhvClustersCache.get(**cluster_query_obj)
            query_obj["cluster"] = cluster.uuid
        elif vpc_name:
            vpc_query_obj = {"name": vpc_name}
            if account_uuid:
                vpc_query_obj["account_uuid"] = account_uuid
            vpc = AhvVpcsCache.get(**vpc_query_obj)
            query_obj["vpc"] = vpc.uuid
        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")

        try:
            if account_uuid:
                entity = super().get(cls.uuid == uuid, cls.account_uuid == account_uuid)
            else:
                entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_uuid")


class AhvImagesCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_DISK_IMAGE
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    image_type = CharField()
    uuid = CharField()
    account_uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "image_type": self.image_type,
            "account_uuid": self.account_uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "IMAGE_TYPE",
            "ACCOUNT_UUID",
            "LAST UPDATED",
        ]
        for entity in cls.select().order_by(cls.image_type):
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["image_type"]),
                    highlight_text(entity_data["account_uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = cls.get_provider_plugin("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for _, e_uuid in account_name_uuid_map.items():
            try:
                res = AhvObj.images(account_uuid=e_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch images for Nutanix_PC Account(uuid={})".format(
                        e_uuid
                    )
                )
                continue

            for entity in res.get("entities", []):
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]
                # TODO add proper validation for karbon images
                image_type = entity["status"]["resources"].get("image_type", "")
                cls.create_entry(
                    name=name, uuid=uuid, image_type=image_type, account_uuid=e_uuid
                )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for image {}".format(name))
            sys.exit(-1)

        image_type = kwargs.get("image_type", "")
        # store data in table
        super().create(
            name=name, uuid=uuid, image_type=image_type, account_uuid=account_uuid
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for fetching image {}".format(name))
            sys.exit(-1)

        image_type = kwargs.get("image_type", None)
        if not image_type:
            LOG.error("image_type not provided for image {}".format(name))
            sys.exit(-1)

        query_obj = {
            "name": name,
            "image_type": image_type,
            "account_uuid": account_uuid,
        }

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")

        try:
            if account_uuid:
                entity = super().get(cls.uuid == uuid, cls.account_uuid == account_uuid)
            else:
                entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_uuid")


class ProjectCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.PROJECT
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    accounts_data = CharField()
    whitelisted_subnets = CharField()
    whitelisted_clusters = CharField()
    whitelisted_vpcs = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "accounts_data": json.loads(self.accounts_data),
            "whitelisted_subnets": json.loads(self.whitelisted_subnets),
            "whitelisted_clusters": json.loads(self.whitelisted_clusters),
            "whitelisted_vpcs": json.loads(self.whitelisted_vpcs),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""
        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()

        payload = {"length": 200, "offset": 0, "filter": "state!=DELETED;type!=nutanix"}
        account_uuid_type_map = client.account.get_uuid_type_map(payload)

        # store subnets for nutanix_pc accounts in some map, else we had to subnets api
        # for each project (Speed very low in case of ~1000 projects)
        ntnx_pc_account_subnet_map = dict()
        ntnx_pc_account_vpc_map = dict()
        ntnx_pc_account_cluster_map = dict()
        ntnx_pc_subnet_cluster_map = dict()
        ntnx_pc_subnet_vpc_map = dict()
        for _acct_uuid in account_uuid_type_map.keys():
            if account_uuid_type_map[_acct_uuid] == "nutanix_pc":
                ntnx_pc_account_subnet_map[_acct_uuid] = list()
                ntnx_pc_account_vpc_map[_acct_uuid] = list()
                ntnx_pc_account_cluster_map[_acct_uuid] = list()

        # Get the subnets for each nutanix_pc account
        AhvVmProvider = cls.get_provider_plugin("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()
        for acct_uuid in ntnx_pc_account_subnet_map.keys():
            LOG.debug(
                "Fetching subnets for nutanix_pc account_uuid {}".format(acct_uuid)
            )
            res = {}
            try:
                res = AhvObj.subnets(account_uuid=acct_uuid)
            except Exception as exp:
                LOG.exception(exp)
                LOG.warning(
                    "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                        acct_uuid
                    )
                )
                continue

            for row in res.get("entities", []):
                _sub_uuid = row["metadata"]["uuid"]
                ntnx_pc_account_subnet_map[acct_uuid].append(_sub_uuid)
                if row["status"]["resources"]["subnet_type"] == "VLAN":
                    ntnx_pc_subnet_cluster_map[_sub_uuid] = row["status"][
                        "cluster_reference"
                    ]["uuid"]
                elif row["status"]["resources"]["subnet_type"] == "OVERLAY":
                    ntnx_pc_subnet_vpc_map[_sub_uuid] = row["status"]["resources"][
                        "vpc_reference"
                    ]["uuid"]

            LOG.debug(
                "Fetching clusters for nutanix_pc account_uuid {}".format(acct_uuid)
            )
            res = {}
            try:
                res = AhvObj.clusters(account_uuid=acct_uuid)
            except Exception as exp:
                LOG.exception(exp)
                LOG.warning(
                    "Unable to fetch clusters for Nutanix_PC Account(uuid={})".format(
                        acct_uuid
                    )
                )
            for row in res.get("entities", []):
                ntnx_pc_account_cluster_map[acct_uuid].append(row["metadata"]["uuid"])

            LOG.debug("Fetching VPCs for nutanix_pc account_uuid {}".format(acct_uuid))
            res = {}
            try:
                res = AhvObj.vpcs(account_uuid=acct_uuid)
            except Exception as exp:
                LOG.exception(exp)
                LOG.warning(
                    "Unable to fetch VPCs for Nutanix_PC Account(uuid={})".format(
                        acct_uuid
                    )
                )
            for row in res.get("entities", []):
                ntnx_pc_account_vpc_map[acct_uuid].append(row["metadata"]["uuid"])

        # Getting projects data
        res_entities, err = client.project.list_all(ignore_error=True)
        if err:
            LOG.exception(err)

        for entity in res_entities:
            # populating a map to lookup the account to which a subnet belongs
            whitelisted_subnets = dict()
            whitelisted_clusters = dict()
            whitelisted_vpcs = dict()

            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]

            account_list = entity["status"]["resources"].get(
                "account_reference_list", []
            )

            cluster_uuids = [
                cluster["uuid"]
                for cluster in entity["status"]["resources"].get(
                    "cluster_reference_list", []
                )
            ]
            vpc_uuids = [
                vpc["uuid"]
                for vpc in entity["status"]["resources"].get("vpc_reference_list", [])
            ]

            project_subnets_ref_list = entity["spec"].get("resources", {}).get(
                "external_network_list", []
            ) + entity["spec"].get("resources", {}).get("subnet_reference_list", [])
            project_subnet_uuids = [item["uuid"] for item in project_subnets_ref_list]

            account_map = {}
            for account in account_list:
                account_uuid = account["uuid"]
                # As projects may have deleted accounts registered
                if account_uuid not in account_uuid_type_map:
                    continue

                account_type = account_uuid_type_map[account_uuid]

                if not account_map.get(account_type):
                    account_map[account_type] = []

                account_map[account_type].append(account_uuid)

                # for PC accounts add subnets to subnet_to_account_map. Will use it to populate whitelisted_subnets
                if account_type == "nutanix_pc":
                    whitelisted_subnets[account_uuid] = list(
                        set(project_subnet_uuids)
                        & set(ntnx_pc_account_subnet_map[account_uuid])
                    )

                    for _subnet_uuid in whitelisted_subnets[account_uuid]:
                        _subnet_cluster_uuid = ntnx_pc_subnet_cluster_map.get(
                            _subnet_uuid
                        )
                        if (
                            _subnet_cluster_uuid
                            and _subnet_cluster_uuid not in cluster_uuids
                        ):
                            cluster_uuids.append(_subnet_cluster_uuid)
                        _subnet_vpc_uuid = ntnx_pc_subnet_vpc_map.get(_subnet_uuid)
                        if _subnet_vpc_uuid and _subnet_vpc_uuid not in vpc_uuids:
                            vpc_uuids.append(_subnet_vpc_uuid)

                    whitelisted_vpcs[account_uuid] = list(
                        set(vpc_uuids) & set(ntnx_pc_account_vpc_map[account_uuid])
                    )

                    whitelisted_clusters[account_uuid] = list(
                        set(cluster_uuids)
                        & set(ntnx_pc_account_cluster_map[account_uuid])
                    )

            accounts_data = json.dumps(account_map)

            whitelisted_subnets = json.dumps(whitelisted_subnets)
            whitelisted_clusters = json.dumps(whitelisted_clusters)
            whitelisted_vpcs = json.dumps(whitelisted_vpcs)
            cls.create_entry(
                name=name,
                uuid=uuid,
                accounts_data=accounts_data,
                whitelisted_subnets=whitelisted_subnets,
                whitelisted_clusters=whitelisted_clusters,
                whitelisted_vpcs=whitelisted_vpcs,
            )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        accounts_data = kwargs.get("accounts_data", "{}")
        whitelisted_subnets = kwargs.get("whitelisted_subnets", "[]")
        whitelisted_clusters = kwargs.get("whitelisted_clusters", "[]")
        whitelisted_vpcs = kwargs.get("whitelisted_vpcs", "[]")
        super().create(
            name=name,
            uuid=uuid,
            accounts_data=accounts_data,
            whitelisted_subnets=whitelisted_subnets,
            whitelisted_clusters=whitelisted_clusters,
            whitelisted_vpcs=whitelisted_vpcs,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """returns project data for project uuid"""

        # update by latest data
        client = get_api_client()

        payload = {"length": 200, "offset": 0, "filter": "state!=DELETED;type!=nutanix"}
        account_uuid_type_map = client.account.get_uuid_type_map(payload)

        res, err = client.project.read(uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            return {}

        project_data = res.json()
        project_name = project_data["spec"]["name"]
        account_list = project_data["spec"]["resources"].get(
            "account_reference_list", []
        )
        project_subnets_ref_list = project_data["spec"].get("resources", {}).get(
            "external_network_list", []
        ) + project_data["spec"].get("resources", {}).get("subnet_reference_list", [])
        project_subnet_uuids = [item["uuid"] for item in project_subnets_ref_list]

        project_cluster_uuids = [
            cluster["uuid"]
            for cluster in project_data["status"]["resources"].get(
                "cluster_reference_list", []
            )
        ]
        project_vpc_uuids = [
            vpc["uuid"]
            for vpc in project_data["status"]["resources"].get("vpc_reference_list", [])
        ]

        # populating a map to lookup the account to which a subnet belongs
        whitelisted_subnets = dict()
        whitelisted_clusters = dict()
        whitelisted_vpcs = dict()
        account_map = dict()
        for _acc in account_list:
            account_uuid = _acc["uuid"]

            # As projects may have deleted accounts registered
            if account_uuid not in account_uuid_type_map:
                continue
            account_type = account_uuid_type_map[account_uuid]
            if account_type not in account_map:
                account_map[account_type] = [account_uuid]
            else:
                account_map[account_type].append(account_uuid)

            if account_type == "nutanix_pc":
                AhvVmProvider = cls.get_provider_plugin("AHV_VM")
                AhvObj = AhvVmProvider.get_api_obj()

                filter_query = "_entity_id_=={}".format("|".join(project_subnet_uuids))
                LOG.debug(
                    "fetching following subnets {} for nutanix_pc account_uuid {}".format(
                        project_subnet_uuids, account_uuid
                    )
                )
                try:
                    res = AhvObj.subnets(
                        account_uuid=account_uuid, filter_query=filter_query
                    )
                except Exception:
                    LOG.warning(
                        "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                            account_uuid
                        )
                    )
                    continue

                whitelisted_subnets[account_uuid] = [
                    row["metadata"]["uuid"] for row in res["entities"]
                ]
                for row in res.get("entities", []):
                    _cluster_uuid = (row["status"].get("cluster_reference") or {}).get(
                        "uuid", ""
                    )
                    _vpc_uuid = (
                        row["status"]["resources"].get("vpc_reference") or {}
                    ).get("uuid", "")
                    whitelisted_subnets[account_uuid].append(row["metadata"]["uuid"])
                    if (
                        row["status"]["resources"]["subnet_type"] == "VLAN"
                        and _cluster_uuid not in project_cluster_uuids
                    ):
                        project_cluster_uuids.append(_cluster_uuid)
                    elif (
                        row["status"]["resources"]["subnet_type"] == "OVERLAY"
                        and _vpc_uuid not in project_vpc_uuids
                    ):
                        project_vpc_uuids.append(_vpc_uuid)

                # fetch clusters
                if project_cluster_uuids:
                    filter_query = "_entity_id_=={}".format(
                        "|".join(project_cluster_uuids)
                    )
                    LOG.debug(
                        "fetching following cluster {} for nutanix_pc account_uuid {}".format(
                            project_cluster_uuids, account_uuid
                        )
                    )
                    try:
                        res = AhvObj.clusters(
                            account_uuid=account_uuid, filter_query=filter_query
                        )
                    except Exception:
                        LOG.warning(
                            "Unable to fetch clusters for Nutanix_PC Account(uuid={})".format(
                                account_uuid
                            )
                        )
                        continue

                    whitelisted_clusters[account_uuid] = [
                        row["metadata"]["uuid"] for row in res["entities"]
                    ]

                # fetch vpcs
                if project_vpc_uuids:
                    filter_query = "_entity_id_=={}".format("|".join(project_vpc_uuids))
                    LOG.debug(
                        "fetching following vpcs {} for nutanix_pc account_uuid {}".format(
                            project_vpc_uuids, account_uuid
                        )
                    )
                    try:
                        res = AhvObj.vpcs(
                            account_uuid=account_uuid, filter_query=filter_query
                        )
                    except Exception:
                        LOG.warning(
                            "Unable to fetch vpcs for Nutanix_PC Account(uuid={})".format(
                                account_uuid
                            )
                        )
                        continue

                    whitelisted_vpcs[account_uuid] = [
                        row["metadata"]["uuid"] for row in res["entities"]
                    ]

        accounts_data = json.dumps(account_map)
        whitelisted_subnets = json.dumps(whitelisted_subnets)
        whitelisted_clusters = json.dumps(whitelisted_clusters)
        whitelisted_vpcs = json.dumps(whitelisted_vpcs)
        return {
            "name": project_name,
            "uuid": uuid,
            "accounts_data": accounts_data,
            "whitelisted_subnets": whitelisted_subnets,
            "whitelisted_clusters": whitelisted_clusters,
            "whitelisted_vpcs": whitelisted_vpcs,
        }

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to project table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from project"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to project table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        q = cls.update(
            {
                cls.accounts_data: db_data["accounts_data"],
                cls.whitelisted_subnets: db_data["whitelisted_subnets"],
                cls.whitelisted_vpcs: db_data["whitelisted_vpcs"],
                cls.whitelisted_clusters: db_data["whitelisted_clusters"],
            }
        ).where(cls.uuid == uuid)
        q.execute()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class EnvironmentCache(CacheTableBase):
    __cache_type__ = "environment"
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    project_uuid = CharField()
    accounts_data = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "project_uuid": self.project_uuid,
            "accounts_data": json.loads(self.accounts_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""
        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "PROJECT_UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data.get("project_uuid", "")),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()

        env_list = client.environment.list_all()
        for entity in env_list:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            project_uuid = (
                entity["metadata"].get("project_reference", {}).get("uuid", "")
            )

            # ignore environments that are not associated to a project
            if not project_uuid:
                continue

            infra_inclusion_list = entity["status"]["resources"].get(
                "infra_inclusion_list", []
            )
            account_map = {}
            for infra in infra_inclusion_list:
                account_type = infra["type"]
                account_uuid = infra["account_reference"]["uuid"]
                account_data = dict(
                    uuid=account_uuid,
                    name=infra["account_reference"]["name"],
                )

                if account_type == "nutanix_pc":
                    AhvVmProvider = cls.get_provider_plugin("AHV_VM")
                    AhvObj = AhvVmProvider.get_api_obj()
                    subnet_refs = infra.get("subnet_references", [])
                    account_data["subnet_uuids"] = [row["uuid"] for row in subnet_refs]
                    cluster_refs = infra.get("cluster_references", [])
                    account_data["cluster_uuids"] = [
                        row["uuid"] for row in cluster_refs
                    ]
                    vpc_refs = infra.get("vpc_references", [])
                    account_data["vpc_uuids"] = [row["uuid"] for row in vpc_refs]

                    # It may happen, that cluster reference is not present in migrated environment
                    res = {}
                    filter_query = "_entity_id_=={}".format(
                        "|".join(account_data["subnet_uuids"])
                    )
                    try:
                        res = AhvObj.subnets(
                            account_uuid=account_uuid, filter_query=filter_query
                        )
                    except Exception as exp:
                        LOG.exception(exp)
                        LOG.warning(
                            "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                                account_uuid
                            )
                        )
                        continue
                    for row in res.get("entities", []):
                        _subnet_type = row["status"]["resources"]["subnet_type"]
                        if (
                            _subnet_type == "VLAN"
                            and row["status"]["cluster_reference"]["uuid"]
                            not in account_data["cluster_uuids"]
                        ):
                            account_data["cluster_uuids"].append(
                                row["status"]["cluster_reference"]["uuid"]
                            )
                        elif (
                            _subnet_type == "OVERLAY"
                            and row["status"]["resources"]["vpc_reference"]["uuid"]
                            not in account_data["vpc_uuids"]
                        ):
                            account_data["vpc_uuids"].append(
                                row["status"]["resources"]["vpc_reference"]["uuid"]
                            )

                if not account_map.get(account_type):
                    account_map[account_type] = []

                account_map[account_type].append(account_data)

            accounts_data = json.dumps(account_map)
            cls.create_entry(
                name=name,
                uuid=uuid,
                accounts_data=accounts_data,
                project_uuid=project_uuid,
            )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        super().create(
            name=name,
            uuid=uuid,
            accounts_data=kwargs.get("accounts_data", "{}"),
            project_uuid=kwargs.get("project_uuid", ""),
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}
        project_uuid = kwargs.get("project_uuid", "")
        if project_uuid:
            query_obj["project_uuid"] = project_uuid

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """fetches one entity data"""

        client = get_api_client()
        res, err = client.environment.read(uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            return {}

        entity = res.json()
        env_name = entity["status"]["name"]
        project_uuid = entity["metadata"].get("project_reference", {}).get("uuid", "")
        infra_inclusion_list = entity["status"]["resources"].get(
            "infra_inclusion_list", []
        )
        account_map = {}
        for infra in infra_inclusion_list:
            _account_type = infra["type"]
            _account_uuid = infra["account_reference"]["uuid"]
            _account_data = dict(
                uuid=infra["account_reference"]["uuid"],
                name=infra["account_reference"].get("name", ""),
            )

            if _account_type == "nutanix_pc":
                AhvVmProvider = cls.get_provider_plugin("AHV_VM")
                AhvObj = AhvVmProvider.get_api_obj()
                subnet_refs = infra.get("subnet_references", [])
                _account_data["subnet_uuids"] = [row["uuid"] for row in subnet_refs]
                cluster_refs = infra.get("cluster_references", [])
                _account_data["cluster_uuids"] = [row["uuid"] for row in cluster_refs]
                vpc_refs = infra.get("vpc_references", [])
                _account_data["vpc_uuids"] = [row["uuid"] for row in vpc_refs]

                # It may happen, that cluster reference is not present in migrated environment
                res = {}
                filter_query = "_entity_id_=={}".format(
                    "|".join(_account_data["subnet_uuids"])
                )
                try:
                    res = AhvObj.subnets(
                        account_uuid=_account_uuid, filter_query=filter_query
                    )
                except Exception as exp:
                    LOG.exception(exp)
                    LOG.warning(
                        "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                            _account_uuid
                        )
                    )
                    continue
                for row in res.get("entities", []):
                    _subnet_type = row["status"]["resources"]["subnet_type"]
                    if (
                        _subnet_type == "VLAN"
                        and row["status"]["cluster_reference"]["uuid"]
                        not in _account_data["cluster_uuids"]
                    ):
                        _account_data["cluster_uuids"].append(
                            row["status"]["cluster_reference"]["uuid"]
                        )
                    elif (
                        _subnet_type == "OVERLAY"
                        and row["status"]["resources"]["vpc_reference"]["uuid"]
                        not in _account_data["vpc_uuids"]
                    ):
                        _account_data["vpc_uuids"].append(
                            row["status"]["resources"]["vpc_reference"]["uuid"]
                        )

            if not account_map.get(_account_type):
                account_map[_account_type] = []

            account_map[_account_type].append(_account_data)

        accounts_data = json.dumps(account_map)
        return {
            "name": env_name,
            "uuid": uuid,
            "accounts_data": accounts_data,
            "project_uuid": project_uuid,
        }

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from env table"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        q = cls.update(
            {
                cls.accounts_data: db_data["accounts_data"],
                cls.project_uuid: db_data["project_uuid"],
            }
        ).where(cls.uuid == uuid)
        q.execute()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class UsersCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.USER
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    display_name = CharField()
    directory = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "display_name": self.display_name,
            "directory": self.directory,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "DISPLAY_NAME",
            "UUID",
            "DIRECTORY",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["display_name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["directory"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        directory = kwargs.get("directory", "")
        if not directory:
            LOG.error(
                "Directory_service not supplied for creating user {}".format(name)
            )
            sys.exit(-1)

        display_name = kwargs.get("display_name") or ""
        super().create(
            name=name, uuid=uuid, directory=directory, display_name=display_name
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        entities = client.user.list_all(api_limit=500)

        for entity in entities:

            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            display_name = entity["status"]["resources"].get("display_name") or ""
            directory_service_user = (
                entity["status"]["resources"].get("directory_service_user") or dict()
            )
            directory_service_ref = (
                directory_service_user.get("directory_service_reference") or dict()
            )
            directory_service_name = directory_service_ref.get("name", "LOCAL")

            if directory_service_name:
                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    display_name=display_name,
                    directory=directory_service_name,
                )

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}

        display_name = kwargs.get("display_name", "")
        if display_name:
            query_obj["display_name"] = display_name

        directory = kwargs.get("directory", "")
        if directory:
            query_obj["directory"] = directory

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """fetches one entity data"""

        client = get_api_client()
        res, err = client.user.read(uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            return {}

        entity = res.json()
        name = entity["status"]["name"]
        display_name = entity["status"]["resources"].get("display_name") or ""
        directory_service_user = (
            entity["status"]["resources"].get("directory_service_user") or dict()
        )
        directory_service_ref = (
            directory_service_user.get("directory_service_reference") or dict()
        )
        directory_service_name = directory_service_ref.get("name", "LOCAL")

        return {
            "name": name,
            "uuid": uuid,
            "display_name": display_name,
            "directory": directory_service_name,
        }

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from env table"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        q = cls.update(
            {
                cls.name: db_data["name"],
                cls.display_name: db_data["display_name"],
                cls.directory: db_data["directory"],
            }
        ).where(cls.uuid == uuid)
        q.execute()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class RolesCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.ROLE
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        super().create(name=name, uuid=uuid)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        Obj = get_resource_api("roles", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create_entry(name=name, uuid=uuid)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """fetches one entity data"""

        client = get_api_client()
        res, err = client.role.read(uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            return {}

        entity = res.json()
        name = entity["status"]["name"]

        return {"name": name, "uuid": uuid}

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from env table"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class DirectoryServiceCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.DIRECTORY_SERVICE
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        super().create(name=name, uuid=uuid)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        Obj = get_resource_api("directory_services", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create_entry(name=name, uuid=uuid)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class UserGroupCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.USER_GROUP
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    display_name = CharField()
    directory = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "display_name": self.display_name,
            "directory": self.directory,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "DISPLAY_NAME",
            "UUID",
            "DIRECTORY",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["display_name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["directory"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        directory = kwargs.get("directory", "")
        if not directory:
            LOG.error(
                "Directory_service not supplied for creating user {}".format(name)
            )
            sys.exit(-1)

        display_name = kwargs.get("display_name") or ""
        super().create(
            name=name, uuid=uuid, directory=directory, display_name=display_name
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        Obj = get_resource_api("user_groups", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            state = entity["status"]["state"]
            if state != "COMPLETE":
                continue

            e_resources = entity["status"]["resources"]

            directory_service_user_group = (
                e_resources.get("directory_service_user_group") or dict()
            )
            distinguished_name = directory_service_user_group.get("distinguished_name")

            directory_service_ref = (
                directory_service_user_group.get("directory_service_reference")
                or dict()
            )
            directory_service_name = directory_service_ref.get("name", "")

            display_name = e_resources.get("display_name", "")
            uuid = entity["metadata"]["uuid"]

            if directory_service_name and distinguished_name:
                cls.create_entry(
                    name=distinguished_name,
                    uuid=uuid,
                    display_name=display_name,
                    directory=directory_service_name,
                )

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}

        display_name = kwargs.get("display_name", "")
        if display_name:
            query_obj["display_name"] = display_name

        directory = kwargs.get("directory", "")
        if directory:
            query_obj["directory"] = directory

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """fetches one entity data"""

        client = get_api_client()
        res, err = client.group.read(uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            return {}

        entity = res.json()
        e_resources = entity["status"]["resources"]

        directory_service_user_group = (
            e_resources.get("directory_service_user_group") or dict()
        )
        distinguished_name = directory_service_user_group.get("distinguished_name")

        directory_service_ref = (
            directory_service_user_group.get("directory_service_reference") or dict()
        )
        directory_service_name = directory_service_ref.get("name", "")

        display_name = e_resources.get("display_name", "")
        uuid = entity["metadata"]["uuid"]

        return {
            "name": distinguished_name,
            "uuid": uuid,
            "display_name": display_name,
            "directory": directory_service_name,
        }

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from env table"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to env table"""

        db_data = cls.fetch_one(uuid, **kwargs)
        q = cls.update(
            {
                cls.name: db_data["name"],
                cls.display_name: db_data["display_name"],
                cls.directory: db_data["directory"],
            }
        ).where(cls.uuid == uuid)
        q.execute()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AhvNetworkFunctionChain(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN
    feature_min_version = "2.7.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()
        Obj = get_resource_api("network_function_chains", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create_entry(name=name, uuid=uuid)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        super().create(name=name, uuid=uuid)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        try:
            entity = super().get(cls.name == name)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AppProtectionPolicyCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.PROTECTION_POLICY
    feature_min_version = "3.3.0"
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    rule_name = CharField()
    rule_uuid = CharField()
    rule_expiry = IntegerField()
    rule_type = CharField()
    project_name = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "rule_name": self.rule_name,
            "rule_uuid": self.rule_uuid,
            "rule_expiry": self.rule_expiry,
            "rule_type": self.rule_type,
            "project_name": self.project_name,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def get_detail_dict_list(cls, query_obj, *args, **kwargs):
        entity_details = []
        for entity in query_obj:
            entity_details.append(entity.get_detail_dict())
        return entity_details

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "RULE NAME",
            "RULE TYPE",
            "EXPIRY (DAYS)",
            "PROJECT",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            if not entity_data["rule_expiry"]:
                entity_data["rule_expiry"] = "-"
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["rule_name"]),
                    highlight_text(entity_data["rule_type"]),
                    highlight_text(entity_data["rule_expiry"]),
                    highlight_text(entity_data["project_name"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()
        Obj = get_resource_api(
            "app_protection_policies", client.connection, calm_api=True
        )
        entities = Obj.list_all()

        for entity in entities:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            project_reference = entity["metadata"].get("project_reference", {})
            for rule in entity["status"]["resources"]["app_protection_rule_list"]:
                expiry = 0
                rule_type = ""
                if rule.get("remote_snapshot_retention_policy", {}):
                    rule_type = "Remote"
                    expiry = (
                        rule["remote_snapshot_retention_policy"]
                        .get("snapshot_expiry_policy", {})
                        .get("multiple", 0)
                    )
                elif rule.get("local_snapshot_retention_policy", {}):
                    rule_type = "Local"
                    expiry = (
                        rule["local_snapshot_retention_policy"]
                        .get("snapshot_expiry_policy", {})
                        .get("multiple", 0)
                    )
                rule_name = rule["name"]
                rule_uuid = rule["uuid"]
                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    rule_name=rule_name,
                    rule_uuid=rule_uuid,
                    project_name=project_reference.get("name", ""),
                    rule_expiry=expiry,
                    rule_type=rule_type,
                )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        rule_name = kwargs.get("rule_name", "")
        rule_uuid = kwargs.get("rule_uuid", "")
        rule_expiry = kwargs.get("rule_expiry", 0)
        rule_type = kwargs.get("rule_type", "")
        project_name = kwargs.get("project_name", "")
        if not rule_uuid:
            LOG.error(
                "Protection Rule UUID not supplied for Protection Policy {}".format(
                    name
                )
            )
            sys.exit("Missing rule_uuid for protection policy")
        super().create(
            name=name,
            uuid=uuid,
            rule_name=rule_name,
            rule_uuid=rule_uuid,
            rule_expiry=rule_expiry,
            rule_type=rule_type,
            project_name=project_name,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        rule_uuid = kwargs.get("rule_uuid", "")
        rule_name = kwargs.get("rule_name", "")
        query_obj = {"name": name, "project_name": kwargs.get("project_name", "")}
        if rule_name:
            query_obj["rule_name"] = rule_name
        elif rule_uuid:
            query_obj["rule_uuid"] = rule_uuid

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            query_obj = super().select().where(cls.uuid == uuid)
            return cls.get_detail_dict_list(query_obj)

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "rule_uuid")


class PolicyEventCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.POLICY_EVENT
    feature_min_version = "3.5.0"
    is_policy_required = is_policy_check_required()
    is_approval_policy_required = True
    entity_type = CharField()
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "entity_type": self.entity_type,
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["ENTITY_TYPE", "NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["entity_type"]),
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        entity_type = kwargs.get("entity_type", "")
        if not entity_type:
            LOG.error(
                "Entity type not supplied for fetching policy_event {}".format(name)
            )
            sys.exit(
                "Entity type not supplied for fetching policy_event={}".format(name)
            )

        super().create(name=name, uuid=uuid, entity_type=entity_type)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        res, err = client.policy_event.list()
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            LOG.error("Failed to list policy attributes")
            sys.exit("Failed to list policy attributes")

        res = res.json()
        for entity in res.get("entities", []):
            query_obj = {
                "entity_type": entity["status"]["resources"]["entity_type"],
                "name": entity["status"]["name"],
                "uuid": entity["metadata"]["uuid"],
            }
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class PolicyAttributesCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.POLICY_ATTRIBUTES
    feature_min_version = "3.5.0"
    is_policy_required = is_policy_check_required()
    is_approval_policy_required = True
    event_name = CharField()
    name = CharField()
    type = CharField()
    operators = CharField()
    jsonpath = CharField()

    def get_detail_dict(self, *args, **kwargs):
        return {
            "event_name": self.event_name,
            "name": self.name,
            "type": self.type,
            "operators": self.operators,
            "jsonpath": self.jsonpath,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["EVENT_NAME", "Name", "TYPE", "OPERATOR_LIST"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            table.add_row(
                [
                    highlight_text(entity_data["event_name"]),
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["type"]),
                    highlight_text(entity_data["operators"]),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, **kwargs):
        event_name = kwargs.get("event_name", "")
        if not event_name:
            LOG.error(
                "Event name not supplied for fetching policy_attribute {}".format(
                    event_name
                )
            )
            sys.exit(
                "Event name not supplied for fetching policy_attribute {}".format(
                    event_name
                )
            )

        super().create(
            event_name=event_name,
            name=name,
            type=kwargs.get("type", ""),
            operators=kwargs.get("operators", ""),
            jsonpath=kwargs.get("jsonpath", ""),
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        res, err = client.policy_attributes.list()
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            LOG.error("Failed to list policy attributes")
            sys.exit("Failed to list policy attributes")

        res = res.json()
        for entity in res.get("events", []):
            event_name = entity["name"]
            for attribute in entity["attributes"]:
                query_obj = {
                    "event_name": event_name,
                    "name": attribute["name"],
                    "type": attribute["type"],
                    "operators": attribute["operators"],
                    "jsonpath": attribute["jsonpath"],
                }
                cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"event_name": kwargs.get("event_name"), "name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("event_name", "name")


class PolicyActionTypeCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.POLICY_ACTION_TYPE
    feature_min_version = "3.5.0"
    is_policy_required = is_policy_check_required()
    is_approval_policy_required = True
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        super().create(name=name, uuid=uuid)

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        res, err = client.policy_action_types.list()
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            LOG.error("Failed to list policy attributes")
            sys.exit("Failed to list policy attributes")

        res = res.json()
        for entity in res.get("entities", []):
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create_entry(name=name, uuid=uuid)

    @classmethod
    def get_entity_data(cls, name, **kwargs):

        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class TunnelCache(CacheTableBase):
    """This class is used to manage the cache for account tunnels."""

    __cache_type__ = CACHE.ENTITY.TUNNEL
    feature_min_version = TUNNEL.FEATURE_MIN_VERSION
    is_policy_required = is_policy_check_required()
    name = CharField()
    description = CharField()
    uuid = CharField()
    state = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "description": self.description,
            "uuid": self.uuid,
            "state": self.state,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes all entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        """creates a new entry in the tunnel cache table"""
        state = kwargs.get("state", "")
        description = kwargs.get("description", "")

        super().create(
            name=name,
            description=description,
            uuid=uuid,
            state=state,
        )

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if len(cls.select()) == 0:
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "DESCRIPTION",
            "UUID",
            "STATE",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["description"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["state"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls):
        """Sync the table from server"""

        # Clear old data
        cls.clear()

        client = get_api_client()
        length = 250
        offset = 0
        total_matches = None
        all_entities = []

        while total_matches is None or offset < total_matches:
            payload = {
                "length": length,
                "offset": offset,
                "filter": "(state!=DELETED);type!=network_group",
            }

            res, err = client.tunnel.list(payload)
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            res = res.json()
            if total_matches is None:
                total_matches = res.get("metadata", {}).get("total_matches", 0)

            all_entities.extend(res.get("entities", []))
            offset += length

        for entity in all_entities:
            name = entity["status"]["name"]
            backend_state = entity["status"].get("state", "")
            state = TUNNEL.BACKEND_TO_UI_STATE_MAPPING.get(backend_state, "")
            if not state:
                LOG.warning(
                    "Tunnel with name {} found with invalid state: {}".format(
                        name, backend_state
                    )
                )

            query_obj = {
                "name": name,
                "description": entity["status"].get("description", "-"),
                "uuid": entity["metadata"]["uuid"],
                "state": state,
            }
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def fetch_one(cls, uuid):
        """returns tunnel data for tunnel uuid"""
        # update by latest data
        client = get_api_client()

        res, err = client.tunnel.read(uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity = res.json()
        backend_state = entity["status"].get("state", "")
        state = TUNNEL.BACKEND_TO_UI_STATE_MAPPING.get(backend_state, "")
        query_obj = {
            "name": entity["status"]["name"],
            "description": entity["status"].get("description", "-"),
            "uuid": entity["metadata"]["uuid"],
            "state": state,
        }
        return query_obj

    @classmethod
    def add_one(cls, uuid, **kwargs):
        """adds one entry to tunnel table"""

        query_obj = cls.fetch_one(uuid)
        cls.create_entry(**query_obj)

    @classmethod
    def update_one(cls, uuid, **kwargs):
        """updates single entry to tunnel table"""

        query_obj = cls.fetch_one(uuid)
        cls.update(
            {
                cls.name: query_obj["name"],
                cls.description: query_obj["description"],
                cls.state: query_obj["state"],
                cls.last_update_time: datetime.datetime.now(),
            }
        ).where(cls.uuid == uuid).execute()

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one entity from project"""

        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


"""
NDB Entities Cache
"""


class NDB_DatabaseCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.DATABASE
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    _type = CharField()
    status = CharField()
    clone = BooleanField()
    clustered = BooleanField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "type": self._type,
            "status": self.status,
            "clone": self.clone,
            "clustered": self.clustered,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "TYPE",
            "STATUS",
            "UUID",
            "ACCOUNT NAME",
            "CLONE",
            "CLUSTERED",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["type"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["clone"]),
                    highlight_text(entity_data["clustered"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB Database {} entry".format(
                    name
                )
            )
            sys.exit(-1)

        _type = kwargs.get("_type", "")
        status = kwargs.get("status", "")
        clone = kwargs.get("clone", False)
        clustered = kwargs.get("clustered", False)
        platform_data = kwargs.get("platform_data", "{}")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            _type=_type,
            status=status,
            clone=clone,
            clustered=clustered,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for databases, this should be fixed when other databases type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "Postgres Database Instance",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["database_instances"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for database in platform_res["database_instances"]:
                query_obj = {
                    "name": database["name"],
                    "uuid": database["id"],
                    "account_name": entity["metadata"]["name"],
                    "status": database.get("status", ""),
                    "_type": database.get("type", ""),
                    "clone": database.get("clone", False),
                    "clustered": database.get("clustered", False),
                    "platform_data": json.dumps(database),
                }
                cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        _type = kwargs.get("type", "")
        if _type:
            query_obj["_type"] = _type

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_name", "_type")


class NDB_ProfileCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    _type = CharField()
    status = CharField()
    engine_type = CharField()
    system_profile = BooleanField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "type": self._type,
            "status": self.status,
            "engine_type": self.engine_type,
            "system_profile": self.system_profile,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "TYPE",
            "STATUS",
            "UUID",
            "ACCOUNT NAME",
            "ENGINE",
            "SYSTEM PROFILE",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["type"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["engine_type"]),
                    highlight_text(entity_data["system_profile"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB Profile {} entry".format(
                    name
                )
            )
            sys.exit(-1)

        _type = kwargs.get("_type", "")
        status = kwargs.get("status", "")
        engine_type = kwargs.get("engine_type", "")
        system_profile = kwargs.get("system_profile", False)
        platform_data = kwargs.get("platform_data", "{}")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            _type=_type,
            status=status,
            engine_type=engine_type,
            system_profile=system_profile,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        from calm.dsl.builtins.models.constants import NutanixDB as NutanixDBConst

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for profiles, this should be fixed when other profiles type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "Profile",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["profiles"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for profile in platform_res["profiles"]:
                if profile.get("engine_type", "") in ["postgres_database", "Generic"]:
                    query_obj = {
                        "name": profile["name"],
                        "uuid": profile["id"],
                        "account_name": entity["metadata"]["name"],
                        "status": profile.get("status", ""),
                        "_type": profile.get("type", ""),
                        "engine_type": profile.get("engine_type", ""),
                        "system_profile": profile.get("system_profile", False),
                        "platform_data": json.dumps(profile),
                    }
                    cls.create_entry(**query_obj)

                    if profile.get("type", "") == NutanixDBConst.PROFILE.SOFTWARE:
                        for version in profile.get("versions", []):
                            query_obj = {
                                "name": version["name"],
                                "uuid": version["id"],
                                "account_name": entity["metadata"]["name"],
                                "status": version.get("status", ""),
                                "_type": NutanixDBConst.PROFILE.SOFTWARE_PROFILE_VERSION,
                                "engine_type": version.get("engine_type", ""),
                                "system_profile": version.get("system_profile", False),
                                "platform_data": json.dumps(version),
                            }
                            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        _type = kwargs.get("type", "")
        if _type:
            query_obj["_type"] = _type

        engine_type = kwargs.get("engine_type", "")
        if engine_type:
            query_obj["engine_type"] = engine_type

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey(
            "name", "uuid", "account_name", "_type", "engine_type"
        )


class NDB_SLACache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    continuous_retention = IntegerField()
    daily_retention = IntegerField()
    weekly_retention = IntegerField()
    monthly_retention = IntegerField()
    quartely_retention = IntegerField()
    yearly_retention = IntegerField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "continuous_retention": self.continuous_retention,
            "daily_retention": self.daily_retention,
            "weekly_retention": self.weekly_retention,
            "monthly_retention": self.monthly_retention,
            "quartely_retention": self.quartely_retention,
            "yearly_retention": self.yearly_retention,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "ACCOUNT NAME",
            "CONTINOUS",
            "DAILY",
            "WEEKLY",
            "MONTHLY",
            "QUATERLY",
            "YEARLY",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["continuous_retention"]),
                    highlight_text(entity_data["daily_retention"]),
                    highlight_text(entity_data["weekly_retention"]),
                    highlight_text(entity_data["monthly_retention"]),
                    highlight_text(entity_data["quartely_retention"]),
                    highlight_text(entity_data["yearly_retention"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB SLA {} entry".format(name)
            )
            sys.exit(-1)

        platform_data = kwargs.get("platform_data", "{}")
        continuous_retention = kwargs.get("continuous_retention", 0)
        daily_retention = kwargs.get("daily_retention", 0)
        weekly_retention = kwargs.get("weekly_retention", 0)
        monthly_retention = kwargs.get("monthly_retention", 0)
        quartely_retention = kwargs.get("quartely_retention", 0)
        yearly_retention = kwargs.get("yearly_retention", 0)

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            continuous_retention=continuous_retention,
            daily_retention=daily_retention,
            weekly_retention=weekly_retention,
            monthly_retention=monthly_retention,
            quartely_retention=quartely_retention,
            yearly_retention=yearly_retention,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for slas, this should be fixed when other slas type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "SLA",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["slas"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for sla in platform_res["slas"]:
                query_obj = {
                    "name": sla["name"],
                    "uuid": sla["id"],
                    "account_name": entity["metadata"]["name"],
                    "continuous_retention": sla.get("continuous_retention", 0),
                    "daily_retention": sla.get("daily_retention", 0),
                    "weekly_retention": sla.get("weekly_retention", 0),
                    "monthly_retention": sla.get("monthly_retention", 0),
                    "quartely_retention": sla.get("quartely_retention", 0),
                    "yearly_retention": sla.get("yearly_retention", 0),
                    "platform_data": json.dumps(sla),
                }
                cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_name")


class NDB_ClusterCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.CLUSTER
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    status = CharField()
    healthy = BooleanField()
    hypervisor_type = CharField()
    nx_cluster_uuid = CharField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "status": self.status,
            "healthy": self.healthy,
            "hypervisor_type": self.hypervisor_type,
            "nx_cluster_uuid": self.nx_cluster_uuid,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "ACCOUNT NAME",
            "STATUS",
            "HEALTHY",
            "HYPERVISOR TYPE",
            "NX CLUSTER UUID",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["healthy"]),
                    highlight_text(entity_data["hypervisor_type"]),
                    highlight_text(entity_data["nx_cluster_uuid"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB SLA {} entry".format(name)
            )
            sys.exit(-1)

        platform_data = kwargs.get("platform_data", "{}")
        status = kwargs.get("status", "")
        healthy = kwargs.get("healthy", False)
        hypervisor_type = kwargs.get("hypervisor_type", "")
        nx_cluster_uuid = kwargs.get("nx_cluster_uuid", "")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            status=status,
            healthy=healthy,
            hypervisor_type=hypervisor_type,
            nx_cluster_uuid=nx_cluster_uuid,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for clusters, this should be fixed when other clusters type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "Cluster",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["clusters"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for cluster in platform_res["clusters"]:
                query_obj = {
                    "name": cluster["name"],
                    "uuid": cluster["id"],
                    "account_name": entity["metadata"]["name"],
                    "status": cluster.get("status", ""),
                    "healthy": cluster.get("healthy", False),
                    "hypervisor_type": cluster.get("hypervisor_type", ""),
                    "nx_cluster_uuid": cluster.get("nx_cluster_uuid", ""),
                    "platform_data": json.dumps(cluster),
                }
                cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_name")


class NDB_TimeMachineCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TIME_MACHINE
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    status = CharField()
    _type = CharField()
    clustered = BooleanField()
    slas = CharField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "status": self.status,
            "_type": self._type,
            "clustered": self.clustered,
            "slas": json.loads(self.slas),
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "ACCOUNT NAME",
            "STATUS",
            "TYPE",
            "CLUSTERED",
            "SLAs",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["_type"]),
                    highlight_text(entity_data["clustered"]),
                    highlight_text(entity_data["slas"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB SLA {} entry".format(name)
            )
            sys.exit(-1)

        platform_data = kwargs.get("platform_data", "{}")
        status = kwargs.get("status", "")
        _type = kwargs.get("_type", "")
        clustered = kwargs.get("clustered", False)
        slas = kwargs.get("slas", "[]")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            status=status,
            _type=_type,
            clustered=clustered,
            slas=slas,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):
            platform_res, err = client.resource_types.get_platform_list(
                "Time Machine",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["time_machines"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for time_machine in platform_res["time_machines"]:

                # for now we filter postgres_database for time_machines, this should be fixed when other time_machines type are introduced
                if time_machine.get("type", "") in ["postgres_database"]:
                    query_obj = {
                        "name": time_machine["name"],
                        "uuid": time_machine["id"],
                        "account_name": entity["metadata"]["name"],
                        "status": time_machine.get("status", ""),
                        "_type": time_machine.get("type", ""),
                        "clustered": time_machine.get("clustered", False),
                        "slas": json.dumps(
                            [sla.get("name", "") for sla in time_machine.get("sla", [])]
                        ),
                        "platform_data": json.dumps(time_machine),
                    }
                    cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        _type = kwargs.get("type", "")
        if _type:
            query_obj["_type"] = _type

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_name", "_type")


class NDB_SnapshotCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SNAPSHOT
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    status = CharField()
    _type = CharField()
    time_machine_id = CharField()
    snapshot_timestamp = CharField()
    timezone = CharField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "status": self.status,
            "_type": self._type,
            "time_machine_id": self.time_machine_id,
            "snapshot_timestamp": self.snapshot_timestamp,
            "timezone": self.timezone,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "TIME STAMP",
            "TIME ZONE",
            "UUID",
            "ACCOUNT NAME",
            "STATUS",
            "TYPE",
            "TIME MACHINE ID",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["snapshot_timestamp"]),
                    highlight_text(entity_data["timezone"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["_type"]),
                    highlight_text(entity_data["time_machine_id"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB SLA {} entry".format(name)
            )
            sys.exit(-1)

        platform_data = kwargs.get("platform_data", "{}")
        status = kwargs.get("status", "")
        _type = kwargs.get("_type", "")
        time_machine_id = kwargs.get("time_machine_id", "")
        timezone = kwargs.get("timezone", "")
        snapshot_timestamp = kwargs.get("snapshot_timestamp", "")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            status=status,
            _type=_type,
            time_machine_id=time_machine_id,
            timezone=timezone,
            snapshot_timestamp=snapshot_timestamp,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for snapshots, this should be fixed when other snapshots type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "Snapshot",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["snapshots"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for snapshot in platform_res["snapshots"]:
                if NDB_TimeMachineCache.get_entity_data_using_uuid(
                    snapshot.get("time_machine_id", "")
                ):
                    query_obj = {
                        "name": snapshot["name"],
                        "uuid": snapshot["id"],
                        "account_name": entity["metadata"]["name"],
                        "status": snapshot.get("status", ""),
                        "_type": snapshot.get("type", ""),
                        "time_machine_id": snapshot.get("time_machine_id", ""),
                        "snapshot_timestamp": snapshot.get("snapshot_timestamp", ""),
                        "timezone": snapshot.get("timezone", ""),
                        "platform_data": json.dumps(snapshot),
                    }
                    cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        time_machine_id = kwargs.get("time_machine_id", "")
        if account_name:
            query_obj["time_machine_id"] = time_machine_id

        snapshot_timestamp = kwargs.get("snapshot_timestamp", "")
        if account_name:
            query_obj["snapshot_timestamp"] = snapshot_timestamp

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey(
            "name", "uuid", "account_name", "snapshot_timestamp", "time_machine_id"
        )


class NDB_TagCache(CacheTableBase):
    __cache_type__ = CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG
    feature_min_version = "3.7.0"
    is_policy_required = True if not NCM_ENABLED else False
    name = CharField()
    uuid = CharField()
    account_name = CharField()
    status = CharField()
    entity_type = CharField()
    values = IntegerField()
    platform_data = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "account_name": self.account_name,
            "status": self.status,
            "entity_type": self.entity_type,
            "values": self.values,
            "platform_data": json.loads(self.platform_data),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = [
            "NAME",
            "UUID",
            "ACCOUNT NAME",
            "STATUS",
            "ENTITY TYPE",
            "VALUES",
            "LAST UPDATED",
        ]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["account_name"]),
                    highlight_text(entity_data["status"]),
                    highlight_text(entity_data["entity_type"]),
                    highlight_text(entity_data["values"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_name = kwargs.get("account_name", "")
        if not account_name:
            LOG.error(
                "account_name not supplied for creating NDB SLA {} entry".format(name)
            )
            sys.exit(-1)

        platform_data = kwargs.get("platform_data", "{}")
        status = kwargs.get("status", "")
        entity_type = kwargs.get("entity_type", "")
        values = kwargs.get("values", "")

        super().create(
            name=name,
            uuid=uuid,
            account_name=account_name,
            status=status,
            entity_type=entity_type,
            values=values,
            platform_data=platform_data,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        ContextObj = get_context()
        stratos_config = ContextObj.get_stratos_config()
        if not stratos_config.get("stratos_status", False):
            LOG.info("Stratos not enabled, skipping NDB Database synchronization")
            return

        client = get_api_client()
        account_payload = {
            "length": 250,
            "filter": "state==VERIFIED;type==NDB;child_account==true",
        }

        res, err = client.account.list(account_payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):

            # for now we call "Postgres Database Instance" list for tags, this should be fixed when other tags type are introduced
            platform_res, err = client.resource_types.get_platform_list(
                "Tag",
                entity["metadata"]["uuid"],
                args=None,
                outargs=["tags"],
            )
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            platform_res = platform_res.json()
            for tag in platform_res["tags"]:

                query_obj = {
                    "name": tag["name"],
                    "uuid": tag["id"],
                    "account_name": entity["metadata"]["name"],
                    "status": tag.get("status", ""),
                    "entity_type": tag.get("entity_type", ""),
                    "values": tag.get("values", 0),
                    "platform_data": json.dumps(tag),
                }
                cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        account_name = kwargs.get("account_name", "")
        if account_name:
            query_obj["account_name"] = account_name

        _type = kwargs.get("type", "")
        if _type:
            query_obj["entity_type"] = _type

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_name", "entity_type")


class GlobalVariableCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.GLOBAL_VARIABLE
    feature_min_version = GLOBAL_VARIABLE.MIN_SUPPORTED_VERSION
    is_policy_required = False
    name = CharField()
    uuid = CharField()
    val_type = CharField()
    var_type = CharField()
    state = CharField()
    value = CharField()
    project_reference_list = BlobField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "val_type": self.val_type,
            "state": self.state,
            "value": self.value,
            "project_reference_list": json.loads(self.project_reference_list),
            "last_update_time": self.last_update_time,
            "var_type": self.var_type,
        }

    @classmethod
    def _get_dict_for_db_upsert(cls, entity):
        return {
            "name": entity["status"]["name"],
            "uuid": entity["metadata"]["uuid"],
            "val_type": entity["status"]["resources"].get("val_type", ""),
            "value": entity["status"]["resources"].get("value", ""),
            "project_reference_list": json.dumps(
                entity["status"]["resources"].get("project_reference_list", {})
            ),
            "state": entity["status"]["state"],
            "var_type": entity["status"]["resources"].get("type", ""),
        }

    @classmethod
    def add_one_by_entity_dict(cls, entity):
        """adds one entry to global variable table"""
        db_data = cls._get_dict_for_db_upsert(entity)
        cls.create_entry(**db_data)

    @classmethod
    def delete_one(cls, uuid, **kwargs):
        """deletes one global variable entity from cache"""
        obj = cls.get(cls.uuid == uuid)
        obj.delete_instance()

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def show_data(cls):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "TYPE", "VALUE", "STATE", "LAST UPDATED"]
        for entity in cls.select():
            entity_data = entity.get_detail_dict()
            last_update_time = arrow.get(
                entity_data["last_update_time"].astimezone(datetime.timezone.utc)
            ).humanize()
            value = entity_data["value"]
            if entity_data["var_type"] in VARIABLE.DYNAMIC_TYPES:
                value = "DYNAMIC VALUE"
            table.add_row(
                [
                    highlight_text(entity_data["name"]),
                    highlight_text(entity_data["uuid"]),
                    highlight_text(entity_data["val_type"]),
                    highlight_text(value),
                    highlight_text(entity_data["state"]),
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        val_type = kwargs.get("val_type", "")
        state = kwargs.get("state", "")
        value = kwargs.get("value", "")
        project_reference_list = kwargs.get("project_reference_list", "[]")
        var_type = kwargs.get("var_type", "")

        super().create(
            name=name,
            uuid=uuid,
            val_type=val_type,
            state=state,
            value=value,
            project_reference_list=project_reference_list,
            var_type=var_type,
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": ""}

        res, err = client.global_variable.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res.get("entities", []):
            query_obj = cls._get_dict_for_db_upsert(entity)
            cls.create_entry(**query_obj)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class VersionTable(BaseModel):
    name = CharField()
    version = CharField()
    pc_ip = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def get_entity_data(cls, name):
        query_obj = {"name": name}

        try:
            entity = super().get(**query_obj)
            return entity.get_detail_dict()
        except DoesNotExist:
            return dict()

    def get_detail_dict(self):
        return {"name": self.name, "pc_ip": self.pc_ip, "version": self.version}


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
