import click
from .__init__ import get
from .bps import get_blueprint_list


@get.command("bps")
@click.option("--name", default=None, help="Search for blueprints by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter blueprints by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""
    get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items)
