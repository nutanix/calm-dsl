import click

from .acps import (
    get_acps,
    create_acp,
    get_system_roles,
    delete_acp,
    update_acp,
    describe_acp,
)
from .main import get, create, delete, update, describe


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
@click.option("--user", "-u", "users", multiple=True, default=[])
@click.option("--group", "-g", "groups", multiple=True, default=[])
@click.option("--name", "-name", default=None)
def _create_acp(role, project, users, groups, name):
    """Creates an acp"""

    create_acp(role, project, users, groups, name)


@delete.command("acp")
@click.argument("acp_name")
@click.option("--project", "-p", required=True, help="ACP project name")
def _delete_acp(acp_name, project):
    """Deletes an acp"""

    delete_acp(acp_name, project)


@update.command("acp")
@click.argument("acp_name")
@click.option("--project", "-p", required=True, help="ACP project name")
@click.option("--add_user", "-au", "add_user_list", multiple=True, default=[])
@click.option("--add_group", "-ag", "add_group_list", multiple=True, default=[])
@click.option("--remove_user", "-ru", "remove_user_list", multiple=True, default=[])
@click.option("--remove_group", "-rg", "remove_group_list", multiple=True, default=[])
def _update_acp(
    acp_name,
    project,
    add_user_list,
    add_group_list,
    remove_user_list,
    remove_group_list,
):
    """Updates an acp"""

    update_acp(
        acp_name=acp_name,
        project_name=project,
        add_user_list=add_user_list,
        add_group_list=add_group_list,
        remove_user_list=remove_user_list,
        remove_group_list=remove_group_list,
    )


@describe.command("acp")
@click.argument("acp_name")
@click.option("--project", "-p", required=True, help="ACP project name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_acp(acp_name, project, out):
    """Describe an acp"""

    describe_acp(acp_name=acp_name, project_name=project, out=out)
