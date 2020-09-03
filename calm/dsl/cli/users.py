import click
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.builtins import Ref
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_users(name, filter_by, limit, offset, quiet, out):
    """ Get the users, optionally filtered by a string """

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

    res, err = client.user.list(params=params)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch users from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No user found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "DISPLAY NAME", "TYPE", "STATE", "UUID"]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"].get("display_name", "")),
                highlight_text(row["resources"]["user_type"]),
                highlight_text(row["state"]),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)


def create_user(name, directory_service):

    client = get_api_client()

    params = {"length": 1000}
    user_name_uuid_map = client.user.get_name_uuid_map(params)

    if user_name_uuid_map.get("name"):
        LOG.error("User with name {} already exists".format(name))
        sys.exit(-1)

    user_payload = {
        "spec": {
            "resources": {
                "directory_service_user": {
                    "user_principal_name": name,
                    "directory_service_reference": Ref.DirectoryService(
                        directory_service
                    ),
                }
            }
        },
        "metadata": {"kind": "user", "spec_version": 0},
    }

    res, err = client.user.create(user_payload)
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


def delete_user(user_names):

    client = get_api_client()
    params = {"length": 1000}
    user_name_uuid_map = client.user.get_name_uuid_map(params)

    for name in user_names:
        user_uuid = user_name_uuid_map.get(name, "")
        if not user_uuid:
            LOG.error("User {} doesn't exists".format(name))
            sys.exit(-1)

        res, err = client.user.delete(user_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        LOG.info("User {} deleted".format(name))
    LOG.warning("Please update cache.")
