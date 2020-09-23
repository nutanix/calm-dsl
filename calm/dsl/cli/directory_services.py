import click
import json
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_directory_services(name, filter_by, limit, offset, quiet, out):
    """ Get the directory services, optionally filtered by a string """

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.directory_service.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch directory_services from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No directory service found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DIRECTORY TYPE",
        "DOMAIN NAME",
        "URL",
        "STATE",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"]["directory_type"]),
                highlight_text(row["resources"]["domain_name"]),
                highlight_text(row["resources"]["url"]),
                highlight_text(row["state"]),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)
