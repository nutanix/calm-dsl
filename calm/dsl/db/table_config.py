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
import datetime
from prettytable import PrettyTable

from calm.dsl.api import get_resource_api, get_api_client

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
    def clear(cls):
        """removes entire data from table"""
        for db_entity in cls.select():
            db_entity.delete_instance()


class AhvSubnetsCache(CacheTableBase):
    __cache_type__ = "ahv_subnet"
    name = CharField()
    uuid = CharField()
    cluster_name = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "cluster_name": self.cluster_name,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def create(cls, **kwargs):
        super().create(
            name=kwargs["name"],
            uuid=kwargs["uuid"],
            cluster_name=kwargs["cluster_name"],
        )

    @classmethod
    def get_entity_uuid(cls, **kwargs):

        try:
            if kwargs.get("cluster_name"):
                entity = super().get(
                    cls.name == kwargs["name"],
                    cls.cluster_name == kwargs["cluster_name"],
                )

            else:
                entity = super().get(cls.name == kwargs["name"])
            return entity.uuid

        except DoesNotExist:
            return None

    @classmethod
    def show_data(cls):
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
                    highlight_text(entity_data["cluster_name"]),
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
        Obj = get_resource_api("subnets", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cluster_ref = entity["status"]["cluster_reference"]

            cluster_name = cluster_ref.get("name", "")

            cls.create(name=name, uuid=uuid, cluster_name=cluster_name)

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("name", "uuid")


class AhvImagesCache(CacheTableBase):
    __cache_type__ = "ahv_disk_image"
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def create(cls, **kwargs):
        super().create(
            name=kwargs["name"], uuid=kwargs["uuid"],
        )

    @classmethod
    def get_entity_uuid(cls, **kwargs):

        try:
            entity = super().get(cls.name == kwargs["name"])
            return entity.uuid

        except DoesNotExist:
            return None

    @classmethod
    def sync(cls):

        # clear old data
        cls.clear()

        # update by latest data
        client = get_api_client()
        Obj = get_resource_api("images", client.connection)
        res, err = Obj.list({"length": 1000})
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["name"]
            uuid = entity["metadata"]["uuid"]
            cls.create(name=name, uuid=uuid)

    @classmethod
    def show_data(cls):
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


class ProjectCache(CacheTableBase):
    __cache_type__ = "project"
    name = CharField()
    uuid = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def create(cls, **kwargs):
        super().create(
            name=kwargs["name"], uuid=kwargs["uuid"],
        )

    @classmethod
    def get_entity_uuid(cls, **kwargs):

        try:
            entity = super().get(cls.name == kwargs["name"])
            return entity.uuid

        except DoesNotExist:
            return None

    @classmethod
    def sync(cls):

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
            cls.create(name=name, uuid=uuid)

    @classmethod
    def show_data(cls):
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
