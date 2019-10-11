import click
import json

from .main import get, describe, delete, create
from .endpoints import (
    get_endpoint_list,
    compile_endpoint,
    delete_endpoint,
    describe_endpoint
)


@get.command("endpoints")
@click.option(
    "--name", "-n", default=None, help="Endpoint name (Optional)"
)
@click.option(
    "--filter", "filter_by", default=None, help="Filter endpoints by this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.option("--offset", default=0, help="Offset results by the specified amount")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only endpoint names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.pass_obj
def _get_endpoint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the endpoints, optionally filtered by a string"""
    get_endpoint_list(obj, name, filter_by, limit, offset, quiet, all_items)


def create_endpoint(client, endpoint_payload, name=None, description=None, project_name=None):

    endpoint_payload.pop("status", None)

    if name:
        endpoint_payload["spec"]["name"] = name
        endpoint_payload["metadata"]["name"] = name

    if description:
        endpoint_payload["spec"]["description"] = description

    endpoint_resources = endpoint_payload["spec"]["resources"]
    endpoint_name = endpoint_payload["spec"]["name"]
    endpoint_desc = endpoint_payload["spec"]["description"]

    if project_name:
        params = {"filter": "name=={}".format(project_name)}
        res, err = client.project.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()
        entities = res.get("entities", None)
        if not entities:
            return None, {"error": ">> No project found with name {} >>".format(name)}
        if len(entities) != 1:
            return None, {"error": "More than one project found - {}".format(entities)}
        click.echo(">> Project {} found >>".format(project_name))

        project_ref = {
            "uuid": entities[0]["metadata"]["uuid"],
            "kind": "project"
        }
    else:
        project_ref = None

    return client.endpoint.upload_with_secrets(
        endpoint_name, endpoint_desc, endpoint_resources, project_ref=project_ref
    )


def create_endpoint_from_json(client, path_to_json, name=None, description=None, project=None):

    endpoint_payload = json.loads(open(path_to_json, "r").read())
    return create_endpoint(client, endpoint_payload, name=name,
                           description=description, project_name=project)


def create_endpoint_from_dsl(client, endpoint_file, name=None, description=None, project=None):

    endpoint_payload = compile_endpoint(endpoint_file)
    if endpoint_payload is None:
        err_msg = "User endpoint not found in {}".format(endpoint_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_endpoint(client, endpoint_payload, name=name,
                           description=description, project_name=project)


@create.command("endpoint")
@click.option(
    "--file",
    "-f",
    "endpoint_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Endpoint file to upload",
)
@click.option(
    "--name", "-n", default=None, help="Endpoint name (Optional)"
)
@click.option(
    "--project", "-p", default=None, help="Project name (Optional)"
)
@click.option("--description", default=None, help="Endpoint description (Optional)")
@click.pass_obj
def create_endpoint_command(obj, endpoint_file, name, description, project):
    """Creates a endpoint"""

    client = obj.get("client")
    if not project:
        project = "default"

    if endpoint_file.endswith(".json"):
        res, err = create_endpoint_from_json(
            client, endpoint_file, name=name, description=description, project=project
        )
    elif endpoint_file.endswith(".py"):
        res, err = create_endpoint_from_dsl(
            client, endpoint_file, name=name, description=description, project=project
        )
    else:
        click.echo("Unknown file format {}".format(endpoint_file))
        return

    if err:
        click.echo(err["error"])
        return

    endpoint = res.json()
    endpoint_state = endpoint["status"]["state"]
    endpoint_name = endpoint["status"]["name"]
    click.echo(">> Endpoint {} created".format(endpoint_name))
    assert endpoint_state in ["running", "provisioning"]


@delete.command("endpoint")
@click.argument("endpoint_names", nargs=-1)
@click.pass_obj
def _delete_endpoint(obj, endpoint_names):
    """Deletes endpoints"""

    delete_endpoint(obj, endpoint_names)


@describe.command("endpoint")
@click.argument("endpoint_name")
@click.pass_obj
def _describe_endpoint(obj, endpoint_name):
    """Describe a endpoint"""

    describe_endpoint(obj, endpoint_name)
