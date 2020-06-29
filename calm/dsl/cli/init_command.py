import click
import os
import json
import sys

from calm.dsl.config import (
    init_config,
    get_default_config_file,
    set_config,
    update_init_config,
    get_user_config_file,
    get_default_db_file,
    get_default_local_dir,
)
from calm.dsl.db import init_db_handle
from calm.dsl.api import get_resource_api, update_client_handle, get_client_handle
from calm.dsl.store import Cache
from calm.dsl.init import init_bp, init_runbook
from calm.dsl.providers import get_provider_types

from .main import init, set
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


@init.command("dsl")
@click.option(
    "--ip",
    "-i",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    "-P",
    envvar="PRISM_SERVER_PORT",
    default=None,
    help="Prism Central server port number",
)
@click.option(
    "--username",
    "-u",
    envvar="PRISM_USERNAME",
    default=None,
    help="Prism Central username",
)
@click.option(
    "--password",
    "-p",
    envvar="PRISM_PASSWORD",
    default=None,
    help="Prism Central password",
)
@click.option(
    "--db_file",
    "-d",
    "db_file",
    envvar="DATABASE_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to local database file",
)
@click.option(
    "--local_dir",
    "-ld",
    envvar="LOCAL_DIR",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to local directory for storing secrets",
)
@click.option(
    "--config",
    "-c",
    "config_file",
    envvar="CONFIG FILE LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file",
)
@click.option("--project", "-pj", "project_name", help="Project name for entity")
@click.option(
    "--use_custom_defaults",
    "-cd",
    is_flag=True,
    default=False,
    help="Use custom defaults for init configuration",
)
def initialize_engine(
    ip,
    port,
    username,
    password,
    project_name,
    db_file,
    local_dir,
    config_file,
    use_custom_defaults,
):
    """Initializes the calm dsl engine"""

    set_server_details(
        ip=ip,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        db_file=db_file,
        local_dir=local_dir,
        config_file=config_file,
        use_custom_defaults=use_custom_defaults,
    )
    init_db()
    sync_cache()

    click.echo("\nHINT: To get started, follow the 3 steps below:")
    click.echo("1. Initialize an example blueprint DSL: calm init bp")
    click.echo(
        "2. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py"
    )
    click.echo(
        "3. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i"
    )

    click.echo("\nKeep Calm and DSL On!\n")


def set_server_details(
    ip,
    port,
    username,
    password,
    project_name,
    db_file,
    local_dir,
    config_file,
    use_custom_defaults,
):

    if not (ip and port and username and password and project_name):
        click.echo("Please provide Calm DSL settings:\n")

    host = ip or click.prompt("Prism Central IP", default="")
    port = port or click.prompt("Port", default="9440")
    username = username or click.prompt("Username", default="admin")
    password = password or click.prompt("Password", default="", hide_input=True)
    project_name = project_name or click.prompt("Project", default="default")

    # Default log-level
    log_level = "INFO"

    if use_custom_defaults:
        # Prompt for config file
        config_file = config_file or click.prompt(
            "Config File location", default=get_default_config_file()
        )

        # Prompt for local dir location  at initializing dsl
        local_dir = local_dir or click.prompt(
            "Local files directory", default=get_default_local_dir()
        )

        # Prompt for db file location at initializing dsl
        db_file = db_file or click.prompt(
            "DSL local store location", default=get_default_db_file()
        )

    else:
        config_file = config_file or get_default_config_file()
        local_dir = local_dir or get_default_local_dir()
        db_file = db_file or get_default_db_file()

    LOG.info("Checking if Calm is enabled on Server")
    # Get temporary client handle
    client = get_client_handle(host, port, auth=(username, password), temp=True)
    Obj = get_resource_api("services/nucalm/status", client.connection)
    res, err = Obj.read()

    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    service_enablement_status = result["service_enablement_status"]
    LOG.info(service_enablement_status)

    # Updating init file data
    update_init_config(config_file=config_file, db_file=db_file, local_dir=local_dir)

    LOG.info("Writing config to {}".format(config_file))
    init_config(host, port, username, password, project_name, log_level)

    # Update client handle with new settings if no exception occurs
    update_client_handle(host, port, auth=(username, password))


def init_db():
    LOG.info("Creating local database")
    init_db_handle()


def sync_cache():
    Cache.sync()


@init.command("bp")
@click.option("--name", "-n", "bp_name", default="Hello", help="Name of blueprint")
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
def init_dsl_bp(bp_name, dir_name, provider_type):
    """Creates a starting directory for blueprint"""

    if not bp_name.isidentifier():
        LOG.error("Blueprint name '{}' is not a valid identifier".format(bp_name))
        sys.exit(-1)

    init_bp(bp_name, dir_name, provider_type)


@init.command("runbook")
@click.option("--name", "-n", "runbook_name", default="Hello", help="Name of runbook")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the runbook"
)
@click.option("--ip", help="VM IP for the sample runbook")
def init_dsl_runbook(runbook_name, dir_name, ip):
    """Creates a starting directory for runbook"""

    if not runbook_name.isidentifier():
        LOG.error("Runbook name '{}' is not a valid identifier".format(runbook_name))
        sys.exit(-1)

    init_runbook(runbook_name, dir_name, vm_ip=ip)


@set.command("config")
@click.option(
    "--ip",
    "-i",
    "host",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    "-P",
    envvar="PRISM_SERVER_PORT",
    default=None,
    help="Prism Central server port number",
)
@click.option(
    "--username",
    "-u",
    envvar="PRISM_USERNAME",
    default=None,
    help="Prism Central username",
)
@click.option(
    "--password",
    "-p",
    envvar="PRISM_PASSWORD",
    default=None,
    help="Prism Central password",
)
@click.option("--project", "-pj", "project_name", help="Project name for entity")
@click.option(
    "--db_file",
    "-d",
    "db_location",
    envvar="DATABASE_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to local database file",
)
@click.option(
    "--local_dir",
    "-ld",
    envvar="LOCAL_DIR",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to local directory for storing secrets",
)
@click.option("--log_level", "-l", default=None, help="Default log level")
@click.argument("config_file", default=get_user_config_file())
def _set_config(
    host,
    port,
    username,
    password,
    project_name,
    db_location,
    log_level,
    config_file,
    local_dir,
):
    """writes the configuration to config file"""

    set_config(
        host,
        port,
        username,
        password,
        project_name,
        db_location,
        log_level,
        local_dir=local_dir,
        config_file=config_file,
    )
