import datetime
import click

from calm.dsl.store import Cache

from .main import show, update, clear
from .utils import highlight_text
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@show.command("cache")
def show_cache_command():
    """Display the cache data"""

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
    type=click.Choice(Cache.get_cache_tables().keys()),
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
