import json
import time
# import sys
# import uuid
# import pathlib

# from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable
# from black import format_file_in_place, WriteBack, FileMode

# from calm.dsl.runbooks import runbook, create_runbook_payload
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
# from calm.dsl.store import Cache
from .utils import (
    # Display,
    get_name_query,
    highlight_text,
    get_states_filter,
    # get_module_from_file,
)
from .constants import TASKS  # , RUNLOG
# from .runlog import get_completion_func, get_runlog_status
# from .endpoints import get_endpoint

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
        total_runs = int(row.get("run_count", 0)) + int(row.get("running_runs", 0))

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(','.join(projects)),
                highlight_text(row["state"]),
                highlight_text(row["resources"]["type"]),
                highlight_text(row.get("resources", {}).get("attrs", {}).get("script_type", "")),
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
        task.pop("status", None)
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
        click.echo("Script Type: " + highlight_text(task["status"].get("resources", {}).get("attrs", {}).get("script_type", "")))
    click.echo(
        "Owner: " + highlight_text(task["metadata"]["owner_reference"]["name"]), nl=False
    )
    click.echo(
        " Projects: " + highlight_text(','.join(projects))
    )

    created_on = int(task["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    if task["status"]["resources"]["type"] == TASKS.TASK_TYPES.HTTP:
        click.echo(
            "Request URL: " + highlight_text(task["status"]["resources"]["attrs"]["url"])
        )
        click.echo(
            "Request Method: " + highlight_text(task["status"]["resources"]["attrs"]["method"])
        )
        click.echo(
            "Content Type: " + highlight_text(task["status"]["resources"]["attrs"]["content_type"])
        )
        click.echo(
            "Headers: " + highlight_text(json.dumps(task["status"]["resources"]["attrs"]["headers"]))
        )
        click.echo(
            "Expected Response Options: " + highlight_text(json.dumps(task["status"]["resources"]["attrs"]["expected_response_params"]))
        )
    else:
        click.echo(
            "Script Data: \n\n" + highlight_text(task["status"]["resources"]["attrs"]["script"])
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