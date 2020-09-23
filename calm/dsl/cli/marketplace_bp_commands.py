import click

from .marketplace_commands_main import (
    marketplace_get,
    marketplace_describe,
    marketplace_launch,
    marketplace_decompile,
    marketplace_approve,
    marketplace_publish,
    marketplace_update,
    marketplace_delete,
    marketplace_reject,
    marketplace_unpublish,
    publish,
)
from .marketplace_bps import (
    get_marketplace_items,
    get_marketplace_bps,
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
    decompile_marketplace_bp,
)
from .constants import MARKETPLACE_BLUEPRINT

APP_STATES = [
    MARKETPLACE_BLUEPRINT.STATES.PENDING,
    MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
    MARKETPLACE_BLUEPRINT.STATES.REJECTED,
    MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_BLUEPRINT.SOURCES.GLOBAL,
    MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
]


@marketplace_get.command("items")
@click.option("--name", "-n", default=None, help="Filter by name of marketplace items")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only marketplace item names",
)
@click.option(
    "--app_family",
    "-f",
    default="All",
    help="Filter by app family category of marketplace item",
)
@click.option(
    "--display_all",
    "-d",
    is_flag=True,
    default=False,
    help="Show all marketplace blueprints which are published",
)
def _get_marketplace_items(name, quiet, app_family, display_all):
    """Get marketplace store blueprints"""

    get_marketplace_items(
        name=name, quiet=quiet, app_family=app_family, display_all=display_all
    )


# TODO Add limit and offset
@marketplace_get.command("bps")
@click.option(
    "--name", "-n", default=None, help="Filter by name of marketplace blueprints"
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only marketplace blueprint names",
)
@click.option(
    "--app_family",
    "-f",
    default="All",
    help="Filter by app family category of marketplace blueprints",
)
@click.option(
    "--app_state",
    "-a",
    "app_states",
    type=click.Choice(APP_STATES),
    multiple=True,
    help="filter by state of marketplace blueprints",
)
def _get_marketplace_bps(name, quiet, app_family, app_states):
    """Get marketplace manager blueprints"""

    get_marketplace_bps(
        name=name, quiet=quiet, app_family=app_family, app_states=app_states
    )


@marketplace_describe.command("item")
@click.argument("name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
@click.option("--version", "-v", default=None, help="Version of marketplace item")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for marketplace item",
)
def _describe_marketplace_item(name, out, version, source):
    """Describe a marketplace store item"""

    describe_marketplace_item(name=name, out=out, version=version, app_source=source)


@marketplace_describe.command("bp")
@click.argument("name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format.",
)
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of marketplace blueprint",
)
def _describe_marketplace_bp(name, out, version, source, app_state):
    """Describe a marketplace manager blueprint"""

    describe_marketplace_bp(
        name=name, out=out, version=version, app_source=source, app_state=app_state
    )


@marketplace_launch.command("bp")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
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
    help="Ignore runtime variables and use defaults for blueprint launch",
)
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
def _launch_marketplace_bp(
    name, version, project, app_name, profile_name, ignore_runtime_variables, source
):
    """Launch a marketplace manager blueprint"""

    launch_marketplace_bp(
        name=name,
        version=version,
        project=project,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        app_source=source,
    )


@marketplace_launch.command("item")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option("--project", "-pj", default=None, help="Project for the application")
@click.option("--app_name", "-a", default=None, help="Name of app")
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
    help="Ignore runtime variables and use defaults for blueprint launch",
)
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
def _launch_marketplace_item(
    name, version, project, app_name, profile_name, ignore_runtime_variables, source
):
    """Launch a marketplace store item"""

    launch_marketplace_item(
        name=name,
        version=version,
        project=project,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        app_source=source,
    )


@marketplace_decompile.command("bp", experimental=True)
@click.argument("mpi_name")
@click.option("--name", "-n", default=None, help="Name of blueprint")
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option("--project", "-p", default=None, help="Project for the blueprint")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Interactive Mode to provide the value for secrets",
)
def _decompile_marketplace_bp(mpi_name, version, project, name, source, with_secrets):
    """Decompiles marketplace manager blueprint"""

    decompile_marketplace_bp(
        name=mpi_name,
        version=version,
        project=project,
        bp_name=name,
        app_source=None,
        with_secrets=with_secrets,
    )


@publish.command("bp")
@click.argument("bp_name")
@click.option("--version", "-v", required=True, help="Version of marketplace blueprint")
@click.option("--name", "-n", default=None, help="Name of marketplace Blueprint")
@click.option(
    "--description", "-d", default="", help="Description for marketplace blueprint"
)
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
    "--publish_to_marketplace",
    "-pm",
    is_flag=True,
    default=False,
    help="Publish the blueprint directly to marketplace skipping the steps to approve, etc.",
)
@click.option(
    "--auto_approve",
    "-aa",
    is_flag=True,
    default=False,
    help="Auto approves the blueprint",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace blueprint (used for approving blueprint)",
)
@click.option(
    "--category",
    "-c",
    default=None,
    help="Category for marketplace blueprint (used for approving blueprint)",
)
@click.option(
    "--file",
    "-f",
    "icon_file",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of app icon image to be uploaded",
)
@click.option(
    "--icon_name", "-i", default=None, help="App icon name for marketpalce blueprint"
)
def publish_bp(
    bp_name,
    name,
    version,
    description,
    with_secrets,
    existing_markeplace_bp,
    publish_to_marketplace,
    projects=[],
    category=None,
    auto_approve=False,
    icon_name=False,
    icon_file=None,
):
    """Publish a blueprint to marketplace manager"""

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
            publish_to_marketplace=publish_to_marketplace,
            projects=projects,
            category=category,
            auto_approve=auto_approve,
            icon_name=icon_name,
            icon_file=icon_file,
        )

    else:
        publish_bp_as_existing_marketplace_bp(
            bp_name=bp_name,
            marketplace_bp_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
            publish_to_marketplace=publish_to_marketplace,
            projects=projects,
            category=category,
            auto_approve=auto_approve,
            icon_name=icon_name,
            icon_file=icon_file,
        )


@marketplace_approve.command("bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option(
    "--category", "-c", default=None, help="Category for marketplace blueprint"
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace blueprint",
)
def approve_bp(name, version, category, projects=[]):
    """Approves a marketplace manager blueprint"""

    approve_marketplace_bp(
        bp_name=name, version=version, projects=projects, category=category
    )


@marketplace_publish.command("bp")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option(
    "--category", "-c", default=None, help="Category for marketplace blueprint"
)
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for marketplace blueprint",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace blueprint",
)
def _publish_marketplace_bp(name, version, category, source, projects=[]):
    """Publish a marketplace blueprint to marketplace store"""

    publish_marketplace_bp(
        bp_name=name,
        version=version,
        projects=projects,
        category=category,
        app_source=source,
    )


@marketplace_update.command("bp")
@click.argument("name", nargs=1)
@click.option(
    "--version", "-v", required=True, help="Version of marketplace blueprint"
)  # Required to prevent unwanted update of published mpi
@click.option(
    "--category", "-c", default=None, help="Category for marketplace blueprint"
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace blueprint",
)
@click.option("--description", "-d", help="Description for marketplace blueprint")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for marketplace blueprint",
)
def _update_marketplace_bp(name, version, category, projects, description, source):
    """Update a marketplace manager blueprint"""

    update_marketplace_bp(
        name=name,
        version=version,
        category=category,
        projects=projects,
        description=description,
        app_source=source,
    )


@marketplace_delete.command("bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace blueprint"
)  # Required to prevent unwanted delete of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of marketplace blueprint",
)
def _delete_marketplace_bp(name, version, source, app_state):
    """Deletes marketplace manager blueprint"""

    delete_marketplace_bp(
        name=name, version=version, app_source=source, app_state=app_state
    )


@marketplace_reject.command("bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace blueprint"
)  # Required to prevent unwanted rejection of unknown mpi
def _reject_marketplace_bp(name, version):
    """Reject marketplace manager blueprint"""

    reject_marketplace_bp(name=name, version=version)


@marketplace_unpublish.command("bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace blueprint"
)  # Required to prevent unwanted unpublish of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace blueprint",
)
def _unpublish_marketplace_bp(name, version, source):
    """Unpublish marketplace store blueprint"""

    unpublish_marketplace_bp(name=name, version=version, app_source=source)
