import click

from .main import get
from .protection_policies import get_protection_policies
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("protection-policies")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option("--project", "-p", help="Project name")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only names of protection rules and corresponding policy",
)
def protection_policy_list(limit, offset, project, quiet):
    """Get all protection policies"""
    get_protection_policies(limit, offset, project, quiet)
