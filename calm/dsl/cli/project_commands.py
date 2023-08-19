import click
import sys

from .projects import (
    get_projects,
    compile_project_command,
    create_project_from_dsl,
    describe_project,
    delete_project,
    update_project_from_dsl,
    update_project_using_cli_switches,
)
from .main import create, get, update, delete, describe, compile
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("projects")
@click.option("--name", "-n", default=None, help="Search for projects by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter projects by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only project names"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_projects(name, filter_by, limit, offset, quiet, out):
    """Get projects, optionally filtered by a string"""

    get_projects(name, filter_by, limit, offset, quiet, out)


@compile.command("project")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Project file",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_project_command(project_file, out):
    """Compiles a DSL (Python) project into JSON or YAML"""
    compile_project_command(project_file, out)


@create.command("project")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Project file to upload",
    required=True,
)
@click.option(
    "--name", "-n", "project_name", type=str, default="", help="Project name(optional)"
)
@click.option(
    "--description", "-d", default=None, help="Blueprint description (Optional)"
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
def _create_project(project_file, project_name, description, no_cache_update):
    """Creates a project"""

    if project_file.endswith(".py"):
        create_project_from_dsl(
            project_file, project_name, description, no_cache_update
        )
    else:
        LOG.error("Unknown file format")
        return


@delete.command("project")
@click.argument("project_names", nargs=-1)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
def _delete_project(project_names, no_cache_update):
    """Deletes a project"""

    delete_project(project_names, no_cache_update)


@describe.command("project")
@click.argument("project_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_project(project_name, out):
    """Describe a project"""

    describe_project(project_name, out)


@update.command("project")
@click.argument("project_name")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Project file to upload",
)
@click.option(
    "--add_user",
    "-au",
    "add_user_list",
    help="name of user to be added",
    multiple=True,
    default=[],
)
@click.option(
    "--add_group",
    "-ag",
    "add_group_list",
    help="name of group to be added",
    multiple=True,
    default=[],
)
@click.option(
    "--add_account",
    "-aa",
    "add_account_list",
    help="name of account to be added",
    multiple=True,
    default=[],
)
@click.option(
    "--remove_account",
    "-ra",
    "remove_account_list",
    help="name of account to be removed",
    multiple=True,
    default=[],
)
@click.option(
    "--remove_user",
    "-ru",
    "remove_user_list",
    help="name of user to be removed",
    multiple=True,
    default=[],
)
@click.option(
    "--remove_group",
    "-rg",
    "remove_group_list",
    help="name of group to be removed",
    multiple=True,
    default=[],
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
@click.option(
    "--append-only",
    "-ao",
    "append_only",
    is_flag=True,
    default=False,
    help="if true, will only append the users, groups, subnets, external networks, accounts, vpc and cluster from the project_file",
)
@click.option(
    "--disable-quotas",
    "-dq",
    "disable_quotas",
    is_flag=True,
    default=False,
    help="if true, will disable quotas at project level",
)
@click.option(
    "--enable-quotas",
    "-eq",
    "enable_quotas",
    is_flag=True,
    default=False,
    help="if true, will enable quotas at project level",
)
def _update_project(
    project_name,
    project_file,
    add_user_list,
    add_group_list,
    add_account_list,
    remove_account_list,
    remove_user_list,
    remove_group_list,
    no_cache_update,
    append_only,
    disable_quotas,
    enable_quotas,
):
    """
        Updates a project.

    \b
    Usability:
        a. If project_file is given, command will use file to update project. Environment updation is not allowed
           If the project already has quotas set and enabled and quotas are present in project_file then the quotas would be updated
           If the project already has quotas set and enabled and there are no quotas in project_file then the original quotas would be left as it is.
           If the project did not have quotas enabled/set and the project_file has quotas then the quotas would be enabled and set.
        b. If project_file is not given , project will be updated based on other cli switches
           i.e. add_user, add_group, remove_user, remove_group, disable_quotas, enable_quotas
                disable_quotas - It will disable the project level quotas without affecting their values
                enable_quotas - It will enable the project level quotas without affecting their values
        c. Project ACPs will be updated synchronously you remove users/groups from project
    """

    if not (
        project_file
        or add_user_list
        or add_group_list
        or add_account_list
        or remove_account_list
        or remove_user_list
        or remove_group_list
        or disable_quotas
        or enable_quotas
    ):
        LOG.error(
            "Either project file or add/remove paramters for users/groups or --quota-disable/--enable-quotas flag should be given"
        )
        sys.exit(-1)

    if project_file:
        if project_file.endswith(".py"):
            update_project_from_dsl(
                project_name=project_name,
                project_file=project_file,
                no_cache_update=no_cache_update,
                append_only=append_only,
            )
            return
        else:
            LOG.error("Unknown file format")
            return

    if enable_quotas and disable_quotas:
        LOG.error(
            "Either provide --enable-quotas/--disable-quotas, both at the same time is invalid"
        )
        sys.exit(-1)

    update_project_using_cli_switches(
        project_name=project_name,
        add_user_list=add_user_list,
        add_group_list=add_group_list,
        remove_user_list=remove_user_list,
        remove_group_list=remove_group_list,
        add_account_list=add_account_list,
        remove_account_list=remove_account_list,
        disable_quotas=disable_quotas,
        enable_quotas=enable_quotas,
    )
