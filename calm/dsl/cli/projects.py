import time
import warnings
import click
import arrow
from prettytable import PrettyTable

from .utils import get_name_query, highlight_text


def get_projects(obj, name, filter_by, limit, offset, quiet):
    """ Get the projects, optionally filtered by a string"""

    client = obj.get("client")
    config = obj.get("config")

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    # right now there is no support for filter by state of project

    if filter_query:
        params["filter"] = filter_query

    res, err = client.project.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch projects from {}".format(pc_ip)))
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
        "STATE",
        "OWNER",
        "USER COUNT",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        creation_time = arrow.get(metadata["creation_time"]).timestamp
        last_update_time = arrow.get(metadata["last_update_time"])

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(row["state"]),
                highlight_text(metadata["owner_reference"]["name"]),
                highlight_text(len(row["resources"]["user_reference_list"])),
                highlight_text(time.ctime(creation_time)),
                "{}".format(last_update_time.humanize()),
                highlight_text(metadata["uuid"])
            ]
        )
    click.echo(table)
