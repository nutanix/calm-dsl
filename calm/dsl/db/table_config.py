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
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)
# Proxy database
dsl_database = SqliteDatabase(None)


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

                # store cluster accounts for PC account (Note it will store cluster name not account name)
                for pe_acc in (
                    entity["status"]["resources"]
                    .get("data", {})
                    .get("cluster_account_reference_list", [])
                ):
                    group = data.setdefault("clusters", {})
                    group[pe_acc["uuid"]] = (
                        pe_acc.get("resources", {})
                        .get("data", {})
                        .get("cluster_name", "")
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

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


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
            try:
                res = AhvObj.clusters(account_uuid=pc_acc_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch clusters for Nutanix_PC Account(uuid={})".format(
                        pc_acc_name
                    )
                )
                continue

            # TODO the order of cache sync is how their model is defined in table_config.py file
            account = AccountCache.get(uuid=pc_acc_uuid)
            account_clusters_data = json.loads(account.data).get("clusters", {})
            account_clusters_data_rev = {v: k for k, v in account_clusters_data.items()}

            for entity in res.get("entities", []):
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]
                cluster_resources = entity["status"]["resources"]
                service_list = cluster_resources.get("config", {}).get(
                    "service_list", []
                )

                # Here, AHV denotes the 'PE' functionality of a cluster
                if "AOS" not in service_list:
                    LOG.debug(
                        "Cluster '{}' with UUID '{}' having function {} is not an AHV PE cluster".format(
                            name, uuid, service_list
                        )
                    )
                    continue

                # For esxi clusters, there will not be any pe account
                if not account_clusters_data_rev.get(name, ""):
                    LOG.debug(
                        "Ignoring cluster '{}' with uuid '{}', as it doesn't have any pc account".format(
                            name, uuid
                        )
                    )
                    continue

                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    pe_account_uuid=account_clusters_data_rev.get(name, ""),
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

        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return dict()

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "account_uuid")


class AhvSubnetsCache(CacheTableBase):
    __cache_type__ = CACHE.ENTITY.AHV_SUBNET
    feature_min_version = "2.7.0"
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
    __cache_type__ = "app_protection_policy"
    feature_min_version = "3.3.0"
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

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid", "rule_uuid")


class VersionTable(BaseModel):
    name = CharField()
    version = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {"name": self.name, "version": self.version}


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
