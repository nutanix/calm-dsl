import click
import json
import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context

from .main import (
    describe,
    get,
    create,
    compile,
    delete,
    test,
    watch,
    abort,
    decompile,
    format,
)
from .providers import (
    describe_provider,
    create_provider_from_dsl,
    compile_provider_command,
    get_providers,
    delete_providers,
    run_provider_verify_command,
    watch_action_execution,
    abort_action_execution,
    run_resource_type_action_command,
    decompile_provider,
    format_provider_file,
)

LOG = get_logging_handle(__name__)


@describe.command("provider")
@click.argument("provider_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_provider(provider_name, out):
    """Describe a provider"""

    describe_provider(provider_name, out)


@get.command("providers", feature_min_version="4.0.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for provider by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter provider by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only provider names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_providers(name, filter_by, limit, offset, quiet, all_items, out):
    """Get providers, optionally filtered by a string"""

    get_providers(name, filter_by, limit, offset, quiet, all_items, out=out)


@create.command("provider", feature_min_version="4.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "provider_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Provider file to upload",
)
@click.option("--name", "-n", default=None, help="Provider name (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing provider with the same name before create.",
)
@click.option(
    "--icon-file",
    "-I",
    "icon_file",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of image to be uploaded as provider icon",
)
@click.option(
    "--icon-name",
    "-i",
    default=None,
    help="Provider icon name",
)
@click.option(
    "--passphrase",
    "-ps",
    "passphrase",
    default=None,
    help="Passphrase for the encrypted secret values in provider",
)
def _create_provider(
    provider_file,
    name,
    force,
    icon_name=None,
    icon_file=None,
    passphrase=None,
):
    """
    Creates a custom provider
    """

    if provider_file.endswith(".py"):
        res, err = create_provider_from_dsl(
            provider_file,
            name=name,
            force_create=force,
            icon_name=icon_name,
            icon_file=icon_file,
            passphrase=passphrase,
        )
    else:
        LOG.error("Unknown file format {}".format(provider_file))
        return

    if err:
        LOG.error(err["error"])
        return

    provider = res.json()

    provider_name = provider["metadata"]["name"]
    provider_uuid = provider["metadata"]["uuid"]
    provider_status = provider.get("status", {})
    provider_state = provider_status.get("state", "DRAFT")
    LOG.debug("Provider {} has state: {}".format(provider_name, provider_state))

    if provider_state == "DRAFT":
        msg_list = provider_status.get("message_list", [])

        if not msg_list:
            LOG.error("Provider {} created with errors.".format(provider_name))
            LOG.debug(json.dumps(provider_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msg = ""
            path = msg_dict.get("path", "")
            if path:
                msg = path + ": "
            msgs.append(msg + msg_dict.get("message", ""))

        LOG.error(
            "Provider {} created with {} error(s):".format(provider_name, len(msg_list))
        )
        click.echo("\n".join(msgs))
        sys.exit(-1)

    LOG.info("Provider {} created successfully.".format(provider_name))

    context = get_context()
    server_config = context.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/dm/self_service/providers/{}".format(
        pc_ip, pc_port, provider_uuid
    )
    stdout_dict = {
        "name": provider_name,
        "uuid": provider_uuid,
        "link": link,
        "state": provider_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


@compile.command("provider", feature_min_version="4.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "provider_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Provider file to compile",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format",
)
def _compile_provider_command(provider_file, out):
    """Compiles a DSL (Python) provider into JSON or YAML"""
    compile_provider_command(provider_file, out)


@delete.command("providers", feature_min_version="4.0.0", experimental=True)
@click.argument("provider_names", nargs=-1)
def _delete_provider(provider_names):
    """Deletes one or more providers"""

    delete_providers(provider_names)


@test.command("provider-verify", feature_min_version="4.0.0", experimental=True)
@click.argument("provider_name")
@click.option(
    "--ignore_input_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore input variables and use defaults",
)
@click.option(
    "--input-file",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path to python file for input variables",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
def _run_provider_verify_command(
    provider_name, watch, ignore_input_variables, input_file=None
):
    """Execute the verify action of Provider specified by name. All input variables will be prompted by default. When passing the 'ignore_input_variables' flag, no variables will be prompted and all default values will be used. The default values can be overridden by passing a Python file via 'input_file'. When passing a Python file, no variables will be prompted.

    \b
    >: input_file: Python file consisting of variables 'variable_list'
    Ex: variable_list = [
        {
            "value": "<Variable Value>",
            "name": "<Variable Name>"
        }
    ]"""
    run_provider_verify_command(
        provider_name, watch, ignore_input_variables, input_file=input_file
    )


@watch.command(
    "provider-verify-execution", feature_min_version="4.0.0", experimental=True
)
@click.argument("runlog_uuid")
def _watch_verify_action_execution(runlog_uuid):
    """Watch the verify action execution using given runlog UUID"""

    watch_action_execution(runlog_uuid)


@abort.command(
    "provider-verify-execution", feature_min_version="4.0.0", experimental=True
)
@click.argument("runlog_uuid")
def _abort_verify_action_execution(runlog_uuid):
    """Abort the verify action execution"""
    abort_action_execution(runlog_uuid)


@test.command("resource-type-action", feature_min_version="4.0.0", experimental=True)
@click.argument("provider_name")
@click.argument("resource_type_name")
@click.argument("action_name")
@click.option(
    "--ignore_input_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore input variables and use defaults",
)
@click.option(
    "--input-file",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path to python file for input variables",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
def _run_resource_type_action_command(
    provider_name,
    resource_type_name,
    action_name,
    watch,
    ignore_input_variables,
    input_file=None,
):
    """Execute a ResourceType action specified by name. All input variables will be prompted by default. When passing the 'ignore_input_variables' flag, no variables will be prompted and all default values will be used. The default values can be overridden by passing a Python file via 'input_file'. When passing a Python file, no variables will be prompted.

    \b
    >: input_file: Python file consisting of variables 'variable_list'
    Ex: variable_list = [
        {
            "value": "<Variable Value>",
            "name": "<Variable Name>"
        }
    ]"""
    run_resource_type_action_command(
        provider_name,
        resource_type_name,
        action_name,
        watch,
        ignore_input_variables,
        input_file=input_file,
    )


@watch.command(
    "resource-type-action-execution", feature_min_version="4.0.0", experimental=True
)
@click.argument("runlog_uuid")
def _watch_rt_action_execution(runlog_uuid):
    """Watch the ResourceType action execution using given runlog UUID"""

    watch_action_execution(runlog_uuid)


@abort.command(
    "resource-type-action-execution", feature_min_version="4.0.0", experimental=True
)
@click.argument("runlog_uuid")
def _abort_rt_action_execution(runlog_uuid):
    """Abort the ResourceType action execution"""
    abort_action_execution(runlog_uuid)


@decompile.command("provider", feature_min_version="4.0.0", experimental=True)
@click.argument("name", required=False)
@click.option(
    "--file",
    "-f",
    "provider_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to Provider file",
)
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Interactive Mode to provide the value for secrets",
)
@click.option(
    "--passphrase",
    "-ps",
    "passphrase",
    default=None,
    required=False,
    help="Passphrase to import secrets",
)
@click.option(
    "--prefix",
    "-p",
    default="",
    help="Prefix used for appending to entities name(Reserved name cases)",
)
@click.option(
    "--dir",
    "-d",
    "provider_dir",
    default=None,
    help="Provider directory location used for placing decompiled entities",
)
@click.option(
    "--no-format",
    "-nf",
    "no_format",
    is_flag=True,
    default=False,
    help="Disable formatting the decompiled provider using black",
)
def _decompile_provider(
    name, provider_file, with_secrets, prefix, provider_dir, passphrase, no_format
):
    """Decompiles provider present on server or json file"""

    decompile_provider(
        name,
        provider_file,
        with_secrets,
        prefix,
        provider_dir,
        passphrase,
        no_format=no_format,
    )


@format.command("provider", feature_min_version="4.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "provider_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Provider file to format",
)
def _format_provider_command(provider_file):
    """Formats Provider DSL file using black"""

    format_provider_file(provider_file)
