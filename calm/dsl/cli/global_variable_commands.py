import click

from calm.dsl.log import get_logging_handle

from .main import compile, decompile, get, describe, delete, create, update, usage
from .global_variable import (
    get_global_variable_list,
    create_global_variable_command,
    update_global_variable_command,
    describe_global_variable,
    delete_global_variable,
    compile_global_variable_command,
    decompile_global_variable_command,
    get_global_variable_usage,
)

LOG = get_logging_handle(__name__)


# ============ CRUD commands ============


@get.command("global-variable")
@click.option("--name", "-n", default=None, help="Search for global variables by name")
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter global variables by this string",
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only global variable names.",
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_global_variable_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the global variables, optionally filtered by a string"""

    get_global_variable_list(name, filter_by, limit, offset, quiet, all_items, out)


@create.command("global-variable")
@click.option(
    "--file",
    "-f",
    "global_variable_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Global variable file to upload",
)
@click.option("--name", "-n", default=None, help="Global variable name (Optional)")
@click.option(
    "--description", default=None, help="Global variable description (Optional)"
)
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing global variable with the same name before create.",
)
def _create_global_variable_command(global_variable_file, name, description, force):
    """Creates a global variable"""

    create_global_variable_command(global_variable_file, name, description, force)


@update.command("global-variable")
@click.option(
    "--file",
    "-f",
    "global_variable_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Global variable file to upload",
)
@click.option("--name", "-n", default=None, required=True, help="Global variable name")
@click.option(
    "--description", default=None, help="Global variable description (Optional)"
)
def _update_global_variable_command(global_variable_file, name, description):
    """Updates a global variable"""

    update_global_variable_command(global_variable_file, name, description)


@delete.command("global-variable")
@click.argument("global_variable_names", nargs=-1)
def _delete_global_variable(global_variable_names):
    """Deletes a global variable"""

    delete_global_variable(global_variable_names)


# ============ Describe command ============


@describe.command("global-variable")
@click.argument("global_variable_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
def _describe_global_variable(global_variable_name, out):
    """Describe a global variable"""

    describe_global_variable(global_variable_name, out)


# ============ Compile and Decompile commands ============


@compile.command("global-variable", experimental=True)
@click.option(
    "--file",
    "-f",
    "global_variable_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Global variable file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
def _compile_global_variable_command(global_variable_file, out):
    """Compiles a DSL (Python) global varibale into JSON or YAML"""
    compile_global_variable_command(global_variable_file, out)


@decompile.command("global-variable", experimental=True)
@click.argument("name", required=False)
@click.option(
    "--file",
    "-f",
    "global_variable_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to Global variable file",
)
@click.option(
    "--prefix",
    "-p",
    default="",
    help="Prefix used for appending to entities name(Reserved name cases)",
)
@click.option(
    "--dir",
    "-d",
    "global_variable_dir",
    default=None,
    help="Global variable directory location used for placing decompiled entities",
)
@click.option(
    "--no-format",
    "-nf",
    "no_format",
    is_flag=True,
    default=False,
    help="Disable formatting the decompiled global variable using black",
)
def _decompile_global_variable_command(
    name, global_variable_file, prefix, global_variable_dir, no_format
):
    """Decompiles global variable present on server or json file"""

    decompile_global_variable_command(
        name, global_variable_file, prefix, global_variable_dir, no_format=no_format
    )


# ============ Usage command ============


@usage.command("global-variable")
@click.argument("name", required=True)
def _get_global_variable_usage(name):
    """Fetch usage of a global variable"""

    get_global_variable_usage(name)
