from ruamel import yaml
import click
import json

import click_completion
import click_completion.core
from click_didyoumean import DYMGroup
from click_repl import repl

# TODO - move providers to separate file
from calm.dsl.providers import get_provider, get_provider_types
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.tools import get_logging_handle, simple_verbosity_option, show_trace_option

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

click_completion.init()
LOG = get_logging_handle(__name__)


@click.group(context_settings=CONTEXT_SETTINGS)
@simple_verbosity_option(LOG)
@show_trace_option(LOG)
@click.version_option("0.1")
@click.pass_context
def main(ctx):
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
    ctx.obj["verbose"] = True


@main.group(cls=DYMGroup)
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

    with open(spec_file) as f:
        spec = yaml.safe_load(f.read())

    try:
        Provider = get_provider(provider_type)
        Provider.validate_spec(spec)

        LOG.info("File {} is a valid {} spec.".format(spec_file, provider_type))
    except Exception as ee:
        LOG.info("File {} is invalid {} spec".format(spec_file, provider_type))
        raise Exception(ee.message)


@main.group(cls=DYMGroup)
def get():
    """Get various things like blueprints, apps: `get apps` and `get bps` are the primary ones."""
    pass


@main.group(cls=DYMGroup)
def show():
    """Shows the cached data(Dynamic data) etc."""
    pass


@main.group(cls=DYMGroup)
def clear():
    """Clear the data stored in local db: cache, secrets etc."""
    pass


@main.group(cls=DYMGroup)
def init():
    """Initializes the dsl for basic configs and bp directory etc."""
    pass


@get.group(cls=DYMGroup)
def server():
    """Get calm server details"""
    pass


@server.command("status")
@click.pass_obj
def get_server_status(obj):
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

    LOG.info(service_enablement_status)
    LOG.info("Server URL: {}".format(client.connection.base_url))
    # TODO - Add info about PC and Calm server version


@main.group(cls=DYMGroup)
def compile():
    """Compile blueprint to json / yaml"""
    pass


@main.group(cls=DYMGroup)
def create():
    """Create entities in CALM (blueprint, project) """
    pass


@main.group(cls=DYMGroup)
def delete():
    """Delete entities"""
    pass


@main.group(cls=DYMGroup)
def launch():
    """Launch blueprints to create Apps"""
    pass


@main.group(cls=DYMGroup)
def publish():
    """Publish blueprints to marketplace"""
    pass


@main.group(cls=DYMGroup)
def approve():
    """Approve blueprints in marketplace manager"""
    pass


@main.group(cls=DYMGroup)
def unpublish():
    """Unpublish blueprints from marketplace"""
    pass


@main.group(cls=DYMGroup)
def reject():
    """Reject blueprints from marketplace manager"""
    pass


@main.group(cls=DYMGroup)
def describe():
    """Describe apps, blueprints, projects, accounts"""
    pass


@main.group(cls=DYMGroup)
def run():
    """Run actions in an app"""
    pass


@main.group(cls=DYMGroup)
def watch():
    """Track actions running on apps"""
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
@click.pass_obj
def create_provider_spec(obj, provider_type):
    """Creates a provider_spec"""

    Provider = get_provider(provider_type)
    Provider.create_spec()


@main.group(cls=DYMGroup)
def update():
    """Update entities"""
    pass


@main.group(cls=DYMGroup)
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


@main.group(cls=DYMGroup, help=completion_cmd_help)
def completion():
    pass


@main.command("prompt")
def calmrepl():
    """Enable an interactive prompt shell"""
    repl(click.get_current_context())


@main.group(cls=DYMGroup)
def set():
    """Sets the entities"""
    pass
