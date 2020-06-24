from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    BlobField,
    DateTimeField,
    ForeignKeyField,
    CompositeKey,
    DoesNotExist,
)
import datetime
import click
import arrow
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.tools import get_logging_handle
from calm.dsl.providers import get_provider

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

        if not hasattr(cls, "__cache_type__"):
            raise TypeError("Base table does not have a cache type attribute")

        cache_type = cls.__cache_type__
        cls.tables[cache_type] = cls

    def get_detail_dict(self):
        raise NotImplementedError("get_detail_dict helper not implemented")

    @classmethod
    def get_cache_tables(cls):
        return cls.tables

    @classmethod
    def clear(cls):
        """removes entire data from table"""
        raise NotImplementedError("clear helper not implemented")

    @classmethod
    def show_data(cls):
        raise NotImplementedError("show_data helper not implemented")

    @classmethod
    def sync(cls):
        raise NotImplementedError("sync helper not implemented")

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        raise NotImplementedError("create_entry helper not implemented")

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        raise NotImplementedError("get_entity_data helper not implemented")

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        raise NotImplementedError("get_entity_data_using_uuid helper not implemented")


class AhvSubnetsCache(CacheTableBase):
    __cache_type__ = "ahv_subnet"
    name = CharField()
    uuid = CharField()
    cluster = CharField()
    account_uuid = CharField(default="")
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "cluster": self.cluster,
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
            "CLUSTER_NAME",
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
                    highlight_text(entity_data["cluster"]),
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
        payload = {"length": 250, "filter": "type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for e_name, e_uuid in account_name_uuid_map.items():
            res = AhvObj.subnets(account_uuid=e_uuid)

            for entity in res["entities"]:
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]
                cluster_ref = entity["status"]["cluster_reference"]
                cluster_name = cluster_ref.get("name", "")

                cls.create_entry(
                    name=name, uuid=uuid, cluster=cluster_name, account_uuid=e_uuid
                )

        # For older version < 2.9.0
        # Add working for older versions too

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for subnet {}".format(name))
            sys.exit(-1)

        cluster_name = kwargs.get("cluster", None)
        if not cluster_name:
            LOG.error("cluster not supplied for subnet {}".format(name))
            sys.exit(-1)

        # store data in table
        super().create(
            name=name, uuid=uuid, cluster=cluster_name, account_uuid=account_uuid
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        account_uuid = kwargs.get("account_uuid", "")
        if not account_uuid:
            LOG.error("Account UUID not supplied for fetching subnet {}".format(name))
            sys.exit(-1)

        cluster_name = kwargs.get("cluster", "")
        try:
            if cluster_name:
                entity = super().get(
                    cls.name == name,
                    cls.cluster == cluster_name,
                    cls.account_uuid == account_uuid,
                )
            else:
                # The get() method is shorthand for selecting with a limit of 1
                # If more than one row is found, the first row returned by the database cursor
                entity = super().get(cls.name == name, cls.account_uuid == account_uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

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
            return None

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AhvImagesCache(CacheTableBase):
    __cache_type__ = "ahv_disk_image"
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
        payload = {"length": 250, "filter": "type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for e_name, e_uuid in account_name_uuid_map.items():
            res = AhvObj.images(account_uuid=e_uuid)
            for entity in res["entities"]:
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

        try:
            entity = super().get(
                cls.name == name,
                cls.image_type == image_type,
                cls.account_uuid == account_uuid,
            )
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

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
            return None

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class ProjectCache(CacheTableBase):
    __cache_type__ = "project"
    name = CharField()
    uuid = CharField()
    accounts_data = CharField()
    whitelisted_subnets = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "accounts_data": json.loads(self.accounts_data),
            "whitelisted_subnets": json.loads(self.whitelisted_subnets),
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
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        # Single account per provider_type can be added to project
        account_uuid_type_map = {}
        for entity in res["entities"]:
            a_uuid = entity["metadata"]["uuid"]
            a_type = entity["status"]["resources"]["type"]
            account_uuid_type_map[a_uuid] = a_type

        Obj = get_resource_api("projects", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]

            account_list = entity["status"]["resources"]["account_reference_list"]
            account_map = {}
            for account in account_list:
                account_uuid = account["uuid"]
                account_type = account_uuid_type_map[account_uuid]

                # For now only single provider account per provider is allowed
                account_map[account_type] = account_uuid

            accounts_data = json.dumps(account_map)

            subnets_ref_list = entity["status"]["resources"]["subnet_reference_list"]
            subnets_uuid_list = []
            for subnet in subnets_ref_list:
                subnets_uuid_list.append(subnet["uuid"])

            external_network_ref_list = entity["spec"]["resources"].get(
                "external_network_list", []
            )
            for subnet in external_network_ref_list:
                subnets_uuid_list.append(subnet["uuid"])

            subnets_uuid_list = json.dumps(subnets_uuid_list)
            cls.create_entry(
                name=name,
                uuid=uuid,
                accounts_data=accounts_data,
                whitelisted_subnets=subnets_uuid_list,
            )

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        accounts_data = kwargs.get("accounts_data", "{}")
        whitelisted_subnets = kwargs.get("whitelisted_subnets", "[]")
        super().create(
            name=name,
            uuid=uuid,
            accounts_data=accounts_data,
            whitelisted_subnets=whitelisted_subnets,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        try:
            entity = super().get(cls.name == name)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    @classmethod
    def get_entity_data_using_uuid(cls, uuid, **kwargs):
        try:
            entity = super().get(cls.uuid == uuid)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AhvNetworkFunctionChain(CacheTableBase):
    __cache_type__ = "ahv_network_function_chain"
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
        super().create(
            name=name, uuid=uuid,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        try:
            entity = super().get(cls.name == name)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class VersionTable(BaseModel):
    name = CharField()
    version = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "version": self.version,
        }


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
