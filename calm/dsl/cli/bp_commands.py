import json
import time
import sys
import click

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

from .secrets import find_secret, create_secret
from .utils import Display, highlight_text
from .main import get, compile, describe, create, launch, delete, decompile, format
from .bps import (
    get_blueprint_list,
    describe_bp,
    format_blueprint_command,
    compile_blueprint_command,
    compile_blueprint,
    launch_blueprint_simple,
    delete_blueprint,
    decompile_bp,
    create_blueprint_from_json,
    create_blueprint_from_dsl,
)
from .apps import watch_app

LOG = get_logging_handle(__name__)


@get.command("bps")
@click.option("--name", "-n", default=None, help="Search for blueprints by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter blueprints by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_blueprint_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the blueprints, optionally filtered by a string"""

    get_blueprint_list(name, filter_by, limit, offset, quiet, all_items, out)


@describe.command("bp")
@click.argument("bp_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_bp(bp_name, out):
    """Describe a blueprint"""

    describe_bp(bp_name, out)


@format.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to format",
)
def _format_blueprint_command(bp_file):
    """Formats blueprint file using black"""

    format_blueprint_command(bp_file)


@compile.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to upload",
)
@click.option(
    "--brownfield_deployments",
    "-b",
    "brownfield_deployment_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Brownfield Deployment file",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_blueprint_command(bp_file, brownfield_deployment_file, out):
    """Compiles a DSL (Python) blueprint into JSON or YAML"""
    compile_blueprint_command(bp_file, brownfield_deployment_file, out)


@decompile.command("bp", experimental=True)
@click.argument("name", required=False)
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to Blueprint file",
)
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Interactive Mode to provide the value for secrets",
)
def _decompile_bp(name, bp_file, with_secrets):
    """Decompiles blueprint present on server or json file"""

    decompile_bp(name, bp_file, with_secrets)


@create.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to upload",
)
@click.option("--name", "-n", default=None, help="Blueprint name (Optional)")
@click.option(
    "--description", "-d", default=None, help="Blueprint description (Optional)"
)
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing blueprint with the same name before create.",
)
def create_blueprint_command(bp_file, name, description, force):
    """Creates a blueprint"""

    client = get_api_client()

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description, force_create=force
        )
    elif bp_file.endswith(".py"):
        res, err = create_blueprint_from_dsl(
            client, bp_file, name=name, description=description, force_create=force
        )
    else:
        LOG.error("Unknown file format {}".format(bp_file))
        return

    if err:
        LOG.error(err["error"])
        return

    bp = res.json()
    bp_uuid = bp["metadata"]["uuid"]
    bp_name = bp["metadata"]["name"]
    bp_status = bp.get("status", {})
    bp_state = bp_status.get("state", "DRAFT")
    LOG.debug("Blueprint {} has state: {}".format(bp_name, bp_state))

    if bp_state != "ACTIVE":
        msg_list = bp_status.get("message_list", [])
        if not msg_list:
            LOG.error("Blueprint {} created with errors.".format(bp_name))
            LOG.debug(json.dumps(bp_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Blueprint {} created with {} error(s): {}".format(
                bp_name, len(msg_list), msgs
            )
        )
        sys.exit(-1)

    LOG.info("Blueprint {} created successfully.".format(bp_name))

    context = get_context()
    server_config = context.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/blueprints/{}".format(
        pc_ip, pc_port, bp_uuid
    )
    stdout_dict = {"name": bp_name, "link": link, "state": bp_state}
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


@launch.command("bp")
@click.argument("blueprint_name")
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
    "--launch_params",
    "-l",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to python file for runtime editables",
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
def launch_blueprint_command(
    blueprint_name,
    app_name,
    ignore_runtime_variables,
    profile_name,
    launch_params,
    watch,
    poll_interval,
    blueprint=None,
):
    """Launches a blueprint.
    All runtime variables will be prompted by default. When passing the 'ignore_runtime_editable' flag, no variables will be prompted and all default values will be used.
    The blueprint default values can be overridden by passing a Python file via 'launch_params'. Any variable not defined in the Python file will keep the default value defined in the blueprint. When passing a Python file, no variables will be prompted.

    \b
    >: launch_params: Python file consisting of variables 'variable_list' and 'substrate_list'
    Ex: variable_list = {
        "value": {"value": <Variable Value>},
        "context": <Context for variable>
        "name": "<Variable Name>"
    }
    substrate_list = {
        "value":  {
            <substrate_editable_data_object>
        },
        "name": <Substrate Name>,
    }
    Sample context for variables:
        1. context = "<Profile Name>"    # For variable under profile
        2. context = "<Service Name>"    # For variable under service"""

    app_name = app_name or "App-{}-{}".format(blueprint_name, int(time.time()))
    launch_blueprint_simple(
        blueprint_name,
        app_name,
        blueprint=blueprint,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        launch_params=launch_params,
    )
    if watch:

        def display_action(screen):
            watch_app(app_name, screen)
            screen.wait_for_input(10.0)

        Display.wrapper(display_action, watch=True)
        LOG.info("Action runs completed for app {}".format(app_name))


@delete.command("bp")
@click.argument("blueprint_names", nargs=-1)
def _delete_blueprint(blueprint_names):
    """Deletes a blueprint"""

    delete_blueprint(blueprint_names)
