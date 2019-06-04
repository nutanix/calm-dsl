import time
import warnings
import click
import arrow
from prettytable import PrettyTable

from .utils import get_name_query, highlight_text
from calm.dsl.builtins import ProjectValidator


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


def get_project(client, name):

    params = {"filter": "name=={}".format(name)}

    res, err = client.project.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    project = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one project found - {}".format(entities))

        click.echo(">> {} found >>".format(name))
        project = entities[0]
    else:
        raise Exception(">> No project found with name {} found >>".format(name))
    return project


def delete_project(obj, project_names):

    client = obj.get("client")

    for project_name in project_names:
        project = get_project(client, project_name)
        project_id = project["metadata"]["uuid"]
        res, err = client.project.delete(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        click.echo("Project {} deleted".format(project_name))


def create_project(client, payload):

    validator = ProjectValidator()
    name = payload["project_detail"]["name"]

    # check if project having same name exists
    click.echo("Searching for projects having same name ")
    params = {"filter": "name=={}".format(name)}
    res, err = client.project.list(params=params)
    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) > 0:
            err_msg = "Project with name {} already exists". format(name)
            err = {"error": err_msg, "code": -1}
            return None, err

    click.echo("No project with same name exists")
    click.echo("Creating the project {}". format(name))

    # validating the payload
    validator.validate_dict(payload)
    payload = {
        'api_version': "3.0",     # TODO Remove by a constant
        'metadata': {
            'kind': 'project'
        },
        'spec': payload
    }

    return client.project.create(payload)
