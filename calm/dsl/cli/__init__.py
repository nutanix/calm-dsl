import json

import click
from calm.dsl.tools import ping

from .config import get_api_client, set_config
from .apps import get_apps, describe_app, delete_app, run_actions, watch_app
from .bps import (
    get_blueprint_list,
    compile_blueprint_command,
    compile_blueprint,
    launch_blueprint_simple,
    delete_blueprint,
)


@click.group()
@click.pass_context
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("0.1")
def main(ctx, verbose):
    """Calm CLI"""
    ctx.ensure_object(dict)
    ctx.obj["client"] = get_api_client()
    ctx.obj["verbose"] = verbose


@main.command("configure")
@click.option(
    "--ip",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    envvar="PRISM_SERVER_PORT",
    default="9440",
    help="Prism Central server port number. Defaults to 9440.",
)
@click.option(
    "--username",
    envvar="PRISM_USERNAME",
    default="admin",
    help="Prism Central username",
)
@click.option(
    "--password", envvar="PRISM_PASSWORD", default=None, help="Prism Central password"
)
@click.option(
    "--config",
    "-c",
    "config_file",
    envvar="CALM_CONFIG",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file, defaults to ~/.calm/config",
)
@click.pass_obj
def _set_config(obj, ip, port, username, password, config_file):
    """Configure values for PC details (IP, Port, Credentials) and Projects"""
    set_config(
        ip=ip, port=port, username=username, password=password, config_file=config_file
    )


@main.group()
def get():
    """Get various things like blueprints, apps and so on"""
    pass


@get.group()
def server():
    """Get calm server details"""
    pass


@server.command("status")
@click.pass_obj
def get_server_status(obj):
    """Get calm server connection status"""

    client = obj.get("client")
    host = client.connection.host
    ping_status = "Success" if ping(ip=host) is True else "Fail"

    click.echo("Server Ping Status: {}".format(ping_status))
    click.echo("Server URL: {}".format(client.connection.base_url))
    # TODO - Add info about PC and Calm server version


@get.command("bps")
@click.option("--name", default=None, help="Search for blueprints by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter blueprints by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""
    get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items)


@get.command("apps")
@click.option("--name", default=None, help="Search for apps by name")
@click.option("--filter", "filter_by", default=None, help="Filter apps by this string")
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only application names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_apps(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get Apps, optionally filtered by a string"""
    get_apps(obj, name, filter_by, limit, offset, quiet, all_items)


@main.group()
def compile():
    """Compile blueprint to json / yaml"""
    pass


@compile.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Blueprint file to upload",
)
@click.option(
    "--out",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
def _compile_blueprint_command(bp_file, out):
    """Compiles a DSL (Python) blueprint into JSON or YAML"""
    compile_blueprint_command(bp_file, out)


@main.group()
def create():
    """Create blueprint in Calm, from DSL (Python) or JSON file """
    pass


def create_blueprint(client, bp_payload, name=None, description=None):

    bp_payload.pop("status", None)

    if name:
        bp_payload["spec"]["name"] = name
        bp_payload["metadata"]["name"] = name

    if description:
        bp_payload["spec"]["description"] = description

    bp_resources = bp_payload["spec"]["resources"]
    bp_name = bp_payload["spec"]["name"]
    bp_desc = bp_payload["spec"]["description"]

    return client.blueprint.upload_with_secrets(bp_name, bp_desc, bp_resources)


def create_blueprint_from_json(client, path_to_json, name=None, description=None):

    bp_payload = json.loads(open(path_to_json, "r").read())
    return create_blueprint(client, bp_payload, name=name, description=description)


def create_blueprint_from_dsl(client, bp_file, name=None, description=None):

    bp_payload = compile_blueprint(bp_file)
    if bp_payload is None:
        err_msg = "User blueprint not found in {}".format(bp_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_blueprint(client, bp_payload, name=name, description=description)


@create.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Blueprint file to upload",
)
@click.option("--name", default=None, help="Blueprint name (Optional)")
@click.option("--description", default=None, help="Blueprint description (Optional)")
@click.pass_obj
def create_blueprint_command(obj, bp_file, name, description):
    """Create a blueprint"""

    client = obj.get("client")

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description
        )
    elif bp_file.endswith(".py"):
        res, err = create_blueprint_from_dsl(
            client, bp_file, name=name, description=description
        )
    else:
        click.echo("Unknown file format {}".format(bp_file))
        return

    if err:
        click.echo(err["error"])
        return

    bp = res.json()
    bp_state = bp["status"]["state"]
    click.echo(">> Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"


@main.group()
def delete():
    """Delete blueprints"""
    pass


@delete.command("bp")
@click.argument("blueprint_names", nargs=-1)
@click.pass_obj
def _delete_blueprint(obj, blueprint_names):
    delete_blueprint(obj, blueprint_names)


@delete.command("app")
@click.argument("app_names", nargs=-1)
@click.option("--soft", "-s", is_flag=True, default=False, help="Soft delete app")
@click.pass_obj
def _delete_app(obj, app_names, soft):
    delete_app(obj, app_names, soft)


@main.group()
def launch():
    """Launch blueprints to create Apps"""
    pass


@launch.command("bp")
@click.argument("blueprint_name")
@click.option("--app_name", default=None, help="Name of your app")
@click.pass_obj
def launch_blueprint_command(obj, blueprint_name, app_name, blueprint=None):

    client = obj.get("client")

    launch_blueprint_simple(client, blueprint_name, app_name, blueprint=blueprint)


@main.group()
def describe():
    """Describe apps and blueprints"""
    pass


@describe.command("app")
@click.argument("app_name")
@click.pass_obj
def _describe_app(obj, app_name):
    """Describe an app"""
    describe_app(obj, app_name)


@main.command("app")
@click.argument("app_name")
@click.argument("action_name")
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.pass_obj
def _run_actions(obj, app_name, action_name, watch):
    """App related functionality: launch, lcm actions, monitor, delete"""

    run_actions(obj, app_name, action_name, watch)


@main.group()
def watch():
    """Track actions running on apps"""
    pass


@watch.command("app")
@click.argument("app_name")
@click.option("--action", default=None, help="Watch specific action")
@click.pass_obj
def _watch_app(obj, app_name, action):
    """Watch an app"""
    watch_app(obj, app_name, action)
