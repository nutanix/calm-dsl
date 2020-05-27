import json
import sys

import click

from calm.dsl.tools import get_logging_handle

from .main import get, list, ls, compile, create, watch, delete, update
from .ahv_vms import (
    get_ahv_vm_list,
    compile_ahv_vm_command,
    create_ahv_vm_command,
    poll_ahv_vm_task,
    delete_ahv_vm_command,
    update_ahv_vm_command,
)

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
    """Compiles a DSL (Python) VM file to JSON or YAML"""
    compile_ahv_vm_command(vm_file, out, no_sync)


@create.command("vm")
@click.option(
    "--file",
    "-f",
    "vm_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path to VM file",
)
@click.option("--name", "-n", default=None, help="VM name (Optional)")
def _create_ahv_vm_command(vm_file, name):
    """Creates a AHV VM"""
    create_ahv_vm_command(vm_file, name)


# TODO add support for multiple vm deletion
@delete.command("vm")
@click.argument("vm_uuid", required=False)
@click.option(
    "--name", "-id", "vm_name", default=None, help="VM name",
)
def _delete_ahv_vm_command(vm_name, vm_uuid):
    """Deletes a ahv vm.

\b
Note:
    If vm uuid is provided, name parameter will be ignored
    """

    delete_ahv_vm_command(name=vm_name, vm_uuid=vm_uuid)


@update.command("vm")
@click.argument("vm_uuid", required=False)
@click.option(
    "--name", "-n", "vm_name", default=None, help="VM name",
)
@click.option(
    "--file",
    "-f",
    "vm_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path to VM file",
)
def _update_ahv_vm_command(vm_name, vm_uuid, vm_file):
    """Updates a ahv vm

\b
Note:
    If name is not given, class name will be used as vm name
    If uuid is not provided, it will search for vms via name field
    """

    update_ahv_vm_command(vm_file=vm_file, vm_name=vm_name, vm_uuid=vm_uuid)


@watch.command("ahv_vm_task")
@click.option("--task_uuid", "-t", required=True, help="Polling the task")
def _poll_ahv_vm_task(task_uuid):

    poll_ahv_vm_task(task_uuid)
