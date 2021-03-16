import click

from .roles import get_roles
from .main import get


@get.command("roles")
@click.option("--name", "-n", default=None, help="Search for roles by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter roles by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only role names")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_roles(name, filter_by, limit, offset, quiet, out):
    """Get roles, optionally filtered by a string"""

    get_roles(name, filter_by, limit, offset, quiet, out)
