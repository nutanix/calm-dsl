import click

from calm.dsl.log import get_logging_handle

from .main import (
    get,
    create,
    compile,
    update,
    enable,
    disable,
    describe,
    delete,
)
from .policy import (
    create_policy_command,
    update_policy_command,
    compile_policy_command,
    enable_policy_command,
    disable_policy_command,
    get_policy_execution_list,
    describe_policy_execution,
    delete_policy,
    describe_policy,
    get_policy_list,
)

LOG = get_logging_handle(__name__)


@get.command("policies", feature_min_version="3.5.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for policy by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter policy by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only policy names."
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
def _get_policy_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the policy, optionally filtered by a string"""

    get_policy_list(name, filter_by, limit, offset, quiet, all_items, out)


@create.command("policy", feature_min_version="3.5.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "policy_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Policy file to upload",
)
@click.option("--name", "-n", default=None, help="Policy name (Optional)")
@click.option("--description", default=None, help="Policy description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="",
)
def _create_policy_command(policy_file, name, description, force):
    """Create a policy"""

    create_policy_command(policy_file, name, description, force)


@update.command("policy", feature_min_version="3.5.0", experimental=True)
@click.argument("policy_name")
@click.option(
    "--file",
    "-f",
    "policy_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Policy file to upload",
)
@click.option("--description", default=None, help="Policy description (Optional)")
def _update_policy_command(policy_file, policy_name, description):
    """Updates a policy"""

    update_policy_command(policy_file, policy_name, description)


@enable.command("policy", feature_min_version="3.5.0", experimental=True)
@click.argument("policy_name")
def _enable_policy_command(policy_name):
    """Enable a policy"""

    enable_policy_command(policy_name)


@disable.command("policy", feature_min_version="3.5.0", experimental=True)
@click.argument("policy_name")
def _disable_policy_command(policy_name):
    """Disable a policy"""

    disable_policy_command(policy_name)


@describe.command("policy", feature_min_version="3.5.0")
@click.argument("policy_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_policy(policy_name, out):
    """Describe a policy"""

    describe_policy(policy_name, out)


@compile.command("policy", feature_min_version="3.5.0")
@click.option(
    "--file",
    "-f",
    "policy_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Policy file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_policy_command(policy_file, out):
    """Compiles a DSL (Python) policy into JSON or YAML"""
    compile_policy_command(policy_file, out)


@delete.command("policy", feature_min_version="3.5.0")
@click.argument("policy_names", nargs=-1)
def _delete_policy(policy_names):
    """Deletes a policy"""

    delete_policy(policy_names)


@get.command("policy-executions", feature_min_version="3.5.0", experimental=True)
@click.argument("policy_name")
@click.option("--name", "-n", default=None, help="Search for policy executions by name")
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter policy execution by this string",
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
    help="Show only policy execution names.",
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
def _get_policy_execution_list(
    policy_name, name, filter_by, limit, offset, quiet, all_items, out
):
    """Get the policy execution, optionally filtered by a string"""

    get_policy_execution_list(
        policy_name, name, filter_by, limit, offset, quiet, all_items, out
    )


@describe.command("policy-execution", feature_min_version="3.5.0")
@click.argument("policy_name")
@click.option(
    "--uuid",
    "uuid",
    help="Approval UUID",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_policy_execution(policy_name, out, uuid=""):
    """Describe a policy execution"""

    describe_policy_execution(policy_name, out, uuid=uuid)
