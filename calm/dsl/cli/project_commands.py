import click
from ruamel import yaml

from .projects import (
    get_projects,
    delete_project,
    create_project,
    describe_project,
    update_project,
)
from .main import create, get, update, delete, describe
from calm.dsl.tools import get_logging_handle

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
@click.pass_obj
def _get_projects(obj, name, filter_by, limit, offset, quiet):
    """Get projects, optionally filtered by a string"""
    get_projects(obj, name, filter_by, limit, offset, quiet)


def create_project_from_file(obj, file_location, project_name):

    project_payload = yaml.safe_load(open(file_location, "r").read())
    if project_name:
        project_payload["project_detail"]["name"] = project_name

    return create_project(obj, project_payload)


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
@click.pass_obj
def _create_project(obj, project_file, project_name):
    """Creates a project"""

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        res, err = create_project_from_file(obj, project_file, project_name)
    else:
        LOG.error("Unknown file format")
        return

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
        return

    project = res.json()
    state = project["status"]["state"]
    LOG.info("Project state: {}".format(state))


@delete.command("project")
@click.argument("project_names", nargs=-1)
@click.pass_obj
def _delete_project(obj, project_names):
    """Deletes a project"""

    delete_project(obj, project_names)


@describe.command("project")
@click.argument("project_name")
@click.pass_obj
def _describe_project(obj, project_name):
    """Describe a project"""

    describe_project(obj, project_name)


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
@click.pass_obj
def _update_project(obj, project_name, project_file):

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        payload = yaml.safe_load(open(project_file, "r").read())
        res, err = update_project(obj, project_name, payload)
    else:
        LOG.error("Unknown file format")
        return

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
        return

    project = res.json()
    state = project["status"]["state"]
    LOG.info("Project state: {}".format(state))
