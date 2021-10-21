import click

from calm.dsl.log import get_logging_handle

from .main import (
    create,
    compile,
    describe,
    delete,
)
from .policy import (
    create_policy_command,
    compile_policy_command,
    delete_policy,
    describe_policy,
)

LOG = get_logging_handle(__name__)


@create.command("policy", feature_min_version="3.5.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "policy_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Policy file to upload",
)
@click.option("--name", "-n", default=None, help="Job name (Optional)")
@click.option("--description", default=None, help="Job description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="",
)
def _create_policy_command(policy_file, name, description, force):
    """Creates a job in scheduler"""

    create_policy_command(policy_file, name, description, force)


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
