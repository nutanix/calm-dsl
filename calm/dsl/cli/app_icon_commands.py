import click

from .main import create, delete, get
from .app_icons import create_app_icon, delete_app_icon, get_app_icon_list


@create.command("app_icon")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to upload",
)
@click.option("--name", "-n", default=None, help="icon name")
def _create_app_icon(file, name):
    """Creates a marketplace app icon"""

    create_app_icon(name, file)


@delete.command("app_icon")
@click.argument("icon_names", nargs=-1)
def _delete_app_icon(icon_names):
    """Deletes a marketplace app icon"""

    delete_app_icon(icon_names)


@get.command("app_icons")
@click.option("--name", "-n", default=None, help="Search for app icons by name")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only app icon names."
)
@click.option(
    "--marketplace_use",
    "-m",
    is_flag=True,
    default=False,
    help="Show whether used for marketplace icon or not",
)
def _get_app_icon_list(name, limit, offset, quiet, marketplace_use):
    """Get the list of app_icons"""

    get_app_icon_list(name, limit, offset, quiet, marketplace_use)
