import click

from .projects import (
    get_projects,
    delete_project,
    create_project,
    describe_project,
    update_project,
)
from .main import create, get, update, delete, describe
from calm.dsl.tools import get_logging_handle
from calm.dsl.builtins import read_spec

LOG = get_logging_handle(__name__)


@get.command("projects")
@click.option("--name", "-n", default=None, help="Search for projects by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter projects by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
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
    help="output format [json|yaml].",
)
def _get_projects(name, filter_by, limit, offset, quiet, out):
    """Get projects, optionally filtered by a string"""

    get_projects(name, filter_by, limit, offset, quiet, out)


def create_project_from_file(file_location, project_name):

    project_payload = read_spec(file_location)
    if project_name:
        project_payload["project_detail"]["name"] = project_name

    return create_project(project_payload)


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
def _create_project(project_file, project_name):
    """Creates a project"""

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        res, err = create_project_from_file(project_file, project_name)
    else:
        LOG.error("Unknown file format")
        return

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    state = project["status"]["state"]
    LOG.info("Project state: {}".format(state))


@delete.command("project")
@click.argument("project_names", nargs=-1)
def _delete_project(project_names):
    """Deletes a project"""

    delete_project(project_names)


@describe.command("project")
@click.argument("project_name")
def _describe_project(project_name):
    """Describe a project"""

    describe_project(project_name)


@update.command("project")
@click.argument("project_name")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Project file to upload",
    required=True,
)
def _update_project(project_name, project_file):
    """Updates a project"""

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        payload = read_spec(project_file)
        res, err = update_project(project_name, payload)
    else:
        LOG.error("Unknown file format")
        return

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    state = project["status"]["state"]
    LOG.info("Project state: {}".format(state))
