import click
import json

from .acps import get_acps, create_acp, get_system_roles, delete_acp, update_acp
from .main import get, create, delete, update


@get.command("acps")
@click.option("--name", "-n", default=None, help="Search for acps by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter acps by this string"
)
@click.option("--project", "-p", required=True, help="ACP project name")
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
def _get_acps(name, project, filter_by, limit, offset, quiet, out):
    """Get acps, optionally filtered by a string"""

    get_acps(name, project, filter_by, limit, offset, quiet, out)


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


@delete.command("acp")
@click.argument("acp_name")
@click.option("--project", "-p", required=True, help="ACP project name")
def _delete_acp(acp_name, project):
    """Deletes a acp"""

    delete_acp(acp_name, project)


@update.command("acp")
@click.argument("acp_name")
@click.option("--project", "-p", required=True, help="ACP project name")
@click.option("--user", "-u", multiple=True, default=[])
@click.option("--group", "-g", multiple=True, default=[])
@click.option("--remove_operation", "-r", is_flag=True, default=False, help="Flag to indicate operation is to remove users/groups from acp")
def _update_acp(acp_name, project, user, group, remove_operation):
    """Updates a a cp"""

    update_acp(
        acp_name=acp_name,
        project_name=project,
        users=user,
        groups=group,
        is_remove_operation=remove_operation,
    )
