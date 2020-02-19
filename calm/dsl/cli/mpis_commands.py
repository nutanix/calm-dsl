import click

from .main import (
    get,
    describe,
    launch,
    publish,
    approve,
    update,
    delete,
    reject,
    unpublish,
)
from .mpis import (
    get_marketplace_items,
    get_marketplace_bps,
    get_app_family_list,
    describe_marketplace_item,
    describe_marketplace_bp,
    launch_marketplace_item,
    launch_marketplace_bp,
    publish_bp_as_new_marketplace_bp,
    publish_bp_as_existing_marketplace_bp,
    approve_marketplace_bp,
    publish_marketplace_bp,
    update_marketplace_bp,
    delete_marketplace_bp,
    reject_marketplace_bp,
    unpublish_marketplace_bp,
)


def _get_app_family_list():
    """adds the 'All' option to categories"""

    categories = get_app_family_list()
    categories.append("All")
    return categories


@get.command("marketplace_items")
@click.option("--name", "-n", default=None, help="Search for mpis by name")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only mpi names")
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
def _get_marketplace_items(obj, name, quiet, app_family, display_all):
    """ List the marketplace items in marketplace"""

    get_marketplace_items(
        name=name, quiet=quiet, app_family=app_family, display_all=display_all
    )


# TODO Add limit and offset
@get.command("marketplace_bps")
@click.option("--name", "-n", default=None, help="Search for mpis by name")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only mpi names")
@click.option(
    "--app_family",
    "-f",
    type=click.Choice(_get_app_family_list()),
    default="All",
    help="App Family Category for mpi",
)
@click.option("--app_state", "-a", "app_states", multiple=True)
@click.pass_obj
def _get_marketplace_bps(obj, name, quiet, app_family, app_states):
    """ List the marketplace blueprints in marketplace manager"""

    get_marketplace_bps(
        name=name, quiet=quiet, app_family=app_family, app_states=app_states
    )


@describe.command("marketplace_item")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.pass_obj
def _describe_marketplace_item(obj, name, version, source):
    """Describe a market place item"""

    describe_marketplace_item(name=name, version=version, app_source=source)


@describe.command("marketplace_bp")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.option("--app_state", "-a", default=None, help="State of marketplace blueprint")
@click.pass_obj
def _describe_marketplace_bp(obj, name, version, source, app_state):
    """
        Describe a market place blueprint
        Two mpi with same name and version can exists if one of them is in REJECTED state
    """

    describe_marketplace_bp(
        name=name, version=version, app_source=source, app_state=app_state
    )


@launch.command("marketplace_bp")
@click.argument("name")
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
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.pass_obj
def _launch_marketplace_bp(
    obj,
    name,
    version,
    project,
    app_name,
    profile_name,
    ignore_runtime_variables,
    source,
):
    """Launch a marketplace blueprint"""

    launch_marketplace_bp(
        name=name,
        version=version,
        project=project,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        app_source=source,
    )


@launch.command("marketplace_item")
@click.argument("name")
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
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.pass_obj
def _launch_marketplace_item(
    obj,
    name,
    version,
    project,
    app_name,
    profile_name,
    ignore_runtime_variables,
    source,
):
    """Launch a marketplace item"""

    launch_marketplace_item(
        name=name,
        version=version,
        project=project,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        app_source=source,
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
@click.option(
    "--force_publish",
    "-f",
    is_flag=True,
    default=False,
    help="Publish the blueprint directly to marketplace skipping the steps to approve, etc.",
)
@click.option("--project", "-p", "projects", multiple=True)
@click.option("--category", "-c", default=None, help="Category for the MPI")
def publish_bp(
    bp_name,
    name,
    version,
    description,
    with_secrets,
    existing_markeplace_bp,
    force_publish,
    projects=[],
    category=None,
):
    """Publish a blueprint to marketplace manager(Pending Approval blueprints)"""

    if not name:
        # Using blueprint name as the marketplace bp name if no name provided
        name = bp_name

    if not existing_markeplace_bp:
        publish_bp_as_new_marketplace_bp(
            bp_name=bp_name,
            marketplace_bp_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
            force_publish=force_publish,
            projects=projects,
            category=category,
        )

    else:
        publish_bp_as_existing_marketplace_bp(
            bp_name=bp_name,
            marketplace_bp_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
            force_publish=force_publish,
            projects=projects,
            category=category,
        )


@approve.command("marketplace_bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option("--category", "-c", default=None, help="Category for the MPI")
@click.option("--project", "-p", "projects", multiple=True)
def approve_bp(name, version, category, projects=[]):
    """Approves a marketplace manager blueprint"""

    approve_marketplace_bp(
        bp_name=name, version=version, projects=projects, category=category
    )


@publish.command("marketplace_bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of MPI")
@click.option("--category", "-c", default=None, help="Category for the MPI")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.option("--project", "-p", "projects", multiple=True)
def _publish_marketplace_bp(name, version, category, source, projects=[]):
    """Publish a marketplace manager blueprint to marketplace"""

    publish_marketplace_bp(
        bp_name=name,
        version=version,
        projects=projects,
        category=category,
        app_source=source,
    )


@update.command("marketplace_bp")
@click.argument("name", nargs=1)
@click.option(
    "--version", "-v", required=True, help="Version of MPI"
)  # Required to provide unwanted update of published mpi
@click.option("--category", "-c", default=None, help="Category for MPI")
@click.option("--project", "-p", "projects", multiple=True)
@click.option("--description", "-d", help="Description for MPI")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
def _update_marketplace_bp(name, version, category, projects, description, source):
    """Update a marketplace_manager blueprint"""

    update_marketplace_bp(
        name=name,
        version=version,
        category=category,
        projects=projects,
        description=description,
        app_source=source,
    )


@delete.command("marketplace_bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of MPI"
)  # Required to provide unwanted delete of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
@click.option("--app_state", "-a", default=None, help="State of marketplace blueprint")
def _delete_marketplace_bp(name, version, source, app_state):
    """Delete marketplace manager blueprint"""

    delete_marketplace_bp(
        name=name, version=version, app_source=source, app_state=app_state
    )


@reject.command("marketplace_bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of MPI"
)  # Required to provide unwanted rejection of unknown mpi
def _reject_marketplace_bp(name, version):
    """Reject marketplace manager blueprint"""

    reject_marketplace_bp(name=name, version=version)


@unpublish.command("marketplace_bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of MPI"
)  # Required to provide unwanted unpublish of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(["GLOBAL_STORE", "LOCAL"]),
    help="App Source for blueprint",
)
def _unpublish_marketplace_bp(name, version, source):
    """Unpublish marketplace blueprint to marketplace manager blueprint"""

    unpublish_marketplace_bp(name=name, version=version, app_source=source)
