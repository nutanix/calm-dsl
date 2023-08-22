import click

from calm.dsl.log import get_logging_handle

from .main import (
    get,
    describe,
)
from .approval_request import (
    describe_approval_request,
    get_approval_request_list,
)

LOG = get_logging_handle(__name__)


@get.command("my-approval-requests", feature_min_version="3.5.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for approval_request by name")
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter approval_request by this string",
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
    help="Show only approval_request names.",
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
def _get_approval_request_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the approval-request, optionally filtered by a string"""

    get_approval_request_list(name, filter_by, limit, offset, quiet, all_items, out)


@describe.command("my-approval-request", feature_min_version="3.5.0")
@click.argument("approval_request_name")
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
def _describe_approval_request(approval_request_name, out, uuid=""):
    """Describe a approval_request"""

    describe_approval_request(approval_request_name, out, uuid=uuid)
