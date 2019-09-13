import json
import click

from calm.dsl.cli.secrets import find_secret, create_secret
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


@get.command("bps")
@click.option("--name", default=None, help="Search for blueprints by name")
@click.option(
    "--filter", "filter_by", default=None, help="Filter blueprints by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only blueprint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""
    get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items)


@describe.command("bp")
@click.argument("bp_name")
@click.pass_obj
def _describe_bp(obj, bp_name):
    """Describe an app"""
    describe_bp(obj, bp_name)


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
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
def _compile_blueprint_command(bp_file, out):
    """Compiles a DSL (Python) blueprint into JSON or YAML"""
    compile_blueprint_command(bp_file, out)


def create_blueprint(client, bp_payload, name=None, description=None, categories=None):

    bp_payload.pop("status", None)

    credential_list = bp_payload["spec"]["resources"]["credential_definition_list"]
    for cred in credential_list:
        if cred["type"] == "SECRET":   # Finding if secret present
            secret = cred["secret"]["value"]

            try:
                value = find_secret(secret)

            except Exception:
                click.echo("\nNo secret corresponding to {} found !!!\n". format(secret))
                value = click.prompt("Please enter its value", hide_input=True)

                choice = click.prompt(
                    "\n{}(y/n)".format(highlight_text("Want to store it locally")),
                    default="n",
                )
                if choice[0] == "y":
                    create_secret(secret, value)

            cred["secret"]["value"] = value
            cred["type"] = "PASSWORD"   # Restore it to PASSWORD

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
@click.option("--name", default=None, help="Blueprint name (Optional)")
@click.option("--description", default=None, help="Blueprint description (Optional)")
@click.pass_obj
def create_blueprint_command(obj, bp_file, name, description):
    """Creates a blueprint"""

    client = obj.get("client")

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description
        )
    elif bp_file.endswith(".py"):
        res, err = create_blueprint_from_dsl(
            client, bp_file, name=name, description=description
        )
    else:
        click.echo("Unknown file format {}".format(bp_file))
        return

    if err:
        click.echo(err["error"])
        return

    bp = res.json()
    bp_state = bp["status"]["state"]
    click.echo(">> Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"


@launch.command("bp")
@click.argument("blueprint_name")
@click.option("--app_name", default=None, help="Name of your app")
@click.option(
    "--ignore_runtime_variables",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults",
)
@click.pass_obj
def launch_blueprint_command(
    obj, blueprint_name, app_name, ignore_runtime_variables, blueprint=None
):

    client = obj.get("client")

    launch_blueprint_simple(
        client,
        blueprint_name,
        app_name,
        blueprint=blueprint,
        patch_editables=not ignore_runtime_variables,
    )


@delete.command("bp")
@click.argument("blueprint_names", nargs=-1)
@click.pass_obj
def _delete_blueprint(obj, blueprint_names):
    """Deletes a blueprint"""

    delete_blueprint(obj, blueprint_names)
