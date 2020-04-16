import click
import arrow
import datetime
from prettytable import PrettyTable

from calm.dsl.store import Cache
from calm.dsl.store import Version

from .main import show, update, clear
from .utils import highlight_text
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def show_cache():

    avl_entities = Cache.list()

    if not avl_entities:
        click.echo(highlight_text("Cache is empty !!!\n"))
        return

    table = PrettyTable()
    table.field_names = ["ENTITY_TYPE", "ENTITY_NAME", "ENTITY_UUID", "LAST UPDATED"]

    for entity in avl_entities:
        last_update_time = arrow.get(
            entity["last_update_time"].astimezone(datetime.timezone.utc)
        ).humanize()
        table.add_row(
            [
                highlight_text(entity["type"]),
                highlight_text(entity["name"]),
                highlight_text(entity["uuid"]),
                highlight_text(last_update_time),
            ]
        )

    click.echo(table)


@show.command("cache")
def show_cache_command():
    """Display the cache data"""

    show_cache()


@clear.command("cache")
def clear_cache():
    """Clear the entities stored in cache"""

    Cache.clear_entities()
    LOG.info(highlight_text("Cache cleared at {}".format(datetime.datetime.now())))


@update.command("cache")
def update_cache():
    """Update the data for dynamic entities stored in the cache"""

    LOG.debug("Updating cache")
    # Update api cache
    Cache.sync()
    # Update version cache
    Version.sync()
    LOG.debug("Success")
    show_cache()
    LOG.info(highlight_text("Cache updated at {}".format(datetime.datetime.now())))
