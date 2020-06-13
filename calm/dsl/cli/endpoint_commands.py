import sys
import click
import json

from calm.dsl.api import get_api_client
from calm.dsl.config import get_config
from calm.dsl.tools import get_logging_handle

from .main import get, describe, delete, create
from .endpoints import (
    get_endpoint_list,
    compile_endpoint,
    delete_endpoint,
    describe_endpoint,
)

LOG = get_logging_handle(__name__)


@get.command("endpoints", feature_min_version="3.0.0")
@click.option("--name", "-n", default=None, help="Search for endpoints by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter endpoints by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option("--offset", "-o", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only endpoint names"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_endpoint_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the endpoints, optionally filtered by a string"""

    get_endpoint_list(name, filter_by, limit, offset, quiet, all_items)


def create_endpoint(client, endpoint_payload, name=None, description=None, force_create=False):

    endpoint_payload.pop("status", None)

    if name:
        endpoint_payload["spec"]["name"] = name
        endpoint_payload["metadata"]["name"] = name

    if description:
        endpoint_payload["spec"]["description"] = description

    endpoint_resources = endpoint_payload["spec"]["resources"]
    endpoint_name = endpoint_payload["spec"]["name"]
    endpoint_desc = endpoint_payload["spec"]["description"]

    return client.endpoint.upload_with_secrets(
        endpoint_name, endpoint_desc, endpoint_resources, force_create=force_create,
    )


def create_endpoint_from_json(client, path_to_json, name=None, description=None, force_create=False):

    endpoint_payload = json.loads(open(path_to_json, "r").read())
    return create_endpoint(client, endpoint_payload, name=name, description=description, force_create=force_create)


def create_endpoint_from_dsl(client, endpoint_file, name=None, description=None, force_create=False):

    endpoint_payload = compile_endpoint(endpoint_file)
    if endpoint_payload is None:
        err_msg = "User endpoint not found in {}".format(endpoint_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_endpoint(client, endpoint_payload, name=name, description=description, force_create=force_create)


@create.command("endpoint", feature_min_version="3.0.0")
@click.option(
    "--file",
    "-f",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Endpoint file to upload",
)
@click.option("--name", "-n", default=None, help="Endpoint name (Optional)")
@click.option("--description", default=None, help="Endpoint description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing blueprint with the same name before create.",
)
def create_endpoint_command(endpoint_file, name, description, force):
    """Creates a endpoint"""

    client = get_api_client()

    if endpoint_file.endswith(".json"):
        res, err = create_endpoint_from_json(
            client, endpoint_file, name=name, description=description, force_create=force
        )
    elif endpoint_file.endswith(".py"):
        res, err = create_endpoint_from_dsl(
            client, endpoint_file, name=name, description=description, force_create=force
        )
    else:
        LOG.error("Unknown file format {}".format(endpoint_file))
        return

    if err:
        LOG.error(err["error"])
        return

    endpoint = res.json()
    endpoint_uuid = endpoint["metadata"]["uuid"]
    endpoint_name = endpoint["metadata"]["name"]
    endpoint_status = endpoint.get("status", {})
    endpoint_state = endpoint_status.get("state", "DRAFT")
    LOG.debug("Endpoint {} has state: {}".format(endpoint_name, endpoint_state))

    if endpoint_state != "ACTIVE":
        msg_list = endpoint_status.get("message_list", [])
        if not msg_list:
            LOG.error("Endpoint {} created with errors.".format(endpoint_name))
            LOG.debug(json.dumps(endpoint_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error("Endpoint {} created with {} error(s): {}.".format(endpoint_name, len(msg_list), msgs))
        sys.exit(-1)

    LOG.info("Endpoint {} created successfully.".format(endpoint_name))
    config = get_config()
    pc_ip = config["SERVER"]["pc_ip"]
    pc_port = config["SERVER"]["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/endpoints/{}".format(pc_ip, pc_port, endpoint_uuid)

    stdout_dict = {
        "name": endpoint_name,
        "link": link,
        "state": endpoint_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


@delete.command("endpoint", feature_min_version="3.0.0")
@click.argument("endpoint_names", nargs=-1)
def _delete_endpoint(endpoint_names):
    """Deletes endpoints"""

    delete_endpoint(endpoint_names)


@describe.command("endpoint", feature_min_version="3.0.0")
@click.argument("endpoint_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [json|yaml].",
)
def _describe_endpoint(endpoint_name, out):
    """Describe a endpoint"""

    describe_endpoint(endpoint_name, out)
