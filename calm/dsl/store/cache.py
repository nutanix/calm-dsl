import click
import sys
import traceback
from peewee import OperationalError, IntegrityError

from .version import Version
from calm.dsl.db import get_db_handle, init_db_handle
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class Cache:
    """Cache class Implementation"""

    @classmethod
    def get_cache_tables(cls):
        """returns tables used for cache purpose"""

        db = get_db_handle()
        db_tables = db.registered_tables

        cache_tables = {}
        for table in db_tables:
            if hasattr(table, "__cache_type__"):
                cache_tables[table.__cache_type__] = table
        return cache_tables

    @classmethod
    def get_entity_data(cls, entity_type, name, **kwargs):
        """returns entity data corresponding to supplied entry using entity name"""

        cache_tables = cls.get_cache_tables()
        if not entity_type:
            LOG.error("No entity type for cache supplied")
            sys.exit(-1)

        db_cls = cache_tables.get(entity_type, None)
        if not db_cls:
            LOG.error("Unknown entity type ({}) supplied".format(entity_type))
            sys.exit(-1)

        try:
            res = db_cls.get_entity_data(name=name, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        return res

    @classmethod
    def get_entity_data_using_uuid(cls, entity_type, uuid, *args, **kwargs):
        """returns entity data corresponding to supplied entry using entity uuid"""

        cache_tables = cls.get_cache_tables()
        if not entity_type:
            LOG.error("No entity type for cache supplied")
            sys.exit(-1)

        db_cls = cache_tables.get(entity_type, None)
        if not db_cls:
            LOG.error("Unknown entity type ({}) supplied".format(entity_type))
            sys.exit(-1)

        try:
            res = db_cls.get_entity_data_using_uuid(uuid=uuid, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        return res

    @classmethod
    def sync(cls):
        """Sync cache by latest data"""

        def sync_tables(tables):
            for table in tables:
                table.sync()
                click.echo(".", nl=False, err=True)

        cache_table_map = cls.get_cache_tables()
        tables = list(cache_table_map.values())

        # Inserting version table at start
        tables.insert(0, Version)

        try:
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)

        except (OperationalError, IntegrityError):
            click.echo(" [Fail]")
            # init db handle once (recreating db if some schema changes are there)
            LOG.info("Removing existing db and updating cache again")
            init_db_handle()
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)
            click.echo(" [Done]", err=True)

    @classmethod
    def sync_table(cls, cache_type):

        cache_table_map = cls.get_cache_tables()
        if cache_type not in cache_table_map:
            LOG.error("Invalid cache_type ('{}') provided".format(cache_type))
            sys.exit(-1)

        cache_table = cache_table_map[cache_type]
        cache_table.sync()

    @classmethod
    def clear_entities(cls):
        """Clear data present in the cache tables"""

        # For now clearing means erasing all data. So reinitialising whole database
        init_db_handle()

    @classmethod
    def show_data(cls):
        """Display data present in cache tables"""

        cache_tables = cls.get_cache_tables()
        for cache_type, table in cache_tables.items():
            click.echo("\n{}".format(cache_type.upper()))
            try:
                table.show_data()
            except OperationalError:
                formatted_exc = traceback.format_exc()
                LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
                LOG.error(
                    "Cache error occurred. Please update cache using 'calm update cache' command"
                )
                sys.exit(-1)
