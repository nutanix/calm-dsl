from .main import main
from .utils import highlight_text
from .configs import set_config
from calm.dsl.tools import ping
from calm.dsl.db import Database, DB_LOCATION
from calm.dsl.api import get_resource_api
from calm.dsl.api.connection import Connection, REQUEST
from calm.dsl.store import Cache

import click
import os
import requests
import json


@main.command("init")
def initialize_engine():
    """Initializes the calm dsl engine"""

    click.echo("Engine Intializing ...")
    click.echo(highlight_text("\n1. Server Configuration"))
    set_server_details()

    click.echo(highlight_text("\n2. Initializing local store"))
    init_db()

    click.echo(highlight_text("\n3. Syncing the cache"))
    sync_cache()

    click.echo(highlight_text("\nAll set \U0001F389. Start creating the bps \U0001F64C"))


def set_server_details():

    host = click.prompt("\tEnter Host IP", default="")
    port = click.prompt("\tEnter Port No.", default="")
    username = click.prompt("\tEnter Username", default="")
    password = click.prompt("\tEnter password", default="", hide_input=True)

    click.echo("\nValidating Host ...")
    ping_status = "Success" if ping(ip=host) is True else "Fail"

    if ping_status == "Fail":
        raise Exception("Unable to ping {}".format(host))
    else:
        click.echo("Ping to host {} is successful \U0001f600".format(host))

    # Validating creds
    click.echo("\nValidating Credentials ...")
    connection_obj = Connection(
        host, port, REQUEST.AUTH_TYPE.BASIC, REQUEST.SCHEME.HTTPS, (username, password)
    )
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
    
    set_config("SERVER", ip=host, port=port, username=username, password=password)


def init_db():
    # Deleting existing db file
    if os.path.exists(DB_LOCATION):
        os.remove(DB_LOCATION)

    Database()
    click.echo("Success \U0001f600")


def sync_cache():
    Cache.sync()
    click.echo("Success \U0001f600")
