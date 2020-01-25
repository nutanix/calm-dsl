import uuid
import click
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_config
from .utils import highlight_text, get_states_filter
from .bps import launch_blueprint_simple


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


def get_mpis(mpi_name, app_family="All", app_states=[], group_member_count=0):
    """
        To call groups() api for marketplace items
        if group_member_count is 0, it will not appply the filter at all
    """

    client = get_api_client()
    filter = "marketplace_item_type_list==APP"

    if app_states:
        filter += get_states_filter(state_key="app_state", states=app_states)

    if app_family != "All":
        filter += ";category_name==AppFamily;category_value=={}".format(app_family)

    if mpi_name:
        filter += ";name=={}".format(mpi_name)

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

    if group_member_count:
        payload["group_member_count"] = group_member_count

    Obj = get_resource_api("groups", client.connection)
    res, err = Obj.create(payload=payload)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    return res


def get_published_mpis(name, quiet, app_family, display_all):

    group_member_count = 0
    if not display_all:
        group_member_count = 1

    res = get_mpis(
        mpi_name=name,
        app_family=app_family,
        app_states=["PUBLISHED"],
        group_member_count=group_member_count,
    )
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


def get_mpi_latest_version(mpi_name, app_states=[]):

    res = get_mpis(mpi_name=mpi_name, app_states=app_states, group_member_count=1)
    group_results = res["group_results"]

    if not group_results:
        raise Exception("No MPI found with name {}".format(mpi_name))

    entity_results = group_results[0]["entity_results"]
    entity_version = get_group_data_value(entity_results[0]["data"], "version")

    return entity_version


def describe_mpi(name, version=None):

    if not version:
        click.echo("Fetching latest version of MPI {} ...".format(name), nl=False)
        version = get_mpi_latest_version(mpi_name=name, app_states=["PUBLISHED"])
        click.echo("[{}]". format(version))

    bp = get_mpi_by_name_n_version(mpi_name=name, mpi_version=version)

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


def convert_mpi_into_blueprint(mpi_name, project_name, mpi_version=None):

    config = get_config()
    client = get_api_client()

    if not mpi_version:
        click.echo("Fetching latest version of MPI {} ...".format(mpi_name), nl=False)
        mpi_version = get_mpi_latest_version(mpi_name=mpi_name, app_states=["PUBLISHED"])
        click.echo("[{}]". format(mpi_version))

    click.echo("Fetching mpi store item ...", nl=False)
    mpi_data = get_mpi_by_name_n_version(mpi_name=mpi_name, mpi_version=mpi_version)
    click.echo("[Success]")

    # Finding the projects associated with mpi
    shared_projects = mpi_data["status"]["resources"]["project_reference_list"]

    project = project_name or config["PROJECT"]["name"]
    project_uuid = None
    project_name_list = []
    for project_ref in shared_projects:
        project_name_list.append(project_ref["name"])
        if project == project_ref["name"]:
            project_uuid = project_ref["uuid"]

    if not shared_projects:
        raise Exception("MPI {} is not shared with any project !!!".format(mpi_name))

    if not project_uuid:
        raise Exception("choose from {} projects".format(project_name_list))

    click.echo("Fetching environment data ...", nl=False)
    res, err = client.project.read(project_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    click.echo("[Success]")

    res = res.json()
    environments = res["status"]["project_status"]["resources"][
        "environment_reference_list"
    ]

    # For now only single environment exists
    env_uuid = environments[0]["uuid"]

    bp_spec = {}
    bp_spec["spec"] = mpi_data["spec"]["resources"]["app_blueprint_template"]["spec"]
    del bp_spec["spec"]["name"]
    bp_spec["spec"]["environment_uuid"] = env_uuid

    bp_spec["spec"]["app_blueprint_name"] = "Mpi-Bp-{}-{}".format(
        mpi_name, str(uuid.uuid4())[-10:]
    )

    bp_spec["metadata"] = {
        "kind": "blueprint",
        "project_reference": {"kind": "project", "uuid": project_uuid},
        "categories": mpi_data["metadata"]["categories"],
    }
    bp_spec["api_version"] = "3.0"

    click.echo("Creating mpi blueprint ...", nl=False)
    bp_res, err = client.blueprint.marketplace_launch(bp_spec)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    click.echo("[Success]")

    bp_res = bp_res.json()

    del bp_res["spec"]["environment_uuid"]
    bp_status = bp_res["status"]["state"]
    if bp_status != "ACTIVE":
        raise Exception("blueprint went to {} state".format(bp_status))

    return bp_res


def launch_mpi(
    mpi_name, version, project, app_name=None, profile_name=None, patch_editables=True,
):

    client = get_api_client()

    bp_payload = convert_mpi_into_blueprint(mpi_name=mpi_name, project_name=project, mpi_version=version)
    bp_name = bp_payload["metadata"].get("name")

    click.echo("Launching mpi blueprint {} ...".format(bp_name))
    app_name = app_name or "Mpi-App-{}-{}".format(mpi_name, str(uuid.uuid4())[-10:])
    launch_blueprint_simple(
        client,
        patch_editables=patch_editables,
        profile_name=profile_name,
        app_name=app_name,
        blueprint=bp_payload,
    )
