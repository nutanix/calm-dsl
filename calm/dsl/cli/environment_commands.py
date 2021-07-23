import click

from .main import get, delete, create
from .environments import (
    create_environment_from_dsl_file,
    get_environment_list,
    delete_environment,
)

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("environments", feature_min_version="3.2.0")
@click.option("--name", "-n", default=None, help="Search for environments by name")
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter environments by this string",
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only environments names."
)
@click.option("--project", "-p", "project_name", help="Project name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_environment_list(name, filter_by, limit, offset, quiet, out, project_name):
    """Get the environment, optionally filtered by a string"""

    get_environment_list(name, filter_by, limit, offset, quiet, out, project_name)


@delete.command("environment", feature_min_version="3.2.0")
@click.argument("environment_name")
@click.option("--project", "-p", "project_name", help="Project name", required=True)
def _delete_environment(environment_name, project_name):
    """Deletes a environment"""

    delete_environment(environment_name, project_name)


@create.command("environment", feature_min_version="3.2.0")
@click.option(
    "--file",
    "-f",
    "env_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of environment file to create",
)
@click.option(
    "--name", "-n", "env_name", default=None, help="Environment name (Optional)"
)
def _create_environment(env_file, env_name):
    """
    Creates a environment
    By default, environment will be created in configured project
    Project can be changed using metadata object in environment py file
    """

    if env_file.endswith(".py"):
        create_environment_from_dsl_file(env_file, env_name)
    else:
        LOG.error("Unknown file format {}".format(env_file))
        return
