import click

from .marketplace_commands_main import (
    marketplace_get,
    marketplace_describe,
    marketplace_launch,
    marketplace_run,
    marketplace_unpublish
)
from .marketplace import (
    get_marketplace_store_items,
    unpublish_marketplace_item,
    describe_marketplace_store_item,
    execute_marketplace_runbook,
    launch_marketplace_item
)
from .constants import MARKETPLACE_ITEM

APP_SOURCES = [
    MARKETPLACE_ITEM.SOURCES.GLOBAL,
    MARKETPLACE_ITEM.SOURCES.LOCAL,
]


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

    describe_marketplace_store_item(name=name, out=out, version=version, app_source=source)


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
@click.option(
    "--filter",
    "filter_by",
    "-fb",
    default=None,
    help="Filter marketplace items by this string",
)
def _get_marketplace_items(name, quiet, app_family, display_all, filter_by):
    """Get marketplace store items"""

    get_marketplace_store_items(
        name=name, quiet=quiet,
        app_family=app_family,
        display_all=display_all,
        filter_by=filter_by,
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


@marketplace_run.command("item")
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
def _run_marketplace_item(
    name, version, project, source, ignore_runtime_variables, watch
):
    """Execute a marketplace item of type runbook"""

    execute_marketplace_runbook(
        name=name,
        version=version,
        project=project,
        app_source=source,
        watch=watch,
        app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
        ignore_runtime_variables=ignore_runtime_variables
    )


@marketplace_unpublish.command("item")
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

    unpublish_marketplace_item(
        name=name,
        version=version,
        app_source=source,
    )
