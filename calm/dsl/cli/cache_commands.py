import click
import arrow
import datetime
from prettytable import PrettyTable

from calm.dsl.store import Cache

from .main import show, update, clear
from .utils import highlight_text
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def show_cache(obj):

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
@click.pass_obj
def show_cache_command(obj):
    show_cache(obj)


@clear.command("cache")
@click.pass_obj
def clear_cache(obj):
    """Clear the entities stored in cache"""

    Cache.clear_entities()
    LOG.info(highlight_text("Cache cleared at {}".format(datetime.datetime.now())))


@update.command("cache")
@click.option(
    "--entity_type",
    "-e",
    default=None,
    type=click.Choice(Cache.get_entity_types()),
    help="Cache entity type",
)
@click.pass_obj
def update_cache(obj, entity_type):
    """Update the data for dynamic entities stored in the cache"""

    LOG.debug("Updating cache")
    Cache.sync(entity_type)
    LOG.debug("Success")
    show_cache(obj)
    LOG.info(highlight_text("Cache updated at {}".format(datetime.datetime.now())))
