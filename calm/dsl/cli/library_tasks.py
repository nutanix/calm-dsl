import os
import json
import time
import sys
import ntpath

import arrow
import click
from prettytable import PrettyTable

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import (
    get_name_query,
    highlight_text,
    get_states_filter,
)
from .constants import TASKS

# from anytree import NodeMixin, RenderTree

LOG = get_logging_handle(__name__)


def get_tasks_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the tasks, optionally filtered by a string"""

    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"

    if all_items:
        filter_query += get_states_filter(TASKS.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.task.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch tasks from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No tasks found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DESCRIPTION",
        "PROJECT",
        "STATE",
        "TASK TYPE",
        "SCRIPT TYPE",
        "CREATED BY",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_by = metadata.get("owner_reference", {}).get("name", "-")
        last_update_time = int(metadata["last_update_time"]) // 1000000
        projects = []
        for project in row["resources"]["project_reference_list"]:
            projects.append(project["name"])

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(",".join(projects)),
                highlight_text(row["state"]),
                highlight_text(row["resources"]["type"]),
                highlight_text(
                    row.get("resources", {}).get("attrs", {}).get("script_type", "")
                ),
                highlight_text(created_by),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def describe_task(task_name, out):
    """Displays task data"""

    client = get_api_client()
    task = get_task(client, task_name, all=True)

    res, err = client.task.read(task["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    task = res.json()

    if out == "json":
        click.echo(json.dumps(task, indent=4, separators=(",", ": ")))
        return

    projects = []
    for project in task["status"]["resources"]["project_reference_list"]:
        projects.append(project["name"])

    click.echo("\n----Task Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(task_name)
        + " (uuid: "
        + highlight_text(task["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(task["status"]["description"]))
    click.echo("Status: " + highlight_text(task["status"]["state"]))
    click.echo("Task Type: " + highlight_text(task["status"]["resources"]["type"]))
    if task["status"]["resources"]["type"] != TASKS.TASK_TYPES.HTTP:
        click.echo(
            "Script Type: "
            + highlight_text(
                task["status"]
                .get("resources", {})
                .get("attrs", {})
                .get("script_type", "")
            )
        )
    if task["status"]["resources"]["type"] == TASKS.TASK_TYPES.SET_VARIABLE:
        click.echo(
            "Output Variables: "
            + highlight_text(
                task["status"]
                .get("resources", {})
                .get("attrs", {})
                .get("eval_variables", [])
            )
        )
    click.echo(
        "Owner: " + highlight_text(task["metadata"]["owner_reference"]["name"]),
        nl=False,
    )
    click.echo(" Projects: " + highlight_text(",".join(projects)))

    created_on = int(task["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    if task["status"]["resources"]["type"] == TASKS.TASK_TYPES.HTTP:
        click.echo(
            "Request URL: "
            + highlight_text(task["status"]["resources"]["attrs"]["url"])
        )
        click.echo(
            "Request Method: "
            + highlight_text(task["status"]["resources"]["attrs"]["method"])
        )
        click.echo(
            "Content Type: "
            + highlight_text(task["status"]["resources"]["attrs"]["content_type"])
        )
        click.echo(
            "Headers: "
            + highlight_text(
                json.dumps(task["status"]["resources"]["attrs"]["headers"])
            )
        )
        click.echo(
            "Expected Response Options: "
            + highlight_text(
                json.dumps(
                    task["status"]["resources"]["attrs"]["expected_response_params"]
                )
            )
        )
    else:
        click.echo(
            "Script Data: \n\n"
            + highlight_text(task["status"]["resources"]["attrs"]["script"])
        )


def get_task(client, name, all=False):

    # find task
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";state!=DELETED"

    res, err = client.task.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    task = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one task found - {}".format(entities))

        LOG.info("{} found ".format(name))
        task = entities[0]
    else:
        raise Exception("No task found with name {}".format(name))
    return task


def delete_task(task_names):

    client = get_api_client()

    for task_name in task_names:
        task = get_task(client, task_name)
        task_id = task["metadata"]["uuid"]
        res, err = client.task.delete(task_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Task Library item {} deleted".format(task_name))


def create_update_task(client, task_payload, name=None, force_create=None):

    task_payload.pop("status", None)
    task_payload.get("metadata").pop("uuid", None)
    task_payload.get("metadata").pop("last_update_time", None)
    task_payload.get("metadata").pop("owner_reference", None)
    task_payload.get("metadata").pop("creation_time", None)

    # check if task with the given name already exists
    params = {"filter": "name=={};state!=DELETED".format(name)}
    res, err = client.task.list(params=params)

    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) > 0:
            if not force_create:
                err_msg = "Task Library item {} already exists. Use --force to delete existing task library item before create.".format(
                    name
                )
                # ToDo: Add command to edit Tasks Library
                err = {"error": err_msg, "code": -1}
                return None, err

            # --force option used in create. Delete existing task library item with same name.
            task_uuid = entities[0]["metadata"]["uuid"]
            _, err = client.task.delete(task_uuid)
            if err:
                return None, err

    config = get_config()
    project_name = config["PROJECT"]["name"]

    # Fetch project details
    params = {"filter": "name=={}".format(project_name)}
    res, err = client.project.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    if not entities:
        raise Exception("No project with name {} exists".format(project_name))

    project_id = entities[0]["metadata"]["uuid"]

    # Setting project reference
    task_payload["metadata"]["project_reference"] = {
        "kind": "project",
        "uuid": project_id,
        "name": project_name,
    }

    res, err = client.task.create(task_payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.error("Failed to create Task Library item {}".format(name))
        sys.exit(-1)

    return res, err


def create_task_from_json(
    client, path_to_json, name=None, description=None, force_create=False
):

    with open(path_to_json, "r") as f:
        task_payload = json.loads(f.read())

    return create_update_task(
        client, task_payload, name=name, force_create=force_create,
    )


def create_task_using_script_file(
    client,
    task_file,
    script_type,
    task_type,
    out_vars=None,
    name=None,
    description=None,
    force_create=False,
):

    with open(task_file, "r") as f:
        task_file_content = f.read()

    if task_file_content is None:
        err_msg = "User task not found in {}".format(task_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    task_resources = {
        "type": task_type,
        "attrs": {"script": task_file_content, "script_type": script_type},
        "variable_list": [],
    }

    if out_vars:
        task_resources["attrs"]["eval_variables"] = out_vars.split(",")

    task_payload = {
        "spec": {
            "name": name,
            "description": description or "",
            "resources": task_resources,
        },
        "metadata": {"spec_version": 1, "name": name, "kind": "app_task"},
        "api_version": "3.0",
    }

    return create_update_task(
        client, task_payload, name=name, force_create=force_create,
    )


def create_task(task_file, name, description, out_vars, force):
    """Creates a task library item"""

    client = get_api_client()
    if not name:
        task_file_name = ntpath.basename(task_file)
        name = os.path.splitext(task_file_name.replace(" ", "_"))[0]

    if task_file.endswith(".json"):
        if out_vars:
            LOG.error("--out-vars is not allowed for file type (.json)")
            return
        res, err = create_task_from_json(
            client, task_file, name=name, description=description, force_create=force
        )
    elif (
        task_file.endswith(".sh")
        or task_file.endswith(".escript")
        or task_file.endswith(".ps1")
    ):
        if task_file.endswith(".sh"):
            script_type = TASKS.SCRIPT_TYPES.SHELL
        elif task_file.endswith(".escript"):
            script_type = TASKS.SCRIPT_TYPES.ESCRIPT
        elif task_file.endswith(".ps1"):
            script_type = TASKS.SCRIPT_TYPES.POWERSHELL

        if out_vars:
            task_type = TASKS.TASK_TYPES.SET_VARIABLE
        else:
            task_type = TASKS.TASK_TYPES.EXEC

        res, err = create_task_using_script_file(
            client,
            task_file,
            script_type,
            task_type,
            out_vars=out_vars,
            name=name,
            description=description,
            force_create=force,
        )
    else:
        LOG.error("Unknown file format {}".format(task_file))
        return

    if err:
        LOG.error(err["error"])
        return

    LOG.info("Task Library item {} created successfully.".format(name))
