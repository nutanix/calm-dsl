import click
from .__init__ import get
from .runbook import get_runbook_list


@get.command("runbooks")
@click.option("--name", default=None, help="Search for runbooks by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter runbooks by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only runbook names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""
    get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items)
