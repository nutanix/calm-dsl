import click
import os
import json
import sys

from copy import deepcopy

from distutils.version import LooseVersion as LV
from urllib.parse import urlparse

from calm.dsl.config import (
    get_context,
    set_dsl_config,
    get_default_config_file,
    get_default_db_file,
    get_default_local_dir,
    get_default_connection_config,
    get_default_log_config,
    init_context,
)
from calm.dsl.db import init_db_handle
from calm.dsl.api import (
    get_resource_api,
    get_client_handle_obj,
    get_multi_client_handle_obj,
)
from calm.dsl.store import Cache
from calm.dsl.init import init_bp, init_runbook, init_provider
from calm.dsl.providers import get_provider_types
from calm.dsl.store import Version
from calm.dsl.constants import (
    POLICY,
    STRATOS,
    DSL_CONFIG,
    CLOUD_PROVIDERS,
    MARKETPLACE,
)
from calm.dsl.builtins import file_exists
from calm.dsl.api.util import get_auth_info, is_ncm_enabled, fetch_host_port_from_url
from .main import init, set
from calm.dsl.log import get_logging_handle, CustomLogging

LOG = get_logging_handle(__name__)
DEFAULT_CONNECTION_CONFIG = get_default_connection_config()
DEFAULT_LOG_CONFIG = get_default_log_config()


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
@click.option(
    "--log_level",
    "-l",
    envvar="CALM_DSL_LOG_LEVEL",
    default=DEFAULT_LOG_CONFIG["level"],
    help="Default log level",
)
@click.option(
    "--retries-enabled/--retries-disabled",
    "-re/-rd",
    default=DEFAULT_CONNECTION_CONFIG["retries_enabled"],
    help="Retries enabled/disabled for api connections",
)
@click.option(
    "--connection-timeout",
    "-ct",
    type=int,
    default=DEFAULT_CONNECTION_CONFIG["connection_timeout"],
    help="Connection timeout for api connections",
)
@click.option(
    "--read-timeout",
    "-rt",
    type=int,
    default=DEFAULT_CONNECTION_CONFIG["read_timeout"],
    help="Read timeout for api connections",
)
@click.option(
    "--api-key",
    "-ak",
    "api_key_location",
    default=None,
    help="Path to api key file for authentication",
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
    log_level,
    retries_enabled,
    connection_timeout,
    read_timeout,
    api_key_location,
):
    """
    \b
    Initializes the calm dsl engine.

    NOTE: Env variables(if available) will be used as defaults for configuration
        i.) CALM_DSL_PC_IP: Prism Central Host
        ii.) CALM_DSL_PC_PORT: Prism Central Port
        iii.) CALM_DSL_PC_USERNAME: Prism Central username
        iv.) CALM_DSL_PC_PASSWORD: Prism Central password
        v.) CALM_DSL_DEFAULT_PROJECT: Default project name
        vi.) CALM_DSL_CONFIG_FILE_LOCATION: Default config file location where dsl config will be stored
        vii.) CALM_DSL_LOCAL_DIR_LOCATION: Default local directory location to store secrets
        viii.) CALM_DSL_DB_LOCATION: Default internal dsl db location

    """
    if api_key_location:
        api_key_location = os.path.expanduser(api_key_location)
        if not file_exists(api_key_location):
            LOG.error("{} not found".format(api_key_location))
            sys.exit(-1)

    set_server_details(
        ip=ip,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        db_file=db_file,
        local_dir=local_dir,
        config_file=config_file,
        log_level=log_level,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        api_key_location=api_key_location,
    )
    init_db()
    sync_cache()

    click.echo("\nHINT: To get started, follow the 3 steps below:")
    click.echo("1. Initialize an example blueprint DSL: calm init bp")
    click.echo(
        "2. Add vm image details according to your use in generated HelloBlueprint/blueprint.py"
    )
    click.echo(
        "3. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py"
    )
    click.echo(
        "4. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i"
    )

    click.echo("\nKeep Calm and DSL On!\n")


def _fetch_cp_feature_status(client):
    """
    Fetch custom provider feature status
    """
    Obj = get_resource_api(
        "features/custom_provider/status", client.connection, calm_api=True
    )
    res, err = Obj.read()
    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    return result.get("status", {}).get("feature_status", {}).get("is_enabled", False)


def _fetch_ncm_decoupled_status(client):
    """
    Fetch NCM decoupled status

    Returns:
        ncm_enabled: bool
        host (str): PC-FQDN
        ncm_host (str): NCM-FQDN
        ncm_port (str): NCM PORT
    """

    ncm_url = None
    ncm_host = None
    ncm_port = None

    ncm_enabled, ncm_url = is_ncm_enabled(client)

    if ncm_enabled:
        LOG.info("Checking if NCM is enabled on Server")
        ncm_host, ncm_port = fetch_host_port_from_url(ncm_url)
        LOG.info("ENABLED")
        LOG.info("NCM-FQDN is: {}".format(ncm_host))

    return ncm_enabled, ncm_host, ncm_port


def set_server_details(
    ip,
    port,
    username,
    password,
    project_name,
    db_file,
    local_dir,
    config_file,
    log_level,
    retries_enabled,
    connection_timeout,
    read_timeout,
    api_key_location,
):

    if not (ip and port and username and password and project_name):
        click.echo("Please provide Calm DSL settings:\n")

    host = ip or click.prompt("Prism Central Host", default="")

    if api_key_location:
        cred = get_auth_info(api_key_location)
        username = cred.get("username")
        password = cred.get("password")
        port = DSL_CONFIG.SAAS_PORT
    else:
        port = port or click.prompt("Port", default="9440")
        username = username or click.prompt("Username", default="admin")
        password = password or click.prompt("Password", default="", hide_input=True)

    project_name = project_name or click.prompt(
        "Project", default=DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
    )

    # Do not prompt for init config variables, Take default values for init.ini file
    config_file = config_file or get_default_config_file()
    local_dir = local_dir or get_default_local_dir()
    db_file = db_file or get_default_db_file()

    if port == DSL_CONFIG.SAAS_PORT:
        if api_key_location:
            LOG.info("Authenticating with username: {}".format(username))
        else:
            LOG.warning(DSL_CONFIG.SAAS_LOGIN_WARN)

    # Get NCM-FQDN using temporary client handle
    client = get_client_handle_obj(host, port, auth=(username, password))
    ncm_enabled, ncm_host, ncm_port = _fetch_ncm_decoupled_status(client)

    # Use temporary multi client handle if NCM is enabled
    if ncm_enabled:
        # update ncm_server_config in DSL context to use it for API routing.
        ContextObj = get_context()
        ContextObj.update_ncm_server_context(ncm_enabled, ncm_host, ncm_port)

        client = get_multi_client_handle_obj(
            host, port, ncm_host, ncm_port, auth=(username, password)
        )

    # check calm enablement status when NCM is not decoupled
    if not ncm_enabled:
        LOG.info("Checking if Calm is enabled on Server")
        Obj = get_resource_api("services/nucalm/status", client.connection)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        result = json.loads(res.content)
        service_enablement_status = result["service_enablement_status"]
        LOG.info(service_enablement_status)

    res, err = client.version.get_calm_version()
    if err:
        LOG.error("Failed to get version")
        click.echo("[Fail]")
        sys.exit(err["error"])
    calm_version = res.content.decode("utf-8")

    # get policy status
    if LV(calm_version) >= LV(POLICY.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api("features/policy", client.connection, calm_api=True)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Policy enabled={}".format(policy_status))
    else:
        LOG.debug("Policy is not supported")
        policy_status = False

    # get approval policy status
    if LV(calm_version) >= LV(POLICY.APPROVAL_POLICY_MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/approval_policy", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        approval_policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Approval Policy enabled={}".format(approval_policy_status))
    else:
        LOG.debug("Approval Policy is not supported")
        approval_policy_status = False

    # get stratos status
    if LV(calm_version) >= LV(STRATOS.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/stratos/status", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        stratos_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("stratos enabled={}".format(stratos_status))
    else:
        LOG.debug("Stratos is not supported")
        stratos_status = False

    if LV(calm_version) >= LV(CLOUD_PROVIDERS.MIN_SUPPORTED_VERSION):
        cp_status = _fetch_cp_feature_status(client)
        LOG.info("CP enabled={}".format(cp_status))
    else:
        LOG.debug("Cloud Providers are not supported")
        cp_status = False

    if project_name != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        LOG.info("Verifying the project details")
        project_name_uuid_map = client.project.get_name_uuid_map(
            params={"filter": "name=={}".format(project_name)}
        )
        if not project_name_uuid_map:
            LOG.error("Project '{}' not found !!!".format(project_name))
            sys.exit(-1)
        LOG.info("Project '{}' verified successfully".format(project_name))

    if api_key_location:
        username = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
        password = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME

    # Writing configuration to file
    set_dsl_config(
        host=host,
        port=port,
        username=username,
        password=password,
        ncm_enabled=ncm_enabled or False,
        ncm_host=ncm_host,
        ncm_port=ncm_port,
        api_key_location=api_key_location or DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME,
        project_name=project_name,
        log_level=log_level,
        config_file=config_file,
        db_location=db_file,
        local_dir=local_dir,
        policy_status=policy_status,
        approval_policy_status=approval_policy_status,
        stratos_status=stratos_status,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        cp_status=cp_status,
    )

    # Updating context for using latest config data
    LOG.info("Updating context for using latest config file data")
    init_context()

    if log_level:
        CustomLogging.set_verbose_level(getattr(CustomLogging, log_level))


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


@init.command("provider", feature_min_version="4.0.0", experimental=True)
@click.option("--name", "-n", "provider_name", default="hello", help="Name of provider")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the provider"
)
def init_dsl_provider(provider_name, dir_name):
    """
    Creates a starting file for provider
    """

    if not provider_name.isidentifier():
        LOG.error("Provider name '{}' is not a valid identifier".format(provider_name))
        sys.exit(-1)

    init_provider(provider_name, dir_name)


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
@click.option(
    "--api-key",
    "-ak",
    "api_key_location",
    default=None,
    help="Path to api key file for authentication",
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
    api_key_location,
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

    # Reading api key location and port from config if not provided
    api_key_location = api_key_location or server_config.get(
        "api_key_location", DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
    )

    # Resetting stored location of api key (for PC login case)
    if api_key_location != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        api_key_location = os.path.expanduser(api_key_location)
    else:
        api_key_location = None

    port = port or server_config["pc_port"]

    cred = get_auth_info(api_key_location)
    stored_username = cred.get("username")
    stored_password = cred.get("password")

    username = username or stored_username
    password = password or stored_password
    project_config = ContextObj.get_project_config()
    project_name = project_name or project_config.get("name")

    if port == DSL_CONFIG.SAAS_PORT:
        if api_key_location:
            LOG.info("Authenticating with username: {}".format(username))
        else:
            LOG.warning(DSL_CONFIG.SAAS_LOGIN_WARN)

    # Get NCM-FQDN using temporary client handle
    client = get_client_handle_obj(host, port, auth=(username, password))
    ncm_enabled, ncm_host, ncm_port = _fetch_ncm_decoupled_status(client)

    # Use temporary multi client handle if NCM is enabled
    if ncm_enabled:
        # update ncm_server_config in DSL context to use it for API routing.
        ContextObj.update_ncm_server_context(ncm_enabled, ncm_host, ncm_port)

        client = get_multi_client_handle_obj(
            host, port, ncm_host, ncm_port, auth=(username, password)
        )

    # check calm enablement status when NCM is not decoupled
    if not ncm_enabled:
        LOG.info("Checking if Calm is enabled on Server")
        Obj = get_resource_api("services/nucalm/status", client.connection)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        result = json.loads(res.content)
        service_enablement_status = result["service_enablement_status"]
        LOG.info(service_enablement_status)

    res, err = client.version.get_calm_version()
    if err:
        LOG.error("Failed to get version")
        click.echo("[Fail]")
        sys.exit(err["error"])
    calm_version = res.content.decode("utf-8")

    # get policy status
    if LV(calm_version) >= LV(POLICY.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api("features/policy", client.connection, calm_api=True)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Policy enabled={}".format(policy_status))
    else:
        LOG.debug("Policy is not supported")
        policy_status = False

    # get approval policy status
    if LV(calm_version) >= LV(POLICY.APPROVAL_POLICY_MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/approval_policy", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        approval_policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Approval Policy enabled={}".format(approval_policy_status))
    else:
        LOG.debug("Approval Policy is not supported")
        approval_policy_status = False

    # get stratos status
    if LV(calm_version) >= LV(STRATOS.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/stratos/status", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        stratos_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("stratos enabled={}".format(stratos_status))
    else:
        LOG.debug("Stratos is not supported")
        stratos_status = False

    if LV(calm_version) >= LV(CLOUD_PROVIDERS.MIN_SUPPORTED_VERSION):
        cp_status = _fetch_cp_feature_status(client)
        LOG.info("CP enabled={}".format(cp_status))
    else:
        LOG.debug("Cloud Providers are not supported")
        cp_status = False

    if project_name != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
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

    if api_key_location:
        username = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
        password = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME

    # Set the dsl configuration
    set_dsl_config(
        host=host,
        port=port,
        username=username,
        password=password,
        ncm_enabled=ncm_enabled or False,
        ncm_host=ncm_host,
        ncm_port=ncm_port,
        api_key_location=api_key_location or DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME,
        project_name=project_name,
        db_location=db_location,
        log_level=log_level,
        local_dir=local_dir,
        config_file=config_file,
        policy_status=policy_status,
        approval_policy_status=approval_policy_status,
        stratos_status=stratos_status,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        cp_status=cp_status,
    )
    LOG.info("Configuration changed successfully")

    # Updating context for using latest config data
    init_context()
    if update_cache:
        sync_cache()
