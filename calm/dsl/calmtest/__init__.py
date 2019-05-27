import click
from ..cli.config import get_config, get_api_client
from .resources import create_resource, read_resource, delete_resource,\
    update_resource, list_resource


@click.group()
@click.option(
    "--ip",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    envvar="PRISM_SERVER_PORT",
    default=9440,
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
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("0.1")
@click.pass_context
def main(ctx, ip, port, username, password, config_file, verbose):
    """Calmtest CLI"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(
        ip=ip, port=port, username=username, password=password, config_file=config_file
    )
    ctx.obj["client"] = get_api_client()
    ctx.obj["verbose"] = verbose


@main.group("create")
def create():
    """ Create entity command """
    pass


@main.group("read")
def read():
    """ Create entity command """
    pass


@main.group("update")
def update():
    """ Create entity command """
    pass


@main.group("delete")
def delete():
    """ Create entity command """
    pass


@main.group("list")
def list():
    """ List entity command """
    pass


# Create Command

@create.command("resource")
@click.option(
    "--url",
    "baseUrl",
    default="",
    help="Relative URL for the call"
)
@click.option(
    "--data",
    "payload",
    default="{}",
    help="Payload for the api call"
)
@click.pass_obj
def _create_resource(obj, baseUrl, payload):
    """ Create resource """
    client = obj.get("client")
    create_resource(client, baseUrl, payload)


# Read Command

@read.command("resource")
@click.option(
    "--url",
    "baseUrl",
    default="",
    help="Relative URL for the call"
)
@click.option(
    "--id",
    default="",
    help="uuid of the entity"
)
@click.pass_obj
def _read_resource(obj, baseUrl, id):
    """ Read resource """
    client = obj.get("client")
    read_resource(client, baseUrl, id)


# Update Command

@update.command("resource")
@click.option(
    "--url",
    "baseUrl",
    default="",
    help="Relative URL for the call"
)
@click.option(
    "--id",
    default="",
    help="uuid of the entity"
)
@click.option(
    "--data",
    "payload",
    default="{}",
    help="Payload for the api call"
)
@click.pass_obj
def _update_resource(obj, baseUrl, id, payload):
    """ Update resource """
    client = obj.get("client")
    update_resource(client, baseUrl, id, payload)


# Delete Command

@delete.command("resource")
@click.option(
    "--url",
    "baseUrl",
    default="",
    help="Relative URL for the call"
)
@click.option(
    "--id",
    default="",
    help="uuid of the entity"
)
@click.pass_obj
def _delete_resource(obj, baseUrl, id):
    """ Delete resource """
    client = obj.get("client")
    delete_resource(client, baseUrl, id)


# List command

@list.command("resource")
@click.option(
    "--url",
    "baseUrl",
    default="",
    help="Relative URL for the call"
)
@click.option(
    "--data",
    "payload",
    default="{}",
    help="Payload for the api call"
)
@click.pass_obj
def _list_resource(obj, baseUrl, payload):
    """ List the resources """
    client = obj.get("client")
    list_resource(client, baseUrl, payload)
