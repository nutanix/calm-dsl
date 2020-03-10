import json
import click

from calm.dsl.api import get_api_client

from .secrets import find_secret, create_secret
from .utils import highlight_text
from .main import get, compile, describe, create, launch, delete
from .bps import (
    get_blueprint_list,
    describe_bp,
    compile_blueprint_command,
    compile_blueprint,
    launch_blueprint_simple,
    delete_blueprint,
)
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("bps")
@click.option("--name", "-n", default=None, help="Search for blueprints by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter blueprints by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_blueprint_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""

    get_blueprint_list(name, filter_by, limit, offset, quiet, all_items)


@describe.command("bp")
@click.argument("bp_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [json|yaml].",
)
def _describe_bp(bp_name, out):
    """Describe a blueprint"""

    describe_bp(bp_name, out)


@compile.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
@click.option(
    "--no-sync",
    "-n",
    is_flag=True,
    default=False,
    help="Doesn't sync the cache on compilation",
)
def _compile_blueprint_command(bp_file, out, no_sync):
    """Compiles a DSL (Python) blueprint into JSON or YAML"""
    compile_blueprint_command(bp_file, out, no_sync)


def create_blueprint(client, bp_payload, name=None, description=None, categories=None):

    bp_payload.pop("status", None)

    credential_list = bp_payload["spec"]["resources"]["credential_definition_list"]
    for cred in credential_list:
        if cred["secret"].get("secret", None):
            secret = cred["secret"].pop("secret")

            try:
                value = find_secret(secret)

            except ValueError:
                click.echo(
                    "\nNo secret corresponding to '{}' found !!!\n".format(secret)
                )
                value = click.prompt("Please enter its value", hide_input=True)

                choice = click.prompt(
                    "\n{}(y/n)".format(highlight_text("Want to store it locally")),
                    default="n",
                )
                if choice[0] == "y":
                    create_secret(secret, value)

            cred["secret"]["value"] = value

    if name:
        bp_payload["spec"]["name"] = name
        bp_payload["metadata"]["name"] = name

    if description:
        bp_payload["spec"]["description"] = description

    bp_resources = bp_payload["spec"]["resources"]
    bp_name = bp_payload["spec"]["name"]
    bp_desc = bp_payload["spec"]["description"]

    categories = bp_payload["metadata"].get("categories", None)

    return client.blueprint.upload_with_secrets(
        bp_name, bp_desc, bp_resources, categories=categories
    )


def create_blueprint_from_json(client, path_to_json, name=None, description=None):

    bp_payload = json.loads(open(path_to_json, "r").read())
    return create_blueprint(client, bp_payload, name=name, description=description)


def create_blueprint_from_dsl(client, bp_file, name=None, description=None):

    bp_payload = compile_blueprint(bp_file)
    if bp_payload is None:
        err_msg = "User blueprint not found in {}".format(bp_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_blueprint(client, bp_payload, name=name, description=description)


@create.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Blueprint file to upload",
)
@click.option("--name", "-n", default=None, help="Blueprint name (Optional)")
@click.option(
    "--description", "-d", default=None, help="Blueprint description (Optional)"
)
def create_blueprint_command(bp_file, name, description):
    """Creates a blueprint"""

    client = get_api_client()

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description
        )
    elif bp_file.endswith(".py"):
        res, err = create_blueprint_from_dsl(
            client, bp_file, name=name, description=description
        )
    else:
        LOG.error("Unknown file format {}".format(bp_file))
        return

    if err:
        LOG.error(err["error"])
        return

    bp = res.json()
    bp_state = bp["status"]["state"]
    LOG.info("Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"


@launch.command("bp")
@click.argument("blueprint_name")
@click.option("--app_name", "-a", default=None, help="Name of your app")
@click.option(
    "--profile_name",
    "-p",
    default=None,
    help="Name of app profile to be used for blueprint launch",
)
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults",
)
def launch_blueprint_command(
    blueprint_name, app_name, ignore_runtime_variables, profile_name, blueprint=None,
):

    launch_blueprint_simple(
        blueprint_name,
        app_name,
        blueprint=blueprint,
        profile_name=profile_name,
        patch_editables=not ignore_runtime_variables,
    )


@delete.command("bp")
@click.argument("blueprint_names", nargs=-1)
def _delete_blueprint(blueprint_names):
    """Deletes a blueprint"""

    delete_blueprint(blueprint_names)
