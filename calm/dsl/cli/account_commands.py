import click

from .accounts import get_accounts, delete_account, describe_account
from .main import get, delete, describe


@get.command("accounts")
@click.option("--name", default=None, help="Search for provider account by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter projects by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only account names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--type",
    "account_type",
    default=None,
    multiple=True,
    help="Search for accounts of specific provider",
    type=click.Choice(["aws", "k8s", "vmware", "azure", "gcp", "nutanix"]),
)
@click.pass_obj
def _get_accounts(
    obj, name, filter_by, limit, offset, quiet, all_items, account_type
):
    """Get accounts, optionally filtered by a string"""
    get_accounts(
        obj, name, filter_by, limit, offset, quiet, all_items, account_type
    )


@delete.command("account")
@click.argument("account_names", nargs=-1)
@click.pass_obj
def _delete_account(obj, account_names):
    """Deletes a account from settings"""

    delete_account(obj, account_names)


@describe.command("account")
@click.argument("account_name")
@click.pass_obj
def _describe_account(obj, account_name):
    """Describe a account"""

    describe_account(obj, account_name)
