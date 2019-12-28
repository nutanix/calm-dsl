import click
import os
import json

from .main import init
from .utils import highlight_text
from .configs import set_config
from calm.dsl.tools import ping
from calm.dsl.db import Database
from calm.dsl.api import get_resource_api, update_client_handle
from calm.dsl.api.connection import Connection, REQUEST
from calm.dsl.store import Cache
from calm.dsl.config import update_config
from calm.dsl.init import init_bp
from calm.dsl.providers import get_provider_types


@init.command("dsl")
def initialize_engine():
    """Initializes the calm dsl engine"""

    click.echo(highlight_text("\nIntializing Engine..."))

    click.echo(highlight_text("\n1. Server Configuration"))
    set_server_details()

    click.echo(highlight_text("\n2. Initializing local store"))
    init_db()

    click.echo(highlight_text("\n3. Syncing the cache"))
    sync_cache()

    click.echo(
        highlight_text("\nAll set \U0001F389. Start creating the bps \U0001F64C")
    )


def set_server_details():

    host = click.prompt("\tEnter Host IP", default="")
    port = click.prompt("\tEnter Port No.", default="9440")
    username = click.prompt("\tEnter Username", default="admin")
    password = click.prompt("\tEnter Password", default="", hide_input=True)

    click.echo("\nValidating Host ...")
    ping_status = "Success" if ping(ip=host) is True else "Fail"

    if ping_status == "Fail":
        raise Exception("Unable to ping {}".format(host))
    else:
        click.echo("Ping to host {} is successful \U0001f600".format(host))

    # Validating creds
    click.echo("\nValidating Credentials ...")
    connection_obj = Connection(host, port, auth=(username, password))
    connection_obj.connect()
    Obj = get_resource_api("services/nucalm/status", connection_obj)
    res, err = Obj.connection._call(Obj.PREFIX, verify=False, method=REQUEST.METHOD.GET)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    else:
        click.echo("Success \U0001f600")
        result = json.loads(res.content)
        service_enablement_status = result["service_enablement_status"]
        click.echo(
            highlight_text(
                "\nCalm Enablement status on {}: {}".format(
                    host, service_enablement_status
                )
            )
        )

    # If validation for host and cred is successful, then update config file
    set_config("SERVER", ip=host, port=port, username=username, password=password)

    # Updating default config object
    update_config()

    # Updating default client handle
    update_client_handle(host, port, auth=(username, password))


def init_db():

    location = click.prompt(
        "\tEnter DSL DB location", default=os.path.expanduser("~/.calm/dsl.db")
    )

    if os.path.exists(location):
        os.remove(location)

    set_config("DB", location=location)

    # Updating default config object
    update_config()

    Database()
    click.echo("Success \U0001f600")


def sync_cache():
    Cache.sync()
    click.echo("Success \U0001f600")


@init.command("bp")
@click.option(
    "--service",
    "-s",
    default="Hello",
    help="Name for service in blueprint"
)
@click.option(
    "--dir_name",
    "-d",
    default=os.getcwd(),
    help="Directory path for the blueprint"
)
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(get_provider_types()),
    default="AHV_VM",
    help="Provider type",
)
def init_dsl_bp(service, dir_name, provider_type):
    """Creates a starting directory for blueprint"""
    init_bp(service, dir_name, provider_type)
