from ruamel import yaml
import click
import json
import copy
import os

import click_completion
import click_completion.core
from click_repl import repl
from prettytable import PrettyTable

# TODO - move providers to separate file
from calm.dsl.providers import get_provider, get_provider_types
from calm.dsl.api import get_api_client, get_resource_api, reset_api_client_handle
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context, get_default_config_file
from calm.dsl.config.env_config import EnvConfig
from calm.dsl.store import Cache
from calm.dsl.constants import DSL_CONFIG
from calm.dsl.builtins.models.utils import set_compile_secrets_flag

from .version_validator import validate_version
from .click_options import simple_verbosity_option, show_trace_option
from .utils import FeatureFlagGroup, highlight_text
from calm.dsl.store import Version
from calm.dsl.config.init_config import get_init_config_handle
from calm.dsl.cli.run_script import *

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

click_completion.init()
LOG = get_logging_handle(__name__)


@click.group(cls=FeatureFlagGroup, context_settings=CONTEXT_SETTINGS)
@simple_verbosity_option(LOG)
@show_trace_option(LOG)
@click.option(
    "--config",
    "-c",
    "config_file",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file, defaults to ~/.calm/config.ini",
)
@click.option(
    "--sync",
    "-s",
    "sync",
    is_flag=True,
    default=False,
    help="Update cache before running command",
)
@click.version_option("3.8.1")
@click.pass_context
def main(ctx, config_file, sync):
    """Calm CLI

    \b
    Commonly used commands:
      calm get apps   -> Get list of apps
      calm get bps   -> Get list of blueprints
      calm launch bp --app_name Fancy-App-1 MyFancyBlueprint   -> Launch a new app from an existing blueprint
      calm create bp -f sample_bp.py --name Sample-App-3   -> Upload a new blueprint from a python DSL file
      calm describe app Fancy-App-1   -> Describe an existing app
      calm app Fancy-App-1 -w my_action   -> Run an action on an app
      calm get runbooks  -> Get list of runbooks
      calm describe runbook MyFancyRunbook   -> Describe an existing runbook
      calm create runbook -f sample_rb.py --name Sample-RB  -> Upload a new runbook from a python DSL file
      calm run runbook MyFancyRunbook -> Runs the existing runbook MyFancyRunbook
      calm run runbook -f sample_rb.py -> Runs the runbook from a python DSL file
      calm get execution_history  -> Get list of runbook executions
      calm get endpoints -> Get list of endpoints
      calm create endpoint -f sample_ep.py --name Sample-Endpoint -> Upload a new endpoint from a python DSL file"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = True
    try:
        ContextObj = get_context()
        old_pc_ip = Version.get_version_data("PC").get("pc_ip", "")
        if config_file:
            if not os.path.exists(config_file):
                raise ValueError("file not found {}".format(config_file))

            if ctx.invoked_subcommand == "init":
                raise ValueError("config file passing is not supported in init command")

            ContextObj.update_config_file_context(config_file=config_file)

        if ctx.invoked_subcommand != "init":
            server_config = ContextObj.get_server_config()

            if old_pc_ip != server_config.get("pc_ip", ""):
                LOG.warning("Host IP changed.")

                if not sync:
                    LOG.warning(
                        "Cache is outdated. Please pass `-s/--sync` if command fails."
                    )

                # reset api client handle, so current context will be used while syncing version cache.
                reset_api_client_handle()
                Version.sync()  # sync version cache so that correct version validation happens.

            # While initializing DSL version may not be present in cache, even if we validate version in this case then
            # it will be version of previous context. Therefore, skipping version validation while initializing.
            validate_version()

    except Exception:
        LOG.debug("Could not validate version")
        pass

    # This is added to ensure non compile commands has secrets in the dictionary.
    set_compile_secrets_flag(True)

    ContextObj = get_context()
    project_config = ContextObj.get_project_config()
    project_name = project_config.get("name")

    if project_name == DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        LOG.warning(DSL_CONFIG.EMPTY_PROJECT_MESSAGE)

    if sync:
        Cache.sync()


@main.group(cls=FeatureFlagGroup)
def validate():
    """Validate provider specs"""
    pass


@validate.command("provider_spec")
@click.option(
    "--file",
    "-f",
    "spec_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of provider spec file",
)
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(get_provider_types()),
    default=None,
    help="Provider type",
)
def validate_provider_spec(spec_file, provider_type):
    """validates provider spec for given provider"""

    with open(spec_file) as f:
        spec = yaml.safe_load(f.read())

    if provider_type == None:
        spec_type = spec.get("type", None)
        recommended_type = "AHV_VM"

        if spec_type == "PROVISION_AWS_VM":
            recommended_type = "AWS_VM"
        elif spec_type == "PROVISION_AZURE_VM":
            recommended_type = "AZURE_VM"
        elif spec_type == "PROVISION_GCP_VM":
            recommended_type = "GCP_VM"
        elif spec_type == "PROVISION_VMWARE_VM":
            recommended_type = "VMWARE_VM"

        if spec_type == None:
            LOG.warning(
                "You haven't chosen a provider type, so we'll proceed with '{}'.".format(
                    recommended_type
                )
            )
        else:
            LOG.warning(
                "You haven't chosen a provider type, and it should be '{}' according to your spec file, so we'll proceed with that.".format(
                    recommended_type
                )
            )
        provider_type = recommended_type

    try:
        Provider = get_provider(provider_type)
        Provider.validate_spec(spec)

        LOG.info("File {} is a valid {} spec.".format(spec_file, provider_type))
    except Exception as ee:
        LOG.info("File {} is invalid {} spec".format(spec_file, provider_type))
        raise Exception(ee.message)


@main.group(cls=FeatureFlagGroup)
def get():
    """Get various things like blueprints, apps: `get apps`, `get bps`, `get endpoints` and `get runbooks` are the primary ones."""
    pass


@main.group(cls=FeatureFlagGroup)
@click.pass_context
def show(ctx):
    """Shows the cached data(Dynamic data) etc."""
    pass


def make_default_short_help(help, max_length=45):
    """Return a condensed version of help string."""
    if not help:
        return ""

    words = help.split()
    total_length = 0
    result = []
    done = False

    for word in words:
        if word[-1:] == ".":
            done = True
        new_length = 1 + len(word) if result else len(word)
        if total_length + new_length > max_length:
            result.append("...")
            done = True
        else:
            if result:
                result.append(" ")
            result.append(word)
        if done:
            break
        total_length += new_length

    return "".join(result)


@show.command("commands")
@click.pass_context
def show_all_commands(ctx):
    """show all commands of dsl cli"""

    ctx_root = ctx.find_root()
    root_cmd = ctx_root.command

    commands_queue = []
    commands_res_list = []

    for subcommand in root_cmd.list_commands(ctx):
        cmd = root_cmd.get_command(ctx, subcommand)

        if isinstance(cmd, FeatureFlagGroup):
            commands_queue.append([subcommand, cmd])
        else:
            if root_cmd.experimental_cmd_map.get(subcommand, False):
                is_experimental = True
            else:
                is_experimental = "-"
            commands_res_list.append(
                (
                    subcommand,
                    getattr(cmd, "__doc__", ""),
                    root_cmd.feature_version_map.get(subcommand, "-"),
                    is_experimental,
                )
            )

    while commands_queue:
        ele = commands_queue.pop(0)
        grp = ele.pop(len(ele) - 1)

        for subcommand in grp.list_commands(ctx):
            cmd = grp.get_command(ctx, subcommand)

            if isinstance(cmd, FeatureFlagGroup):
                ele_temp = copy.deepcopy(ele)
                ele_temp.extend([subcommand, cmd])
                commands_queue.append(ele_temp)
            else:
                ele_temp = copy.deepcopy(ele)
                ele_temp.append(subcommand)
                if grp.experimental_cmd_map.get(subcommand, False):
                    is_experimental = True
                else:
                    is_experimental = "-"
                commands_res_list.append(
                    (
                        " ".join(ele_temp),
                        getattr(cmd, "__doc__", ""),
                        grp.feature_version_map.get(subcommand, "-"),
                        is_experimental,
                    )
                )

    table = PrettyTable()
    table.field_names = ["COMMAND", "HELP", "MIN COMMAND VERSION", "EXPERIMENTAL"]

    for cmd_tuple in commands_res_list:
        cmd_str = "{} {}".format(ctx_root.command_path, cmd_tuple[0])
        cmd_help = make_default_short_help(cmd_tuple[1])
        table.add_row(
            [
                highlight_text(cmd_str),
                highlight_text(cmd_help),
                highlight_text(cmd_tuple[2]),
                highlight_text(cmd_tuple[3]),
            ]
        )

    # left align the command column
    table.align["COMMAND"] = "l"
    click.echo(table)


@main.group(cls=FeatureFlagGroup)
def clear():
    """Clear the data stored in local db: cache, secrets etc."""
    pass


@main.group(cls=FeatureFlagGroup)
def init():
    """Initializes the dsl for basic configs and bp directory etc."""
    pass


@get.group(cls=FeatureFlagGroup)
def server():
    """Get calm server details"""
    pass


@server.command("status")
def get_server_status():
    """Get calm server connection status"""

    LOG.info("Checking if Calm is enabled on Server")
    client = get_api_client()
    Obj = get_resource_api("services/nucalm/status", client.connection)
    res, err = Obj.read()

    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    service_enablement_status = result["service_enablement_status"]

    res, err = client.version.get_calm_version()
    calm_version = res.content.decode("utf-8")

    LOG.info(service_enablement_status)
    LOG.info("Server URL: {}".format(client.connection.base_url))
    LOG.info("Calm Version: {}".format(calm_version))

    res, err = client.version.get_pc_version()
    if not err:
        res = res.json()
        pc_version = res["version"]
        LOG.info("PC Version: {}".format(pc_version))


@main.group(cls=FeatureFlagGroup)
def format():
    """Format blueprint using black"""
    pass


@main.group(cls=FeatureFlagGroup)
def compile():
    """Compile blueprint to json / yaml"""

    # Setting this to make sure during compile secrets are not printed
    set_compile_secrets_flag(EnvConfig.is_compile_secret())


@main.group(cls=FeatureFlagGroup)
def decompile():
    """ """
    pass


@main.group(cls=FeatureFlagGroup)
def create():
    """Create entities in Calm (blueprint, project, endpoint, runbook)"""
    pass


@main.group(cls=FeatureFlagGroup)
def delete():
    """Delete entities"""
    pass


@main.group(cls=FeatureFlagGroup)
def launch():
    """Launch blueprints to create Apps"""
    pass


@main.group(cls=FeatureFlagGroup)
def publish():
    """Publish blueprints to marketplace"""
    pass


@main.group(cls=FeatureFlagGroup)
def approve():
    """Approve blueprints in marketplace manager or approve event triggered by approval policies"""
    pass


@main.group(cls=FeatureFlagGroup)
def unpublish():
    """Unpublish blueprints from marketplace"""
    pass


@main.group(cls=FeatureFlagGroup)
def reject():
    """Reject blueprints from marketplace manager or reject event triggered by approval policies"""
    pass


@main.group(cls=FeatureFlagGroup)
def enable():
    """Enable policies"""
    pass


@main.group(cls=FeatureFlagGroup)
def disable():
    """Disable policies"""
    pass


@main.group(cls=FeatureFlagGroup)
def describe():
    """Describe apps, blueprints, projects, accounts, endpoints, runbooks, providers"""
    pass


@main.group(cls=FeatureFlagGroup)
def run():
    """Run actions in an app or runbooks"""
    pass


@main.group(cls=FeatureFlagGroup)
def watch():
    """Track actions running on apps or runbook executions"""
    pass


@main.group(cls=FeatureFlagGroup)
def pause():
    """Pause running runbook executions"""
    pass


@main.group(cls=FeatureFlagGroup)
def resume():
    """resume paused runbook executions"""
    pass


@main.group(cls=FeatureFlagGroup)
def abort():
    """Abort runbook executions"""
    pass


@main.group(cls=FeatureFlagGroup)
def reset():
    """Reset entity"""


@create.command("provider_spec")
@click.option(
    "--type",
    "provider_type",
    "-t",
    type=click.Choice(get_provider_types()),
    default="AHV_VM",
    help="Provider type",
)
def create_provider_spec(provider_type):
    """Creates a provider_spec"""

    Provider = get_provider(provider_type)
    Provider.create_spec()


@main.group(cls=FeatureFlagGroup)
def update():
    """Update entities"""
    pass


@main.group(cls=FeatureFlagGroup)
def download():
    """Download entities"""
    pass


completion_cmd_help = """Shell completion for click-completion-command
Available shell types:
\b
  %s
Default type: auto
""" % "\n  ".join(
    "{:<12} {}".format(k, click_completion.core.shells[k])
    for k in sorted(click_completion.core.shells.keys())
)


@main.group(cls=FeatureFlagGroup, help=completion_cmd_help)
def completion():
    pass


@main.command("prompt")
def calmrepl():
    """Enable an interactive prompt shell

    > :help

    REPL help:

    External Commands:

      prefix external commands with "!"

    Internal Commands:

      prefix internal commands with ":"

      :exit, :q, :quit  exits the repl

      :?, :h, :help     displays general help information"""
    repl(click.get_current_context())


@main.group(cls=FeatureFlagGroup)
def set():
    """Sets the entities"""
    pass


@main.group("import", cls=FeatureFlagGroup)
def calm_import():
    """Import entities in Calm (task library)"""
    pass


@get.group("library")
def library_get():
    """Get Library entities"""
    pass


@create.group("library")
def library_create():
    """Create Library entities"""
    pass


@calm_import.group("library")
def library_import():
    """Import Library entities"""
    pass


@describe.group("library")
def library_describe():
    """Describe Library entities"""
    pass


@delete.group("library")
def library_delete():
    """Delete Library entities"""
    pass


@main.group(cls=FeatureFlagGroup)
def sync():
    """Sync platform account"""
    pass


@main.group(cls=FeatureFlagGroup)
def verify():
    """Verify an account"""
    pass


@main.command("run-script")
@click.option(
    "--type",
    "-t",
    "script_type",
    type=click.Choice(test_scripts_type()),
    default="escript",
    help="Type of script that need to be tested.",
)
@click.option(
    "--file",
    "-f",
    "script_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="File path of script that need to be tested",
)
@click.option(
    "--project",
    "-p",
    "project_name",
    help="Project used by test scripts",
)
@click.option(
    "--endpoint",
    "-e",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Endpoint to be used while testing shell scripts, powershell scripts and python remote tasks",
)
def run_script(script_type, script_file, project_name, endpoint_file):
    """Tests escripts/shell_scripts/powershell/python scripts for syntactical errors"""
    if script_type == "escript":
        test_escript(script_file, project_name)

    elif script_type == "shell":
        test_shell_script(script_file, endpoint_file, project_name)

    elif script_type == "powershell":
        test_powershell_script(script_file, endpoint_file, project_name)

    elif script_type == "python":
        test_python_script(script_file, endpoint_file, project_name)

    else:
        LOG.error("Invalid script type {}. Use one of {}".format(test_scripts_type()))
        sys.exit(-1)
