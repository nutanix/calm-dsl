import click

from calm.dsl.log import get_logging_handle

from .main import compile, get, describe, delete, create, format
from .endpoints import (
    get_endpoint_list,
    create_endpoint_command,
    delete_endpoint,
    describe_endpoint,
    format_endpoint_command,
    compile_endpoint_command,
)

LOG = get_logging_handle(__name__)


@get.command("endpoints", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for endpoints by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter endpoints by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only endpoint names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_endpoint_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the endpoints, optionally filtered by a string"""

    get_endpoint_list(name, filter_by, limit, offset, quiet, all_items)


@create.command("endpoint", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Endpoint file to upload",
)
@click.option("--name", "-n", default=None, help="Endpoint name (Optional)")
@click.option("--description", default=None, help="Endpoint description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing blueprint with the same name before create.",
)
def _create_endpoint_command(endpoint_file, name, description, force):
    """Creates a endpoint"""

    create_endpoint_command(endpoint_file, name, description, force)


@delete.command("endpoint", feature_min_version="3.0.0", experimental=True)
@click.argument("endpoint_names", nargs=-1)
def _delete_endpoint(endpoint_names):
    """Deletes endpoints"""

    delete_endpoint(endpoint_names)


@describe.command("endpoint", feature_min_version="3.0.0", experimental=True)
@click.argument("endpoint_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
def _describe_endpoint(endpoint_name, out):
    """Describe a endpoint"""

    describe_endpoint(endpoint_name, out)


@format.command("endpoint", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Endpoint file to format",
)
def _format_endpoint_command(endpoint_file):
    format_endpoint_command(endpoint_file)


@compile.command("endpoint", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Endpoint file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
def _compile_endpoint_command(endpoint_file, out):
    """Compiles a DSL (Python) endpoint into JSON or YAML"""
    compile_endpoint_command(endpoint_file, out)
