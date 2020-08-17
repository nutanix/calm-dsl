import click
import sys

from calm.dsl.log import get_logging_handle
from .main import get
from .vms import get_ahv_vm_list, get_brownfield_ahv_vm_list

LOG = get_logging_handle(__name__)


@get.command("vms")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only vms names.")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
@click.option(
    "--unmanaged",
    "-u",
    is_flag=True,
    default=False,
    help="To find Calm Managed/Unmanaged vms",
)
def _get_vm_list(limit, offset, quiet, out, unmanaged):
    """Get the vms, optionally filtered by a string"""

    if unmanaged:
        get_brownfield_ahv_vm_list(limit, offset, quiet, out)

    else:
        get_ahv_vm_list(limit, offset, quiet, out)
