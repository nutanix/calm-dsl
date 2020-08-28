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
)
import datetime
import click
import arrow
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.log import get_logging_handle
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
    cluster_uuid = CharField(
        default=""
    )  # TODO separate out uuid and create separate table for it
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "cluster": self.cluster,
            "cluster_uuid": self.cluster_uuid,
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
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for e_name, e_uuid in account_name_uuid_map.items():
            try:
                res = AhvObj.subnets(account_uuid=e_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch subnets for Nutanix_PC Account(uuid={})".format(
                        e_uuid
                    )
                )
                continue

            for entity in res["entities"]:
                name = entity["status"]["name"]
                uuid = entity["metadata"]["uuid"]
                cluster_ref = entity["status"]["cluster_reference"]
                cluster_name = cluster_ref.get("name", "")
                cluster_uuid = cluster_ref.get("uuid", "")

                cls.create_entry(
                    name=name,
                    uuid=uuid,
                    cluster=cluster_name,
                    account_uuid=e_uuid,
                    cluster_uuid=cluster_uuid,
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

        cluster_uuid = kwargs.get("cluster_uuid", "")

        # store data in table
        super().create(
            name=name,
            uuid=uuid,
            cluster=cluster_name,
            account_uuid=account_uuid,
            cluster_uuid=cluster_uuid,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        query_obj = {"name": name}
        account_uuid = kwargs.get("account_uuid", "")
        if account_uuid:
            query_obj["account_uuid"] = account_uuid

        cluster_name = kwargs.get("cluster", "")
        if cluster_name:
            query_obj["cluster"] = cluster_name

        try:
            # The get() method is shorthand for selecting with a limit of 1
            # If more than one row is found, the first row returned by the database cursor
            entity = super().get(**query_obj)
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
        payload = {"length": 250, "filter": "state==VERIFIED;type==nutanix_pc"}
        account_name_uuid_map = client.account.get_name_uuid_map(payload)

        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        for e_name, e_uuid in account_name_uuid_map.items():
            try:
                res = AhvObj.images(account_uuid=e_uuid)
            except Exception:
                LOG.warning(
                    "Unable to fetch images for Nutanix_PC Account(uuid={})".format(
                        e_uuid
                    )
                )
                continue

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

        query_obj = {
            "name": name,
            "image_type": image_type,
            "account_uuid": account_uuid,
        }

        try:
            entity = super().get(**query_obj)
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


class AccountCache(CacheTableBase):
    __cache_type__ = "account"
    name = CharField()
    uuid = CharField()
    provider_type = CharField()
    is_host = BooleanField(default=False)  # Used for Ntnx accounts only
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "provider_type": self.provider_type,
            "is_host": self.is_host,
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
        table.field_names = ["NAME", "provider_type", "UUID", "LAST UPDATED"]
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

        super().create(
            name=name, uuid=uuid, provider_type=provider_type, is_host=is_host
        )

    @classmethod
    def sync(cls):
        """sync the table from server"""

        # clear old data
        cls.clear()

        client = get_api_client()
        payload = {"length": 250, "filter": "state==VERIFIED;type!=nutanix"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            provider_type = entity["status"]["resources"]["type"]
            query_obj = {
                "name": entity["status"]["name"],
                "uuid": entity["metadata"]["uuid"],
                "provider_type": entity["status"]["resources"]["type"],
            }

            if provider_type == "nutanix_pc":
                query_obj["is_host"] = entity["status"]["resources"]["data"]["host_pc"]

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
                # As projects may have deleted accounts registered
                if account_uuid in account_uuid_type_map:
                    account_type = account_uuid_type_map[account_uuid]
                else:
                    continue

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
        query_obj = {"name": name}
        try:
            entity = super().get(**query_obj)
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


class UsersCache(CacheTableBase):
    __cache_type__ = "user"
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
        Obj = get_resource_api("users", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
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


class RolesCache(CacheTableBase):
    __cache_type__ = "role"
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


class DirectoryServiceCache(CacheTableBase):
    __cache_type__ = "directory_service"
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


class UserGroupCache(CacheTableBase):
    __cache_type__ = "user_group"
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
        super().create(name=name, uuid=uuid)

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
        return {"name": self.name, "version": self.version}


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
