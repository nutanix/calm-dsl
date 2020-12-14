import click

from .accounts import (
    get_accounts,
    delete_account,
    describe_account,
    compile_account_command,
    create_account,
)
from .main import get, delete, describe, create, compile


@get.command("accounts")
@click.option("--name", "-n", default=None, help="Search for provider account by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter projects by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
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
def _get_accounts(name, filter_by, limit, offset, quiet, all_items, account_type):
    """Get accounts, optionally filtered by a string"""

    get_accounts(name, filter_by, limit, offset, quiet, all_items, account_type)


@delete.command("account")
@click.argument("account_names", nargs=-1)
def _delete_account(account_names):
    """Deletes a account from settings"""

    delete_account(account_names)


@describe.command("account")
@click.argument("account_name")
def _describe_account(account_name):
    """Describe a account"""

    describe_account(account_name)


@create.command("account")
@click.option(
    "--file",
    "-f",
    "account_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path to Account file",
)
@click.option("--name", "-n", default=None, help="Account name (Optional)")
def _create_account(account_file, name):
    """Creates an account"""

    create_account(account_file, name)


@compile.command("account")
@click.option(
    "--file",
    "-f",
    "account_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path to Account file",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_account(account_file, out):
    """Creates an account"""

    compile_account_command(account_file, out)
