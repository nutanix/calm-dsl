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
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_config
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

    @classmethod
    def get_cache_tables(cls):
        return cls.tables

    @classmethod
    def clear(cls, *args, **kwargs):
        """removes entire data from table"""
        raise NotImplementedError("clear helper not implemented")

    def get_detail_dict(self, *args, **kwargs):
        raise NotImplementedError("get_detail_dict helper not implemented")

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        raise NotImplementedError("create_entry helper not implemented")

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        raise NotImplementedError("get_entity_data helper not implemented")

    @classmethod
    def show_data(cls, *args, **kwargs):
        raise NotImplementedError("show_data helper not implemented")

    @classmethod
    def sync(cls, *args, **kwargs):
        raise NotImplementedError("sync helper not implemented")


class AhvSubnetsCache(CacheTableBase):
    __cache_type__ = "ahv_subnet"
    name = CharField()
    uuid = CharField()
    cluster = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "cluster": self.cluster,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls, *args, **kwargs):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        cluster_name = kwargs.get("cluster", None)
        if not cluster_name:
            raise ValueError("cluster not supplied for subnet {}".format(name))

        # store data in table
        super().create(
            name=name, uuid=uuid, cluster=cluster_name,
        )

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        cluster_name = kwargs.get("cluster", "")
        try:
            if cluster_name:
                entity = super().get(cls.name == name, cls.cluster == cluster_name,)
            else:
                # The get() method is shorthand for selecting with a limit of 1
                # If more than one row is found, the first row returned by the database cursor
                entity = super().get(cls.name == name)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    @classmethod
    def show_data(cls, *args, **kwargs):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "CLUSTER_NAME", "LAST UPDATED"]
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
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    @classmethod
    def sync(cls, *args, **kwargs):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        # update by latest data
        config = get_config()
        client = get_api_client()

        project_name = config["PROJECT"]["name"]
        params = {"length": 1000, "filter": "name=={}".format(project_name)}
        project_name_uuid_map = client.project.get_name_uuid_map(params)

        if not project_name_uuid_map:
            LOG.error("Invalid project {} in config".format(project_name))
            sys.exit(-1)

        project_id = project_name_uuid_map[project_name]
        res, err = client.project.read(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        project = res.json()
        subnets_list = []
        for subnet in project["status"]["project_status"]["resources"][
            "subnet_reference_list"
        ]:
            subnets_list.append(subnet["uuid"])

        # Extending external subnet's list from remote account
        for subnet in project["status"]["project_status"]["resources"][
            "external_network_list"
        ]:
            subnets_list.append(subnet["uuid"])

        accounts = project["status"]["project_status"]["resources"][
            "account_reference_list"
        ]
        
        reg_accounts = []
        for account in accounts:
            reg_accounts.append(account["uuid"])

        # As account_uuid is required for versions>2.9.0
        account_uuid = ""
        payload = {"length": 250, "filter": "type==nutanix_pc"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            entity_id = entity["metadata"]["uuid"]
            if entity_id in reg_accounts:
                account_uuid = entity_id
                break
        
        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        filter_query = "(_entity_id_=={})".format(
            ",_entity_id_==".join(subnets_list),
        )
        res = AhvObj.subnets(account_uuid=account_uuid, filter_query=filter_query)
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cluster_ref = entity["status"]["cluster_reference"]
            cluster_name = cluster_ref.get("name", "")

            cls.create_entry(name=name, uuid=uuid, cluster=cluster_name)

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AhvImagesCache(CacheTableBase):
    __cache_type__ = "ahv_disk_image"
    name = CharField()
    image_type = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self, *args, **kwargs):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "image_type": self.image_type,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def clear(cls, *args, **kwargs):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

    @classmethod
    def create_entry(cls, name, uuid, **kwargs):
        image_type = kwargs.get("image_type", "")
        # Store data in table
        super().create(name=name, uuid=uuid, image_type=image_type)

    @classmethod
    def get_entity_data(cls, name, **kwargs):
        image_type = kwargs.get("image_type", None)
        if not image_type:
            raise ValueError("image_type not provided for image {}".format(name))

        try:
            entity = super().get(cls.name == name, cls.image_type == image_type)
            return entity.get_detail_dict()

        except DoesNotExist:
            return None

    @classmethod
    def sync(cls, *args, **kwargs):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        # update by latest data
        config = get_config()
        client = get_api_client()

        project_name = config["PROJECT"]["name"]
        params = {"length": 1000, "filter": "name=={}".format(project_name)}
        project_name_uuid_map = client.project.get_name_uuid_map(params)

        if not project_name_uuid_map:
            LOG.error("Invalid project {} in config".format(project_name))
            sys.exit(-1)

        project_id = project_name_uuid_map[project_name]
        res, err = client.project.read(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        project = res.json()
        accounts = project["status"]["project_status"]["resources"][
            "account_reference_list"
        ]
        
        reg_accounts = []
        for account in accounts:
            reg_accounts.append(account["uuid"])

        # As account_uuid is required for versions>2.9.0
        account_uuid = ""
        payload = {"length": 250, "filter": "type==nutanix_pc"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            entity_id = entity["metadata"]["uuid"]
            if entity_id in reg_accounts:
                account_uuid = entity_id
                break
        
        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()
        res = AhvObj.images(account_uuid=account_uuid)

        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            # TODO add proper validation for karbon images
            image_type = entity["status"]["resources"].get("image_type", "")
            cls.create_entry(name=name, uuid=uuid, image_type=image_type)

    @classmethod
    def show_data(cls, *args, **kwargs):
        """display stored data in table"""

        if not len(cls.select()):
            click.echo(highlight_text("No entry found !!!"))
            return

        table = PrettyTable()
        table.field_names = ["NAME", "UUID", "IMAGE_TYPE", "LAST UPDATED"]
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
                    highlight_text(last_update_time),
                ]
            )
        click.echo(table)

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class ProjectCache(CacheTableBase):
    __cache_type__ = "project"
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
    def clear(cls, *args, **kwargs):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

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

    @classmethod
    def sync(cls, *args, **kwargs):
        """sync the table data from server"""
        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()
        Obj = get_resource_api("projects", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create_entry(name=name, uuid=uuid)

    @classmethod
    def show_data(cls, *args, **kwargs):
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
    def clear(cls, *args, **kwargs):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()

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

    @classmethod
    def sync(cls, *args, **kwargs):
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
    def show_data(cls, *args, **kwargs):
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
