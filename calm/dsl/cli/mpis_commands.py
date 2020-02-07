import click

from .main import get, describe, launch, publish, approve
from .mpis import (
    get_published_mpis,
    get_app_family_list,
    describe_mpi,
    launch_mpi,
    publish_bp_as_new_marketplace_bp,
    publish_bp_as_existing_marketplace_bp,
    approve_marketplace_bp,
    publish_marketplace_bp
)


def _get_app_family_list():
    """adds the 'All' option to categories"""

    categories = get_app_family_list()
    categories.append("All")
    return categories


@get.command("marketplace_bps")
@click.option("--name", "-n", default=None, help="Search for mpis by name")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only mpi names.")
@click.option(
    "--app_family",
    "-a",
    type=click.Choice(_get_app_family_list()),
    default="All",
    help="App Family Category for mpi",
)
@click.option(
    "--display_all",
    "-d",
    is_flag=True,
    default=False,
    help="Show all mpis with any version",
)
@click.pass_obj
def _get_mpis(obj, name, quiet, app_family, display_all):
    get_published_mpis(name, quiet, app_family, display_all)


@describe.command("marketplace_bp")
@click.argument("mpi_name")
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.pass_obj
def _describe_mpi(obj, mpi_name, version):
    """Describe a market place item"""

    describe_mpi(mpi_name, version)


@launch.command("marketplace_bp")
@click.argument("mpi_name")
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option("--project", "-pj", default=None, help="Project for the application")
@click.option("--app_name", "-a", default=None, help="Name of your app")
@click.option(
    "--profile_name",
    "-p",
    default=None,
    help="Name of app profile to be used for blueprint launch",
)
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults",
)
@click.pass_obj
def _launch_mpi(
    obj, mpi_name, version, project, app_name, profile_name, ignore_runtime_variables,
):
    """Launch a market place blueprint"""

    launch_mpi(
        mpi_name=mpi_name,
        version=version,
        project=project,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
    )


@publish.command("bp")
@click.argument("bp_name")
@click.option("--version", "-v", required=True, help="Version of MPI")
@click.option("--name", "-n", default=None, help="Name of Marketplace Blueprint")
@click.option("--description", "-d", default="", help="Description for the blueprint")
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Preserve secrets while publishing blueprints to marketpalce",
)
@click.option(
    "--existing_markeplace_bp",
    "-e",
    is_flag=True,
    default=False,
    help="Publish as new version of existing marketplace blueprint",
)
def publish_bp(
    bp_name, name, version, description, with_secrets, existing_markeplace_bp
):

    if not existing_markeplace_bp:
        publish_bp_as_new_marketplace_bp(
            bp_name=bp_name,
            marketplace_bp_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
        )

    else:
        publish_bp_as_existing_marketplace_bp(
            bp_name=bp_name,
            marketplace_bp_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
        )


@approve.command("bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option("--category", "-c", default=None, help="Category for the MPI")
@click.argument("projects", nargs=-1)
def approve_bp(name, version, category, projects=[]):

    approve_marketplace_bp(
        bp_name=name, version=version, projects=projects, category=category
    )


@publish.command("marketplace_bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option("--category", "-c", default=None, help="Category for the MPI")
@click.argument("projects", nargs=-1)
def _publish_marketplace_bp(name, version, category, projects=[]):

    publish_marketplace_bp(bp_name=name, version=version, category=category, projects=projects)
