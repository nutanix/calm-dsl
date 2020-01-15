import json
import click

from calm.dsl.api import get_api_client

from .utils import highlight_text
from .main import get, describe
from .mpis import  get_published_mpis, get_app_family_list, describe_mpi


def _get_app_family_list():
    """adds the 'All' option to categories"""

    categories = get_app_family_list()
    categories.append("All")
    return categories

@get.command("mpis")
@click.option("--name", "-n", default=None, help="Search for mpis by name")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only mpi names."
)
@click.option(
    "--app_family",
    "-a",
    type=click.Choice(_get_app_family_list()),
    default="All",
    help="App Family Category for mpi",
)
@click.option(
    "--display_all", "-d", is_flag=True, default=False, help="Show all mpis with any version"
)
@click.pass_obj
def _get_mpis(obj, name, quiet, app_family, display_all):
    get_published_mpis(name, quiet, app_family, display_all)


@describe.command("mpi")
@click.argument("mpi_name")
@click.option("version", "-v", required=True, help="Version of MPI")
@click.pass_obj
def _describe_mpi(obj, mpi_name, version):
    """Describe a market place item"""

    # TODO Add default version
    describe_mpi(mpi_name, version)
