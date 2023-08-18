import datetime
import click

from calm.dsl.store import Cache
from calm.dsl.constants import CACHE

from .main import show, update, clear
from .utils import highlight_text
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_cache_table_types():
    """returns cache table types"""

    # Note do not use Cache.get_cache_tables().keys(),
    # It will break, container initialization due to cyclic dependency
    table_types = []
    for attr in CACHE.ENTITY.__dict__:
        if not (attr.startswith("__")):
            table_types.append(getattr(CACHE.ENTITY, attr))

    for attr in CACHE.NDB_ENTITY.__dict__:
        if not (attr.startswith("__")):
            table_types.append(
                CACHE.NDB + CACHE.KEY_SEPARATOR + getattr(CACHE.NDB_ENTITY, attr)
            )

    return table_types


@show.command("cache")
@click.option(
    "--entity",
    "-e",
    default=None,
    help="Cache entity, if not given will update whole cache",
    type=click.Choice(get_cache_table_types()),
)
def show_cache_command(entity):
    """Display the cache data"""

    if entity:
        Cache.show_table(entity)
    else:
        Cache.show_data()


@clear.command("cache")
def clear_cache():
    """Clear the entities stored in cache"""

    Cache.clear_entities()
    LOG.info(highlight_text("Cache cleared at {}".format(datetime.datetime.now())))


@update.command("cache")
@click.option(
    "--entity",
    "-e",
    default=None,
    help="Cache entity, if not given will update whole cache",
    type=click.Choice(get_cache_table_types()),
)
def update_cache(entity):
    """Update the data for dynamic entities stored in the cache"""

    if entity:
        Cache.sync_table(entity)
        Cache.show_table(entity)
    else:
        Cache.sync()
        Cache.show_data()
    LOG.info(highlight_text("Cache updated at {}".format(datetime.datetime.now())))
