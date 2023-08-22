import json
import time
import sys
import click

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

from .utils import Display, _get_nested_messages
from .main import get, compile, describe, create, launch, delete, decompile, format
from .bps import (
    get_blueprint_list,
    describe_bp,
    format_blueprint_command,
    compile_blueprint_command,
    launch_blueprint_simple,
    patch_bp_if_required,
    delete_blueprint,
    decompile_bp,
    create_blueprint_from_json,
    create_blueprint_from_dsl,
    create_blueprint_from_dsl_with_encrypted_secrets,
)
from .apps import watch_app
from .utils import FeatureDslOption

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
@click.option(
    "--passphrase",
    "-ps",
    "passphrase",
    default=None,
    required=False,
    help="Passphrase to import secrets",
)
@click.option(
    "--prefix",
    "-p",
    default="",
    help="Prefix used for appending to entities name(Reserved name cases)",
)
@click.option(
    "--dir",
    "-d",
    "bp_dir",
    default=None,
    help="Blueprint directory location used for placing decompiled entities",
)
def _decompile_bp(name, bp_file, with_secrets, prefix, bp_dir, passphrase):
    """Decompiles blueprint present on server or json file"""

    decompile_bp(name, bp_file, with_secrets, prefix, bp_dir, passphrase)


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
@click.option(
    "--passphrase",
    "-ps",
    "passphrase",
    default=None,
    help="Passphrase for the encrypted secret values in blueprint",
)
def create_blueprint_command(bp_file, name, description, force, passphrase):
    """Creates a blueprint"""

    client = get_api_client()

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description, force_create=force
        )
    elif bp_file.endswith(".py"):
        if passphrase:
            res, err = create_blueprint_from_dsl_with_encrypted_secrets(
                client,
                bp_file,
                passphrase,
                name=name,
                description=description,
                force_create=force,
            )
        else:
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
        msg_list = []
        _get_nested_messages("", bp_status, msg_list)

        if not msg_list:
            LOG.error("Blueprint {} created with errors.".format(bp_name))
            LOG.debug(json.dumps(bp_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msg = ""
            path = msg_dict.get("path", "")
            if path:
                msg = path + ": "
            msgs.append(msg + msg_dict.get("message", ""))

        LOG.error(
            "Blueprint {} created with {} error(s):".format(bp_name, len(msg_list))
        )
        click.echo("\n".join(msgs))
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
@click.option(
    "--with_secrets",
    "-ws",
    is_flag=True,
    default=False,
    help="Preserve secrets while launching the blueprint",
)
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
@click.option(
    "--brownfield_deployments",
    "-b",
    "brownfield_deployment_file",
    type=FeatureDslOption(feature_min_version="3.3.0"),
    help="Path of Brownfield Deployment file (Added in 3.3)",
)
def launch_blueprint_command(
    blueprint_name,
    environment,
    with_secrets,
    app_name,
    ignore_runtime_variables,
    profile_name,
    launch_params,
    watch,
    poll_interval,
    blueprint=None,
    brownfield_deployment_file=None,
):
    """Launches a blueprint.
    All runtime variables will be prompted by default. When passing the 'ignore_runtime_variables' flag, no variables will be prompted and all default values will be used.
    The blueprint default values can be overridden by passing a Python file via 'launch_params'. Any variable not defined in the Python file will keep the default value defined in the blueprint. When passing a Python file, no variables will be prompted.

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
        snapshot_config_list = [
            {
                "value":  {
                    "attrs_list": [
                        <attrs_list_editables>
                    ]
                },
                "name": <Snapshot Config Name>,
            }
        ]
    Sample context for variables:
        1. context = "<Profile Name>"    # For variable under profile
        2. context = "<Service Name>"    # For variable under service

    \b
    >: brownfield_deployments: Python file containing brownfield deployments
    """

    app_name = app_name or "App-{}-{}".format(blueprint_name, int(time.time()))
    blueprint_name, blueprint = patch_bp_if_required(
        with_secrets, environment, blueprint_name, profile_name
    )

    launch_blueprint_simple(
        blueprint_name,
        app_name,
        blueprint=blueprint,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
        launch_params=launch_params,
        brownfield_deployment_file=brownfield_deployment_file,
    )
    if watch:

        def display_action(screen):
            watch_app(app_name, screen, poll_interval=poll_interval)
            screen.wait_for_input(10.0)

        Display.wrapper(display_action, watch=True)
        LOG.info("Action runs completed for app {}".format(app_name))


@delete.command("bp")
@click.argument("blueprint_names", nargs=-1)
def _delete_blueprint(blueprint_names):
    """Deletes a blueprint"""

    delete_blueprint(blueprint_names)
