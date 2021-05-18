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
    publish,
    marketplace_unpublish,
)
from .marketplace import (
    get_marketplace_items,
    describe_marketplace_item,
    launch_marketplace_bp,
    publish_bp_as_new_marketplace_bp,
    publish_bp_as_existing_marketplace_bp,
    approve_marketplace_item,
    publish_marketplace_item,
    update_marketplace_item,
    delete_marketplace_item,
    reject_marketplace_item,
    decompile_marketplace_bp,
    unpublish_marketplace_bp,
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
@click.option(
    "--filter",
    "filter_by",
    "-fb",
    default=None,
    help="Filter marketplace blueprints by this string",
)
def _get_marketplace_bps(name, quiet, app_family, app_states, filter_by):
    """Get marketplace manager blueprints"""

    get_marketplace_items(
        name=name,
        quiet=quiet,
        app_family=app_family,
        app_states=app_states,
        filter_by=filter_by,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )


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

    describe_marketplace_item(
        name=name, out=out, version=version, app_source=source, app_state=app_state
    )


@marketplace_launch.command("bp")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of marketplace blueprint")
@click.option("--project", "-pj", default=None, help="Project for the application")
@click.option(
    "--environment", "-e", default=None, help="Environment for the application"
)
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
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.option(
    "--poll-interval",
    "poll_interval",
    "-pi",
    type=int,
    default=10,
    show_default=True,
    help="Give polling interval",
)
@click.option(
    "--launch_params",
    "-l",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to python file for runtime editables",
)
def _launch_marketplace_bp(
    name,
    version,
    project,
    environment,
    app_name,
    profile_name,
    ignore_runtime_variables,
    source,
    launch_params,
    watch,
    poll_interval,
):
    """Launch a marketplace manager blueprint
    All runtime variables will be prompted by default. When passing the 'ignore_runtime_variables' flag, no variables will be prompted and all default values will be used.
    The marketplace-blueprint default values can be overridden by passing a Python file via 'launch_params'. Any variable not defined in the Python file will keep the default
    value defined in the blueprint. When passing a Python file, no variables will be prompted.

    \b
    Note: Dynamic variables will not have a default value. User have to select an option during launch.

    \b
    >: launch_params: Python file consisting of variables 'variable_list' and 'substrate_list'
    Ex: variable_list = [
            {
                "value": {"value": <Variable Value>},
                "context": <Context for variable>
                "name": "<Variable Name>"
            }
        ]
        substrate_list = [
            {
                "value":  {
                    <substrate_editable_data_object>
                },
                "name": <Substrate Name>,
            }
        ]
        deployment_list = [
            {
                "value":  {
                    <deployment_editable_data_object>
                },
                "name": <Deployment Name>,
            }
        ]
        credential_list = [
            {
                "value":  {
                    <credential_editable_data_object>
                },
                "name": <Credential Name>,
            }
        ]
    Sample context for variables:
        1. context = "<Profile Name>"    # For variable under profile
        2. context = "<Service Name>"    # For variable under service
    """

    launch_marketplace_bp(
        name=name,
        version=version,
        project=project,
        environment=environment,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        app_source=source,
        launch_params=launch_params,
        watch=watch,
        poll_interval=poll_interval,
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
@click.option(
    "--dir",
    "-d",
    "bp_dir",
    default=None,
    help="Blueprint directory location used for placing decompiled entities",
)
def _decompile_marketplace_bp(
    mpi_name, version, project, name, source, with_secrets, bp_dir
):
    """Decompiles marketplace manager blueprint


    \b
    Sample command examples:
    i.) calm decompile marketplace bp "Jenkins" : Command will decompile marketplace blueprint "Jenkins" having latest version
    ii.) calm decompile marketplace bp "Jenkins" --version "1.0.0": Command will decompile marketplace blueprint "Jenkins" having "1.0.0" version
    iii.) calm decompile marketplace bp "Jenkins" --name "DSL_JENKINS_BLUEPRINT": Command will decompile marketplace bp "Jenkins" to DSL blueprint having name "DSL_JENKINS_BLUEPRINT" (see the name of blueprint class in decompiled blueprint.py file)"""

    decompile_marketplace_bp(
        name=mpi_name,
        version=version,
        project=project,
        bp_name=name,
        app_source=None,
        with_secrets=with_secrets,
        bp_dir=bp_dir,
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
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Publishes bp to all projects",
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
    all_projects=False,
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
            all_projects=all_projects,
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
            all_projects=all_projects,
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
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve bp to all projects",
)
def approve_bp(name, version, category, all_projects, projects=[]):
    """Approves a marketplace manager blueprint"""

    approve_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
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
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve bp to all projects",
)
def _publish_marketplace_bp(name, version, category, source, all_projects, projects=[]):
    """Publish a marketplace blueprint to marketplace store"""

    publish_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        app_source=source,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
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

    update_marketplace_item(
        name=name,
        version=version,
        category=category,
        projects=projects,
        description=description,
        app_source=source,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
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

    delete_marketplace_item(
        name=name,
        version=version,
        app_source=source,
        app_state=app_state,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )


@marketplace_reject.command("bp")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of marketplace blueprint"
)  # Required to prevent unwanted rejection of unknown mpi
def _reject_marketplace_bp(name, version):
    """Reject marketplace manager blueprint"""

    reject_marketplace_item(
        name=name, version=version, type=MARKETPLACE_ITEM.TYPES.BLUEPRINT
    )


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
