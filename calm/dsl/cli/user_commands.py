import click

from .users import get_users, create_user, delete_user
from .main import get, create, delete


@get.command("users")
@click.option("--name", "-n", default=None, help="Search for users by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter users by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only user names")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_users(name, filter_by, limit, offset, quiet, out):
    """Get users, optionally filtered by a string"""

    get_users(name, filter_by, limit, offset, quiet, out)


@create.command("user")
@click.option("--name", "-n", required=True, help="Principal Name of user")
@click.option(
    "--directory",
    "-d",
    "directory_service",
    required=True,
    help="Directory Service of user",
)
def _create_user(name, directory_service):
    """Creates a user"""

    create_user(name, directory_service)


@delete.command("user")
@click.argument("user_names", nargs=-1)
def _delete_user(user_names):
    """Deletes a user"""

    delete_user(user_names)
