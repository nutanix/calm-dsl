import click
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from .utils import highlight_text


def get_app_family_list():
    """returns the app family list categories"""

    client = get_api_client()
    Obj = get_resource_api("categories/AppFamily", client.connection)

    res, err = Obj.list(params={})
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    categories = []

    for entity in res["entities"]:
        categories.append(entity["value"])

    return categories


def get_group_data_value(data_list, field):
    """ to find the field value in group api call"""

    for entity in data_list:
        if entity["name"] == field:
            return entity["values"][0]["values"][0]

    return None


def trunc_string(data="", max_length=50):

    if len(data) > max_length:
        return data[: max_length - 1] + "..."


def get_published_mpis(name, quiet, app_family, display_all):

    client = get_api_client()

    filter = "marketplace_item_type_list==APP;(app_state==PUBLISHED)"
    if app_family != "All":
        filter += ";category_name==AppFamily;category_value=={}".format(app_family)

    if name:
        filter += ";name=={}".format(name)

    payload = {
        "group_member_sort_attribute": "version",
        "group_member_sort_order": "DESCENDING",
        "grouping_attribute": "app_group_uuid",
        "group_count": 48,
        "group_offset": 0,
        "filter_criteria": filter,
        "entity_type": "marketplace_item",
        "group_member_attributes": [
            {"attribute": "name"},
            {"attribute": "author"},
            {"attribute": "version"},
            {"attribute": "app_state"},
            {"attribute": "description"},
            {"attribute": "app_source"},
        ],
    }

    if not display_all:
        payload["group_member_count"] = 1

    Obj = get_resource_api("groups", client.connection)
    res, err = Obj.create(payload=payload)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    group_results = res["group_results"]

    if quiet:
        for group in group_results:
            entity_results = group["entity_results"]
            entity_data = entity_results[0]["data"]
            click.echo(highlight_text(get_group_data_value(entity_data, "name")))
        return

    table = PrettyTable()
    field_names = ["NAME", "DESCRIPTION", "AUTHOR", "APP_SOURCE", "APP STATE"]
    if display_all:
        field_names.insert(1, "VERSION")
        field_names.append("UUID")

    table.field_names = field_names

    for group in group_results:
        entity_results = group["entity_results"]

        for entity in entity_results:
            entity_data = entity["data"]

            data_row = [
                highlight_text(get_group_data_value(entity_data, "name")),
                highlight_text(
                    trunc_string(get_group_data_value(entity_data, "description"))
                ),
                highlight_text(get_group_data_value(entity_data, "author")),
                highlight_text(get_group_data_value(entity_data, "app_source")),
                highlight_text(get_group_data_value(entity_data, "app_state")),
            ]

            if display_all:
                data_row.insert(
                    1, highlight_text(get_group_data_value(entity_data, "version"))
                )
                data_row.append(highlight_text(entity["entity_id"]))

            table.add_row(data_row)

    click.echo(table)


def describe_mpi(name, version):

    client = get_api_client()
    bp = get_mpi_by_name_n_version(name, version)

    click.echo("\n----MarketPlace Blueprint Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(name)
        + " (uuid: "
        + highlight_text(bp["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(bp["status"]["description"]))
    click.echo("App State: " + highlight_text(bp["status"]["resources"]["app_state"]))
    click.echo("Author: " + highlight_text(bp["status"]["resources"]["author"]))

    project_list = bp["status"]["resources"]["project_reference_list"]
    click.echo("Projects shared with [{}]: ".format(highlight_text(len(project_list))))
    for project in project_list:
        click.echo("\t{}".format(highlight_text(project["name"])))

    categories = bp["metadata"].get("categories", {})
    if categories:
        click.echo("Categories [{}]: ".format(highlight_text(len(categories))))
        for key, value in categories.items():
            click.echo("\t {} : {}".format(highlight_text(key), highlight_text(value)))

    change_log = bp["status"]["resources"]["change_log"]
    if not change_log:
        change_log = "No logs present"

    click.echo("Change Log: " + highlight_text(change_log))
    click.echo("Version: " + highlight_text(bp["status"]["resources"]["version"]))
    click.echo("App Source: " + highlight_text(bp["status"]["resources"]["app_source"]))

    blueprint_template = bp["status"]["resources"]["app_blueprint_template"]
    action_list = blueprint_template["status"]["resources"]["app_profile_list"][0][
        "action_list"
    ]
    click.echo("App actions [{}]: ".format(highlight_text(len(action_list))))
    for action in action_list:
        click.echo("\t{} : ".format(highlight_text(action["name"])), nl=False)
        click.echo(
            highlight_text(
                action["description"]
                if action["description"]
                else "No description avaiable"
            )
        )


def get_mpi_by_name_n_version(mpi_name, mpi_version):
    """
    It will fetch marketplace item with particular version.
    Args:
        rest (object): Rest object
    Returns:
        apps (dict): All bp:uuid dict
    """
    filters = "name==" + mpi_name + ";version==" + mpi_version

    client = get_api_client()
    payload = {
        "length": 250,
        "filter": "name==" + mpi_name + ";version==" + mpi_version,
    }
    res, err = client.market_place.list(params=payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["entities"]:
        message = "no mpi found with name {} and version {}.\nRun 'calm get mpis -d' to get detailed list of mpis".format(
            mpi_name, mpi_version
        )
        raise Exception(message)

    app_uuid = res["entities"][0]["metadata"]["uuid"]
    res, err = client.market_place.read(app_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    return res
