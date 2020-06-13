import json
import sys
import uuid

import click

from calm.dsl.api import get_api_client
from calm.dsl.config import get_config
from calm.dsl.tools import get_logging_handle

from .main import get, describe, delete, run, create, update
from .utils import Display
from .runbooks import (
    get_runbook,
    get_runbook_list,
    compile_runbook,
    get_execution_history,
    run_runbook,
    describe_runbook,
    delete_runbook,
    patch_runbook_runtime_editables,
)

LOG = get_logging_handle(__name__)


@get.command("runbooks", feature_min_version="3.0.0")
@click.option("--name", "-n", default=None, help="Search for runbooks by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter runbooks by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option("--offset", "-o", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only runbook names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_runbook_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""

    get_runbook_list(name, filter_by, limit, offset, quiet, all_items)


@get.command("execution_history", feature_min_version="3.0.0")
@click.option(
    "--name",
    "-n",
    default=None,
    help="Search for previous runbook runs by name of runbook (Optional)",
)
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter previous runbook executions by this string",
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option("--offset", "-o", default=0, help="Offset results by the specified amount")
def _get_execution_history(name, filter_by, limit, offset):
    """Get previous runbook executions, optionally filtered by a string"""

    get_execution_history(name, filter_by, limit, offset)


def create_runbook(client, runbook_payload, name=None, description=None, force_create=False):

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
        runbook_name, runbook_desc, runbook_resources, force_create=force_create
    )


def create_runbook_from_json(client, path_to_json, name=None, description=None, force_create=False):

    runbook_payload = json.loads(open(path_to_json, "r").read())
    return create_runbook(client, runbook_payload, name=name, description=description, force_create=force_create)


def create_runbook_from_dsl(client, runbook_file, name=None, description=None, force_create=False):

    runbook_payload = compile_runbook(runbook_file)
    if runbook_payload is None:
        err_msg = "User runbook not found in {}".format(runbook_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_runbook(client, runbook_payload, name=name, description=description, force_create=force_create)


@create.command("runbook", feature_min_version="3.0.0")
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
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing blueprint with the same name before create.",
)
def create_runbook_command(runbook_file, name, description, force):
    """Creates a runbook"""

    client = get_api_client()

    if runbook_file.endswith(".json"):
        res, err = create_runbook_from_json(
            client, runbook_file, name=name, description=description, force_create=force
        )
    elif runbook_file.endswith(".py"):
        res, err = create_runbook_from_dsl(
            client, runbook_file, name=name, description=description, force_create=force
        )
    else:
        LOG.error("Unknown file format {}".format(runbook_file))
        return

    if err:
        LOG.error(err["error"])
        return

    runbook = res.json()
    runbook_uuid = runbook["metadata"]["uuid"]
    runbook_name = runbook["metadata"]["name"]
    runbook_status = runbook.get("status", {})
    runbook_state = runbook_status.get("state", "DRAFT")
    LOG.debug("Runbook {} has state: {}".format(runbook_name, runbook_state))

    if runbook_state != "ACTIVE":
        msg_list = runbook_status.get("message_list", [])
        if not msg_list:
            LOG.error("Runbook {} created with errors.".format(runbook_name))
            LOG.debug(json.dumps(runbook_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error("Runbook {} created with {} error(s): {}".format(runbook_name, len(msg_list), msgs))
        sys.exit(-1)

    LOG.info("Runbook {} created successfully.".format(runbook_name))
    config = get_config()
    pc_ip = config["SERVER"]["pc_ip"]
    pc_port = config["SERVER"]["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/runbooks/{}".format(pc_ip, pc_port, runbook_uuid)
    stdout_dict = {
        "name": runbook_name,
        "link": link,
        "state": runbook_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


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


@update.command("runbook", feature_min_version="3.0.0")
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
def update_runbook_command(runbook_file, name, description):
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
        LOG.error("Unknown file format {}".format(runbook_file))
        return

    if err:
        LOG.error(err["error"])
        return

    runbook = res.json()
    runbook_uuid = runbook["metadata"]["uuid"]
    runbook_name = runbook["metadata"]["name"]
    runbook_status = runbook.get("status", {})
    runbook_state = runbook_status.get("state", "DRAFT")
    LOG.debug("Runbook {} has state: {}".format(runbook_name, runbook_state))

    if runbook_state != "ACTIVE":
        msg_list = runbook_status.get("message_list", [])
        if not msg_list:
            LOG.error("Runbook {} updated with errors.".format(runbook_name))
            LOG.debug(json.dumps(runbook_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error("Runbook {} updated with {} error(s): {}".format(runbook_name, len(msg_list), msgs))
        sys.exit(-1)

    LOG.info("Runbook {} updated successfully.".format(runbook_name))
    config = get_config()
    pc_ip = config["SERVER"]["pc_ip"]
    pc_port = config["SERVER"]["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/runbooks/{}".format(pc_ip, pc_port, runbook_uuid)
    stdout_dict = {
        "name": runbook_name,
        "link": link,
        "state": runbook_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


@delete.command("runbook", feature_min_version="3.0.0")
@click.argument("runbook_names", nargs=-1)
def _delete_runbook(runbook_names):
    """Deletes a runbook"""

    delete_runbook(runbook_names)


@describe.command("runbook", feature_min_version="3.0.0")
@click.argument("runbook_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [json|yaml].",
)
def _describe_runbook(runbook_name, out):
    """Describe a runbook"""

    describe_runbook(runbook_name, out)


@run.command("runbook", feature_min_version="3.0.0")
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
def run_runbook_command(
    runbook_name,
    watch,
    ignore_runtime_variables,
    runbook_file=None,
    input_file=None,
):

    if runbook_file is None and runbook_name is None:
        LOG.error(
            "One of either Runbook Name or Runbook File is required to run runbook."
        )
        return

    client = get_api_client()
    runbook = None

    if runbook_file:
        LOG.info("Uploading runbook: {}".format(runbook_file))
        name = "runbook" + "_" + str(uuid.uuid4())[:8]
        if runbook_file.endswith(".json"):
            res, err = create_runbook_from_json(client, runbook_file, name=name)
        elif runbook_file.endswith(".py"):
            res, err = create_runbook_from_dsl(client, runbook_file, name=name)
        else:
            LOG.error("Unknown file format {}".format(runbook_file))
            return

        if err:
            LOG.error(err["error"])
            return

        LOG.info("Uploaded runbook: {}".format(runbook_file))
        runbook = res.json()
        runbook_id = runbook["metadata"]["uuid"]
    else:
        runbook_id = get_runbook(client, runbook_name)["metadata"]["uuid"]
        res, err = client.runbook.read(runbook_id)
        if err:
            LOG.error(err["error"])
            return
        runbook = res.json()

    input_data = {}
    if input_file is not None and input_file.endswith(".json"):
        input_data = json.loads(open(input_file, "r").read())
    elif input_file is not None:
        LOG.error("Unknown input file format {}".format(input_file))
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
