import click

from calm.dsl.log import get_logging_handle

from .main import (
    get,
    approve,
    reject,
    describe,
)
from .approval import (
    update_approval_command,
    describe_approval,
    get_approval_list,
)

from .constants import APPROVAL_REQUEST

LOG = get_logging_handle(__name__)


@get.command("approval-requests", feature_min_version="3.5.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for approval by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter approval by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only approval names."
)
@click.option(
    "--all-items",
    "-a",
    is_flag=True,
    help="Get all items, including which are not pending on you",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_approval_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the approval which are currently pending on you, optionally filtered by a string"""

    get_approval_list(name, filter_by, limit, offset, quiet, all_items, out)


@approve.command("approval-request", feature_min_version="3.5.0", experimental=True)
@click.argument("approval_name")
@click.option(
    "--uuid",
    "uuid",
    help="Approval UUID",
)
@click.option(
    "--comment",
    "-c",
    "comment",
    help="Approval comment",
)
def _approve_approval_command(approval_name, comment, uuid=""):
    """Updates a approval"""

    update_approval_command(
        approval_name, APPROVAL_REQUEST.STATES.APPROVED, comment, uuid=uuid
    )


@reject.command("approval-request", feature_min_version="3.5.0", experimental=True)
@click.argument("approval_name")
@click.option(
    "--uuid",
    "uuid",
    help="Approval UUID",
)
@click.option(
    "--comment",
    "-c",
    "comment",
    help="Approval comment",
)
def _reject_approval_command(approval_name, comment, uuid=""):
    """Updates a approval"""

    update_approval_command(
        approval_name, APPROVAL_REQUEST.STATES.REJECTED, comment, uuid=uuid
    )


@describe.command("approval-request", feature_min_version="3.5.0")
@click.argument("approval_name")
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
def _describe_approval(approval_name, out, uuid=""):
    """Describe a approval"""

    describe_approval(approval_name, out, uuid=uuid)
