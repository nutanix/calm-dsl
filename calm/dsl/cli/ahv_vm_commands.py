import json
import sys

import click

from calm.dsl.tools import get_logging_handle

from .main import get, list, ls, compile
from .ahv_vms import get_ahv_vm_list, compile_ahv_vm_command

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


@ls.command("vm")
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


@compile.command("vm")
@click.option(
    "--file",
    "-f",
    "vm_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of VM file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
@click.option(
    "--no-sync",
    "-n",
    is_flag=True,
    default=False,
    help="Doesn't sync the cache on compilation",
)
def _compile_ahv_vm_command(vm_file, out, no_sync):
    """Compiles a DSL (Python) blueprint into JSON or YAML"""
    compile_ahv_vm_command(vm_file, out, no_sync)
