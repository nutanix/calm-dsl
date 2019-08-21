from ruamel import yaml
import click
import click_completion
import click_completion.core

# TODO - move providers to separate file
from calm.dsl.providers import get_provider, get_provider_types
from calm.dsl.tools import ping
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client

from .projects import (
    get_projects,
    delete_project,
    create_project,
    describe_project,
    update_project,
)
from .accounts import get_accounts, delete_account, describe_account

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

click_completion.init()


@click.group(context_settings=CONTEXT_SETTINGS)
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
    """Calm CLI

\b
Commonly used commands:
  calm get apps   -> Get list of apps
  calm get bps   -> Get list of blueprints
  calm launch bp --app_name Fancy-App-1 MyFancyBlueprint   -> Launch a new app from an existing blueprint
  calm create bp -f sample_bp.py --name Sample-App-3   -> Upload a new blueprint from a python DSL file
  calm describe app Fancy-App-1   -> Describe an existing app
  calm app Fancy-App-1 -w my_action   -> Run an action on an app
"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(
        ip=ip, port=port, username=username, password=password, config_file=config_file
    )
    ctx.obj["client"] = get_api_client()
    ctx.obj["verbose"] = verbose


@main.group()
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
    "provider_type",
    type=click.Choice(get_provider_types()),
    default="AHV_VM",
    help="Provider type",
)
def validate_provider_spec(spec_file, provider_type):

    with open(spec_file) as f:
        spec = yaml.safe_load(f.read())

    try:
        Provider = get_provider(provider_type)
        Provider.validate_spec(spec)
        click.echo("File {} is a valid {} spec.".format(spec_file, provider_type))
    except Exception as ee:
        click.echo("File {} is invalid {} spec".format(spec_file, provider_type))
        raise ee


@main.group()
def get():
    """Get various things like blueprints, apps: `get apps` and `get bps` are the primary ones."""
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


@get.command("projects")
@click.option("--name", default=None, help="Search for projects by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter projects by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only project names"
)
@click.pass_obj
def _get_projects(obj, name, filter_by, limit, offset, quiet):
    """Get projects, optionally filtered by a string"""
    get_projects(obj, name, filter_by, limit, offset, quiet)


@get.command("accounts")
@click.option("--name", default=None, help="Search for provider account by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter projects by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only account names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--type",
    "account_type",
    default=None,
    help="Search for accounts of specific provider",
    type=click.Choice(["aws", "k8s", "vmware", "azure", "gcp", "nutanix"]),
)
@click.pass_obj  # TODO ADD filter by type of account
def _get_accounts(obj, name, filter_by, limit, offset, quiet, all_items, account_type):
    """Get accounts, optionally filtered by a string"""
    get_accounts(obj, name, filter_by, limit, offset, quiet, all_items, account_type)


@main.group()
def compile():
    """Compile blueprint to json / yaml"""
    pass


@main.group()
def create():
    """Create entities in CALM (blueprint, project) """
    pass


def create_project_from_file(obj, file_location, project_name):

    project_payload = yaml.safe_load(open(file_location, "r").read())
    if project_name:
        project_payload["project_detail"]["name"] = project_name

    return create_project(obj, project_payload)


@create.command("project")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Project file to upload",
    required=True,
)
@click.option(
    "--name", "project_name", type=str, default="", help="Project name(optional)"
)
@click.pass_obj
def _create_project(obj, project_file, project_name):
    """Creates a project"""

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        res, err = create_project_from_file(obj, project_file, project_name)
    else:
        click.echo("Unknown file format")
        return

    if err:
        click.echo(err["error"])
        return

    project = res.json()
    state = project["status"]["state"]
    click.echo(">> Project state: {}".format(state))


@main.group()
def delete():
    """Delete entities"""
    pass


@delete.command("project")
@click.argument("project_names", nargs=-1)
@click.pass_obj
def _delete_project(obj, project_names):
    """Deletes a project"""

    delete_project(obj, project_names)


@delete.command("account")
@click.argument("account_names", nargs=-1)
@click.pass_obj
def _delete_account(obj, account_names):
    """Deletes a account from settings"""

    delete_account(obj, account_names)


@main.group()
def launch():
    """Launch blueprints to create Apps"""
    pass


@main.group()
def describe():
    """Describe apps, blueprints, projects, accounts"""
    pass


@describe.command("project")
@click.argument("project_name")
@click.pass_obj
def _describe_project(obj, project_name):
    """Describe a project"""

    describe_project(obj, project_name)


@describe.command("account")
@click.argument("account_name")
@click.pass_obj
def _describe_account(obj, account_name):
    """Describe a account"""

    describe_account(obj, account_name)


@main.group()
def run():
    """Run actions in an app"""
    pass


@main.group()
def watch():
    """Track actions running on apps"""
    pass


@create.command("provider_spec")
@click.option(
    "--type",
    "provider_type",
    type=click.Choice(get_provider_types()),
    default="AHV_VM",
    help="Provider type",
)
@click.pass_obj
def create_provider_spec(obj, provider_type):
    """Creates a provider_spec"""

    Provider = get_provider(provider_type)
    Provider.create_spec()


@main.group()
def update():
    """Update entities"""
    pass


@update.command("project")
@click.argument("project_name")
@click.option(
    "--file",
    "-f",
    "project_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Project file to upload",
    required=True,
)
@click.pass_obj
def _update_project(obj, project_name, project_file):

    if project_file.endswith(".json") or project_file.endswith(".yaml"):
        payload = yaml.safe_load(open(project_file, "r").read())
        res, err = update_project(obj, project_name, payload)
    else:
        click.echo("Unknown file format")
        return

    if err:
        click.echo(err["error"])
        return

    project = res.json()
    state = project["status"]["state"]
    click.echo(">> Project state: {}".format(state))


@main.group()
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


@main.group(help=completion_cmd_help)
def completion():
    pass


@completion.command()
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
def show(shell, case_insensitive):
    """Show the click-completion-command completion code"""
    extra_env = (
        {"_CLICK_COMPLETION_COMMAND_CASE_INSENSITIVE_COMPLETE": "ON"}
        if case_insensitive
        else {}
    )
    click.echo(click_completion.core.get_code(shell, extra_env=extra_env))


@completion.command()
@click.option(
    "--append/--overwrite", help="Append the completion code to the file", default=None
)
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@click.argument("path", required=False)
def install(append, case_insensitive, shell, path):
    """Install the click-completion-command completion"""
    extra_env = (
        {"_CLICK_COMPLETION_COMMAND_CASE_INSENSITIVE_COMPLETE": "ON"}
        if case_insensitive
        else {}
    )
    shell, path = click_completion.core.install(
        shell=shell, path=path, append=append, extra_env=extra_env
    )
    click.echo("%s completion installed in %s" % (shell, path))
