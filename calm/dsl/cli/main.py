from ruamel import yaml
import click
import json
import copy

import click_completion
import click_completion.core
from click_repl import repl
from prettytable import PrettyTable

# TODO - move providers to separate file
from calm.dsl.providers import get_provider, get_provider_types
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context
from calm.dsl.store import Cache

from .version_validator import validate_version
from .click_options import simple_verbosity_option, show_trace_option
from .utils import FeatureFlagGroup, highlight_text

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
@click.version_option("0.1")
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
        validate_version()
    except Exception:
        LOG.debug("Could not validate version")
        pass
    if config_file:
        ContextObj = get_context()
        ContextObj.update_config_file_context(config_file=config_file)
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
    default="AHV_VM",
    help="Provider type",
)
def validate_provider_spec(spec_file, provider_type):
    """validates provider spec for given provider"""

    with open(spec_file) as f:
        spec = yaml.safe_load(f.read())

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
    pass


@main.group(cls=FeatureFlagGroup)
def decompile():
    """"""
    pass


@main.group(cls=FeatureFlagGroup)
def create():
    """Create entities in Calm (blueprint, project, endpoint, runbook) """
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
    """Approve blueprints in marketplace manager"""
    pass


@main.group(cls=FeatureFlagGroup)
def unpublish():
    """Unpublish blueprints from marketplace"""
    pass


@main.group(cls=FeatureFlagGroup)
def reject():
    """Reject blueprints from marketplace manager"""
    pass


@main.group(cls=FeatureFlagGroup)
def describe():
    """Describe apps, blueprints, projects, accounts, endpoints, runbooks"""
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
