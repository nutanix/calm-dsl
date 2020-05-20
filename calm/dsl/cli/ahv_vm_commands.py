import json
import sys

import click

from calm.dsl.tools import get_logging_handle

from .main import get, list
from .ahv_vms import get_ahv_vm_list

LOG = get_logging_handle(__name__)


@get.command("vms")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
def _get_ahv_vm_list(limit, offset, quiet):
    """Get VMs"""

    get_ahv_vm_list(limit, offset, quiet)


@list.command("vm")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
def _get_ahv_vm_list(limit, offset, quiet):
    """List VMs"""

    get_ahv_vm_list(limit, offset, quiet)
