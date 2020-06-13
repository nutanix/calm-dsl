import click
import json
import uuid

from calm.dsl.api import get_api_client
from .main import get, describe, delete, run, create, update
from .utils import Display
from .runbooks import (
    get_runbook,
    get_runbook_list,
    compile_runbook,
    get_previous_runs,
    run_runbook,
    describe_runbook,
    delete_runbook,
    patch_runbook_runtime_editables,
)


@get.command("runbooks")
@click.option("--name", "-n", default=None, help="Runbook name (Optional)")
@click.option(
    "--filter", "filter_by", default=None, help="Filter runbooks by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only runbook names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""
    get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items)


@get.command("run_history")
@click.option(
    "--name",
    "-n",
    default=None,
    help="Search for previous runbook runs by name of runbook (Optional)",
)
@click.option(
    "--filter",
    "filter_by",
    default=None,
    help="Filter previous runbook runs by this string",
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.pass_obj
def _get_previous_runs(obj, name, filter_by, limit, offset):
    """Get previous runbook runs, optionally filtered by a string"""
    get_previous_runs(obj, name, filter_by, limit, offset)


def create_runbook(client, runbook_payload, name=None, description=None):

    runbook_payload.pop("status", None)

    if name:
        runbook_payload["spec"]["name"] = name
        runbook_payload["metadata"]["name"] = name

    if description:
        runbook_payload["spec"]["description"] = description

    runbook_resources = runbook_payload["spec"]["resources"]
    runbook_name = runbook_payload["spec"]["name"]
    runbook_desc = runbook_payload["spec"]["description"]

    return client.runbook.upload_with_secrets(
        runbook_name, runbook_desc, runbook_resources
    )


def create_runbook_from_json(client, path_to_json, name=None, description=None):

    runbook_payload = json.loads(open(path_to_json, "r").read())
    return create_runbook(client, runbook_payload, name=name, description=description)


def create_runbook_from_dsl(client, runbook_file, name=None, description=None):

    runbook_payload = compile_runbook(runbook_file)
    if runbook_payload is None:
        err_msg = "User runbook not found in {}".format(runbook_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_runbook(client, runbook_payload, name=name, description=description)


@create.command("runbook")
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to upload",
)
@click.option("--name", "-n", default=None, help="Runbook name (Optional)")
@click.option("--description", default=None, help="Runbook description (Optional)")
@click.pass_obj
def create_runbook_command(obj, runbook_file, name, description):
    """Creates a runbook"""

    client = get_api_client()

    if runbook_file.endswith(".json"):
        res, err = create_runbook_from_json(
            client, runbook_file, name=name, description=description
        )
    elif runbook_file.endswith(".py"):
        res, err = create_runbook_from_dsl(
            client, runbook_file, name=name, description=description
        )
    else:
        click.echo("Unknown file format {}".format(runbook_file))
        return

    if err:
        click.echo(err["error"])
        return

    runbook = res.json()
    runbook_state = runbook["status"]["state"]
    runbook_name = runbook["status"]["name"]
    click.echo(">> Runbook {} created".format(runbook_name))
    assert runbook_state == "ACTIVE"


def update_runbook(client, runbook_payload, name=None, description=None):

    runbook_payload.pop("status", None)

    if name:
        runbook_payload["spec"]["name"] = name
        runbook_payload["metadata"]["name"] = name

    if description:
        runbook_payload["spec"]["description"] = description

    runbook_resources = runbook_payload["spec"]["resources"]
    runbook_name = runbook_payload["spec"]["name"]
    runbook_desc = runbook_payload["spec"]["description"]

    runbook = get_runbook(client, runbook_payload["spec"]["name"])
    uuid = runbook["metadata"]["uuid"]
    spec_version = runbook["metadata"]["spec_version"]

    return client.runbook.update_with_secrets(
        uuid, runbook_name, runbook_desc, runbook_resources, spec_version
    )


def update_runbook_from_json(client, path_to_json, name=None, description=None):

    runbook_payload = json.loads(open(path_to_json, "r").read())
    return update_runbook(client, runbook_payload, name=name, description=description)


def update_runbook_from_dsl(client, runbook_file, name=None, description=None):

    runbook_payload = compile_runbook(runbook_file)
    if runbook_payload is None:
        err_msg = "User runbook not found in {}".format(runbook_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return update_runbook(client, runbook_payload, name=name, description=description)


@update.command("runbook")
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to upload",
)
@click.option("--name", "-n", default=None, required=True, help="Runbook name")
@click.option("--description", default=None, help="Runbook description (Optional)")
@click.pass_obj
def update_runbook_command(obj, runbook_file, name, description):
    """Updates a runbook"""

    client = get_api_client()

    if runbook_file.endswith(".json"):
        res, err = update_runbook_from_json(
            client, runbook_file, name=name, description=description
        )
    elif runbook_file.endswith(".py"):
        res, err = update_runbook_from_dsl(
            client, runbook_file, name=name, description=description
        )
    else:
        click.echo("Unknown file format {}".format(runbook_file))
        return

    if err:
        click.echo(err["error"])
        return

    runbook = res.json()
    runbook_state = runbook["status"]["state"]
    runbook_name = runbook["status"]["name"]
    click.echo(">> Runbook {} updated".format(runbook_name))
    assert runbook_state == "ACTIVE"


@delete.command("runbook")
@click.argument("runbook_names", nargs=-1)
@click.pass_obj
def _delete_runbook(obj, runbook_names):
    """Deletes a runbook"""

    delete_runbook(obj, runbook_names)


@describe.command("runbook")
@click.argument("runbook_name")
@click.pass_obj
def _describe_runbook(obj, runbook_name):
    """Describe a runbook"""

    describe_runbook(obj, runbook_name)


@run.command("runbook")
@click.argument("runbook_name", required=False)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path of Runbook file to directly run runbook",
)
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults",
)
@click.option(
    "--input-file",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path of input file to get the inputs for runbook",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.pass_obj
def run_runbook_command(
    obj,
    runbook_name,
    watch,
    ignore_runtime_variables,
    runbook_file=None,
    input_file=None,
):

    if runbook_file is None and runbook_name is None:
        click.echo(
            "One of either Runbook Name or Runbook File is required to run runbook."
        )
        return

    client = get_api_client()
    runbook = None

    if runbook_file:
        click.echo(">> Uploading runbook: {}".format(runbook_file))
        name = "runbook" + "_" + str(uuid.uuid4())[:8]
        if runbook_file.endswith(".json"):
            res, err = create_runbook_from_json(client, runbook_file, name=name)
        elif runbook_file.endswith(".py"):
            res, err = create_runbook_from_dsl(client, runbook_file, name=name)
        else:
            click.echo("Unknown file format {}".format(runbook_file))
            return

        if err:
            click.echo(err["error"])
            return

        click.echo(">> Uploaded runbook: {}".format(runbook_file))
        runbook = res.json()
        runbook_id = runbook["metadata"]["uuid"]
    else:
        runbook_id = get_runbook(client, runbook_name)["metadata"]["uuid"]
        res, err = client.runbook.read(runbook_id)
        if err:
            click.echo(err["error"])
            return
        runbook = res.json()

    input_data = {}
    if input_file is not None and input_file.endswith(".json"):
        input_data = json.loads(open(input_file, "r").read())
    elif input_file is not None:
        click.echo("Unknown input file format {}".format(input_file))
        return

    payload = {}
    if not ignore_runtime_variables:
        payload = patch_runbook_runtime_editables(client, runbook)

    def render_runbook(screen):
        screen.clear()
        screen.refresh()
        run_runbook(
            screen, client, runbook_id, watch, input_data=input_data, payload=payload
        )
        if runbook_file:
            res, err = client.runbook.delete(runbook_id)
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))
        screen.wait_for_input(10.0)

    Display.wrapper(render_runbook, watch)
