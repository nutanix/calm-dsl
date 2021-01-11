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
from calm.dsl.constants import VM
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
    type=click.Choice(
        [
            VM.AHV,
            VM.AWS,
            VM.AZURE,
            VM.GCP,
            VM.VMWARE,
        ]
    ),
    default=VM.AHV,
    help="Provider type",
)
def _get_vm_list(limit, offset, quiet, out, project, provider_type):
    """Get the brownfield vms, optionally filtered by a string"""

    if provider_type == VM.AHV:
        get_brownfield_ahv_vm_list(limit, offset, quiet, out, project)
    elif provider_type == VM.AWS:
        get_brownfield_aws_vm_list(limit, offset, quiet, out, project)
    elif provider_type == VM.AZURE:
        get_brownfield_azure_vm_list(limit, offset, quiet, out, project)
    elif provider_type == VM.GCP:
        get_brownfield_gcp_vm_list(limit, offset, quiet, out, project)
    elif provider_type == VM.VMWARE:
        # Has issue with it. Fixed in 2.9.8.1 and 3.0.0 (https://jira.nutanix.com/browse/CALM-18635)
        get_brownfield_vmware_vm_list(limit, offset, quiet, out, project)
