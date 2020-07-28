# import json
# import time
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
from .constants import RUNBOOK  # , RUNLOG
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
        filter_query += get_states_filter(RUNBOOK.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.runbook.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch tasks from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No runbook found !!!\n"))
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
        "EXECUTION HISTORY",
        "CREATED BY",
        "LAST EXECUTED AT",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_by = metadata.get("owner_reference", {}).get("name", "-")
        last_run = int(row.get("last_run_time", 0)) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        project = metadata.get("project_reference", {}).get("name", "")
        total_runs = int(row.get("run_count", 0)) + int(row.get("running_runs", 0))

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(total_runs if total_runs else "-"),
                highlight_text(created_by),
                "{}".format(arrow.get(last_run).humanize()) if last_run else "-",
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)
