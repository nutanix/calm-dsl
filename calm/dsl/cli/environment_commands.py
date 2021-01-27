import click

from .main import get, delete
from .environments import get_environment_list, delete_environment


@get.command("environments")
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


@delete.command("environment")
@click.argument("environment_name")
@click.option("--project", "-p", "project_name", help="Project name", required=True)
def _delete_environment(environment_name, project_name):
    """Deletes a environment"""

    delete_environment(environment_name, project_name)
