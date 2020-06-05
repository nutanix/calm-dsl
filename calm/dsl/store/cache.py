import click
import sys

from ..db import get_db_handle
from .version import Version
from calm.dsl.tools import get_logging_handle

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
        """returns entity data corresponding to supplied entry"""

        cache_tables = cls.get_cache_tables()
        if not entity_type:
            LOG.error("No entity type for cache supplied")
            sys.exit(-1)

        db_cls = cache_tables.get(entity_type, None)
        if not db_cls:
            LOG.error("Unknown entity type ({}) supplied".format(entity_type))
            sys.exit(-1)

        return db_cls.get_entity_data(name=name, **kwargs)

    @classmethod
    def sync(cls):
        """Sync cache by latest data"""

        LOG.info("Updating cache", nl=False)

        # Updating version details first
        Version.sync()
        click.echo(".", nl=False, err=True)

        # Updating cache tables
        cache_tables = cls.get_cache_tables()
        for table in list(cache_tables.values()):
            table.sync()
            click.echo(".", nl=False, err=True)

        click.echo(" [Done]", err=True)

    @classmethod
    def clear_entities(cls):
        """Clear data present in the cache tables"""

        cache_tables = cls.get_cache_tables()
        for table in list(cache_tables.values()):
            table.clear()

    @classmethod
    def show_data(cls):
        """Display data present in cache tables"""

        cache_tables = cls.get_cache_tables()
        for cache_type, table in cache_tables.items():
            click.echo("\n{}".format(cache_type.upper()))
            table.show_data()
