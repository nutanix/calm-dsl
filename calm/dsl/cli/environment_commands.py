import click

from .main import get, delete, create, update, compile
from .environments import (
    create_environment_from_dsl_file,
    get_environment_list,
    delete_environment,
    update_environment_from_dsl_file,
    compile_environment_command,
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
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
def _delete_environment(environment_name, project_name, no_cache_update):
    """Deletes a environment"""

    delete_environment(environment_name, project_name, no_cache_update)


@create.command("environment", feature_min_version="3.2.0")
@click.option(
    "--file",
    "-f",
    "env_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of environment file to create",
)
@click.option("--project", "-p", "project_name", help="Project name", required=True)
@click.option(
    "--name", "-n", "env_name", default=None, help="Environment name (Optional)"
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
def _create_environment(env_file, env_name, project_name, no_cache_update):
    """
    Creates a environment to existing project.
    """

    if env_file.endswith(".py"):
        create_environment_from_dsl_file(
            env_file, env_name, project_name, no_cache_update
        )
    else:
        LOG.error("Unknown file format {}".format(env_file))
        return


@update.command("environment", feature_min_version="3.2.0")
@click.argument("env_name")
@click.option("--project", "-p", "project_name", help="Project name", required=True)
@click.option(
    "--file",
    "-f",
    "env_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of environment file to update",
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for project",
)
def _update_environment(env_name, project_name, env_file, no_cache_update):
    """
    Updates environment of an existing project.
    """

    if env_file.endswith(".py"):
        update_environment_from_dsl_file(
            env_name, env_file, project_name, no_cache_update
        )
    else:
        LOG.error("Unknown file format {}".format(env_file))
        return


@compile.command("environment")
@click.option(
    "--file",
    "-f",
    "env_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Environment file",
)
@click.option("--project", "-p", "project_name", help="Project name", required=True)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_environment_command(env_file, project_name, out):
    """Compiles a DSL (Python) environment into JSON or YAML"""

    compile_environment_command(env_file, project_name, out)
