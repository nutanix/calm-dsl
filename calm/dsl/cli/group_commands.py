import click
import json

from .groups import get_groups
from .main import get


@get.command("groups")
@click.option("--name", "-n", default=None, help="Search for groups by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter groups by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only group names"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_groups(name, filter_by, limit, offset, quiet, out):
    """Get groups, optionally filtered by a string"""

    get_groups(name, filter_by, limit, offset, quiet, out)
