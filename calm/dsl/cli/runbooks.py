import time
import warnings
import json
import importlib.util
from pprint import pprint

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable

from .utils import get_name_query, get_states_filter, highlight_text


def get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""

    client = obj.get("client")
    config = obj.get("config")

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by

    # TODO
    # if all_items:
    #    filter_query += get_states_filter(BLUEPRINT.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.runbook.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(pc_ip)))
        return

    json_rows = res.json()["entities"]

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DESCRIPTION",
        "RUN COUNT",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(row["run_count"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)
