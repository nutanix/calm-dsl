import click
import json

from .main import get
from prettytable import PrettyTable
from .utils import get_account_details, highlight_text

from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("vm-recovery-points")
@click.option(
    "--name", "-n", default=None, help="Search for vm recovery points by name"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only recovery point names."
)
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
def _get_vm_list(name, limit, offset, quiet, out, project, account):
    """
    Get vm recovery points

    \b
    >: If there are multiple accounts per provider_type in project, user need to supply the account name
       other than provider type (added in 3.2.0)
    >: Available for ahv provider only

    """

    get_vm_recovery_points(name, limit, offset, quiet, out, project, account)


def get_vm_recovery_points(name, limit, offset, quiet, out, project_name, account_name):
    """displays vm recovery points for a account"""

    client = get_api_client()
    account_detail = get_account_details(
        project_name=project_name, account_name=account_name, provider_type="AHV_VM"
    )

    account_name = account_detail["account"]["name"]
    account_uuid = account_detail["account"]["uuid"]

    account_uuid = account_detail["account"]["uuid"]
    LOG.info("Using account '{}' for listing brownfield vms".format(account_name))

    payload = {
        "filter": "account_uuid=={}".format(account_uuid),
        "length": limit,
        "offset": offset,
    }
    if name:
        payload["filter"] += ";name=={}".format(name)

    res, err = client.vm_recovery_point.list(payload)
    if err:
        LOG.warning(
            "Cannot fetch vm recovery points from account {}".format(account_name)
        )
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No vm recovery point found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "UUID", "STATE", "TYPE", "PARENT_VM_REF"]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(metadata["uuid"]),
                highlight_text(row["state"]),
                highlight_text(row["resources"]["recovery_point_type"]),
                highlight_text(row["resources"]["parent_vm_reference"]["uuid"]),
            ]
        )
    click.echo(table)
