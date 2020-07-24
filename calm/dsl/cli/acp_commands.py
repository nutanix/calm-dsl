import click
import json

from .acps import get_acps, create_acp, get_system_roles
from .main import get, create


@get.command("acps")
@click.option("--name", "-n", default=None, help="Search for acps by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter acps by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only acp names")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_acps(name, filter_by, limit, offset, quiet, out):
    """Get acps, optionally filtered by a string"""

    get_acps(name, filter_by, limit, offset, quiet, out)


@create.command("acp")
@click.option(
    "--role",
    "-r",
    required=True,
    type=click.Choice(get_system_roles()),
    help="ACP role",
)
@click.option("--project", "-p", required=True, help="ACP project name")
@click.option("--user", "-u", multiple=True, default=[])
@click.option("--group", "-g", multiple=True, default=[])
@click.option("--name", "-name", default=None)
def _create_acp(role, project, user, group, name):

    create_acp(role, project, user, group, name)
