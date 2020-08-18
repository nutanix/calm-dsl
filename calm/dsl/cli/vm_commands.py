import click
import sys

from .main import get
from .vms import (
    get_ahv_vm_list,
    get_brownfield_ahv_vm_list,
    get_brownfield_aws_vm_list,
    get_brownfield_azure_vm_list,
    get_brownfield_gcp_vm_list,
    get_brownfield_vmware_vm_list,
)
from calm.dsl.log import get_logging_handle

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
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(["AHV_VM", "AWS_VM", "AZURE_VM", "GCP_VM", "VMWARE_VM"]),
    default="AHV_VM",
    help="Provider type",
)
def _get_vm_list(limit, offset, quiet, out, unmanaged, provider_type):
    """Get the vms, optionally filtered by a string"""

    if unmanaged:
        if provider_type == "AHV_VM":
            get_brownfield_ahv_vm_list(limit, offset, quiet, out)
        elif provider_type == "AWS_VM":
            get_brownfield_aws_vm_list(limit, offset, quiet, out)
        elif provider_type == "AZURE_VM":
            get_brownfield_azure_vm_list(limit, offset, quiet, out)
        elif provider_type == "GCP_VM":
            get_brownfield_gcp_vm_list(limit, offset, quiet, out)
        elif provider_type == "VMWARE_VM":
            # Has issue with it. Fixed in 2.9.8.1 and 3.0.0 (https://jira.nutanix.com/browse/CALM-18635)
            get_brownfield_vmware_vm_list(limit, offset, quiet, out)

    else:
        get_ahv_vm_list(limit, offset, quiet, out)
