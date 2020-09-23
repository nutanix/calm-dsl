import click
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.builtins import Ref
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_groups(name, filter_by, limit, offset, quiet, out):
    """ Get the groups, optionally filtered by a string """

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

    res, err = client.group.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch groups from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No group found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            name = row["resources"]["directory_service_user_group"][
                "distinguished_name"
            ]
            click.echo(highlight_text(name))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "DISPLAY NAME", "TYPE", "STATE", "UUID"]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        table.add_row(
            [
                highlight_text(
                    row["resources"]["directory_service_user_group"][
                        "distinguished_name"
                    ]
                ),
                highlight_text(row["resources"].get("display_name", "")),
                highlight_text(row["resources"]["user_group_type"]),
                highlight_text(row["state"]),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)


def create_group(name):

    client = get_api_client()
    group_payload = {
        "spec": {
            "resources": {"directory_service_user_group": {"distinguished_name": name}}
        },
        "metadata": {"kind": "user_group", "spec_version": 0},
    }

    res, err = client.group.create(group_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": name,
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


def delete_group(group_names):

    client = get_api_client()

    for name in group_names:
        group_ref = Ref.Group(name)
        res, err = client.group.delete(group_ref["uuid"])
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        LOG.info("Group '{}' deleted".format(name))
    LOG.warning("Please update cache.")
