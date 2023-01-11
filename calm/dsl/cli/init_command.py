import click
import os
import json
import sys

from calm.dsl.config import (
    get_context,
    set_dsl_config,
    get_default_config_file,
    get_default_db_file,
    get_default_local_dir,
    get_default_connection_config,
    init_context,
)
from calm.dsl.db import init_db_handle
from calm.dsl.api import get_resource_api, get_client_handle_obj
from calm.dsl.store import Cache
from calm.dsl.init import init_bp, init_runbook
from calm.dsl.providers import get_provider_types

from .main import init, set
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@init.command("dsl")
@click.option(
    "--ip",
    "-i",
    envvar="CALM_DSL_PC_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    "-P",
    envvar="CALM_DSL_PC_PORT",
    default=None,
    help="Prism Central server port number",
)
@click.option(
    "--username",
    "-u",
    envvar="CALM_DSL_PC_USERNAME",
    default=None,
    help="Prism Central username",
)
@click.option(
    "--password",
    "-p",
    envvar="CALM_DSL_PC_PASSWORD",
    default=None,
    help="Prism Central password",
)
@click.option(
    "--db_file",
    "-d",
    "db_file",
    envvar="CALM_DSL_DB_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to local database file",
)
@click.option(
    "--local_dir",
    "-ld",
    envvar="CALM_DSL_LOCAL_DIR_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to local directory for storing secrets",
)
@click.option(
    "--config",
    "-cf",
    "config_file",
    envvar="CALM_DSL_CONFIG_FILE_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file to store dsl configuration",
)
@click.option(
    "--project",
    "-pj",
    "project_name",
    envvar="CALM_DSL_DEFAULT_PROJECT",
    help="Default project name used for entities",
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
):
    """
    \b
    Initializes the calm dsl engine.

    NOTE: Env variables(if available) will be used as defaults for configuration
        i.) CALM_DSL_PC_IP: Prism Central IP
        ii.) CALM_DSL_PC_PORT: Prism Central Port
        iii.) CALM_DSL_PC_USERNAME: Prism Central username
        iv.) CALM_DSL_PC_PASSWORD: Prism Central password
        v.) CALM_DSL_DEFAULT_PROJECT: Default project name
        vi.) CALM_DSL_CONFIG_FILE_LOCATION: Default config file location where dsl config will be stored
        vii.) CALM_DSL_LOCAL_DIR_LOCATION: Default local directory location to store secrets
        viii.) CALM_DSL_DB_LOCATION: Default internal dsl db location

    """

    set_server_details(
        ip=ip,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        db_file=db_file,
        local_dir=local_dir,
        config_file=config_file,
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

    # Default connection params
    default_connection_config = get_default_connection_config()
    retries_enabled = default_connection_config["retries_enabled"]
    connection_timeout = default_connection_config["connection_timeout"]
    read_timeout = default_connection_config["read_timeout"]

    # Do not prompt for init config variables, Take default values for init.ini file
    config_file = config_file or get_default_config_file()
    local_dir = local_dir or get_default_local_dir()
    db_file = db_file or get_default_db_file()

    LOG.info("Checking if Calm is enabled on Server")

    # Get temporary client handle
    client = get_client_handle_obj(host, port, auth=(username, password))
    Obj = get_resource_api("services/nucalm/status", client.connection)
    res, err = Obj.read()

    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    service_enablement_status = result["service_enablement_status"]
    LOG.info(service_enablement_status)

    LOG.info("Verifying the project details")
    project_name_uuid_map = client.project.get_name_uuid_map(
        params={"filter": "name=={}".format(project_name)}
    )
    if not project_name_uuid_map:
        LOG.error("Project '{}' not found !!!".format(project_name))
        sys.exit(-1)
    LOG.info("Project '{}' verified successfully".format(project_name))

    # Writing configuration to file
    set_dsl_config(
        host=host,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        log_level=log_level,
        config_file=config_file,
        db_location=db_file,
        local_dir=local_dir,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
    )

    # Updating context for using latest config data
    LOG.info("Updating context for using latest config file data")
    init_context()


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
@click.option(
    "--bp_type",
    "-b",
    "blueprint_type",
    type=click.Choice(["SINGLE_VM", "MULTI_VM"]),
    default="MULTI_VM",
    help="Blueprint type",
)
def init_dsl_bp(bp_name, dir_name, provider_type, blueprint_type):
    """Creates a starting directory for blueprint"""

    if not bp_name.isidentifier():
        LOG.error("Blueprint name '{}' is not a valid identifier".format(bp_name))
        sys.exit(-1)

    init_bp(bp_name, dir_name, provider_type, blueprint_type)


@init.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", "runbook_name", default="Hello", help="Name of runbook")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the runbook"
)
def init_dsl_runbook(runbook_name, dir_name):
    """Creates a starting directory for runbook"""

    if not runbook_name.isidentifier():
        LOG.error("Runbook name '{}' is not a valid identifier".format(runbook_name))
        sys.exit(-1)

    init_runbook(runbook_name, dir_name)


# @init.command("scheduler", feature_min_version="3.3.0", experimental=True)
# @click.option("--name", "-n", "job_name", default="Hello", help="Name of job")
# @click.option(
#     "--dir_name", "-d", default=os.getcwd(), help="Directory path for the scheduler"
# )
# def init_dsl_scheduler(job_name, dir_name):
#     """Creates a starting directory for runbook"""
#
#     if not job_name.isidentifier():
#         LOG.error("Job name '{}' is not a valid identifier".format(job_name))
#         sys.exit(-1)
#
#     init_scheduler(job_name, dir_name)


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
@click.option(
    "--retries-enabled/--retries-disabled",
    "-re/-rd",
    default=None,
    help="Retries enabled/disabled",
)
@click.option(
    "--connection-timeout",
    "-ct",
    type=int,
    help="connection timeout",
)
@click.option(
    "--read-timeout",
    "-rt",
    type=int,
    help="read timeout",
)
@click.argument("config_file", required=False)
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
    retries_enabled,
    connection_timeout,
    read_timeout,
):
    """writes the configuration to config files i.e. config.ini and init.ini

    \b
    Note: Cache will be updated if supplied host is different from configured host.
    """

    # Fetching context object
    ContextObj = get_context()

    server_config = ContextObj.get_server_config()

    # Update cache if there is change in host ip
    update_cache = host != server_config["pc_ip"] if host else False
    host = host or server_config["pc_ip"]
    username = username or server_config["pc_username"]
    port = port or server_config["pc_port"]
    password = password or server_config["pc_password"]

    project_config = ContextObj.get_project_config()
    project_name = project_name or project_config.get("name") or "default"

    LOG.info("Checking if Calm is enabled on Server")

    # Get temporary client handle
    client = get_client_handle_obj(host, port, auth=(username, password))
    Obj = get_resource_api("services/nucalm/status", client.connection)
    res, err = Obj.read()

    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    service_enablement_status = result["service_enablement_status"]
    LOG.info(service_enablement_status)

    LOG.info("Verifying the project details")
    project_name_uuid_map = client.project.get_name_uuid_map(
        params={"filter": "name=={}".format(project_name)}
    )
    if not project_name_uuid_map:
        LOG.error("Project '{}' not found !!!".format(project_name))
        sys.exit(-1)
    LOG.info("Project '{}' verified successfully".format(project_name))

    log_config = ContextObj.get_log_config()
    log_level = log_level or log_config.get("level") or "INFO"

    # Take init_configuration from user params or init file
    init_config = ContextObj.get_init_config()
    config_file = (
        config_file or ContextObj._CONFIG_FILE or init_config["CONFIG"]["location"]
    )
    db_location = db_location or init_config["DB"]["location"]
    local_dir = local_dir or init_config["LOCAL_DIR"]["location"]

    # Get connection config
    connection_config = ContextObj.get_connection_config()
    if retries_enabled is None:  # Not supplied in command
        retries_enabled = connection_config["retries_enabled"]
    connection_timeout = connection_timeout or connection_config["connection_timeout"]
    read_timeout = read_timeout or connection_config["read_timeout"]

    # Set the dsl configuration
    set_dsl_config(
        host=host,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        db_location=db_location,
        log_level=log_level,
        local_dir=local_dir,
        config_file=config_file,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
    )
    LOG.info("Configuration changed successfully")

    # Updating context for using latest config data
    init_context()
    if update_cache:
        sync_cache()
