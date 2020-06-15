import json
import time
import pathlib

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable
from black import format_file_in_place, WriteBack, FileMode

from calm.dsl.builtins import Endpoint, create_endpoint_payload
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client

from calm.dsl.tools import get_logging_handle

from .utils import (
    get_name_query,
    highlight_text,
    get_states_filter,
    get_module_from_file,
)
from .constants import ENDPOINT
from calm.dsl.store import Cache

LOG = get_logging_handle(__name__)


def get_endpoint_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the endpoints, optionally filtered by a string"""

    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"

    if all_items:
        filter_query += get_states_filter(ENDPOINT.STATES, state_key="_state")
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.endpoint.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch endpoints from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No endpoint found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "TYPE",
        "DESCRIPTION",
        "PROJECT",
        "STATE",
        "CREATED BY",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_by = metadata.get("owner_reference", {}).get("name", "")
        last_update_time = int(metadata["last_update_time"]) // 1000000
        project = (
            metadata["project_reference"]["name"]
            if "project_reference" in metadata
            else None
        )

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["type"]),
                highlight_text(row["description"]),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(created_by),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)


def get_endpoint_module_from_file(endpoint_file):
    """Return Endpoint module given a user endpoint dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_bp", endpoint_file)


def get_endpoint_class_from_module(user_endpoint_module):
    """Returns endpoint class given a module"""

    UserEndpoint = None
    for item in dir(user_endpoint_module):
        obj = getattr(user_endpoint_module, item)
        if isinstance(obj, type(Endpoint)):
            if obj.__bases__[0] is Endpoint:
                UserEndpoint = obj

    return UserEndpoint


def compile_endpoint(endpoint_file):

    user_endpoint_module = get_endpoint_module_from_file(endpoint_file)
    UserEndpoint = get_endpoint_class_from_module(user_endpoint_module)
    if UserEndpoint is None:
        return None

    endpoint_payload = None
    UserEndpointPayload, _ = create_endpoint_payload(UserEndpoint)
    endpoint_payload = UserEndpointPayload.get_dict()

    return endpoint_payload


def compile_endpoint_command(endpoint_file, out):

    endpoint_payload = compile_endpoint(endpoint_file)
    if endpoint_payload is None:
        LOG.error("User endpoint not found in {}".format(endpoint_file))
        return

    config = get_config()

    project_name = config["PROJECT"].get("name", "default")
    project_cache_data = Cache.get_entity_data(entity_type="project", name=project_name)

    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )

    project_uuid = project_cache_data.get("uuid", "")
    endpoint_payload["metadata"]["project_reference"] = {
        "type": "project",
        "uuid": project_uuid,
        "name": project_name,
    }

    if out == "json":
        click.echo(json.dumps(endpoint_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(endpoint_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def get_endpoint(client, name, all=False):

    # find endpoint
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";deleted==FALSE"

    res, err = client.endpoint.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    endpoint = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one endpoint found - {}".format(entities))

        LOG.info("{} found ".format(name))
        endpoint = entities[0]
    else:
        raise Exception("No endpoint found with name {} found".format(name))
    return endpoint


def describe_endpoint(endpoint_name, out):
    """Displays endpoint data"""

    client = get_api_client()
    endpoint = get_endpoint(client, endpoint_name, all=True)

    res, err = client.endpoint.read(endpoint["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    endpoint = res.json()

    if out == "json":
        endpoint.pop("status", None)
        click.echo(json.dumps(endpoint, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Endpoint Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(endpoint_name)
        + " (uuid: "
        + highlight_text(endpoint["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(endpoint["status"]["description"]))
    click.echo("Status: " + highlight_text(endpoint["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(endpoint["metadata"]["owner_reference"]["name"]),
        nl=False,
    )
    project = endpoint["metadata"].get("project_reference", {})
    click.echo(" Project: " + highlight_text(project.get("name", "")))

    created_on = int(endpoint["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    last_updated = int(endpoint["metadata"]["last_update_time"]) // 1000000
    past = arrow.get(last_updated).humanize()
    click.echo(
        "Last Updated: {} ({})\n".format(
            highlight_text(time.ctime(last_updated)), highlight_text(past)
        )
    )
    endpoint_resources = endpoint.get("status").get("resources", {})

    endpoint_type = endpoint_resources.get("type", "")
    endpoint_attrs = endpoint_resources.get("attrs", {})
    click.echo("Type: {}".format(highlight_text(endpoint_type)))
    if endpoint_type == ENDPOINT.TYPES.HTTP:
        url = endpoint_attrs.get("url", "")
        click.echo("URL: {}\n".format(highlight_text(url)))
    else:
        value_type = endpoint_attrs.get("value_type", "IP")
        value_type += "s"
        values = endpoint_attrs.get("values", [])
        element_count = endpoint_resources.get("element_count")
        click.echo("VM Count: {}".format(highlight_text(element_count)))
        click.echo("{}: {}\n".format(value_type, highlight_text(values)))


def delete_endpoint(endpoint_names):

    client = get_api_client()

    for endpoint_name in endpoint_names:
        endpoint = get_endpoint(client, endpoint_name)
        endpoint_id = endpoint["metadata"]["uuid"]
        res, err = client.endpoint.delete(endpoint_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Endpoint {} deleted".format(endpoint_name))


def format_endpoint_command(endpoint_file):
    path = pathlib.Path(endpoint_file)
    LOG.debug("Formatting endpoint {} using black".format(path))
    if format_file_in_place(
        path, fast=False, mode=FileMode(), write_back=WriteBack.DIFF
    ):
        LOG.info("Patching above diff to endpoint - {}".format(path))
        format_file_in_place(
            path, fast=False, mode=FileMode(), write_back=WriteBack.YES
        )
        LOG.info("All done!")
    else:
        LOG.info("Endpoint {} left unchanged.".format(path))
