import click

from .main import get
from .brownfield_vms import get_brownfield_vms
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
@click.option("--account", "-a", help="Account name", default=None)
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
def _get_vm_list(limit, offset, quiet, out, project, provider_type, account):
    """
    Get brownfield vms

    \b
    >: If there are multiple accounts per provider_type in project, user need to supply the account name
       other than provider type (added in 3.2.0)

    """

    get_brownfield_vms(limit, offset, quiet, out, project, provider_type, account)
