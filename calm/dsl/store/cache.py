import peewee
import click

from ..db import get_db_handle
from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


class Cache:
    """Cache class Implementation"""

    cache_types = ["ahv_subnet", "ahv_disk_image"]

    @classmethod
    def get_entity_types(cls):
        """Entity types used in the cache"""
        return list(cls.entity_type_api_map.keys())

    @classmethod
    def create(*args, **kwargs):

        db = get_db_handle()
        entity_type = kwargs.pop("entity_type", None)
        if not entity_type:
            raise Exception("No entity type supplied")

        # TODO validate by proper cache table
        if hasattr(db, entity_type):
            db_cls = getattr(db, entity_type)

        else:
            raise Exception("Unknown entity type")

        db_cls.create(**kwargs)

    @classmethod
    def get_entity_uuid(*args, **kwargs):

        db = get_db_handle()
        entity_type = kwargs.pop("entity_type", None)
        if not entity_type:
            raise Exception("No entity type supplied")

        # TODO validate by proper cache table
        if hasattr(db, entity_type):
            db_cls = getattr(db, entity_type)

        else:
            raise Exception("Unknown entity type")

        return db_cls.get_entity_uuid(**kwargs)

    @classmethod
    def sync(cls):
        """Update the cache by latest data"""

        db = get_db_handle()
        db_tables = db.registered_tables

        # Find cache tables and sync data
        for table in db_tables:
            if hasattr(table, "__cache_type__"):
                table.sync()

    @classmethod
    def clear_entities(cls):
        """Deletes all the data present in the cache"""

        db = get_db_handle()
        db_tables = db.registered_tables

        # Find cache tables and clear data
        for table in db_tables:
            if hasattr(table, "__cache_type__"):
                table.clear()

    @classmethod
    def show_data(cls):
        db = get_db_handle()
        db_tables = db.registered_tables

        # Find cache tables and clear data
        for table in db_tables:
            if hasattr(table, "__cache_type__"):
                cache_type = table.__cache_type__
                click.echo("\n{}".format(cache_type.upper()))
                table.show_data()
