import click

from .main import get
from .brownfield_vms import (
    get_brownfield_ahv_vm_list,
    get_brownfield_aws_vm_list,
    get_brownfield_azure_vm_list,
    get_brownfield_gcp_vm_list,
    get_brownfield_vmware_vm_list,
)
from .utils import FeatureFlagGroup
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.group("brownfield", cls=FeatureFlagGroup)
def brownfield_get():
    """Get brownfield items"""

    pass


@brownfield_get.command("vms")
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
@click.option("--project", "-p", help="Project name", required=True)
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(["AHV_VM", "AWS_VM", "AZURE_VM", "GCP_VM", "VMWARE_VM"]),
    default="AHV_VM",
    help="Provider type",
)
def _get_vm_list(limit, offset, quiet, out, project, provider_type):
    """Get the brownfield vms, optionally filtered by a string"""

    if provider_type == "AHV_VM":
        get_brownfield_ahv_vm_list(limit, offset, quiet, out, project)
    elif provider_type == "AWS_VM":
        get_brownfield_aws_vm_list(limit, offset, quiet, out, project)
    elif provider_type == "AZURE_VM":
        get_brownfield_azure_vm_list(limit, offset, quiet, out, project)
    elif provider_type == "GCP_VM":
        get_brownfield_gcp_vm_list(limit, offset, quiet, out, project)
    elif provider_type == "VMWARE_VM":
        # Has issue with it. Fixed in 2.9.8.1 and 3.0.0 (https://jira.nutanix.com/browse/CALM-18635)
        get_brownfield_vmware_vm_list(limit, offset, quiet, out, project)
