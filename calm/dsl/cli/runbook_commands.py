import click
import json
import uuid

from .main import get, describe, delete, run, create
from .utils import Display
from .runbooks import (
    get_runbook_list,
    compile_runbook,
    get_previous_runs,
    run_runbook,
    describe_runbook,
    delete_runbook,
)


@get.command("runbooks")
@click.option("--name", default=None, help="Search for runbooks by name")
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


@get.command("previous_runs")
@click.option("--name", default=None, help="Search for previous runbook runs by name of runbook")
@click.option("--filter", "filter_by", default=None, help="Filter previous runbook runs by this string")
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only runbook names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_previous_runs(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get previous runbook runs, optionally filtered by a string"""
    get_previous_runs(obj, name, filter_by, limit, offset, quiet, all_items)


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
@click.option("--name", default=None, help="Runbook name (Optional)")
@click.option("--description", default=None, help="Runbook description (Optional)")
@click.pass_obj
def create_runbook_command(obj, runbook_file, name, description):
    """Creates a runbook"""

    client = obj.get("client")

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
    click.echo(">> Runbook state: {}".format(runbook_state))
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
    help="Path of Runbook file to directly run runbook"
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.pass_obj
def run_runbook_command(obj, runbook_name, watch, runbook_file=None):

    if runbook_file is None and runbook_name is None:
        click.echo("One of either Runbook Name or Runbook File is required to run runbook.")
        return

    client = obj.get("client")
    runbook = None

    if runbook_file:
        click.echo(">> Uploading runbook: {}".format(runbook_file))
        name = "runbook" + "_" + str(uuid.uuid4())[:8]
        if runbook_file.endswith(".json"):
            res, err = create_runbook_from_json(
                client, runbook_file, name=name
            )
        elif runbook_file.endswith(".py"):
            res, err = create_runbook_from_dsl(
                client, runbook_file, name=name
            )
        else:
            click.echo("Unknown file format {}".format(runbook_file))
            return

        if err:
            click.echo(err["error"])
            return

        click.echo(">> Uploaded runbook: {}".format(runbook_file))
        runbook = res.json()
        runbook_id = runbook["metadata"]["uuid"]
        res, err = client.runbook.delete(runbook_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

    def render_runbook(screen):
        screen.clear()
        screen.refresh()
        run_runbook(screen, client, runbook_name, watch, runbook=runbook)
        screen.wait_for_input(10.0)

    Display.wrapper(render_runbook, watch)
