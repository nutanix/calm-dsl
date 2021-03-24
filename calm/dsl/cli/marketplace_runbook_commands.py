import click

from .marketplace_commands_main import (
    marketplace_get,
    marketplace_describe,
    marketplace_approve,
    marketplace_publish,
    marketplace_update,
    marketplace_delete,
    marketplace_reject,
    marketplace_run,
    publish,
)
from .marketplace import (
    get_marketplace_items,
    describe_marketplace_item,
    publish_runbook_as_new_marketplace_item,
    publish_runbook_as_existing_marketplace_item,
    approve_marketplace_item,
    publish_marketplace_item,
    update_marketplace_item,
    delete_marketplace_item,
    reject_marketplace_item,
    execute_marketplace_runbook,
)
from .constants import MARKETPLACE_ITEM

APP_STATES = [
    MARKETPLACE_ITEM.STATES.PENDING,
    MARKETPLACE_ITEM.STATES.ACCEPTED,
    MARKETPLACE_ITEM.STATES.REJECTED,
    MARKETPLACE_ITEM.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_ITEM.SOURCES.GLOBAL,
    MARKETPLACE_ITEM.SOURCES.LOCAL,
]


# TODO Add limit and offset
@marketplace_get.command("runbooks", feature_min_version="3.2.0")
@click.option(
    "--name", "-n", default=None, help="Filter by name of marketplace runbooks"
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only marketplace runbooks names",
)
@click.option(
    "--app_family",
    "-f",
    default="All",
    help="Filter by app family category of marketplace runbooks",
)
@click.option(
    "--app_state",
    "-a",
    "app_states",
    type=click.Choice(APP_STATES),
    multiple=True,
    help="filter by state of marketplace runbooks",
)
@click.option(
    "--filter",
    "filter_by",
    "-fb",
    default=None,
    help="Filter marketplace runbooks by this string",
)
def _get_marketplace_runbooks(name, quiet, app_family, app_states, filter_by):
    """Get marketplace manager runbooks"""

    get_marketplace_items(
        name=name,
        quiet=quiet,
        app_family=app_family,
        app_states=app_states,
        filter_by=filter_by,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_describe.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format.",
)
@click.option("--version", "-v", default=None, help="Version of marketplace runbooks")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace runbook",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of marketplace runbook",
)
def _describe_marketplace_runbook(name, out, version, source, app_state):
    """Describe a marketplace manager runbook"""

    describe_marketplace_item(
        name=name, out=out, version=version, app_source=source, app_state=app_state
    )


@marketplace_approve.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of marketplace runbook")
@click.option("--category", "-c", default=None, help="Category for marketplace runbook")
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace runbook",
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve runbook to all runbook",
)
def approve_runbook(name, version, category, all_projects, projects=[]):
    """Approves a marketplace manager runbook"""

    approve_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_publish.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of marketplace runbook")
@click.option("--category", "-c", default=None, help="Category for marketplace runbook")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for marketplace runbook",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace runbook",
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve runbook to all projects",
)
def _publish_marketplace_runbook(
    name, version, category, source, all_projects, projects=[]
):
    """Publish a marketplace runbook to marketplace store"""

    publish_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        app_source=source,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_update.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option(
    "--version", "-v", required=True, help="Version of marketplace runbook"
)  # Required to prevent unwanted update of published mpi
@click.option("--category", "-c", default=None, help="Category for marketplace runbook")
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace runbook",
)
@click.option("--description", "-d", help="Description for marketplace runbook")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for marketplace runbook",
)
def _update_marketplace_runbook(name, version, category, projects, description, source):
    """Update a marketplace manager runbook"""

    update_marketplace_item(
        name=name,
        version=version,
        category=category,
        projects=projects,
        description=description,
        app_source=source,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_delete.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace runbook"
)  # Required to prevent unwanted delete of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace runbook",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of marketplace runbook",
)
def _delete_marketplace_runbook(name, version, source, app_state):
    """Deletes marketplace manager runbook"""

    delete_marketplace_item(
        name=name,
        version=version,
        app_source=source,
        app_state=app_state,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_reject.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace runbook"
)  # Required to prevent unwanted rejection of unknown mpi
def _reject_marketplace_runbook(name, version):
    """Reject marketplace manager runbook"""

    reject_marketplace_item(
        name=name, version=version, type=MARKETPLACE_ITEM.TYPES.RUNBOOK
    )


@publish.command("runbook", feature_min_version="3.2.0")
@click.argument("runbook_name")
@click.option("--version", "-v", required=True, help="Version of marketplace runbook")
@click.option("--name", "-n", default=None, help="Name of marketplace runbook")
@click.option(
    "--description", "-d", default="", help="Description for marketplace runbook"
)
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Preserve secrets while publishing runbooks to marketplace",
)
@click.option(
    "--with_endpoints",
    "-w",
    is_flag=True,
    default=False,
    help="Preserve endpoints publishing runbooks to marketplace",
)
@click.option(
    "--existing_markeplace_runbook",
    "-e",
    is_flag=True,
    default=False,
    help="Publish as new version of existing marketplace runbook",
)
@click.option(
    "--publish_to_marketplace",
    "-pm",
    is_flag=True,
    default=False,
    help="Publish the runbook directly to marketplace skipping the steps to approve, etc.",
)
@click.option(
    "--auto_approve",
    "-aa",
    is_flag=True,
    default=False,
    help="Auto approves the runbook",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for marketplace runbook (used for approving runbook)",
)
@click.option(
    "--category",
    "-c",
    default=None,
    help="Category for marketplace runbook (used for approving runbook)",
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
    "--icon_name", "-i", default=None, help="App icon name for marketplace runbook"
)
def publish_runbook(
    runbook_name,
    name,
    version,
    description,
    with_secrets,
    with_endpoints,
    existing_markeplace_runbook,
    publish_to_marketplace,
    projects=[],
    category=None,
    auto_approve=False,
    icon_name=False,
    icon_file=None,
):
    """Publish a runbook to marketplace manager"""

    if not name:
        # Using runbook name as the marketplace runbook name if no name provided
        name = runbook_name

    if not existing_markeplace_runbook:
        publish_runbook_as_new_marketplace_item(
            runbook_name=runbook_name,
            marketplace_item_name=name,
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
        publish_runbook_as_existing_marketplace_item(
            runbook_name=runbook_name,
            marketplace_item_name=name,
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


@marketplace_run.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of marketplace item")
@click.option("--project", "-pj", default=None, help="Project for the execution")
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults for runbook execution",
)
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of marketplace item",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
def _run_marketplace_runbook(
    name, version, project, source, ignore_runtime_variables, watch
):
    """Execute a marketplace item of type runbook"""

    execute_marketplace_runbook(
        name=name,
        version=version,
        project_name=project,
        app_source=source,
        watch=watch,
        ignore_runtime_variables=ignore_runtime_variables,
    )
