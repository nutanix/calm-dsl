import time
import warnings
import importlib.util

import arrow
import click
from prettytable import PrettyTable

from calm.dsl.builtins import Endpoint, create_endpoint_payload
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client

from .utils import get_name_query, highlight_text, get_states_filter
from .constants import ENDPOINT


def get_endpoint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the endpoints, optionally filtered by a string"""

    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by

    if all_items:
        filter_query += get_states_filter(ENDPOINT.STATES, state_key="_state")
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.endpoint.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch endpoints from {}".format(pc_ip)))
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
        project = metadata.get("project_reference", {}).get("name", "")

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

    spec = importlib.util.spec_from_file_location("calm.dsl.user_bp", endpoint_file)
    user_endpoint_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_endpoint_module)

    return user_endpoint_module


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

        click.echo(">> Endpoint {} found >>".format(name))
        endpoint = entities[0]
    else:
        raise Exception(">> No endpoint found with name {} found >>".format(name))
    return endpoint


def describe_endpoint(obj, endpoint_name):
    client = get_api_client()
    endpoint = get_endpoint(client, endpoint_name, all=True)

    res, err = client.endpoint.read(endpoint["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    endpoint = res.json()

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


def delete_endpoint(obj, endpoint_names):

    client = get_api_client()

    for endpoint_name in endpoint_names:
        endpoint = get_endpoint(client, endpoint_name)
        endpoint_id = endpoint["metadata"]["uuid"]
        res, err = client.endpoint.delete(endpoint_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        click.echo("Endpoint {} deleted".format(endpoint_name))
