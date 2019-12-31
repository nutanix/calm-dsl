import click
import os
import json

from calm.dsl.config import init_config, get_default_user_config_file
from calm.dsl.db import Database
from calm.dsl.api import get_resource_api, update_client_handle
from calm.dsl.api.connection import REQUEST
from calm.dsl.store import Cache
from calm.dsl.init import init_bp
from calm.dsl.providers import get_provider_types

from .main import init


@init.command("dsl")
def initialize_engine():
    """Initializes the calm dsl engine"""

    click.echo("Please provide Calm DSL settings:\n")

    set_server_details()
    init_db()
    sync_cache()

    click.echo("\nHINT: To get started, follow the 3 steps below:")
    click.echo("1. Initialize an example blueprint DSL: calm init bp")
    click.echo(
        "2. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py"
    )
    click.echo(
        "3. Start an application using the blueprint: calm launch bp HelloBlueprint --app_name HelloApp01 -i"
    )

    click.echo("\nKeep Calm and DSL On!\n")


def set_server_details():

    host = click.prompt("Prism Central IP", default="")
    port = click.prompt("Port", default="9440")
    username = click.prompt("Username", default="admin")
    password = click.prompt("Password", default="", hide_input=True)
    project_name = click.prompt("Project", default="default")

    # Keep initial DB location to default. User need not give this option initially.
    # db_location = click.prompt(
    #    "DSL local DB location", default=os.path.expanduser("~/.calm/dsl.db")
    # )

    db_location = os.path.expanduser("~/.calm/dsl.db")

    # Default user config file
    user_config_file = get_default_user_config_file()

    click.echo("Writing config to {} ... ".format(user_config_file), nl=False)
    init_config(host, port, username, password, project_name, db_location)
    click.echo("[Success]")

    click.echo("Checking if Calm is enabled on Server ... ", nl=False)
    # Update client handle with new settings
    client = update_client_handle(host, port, auth=(username, password))
    Obj = get_resource_api("services/nucalm/status", client.connection)
    res, err = Obj.connection._call(Obj.PREFIX, verify=False, method=REQUEST.METHOD.GET)

    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    service_enablement_status = result["service_enablement_status"]
    click.echo("[{}]".format(service_enablement_status))


def init_db():
    click.echo("Creating local database ... ", nl=False)
    Database()
    click.echo("[Success]")


def sync_cache():
    click.echo("Updating Cache ... ", nl=False)
    Cache.sync()
    click.echo("[Success]")


@init.command("bp")
@click.option("--service", "-s", default="Hello", help="Name for service in blueprint")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the blueprint"
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
