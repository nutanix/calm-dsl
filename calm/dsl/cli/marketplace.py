import uuid
import click
import sys
import json
import os

from prettytable import PrettyTable
from distutils.version import LooseVersion as LV

from calm.dsl.builtins import BlueprintType, get_valid_identifier
from calm.dsl.decompile.decompile_render import create_bp_dir
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_context

from .utils import highlight_text, get_states_filter, Display
from .bps import launch_blueprint_simple, get_blueprint
from .runbooks import get_runbook, poll_action, watch_runbook
from .apps import watch_app
from .runlog import get_runlog_status
from .endpoints import get_endpoint
from calm.dsl.builtins.models.helper.common import get_project
from .environments import get_project_environment
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version
from .constants import MARKETPLACE_ITEM

LOG = get_logging_handle(__name__)
APP_STATES = [
    MARKETPLACE_ITEM.STATES.PENDING,
    MARKETPLACE_ITEM.STATES.ACCEPTED,
    MARKETPLACE_ITEM.STATES.REJECTED,
    MARKETPLACE_ITEM.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_ITEM.SOURCES.GLOBAL,
    MARKETPLACE_ITEM.SOURCES.LOCAL,
]


def get_app_family_list():
    """returns the app family list categories"""

    client = get_api_client()
    Obj = get_resource_api("categories/AppFamily", client.connection)

    res, err = Obj.list(params={})
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    categories = []

    for entity in res["entities"]:
        categories.append(entity["value"])

    return categories


def get_group_data_value(data_list, field, value_list=False):
    """to find the field value in group api call
    return whole list of values if value_list is True
    """

    for entity in data_list:
        if entity["name"] == field:
            entity_value = entity["values"]
            if not entity_value:
                return None

            return (
                entity_value[0]["values"]
                if value_list
                else entity_value[0]["values"][0]
            )

    return None


def trunc_string(data=None, max_length=50):

    if not data:
        return "-"

    if len(data) > max_length:
        return data[: max_length - 1] + "..."

    return data


def get_mpis_group_call(
    name=None,
    app_family="All",
    app_states=[],
    group_member_count=0,
    app_source=None,
    app_group_uuid=None,
    type=None,
    filter_by="",
):
    """
    To call groups() api for marketplace items
    if group_member_count is 0, it will not apply the group_count filter
    """

    client = get_api_client()
    filter = "marketplace_item_type_list==APP"

    if app_states:
        filter += get_states_filter(state_key="app_state", states=app_states)

    if app_family != "All":
        filter += ";category_name==AppFamily;category_value=={}".format(app_family)

    if filter_by:
        filter = filter + ";(" + filter_by + ")"

    if name:
        filter += ";name=={}".format(name)

    if app_source:
        filter += ";app_source=={}".format(app_source)

    if app_group_uuid:
        filter += ";app_group_uuid=={}".format(app_group_uuid)

    CALM_VERSION = Version.get_version("Calm")
    if type and LV(CALM_VERSION) >= LV("3.2.0"):
        filter += ";type=={}".format(type)

    payload = {
        "group_member_sort_attribute": "version",
        "group_member_sort_order": "DESCENDING",
        "grouping_attribute": "app_group_uuid",
        "group_count": 64,
        "group_offset": 0,
        "filter_criteria": filter,
        "entity_type": "marketplace_item",
        "group_member_attributes": [
            {"attribute": "name"},
            {"attribute": "type"},
            {"attribute": "author"},
            {"attribute": "version"},
            {"attribute": "categories"},
            {"attribute": "owner_reference"},
            {"attribute": "owner_username"},
            {"attribute": "project_names"},
            {"attribute": "project_uuids"},
            {"attribute": "app_state"},
            {"attribute": "description"},
            {"attribute": "spec_version"},
            {"attribute": "app_attribute_list"},
            {"attribute": "app_group_uuid"},
            {"attribute": "icon_list"},
            {"attribute": "change_log"},
            {"attribute": "app_source"},
        ],
    }

    if group_member_count:
        payload["group_member_count"] = group_member_count

    # TODO Create GroupAPI separately for it.
    Obj = get_resource_api("groups", client.connection)
    res, err = Obj.create(payload=payload)

    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    return res


def get_marketplace_store_items(
    name, quiet, app_family, display_all, filter_by="", type=None
):
    """Lists marketplace store items"""

    group_member_count = 0
    if not display_all:
        group_member_count = 1

    res = get_mpis_group_call(
        name=name,
        app_family=app_family,
        app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
        group_member_count=group_member_count,
        filter_by=filter_by,
        type=type,
    )
    group_results = res["group_results"]

    if quiet:
        for group in group_results:
            entity_results = group["entity_results"]
            entity_data = entity_results[0]["data"]
            click.echo(highlight_text(get_group_data_value(entity_data, "name")))
        return

    table = PrettyTable()
    field_names = ["NAME", "TYPE", "DESCRIPTION", "AUTHOR", "APP_SOURCE"]
    if display_all:
        field_names.insert(1, "VERSION")
        field_names.insert(2, "AVAILABLE TO")
        field_names.append("UUID")

    table.field_names = field_names

    for group in group_results:
        entity_results = group["entity_results"]

        for entity in entity_results:
            entity_data = entity["data"]
            project_names = get_group_data_value(
                entity_data, "project_names", value_list=True
            )
            available_to = "-"
            if project_names:
                project_count = len(project_names)
                if project_count == 1:
                    available_to = "{} Project".format(project_count)
                else:
                    available_to = "{} Projects".format(project_count)

            data_row = [
                highlight_text(get_group_data_value(entity_data, "name")),
                highlight_text(get_group_data_value(entity_data, "type")),
                highlight_text(
                    trunc_string(get_group_data_value(entity_data, "description"))
                ),
                highlight_text(get_group_data_value(entity_data, "author")),
                highlight_text(get_group_data_value(entity_data, "app_source")),
            ]

            if display_all:
                data_row.insert(
                    1, highlight_text(get_group_data_value(entity_data, "version"))
                )
                data_row.insert(2, highlight_text(available_to))
                data_row.append(highlight_text(entity["entity_id"]))

            table.add_row(data_row)

    click.echo(table)


def get_marketplace_items(
    name, quiet, app_family, app_states=[], filter_by="", type=None
):
    """List all the marketlace items listed in the manager"""

    res = get_mpis_group_call(
        name=name,
        app_family=app_family,
        app_states=app_states,
        filter_by=filter_by,
        type=type,
    )
    group_results = res["group_results"]

    if quiet:
        for group in group_results:
            entity_results = group["entity_results"]
            entity_data = entity_results[0]["data"]
            click.echo(highlight_text(get_group_data_value(entity_data, "name")))
        return

    table = PrettyTable()
    field_names = [
        "NAME",
        "TYPE",
        "APP_SOURCE",
        "OWNER",
        "AUTHOR",
        "AVAILABLE TO",
        "VERSION",
        "CATEGORY",
        "STATUS",
        "UUID",
    ]

    table.field_names = field_names

    for group in group_results:
        entity_results = group["entity_results"]

        for entity in entity_results:
            entity_data = entity["data"]
            project_names = get_group_data_value(
                entity_data, "project_names", value_list=True
            )
            available_to = "-"
            if project_names:
                project_count = len(project_names)
                if project_count == 1:
                    available_to = "{} Project".format(project_count)
                else:
                    available_to = "{} Projects".format(project_count)

            categories = get_group_data_value(entity_data, "categories")
            category = "-"
            if categories:
                category = categories.split(":")[1]

            owner = get_group_data_value(entity_data, "owner_username")
            if not owner:
                owner = "-"

            data_row = [
                highlight_text(get_group_data_value(entity_data, "name")),
                highlight_text(get_group_data_value(entity_data, "type")),
                highlight_text(get_group_data_value(entity_data, "app_source")),
                highlight_text(owner),
                highlight_text(get_group_data_value(entity_data, "author")),
                highlight_text(available_to),
                highlight_text(get_group_data_value(entity_data, "version")),
                highlight_text(category),
                highlight_text(get_group_data_value(entity_data, "app_state")),
                highlight_text(entity["entity_id"]),
            ]

            table.add_row(data_row)

    click.echo(table)


def get_mpi_latest_version(name, app_source=None, app_states=[], type=None):

    res = get_mpis_group_call(
        name=name,
        app_states=app_states,
        group_member_count=1,
        app_source=app_source,
        type=type,
    )
    group_results = res["group_results"]

    if not group_results:
        LOG.error("No Marketplace Item found with name {}".format(name))
        sys.exit(-1)

    entity_results = group_results[0]["entity_results"]
    entity_version = get_group_data_value(entity_results[0]["data"], "version")

    return entity_version


def get_mpi_by_name_n_version(name, version, app_states=[], app_source=None, type=None):
    """
    It will fetch marketplace item with particular version.
    Special case: As blueprint with state REJECTED and other can coexist with same name and version
    """

    client = get_api_client()
    filter = "name==" + name + ";version==" + version

    if app_states:
        filter += get_states_filter(state_key="app_state", states=app_states)

    if app_source:
        filter += ";app_source=={}".format(app_source)

    CALM_VERSION = Version.get_version("Calm")
    if type and LV(CALM_VERSION) >= LV("3.2.0"):
        filter += ";type=={}".format(type)

    payload = {"length": 250, "filter": filter}

    LOG.debug("Calling list api on marketplace_items")
    res, err = client.market_place.list(params=payload)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    if not res["entities"]:
        LOG.error(
            "No Marketplace Item found with name {} and version {}".format(
                name, version
            )
        )
        sys.exit(-1)

    app_uuid = res["entities"][0]["metadata"]["uuid"]
    LOG.debug("Reading marketplace_item with uuid {}".format(app_uuid))
    res, err = client.market_place.read(app_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    return res


def describe_marketplace_store_item(
    name, out, version=None, app_source=None, type=None
):
    """describes the marketplace blueprint related to marketplace item"""

    describe_marketplace_item(
        name=name,
        out=out,
        version=version,
        app_source=app_source,
        app_state=MARKETPLACE_ITEM.STATES.PUBLISHED,
        type=type,
    )


def describe_marketplace_item(
    name, out, version=None, app_source=None, app_state=None, type=None
):
    """describes the marketplace item"""

    CALM_VERSION = Version.get_version("Calm")

    app_states = [app_state] if app_state else []
    if not version:
        LOG.info("Fetching latest version of Marketplace Item {} ".format(name))
        version = get_mpi_latest_version(
            name=name, app_source=app_source, app_states=app_states, type=type
        )
        LOG.info(version)

    LOG.info("Fetching details of Marketplace Item {}".format(name))
    mpi = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_states=app_states,
        app_source=app_source,
        type=type,
    )

    if out == "json":
        blueprint = mpi["status"]["resources"]["app_blueprint_template"]
        blueprint.pop("status", None)
        click.echo(json.dumps(blueprint, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----MarketPlace Item Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(name)
        + " (uuid: "
        + highlight_text(mpi["metadata"]["uuid"])
        + ")"
    )

    if LV(CALM_VERSION) >= LV("3.2.0"):
        click.echo("Type: " + highlight_text(mpi["status"]["resources"]["type"]))

    click.echo("Description: " + highlight_text(mpi["status"]["description"]))
    click.echo("App State: " + highlight_text(mpi["status"]["resources"]["app_state"]))
    click.echo("Author: " + highlight_text(mpi["status"]["resources"]["author"]))

    project_name_list = mpi["status"]["resources"]["project_reference_list"]
    click.echo(
        "Projects shared with [{}]: ".format(highlight_text(len(project_name_list)))
    )
    for project in project_name_list:
        click.echo("\t{}".format(highlight_text(project["name"])))

    categories = mpi["metadata"].get("categories", {})
    if categories:
        click.echo("Categories [{}]: ".format(highlight_text(len(categories))))
        for key, value in categories.items():
            click.echo("\t {} : {}".format(highlight_text(key), highlight_text(value)))

    change_log = mpi["status"]["resources"]["change_log"]
    if not change_log:
        change_log = "No logs present"

    click.echo("Change Log: " + highlight_text(change_log))
    click.echo("Version: " + highlight_text(mpi["status"]["resources"]["version"]))
    click.echo(
        "App Source: " + highlight_text(mpi["status"]["resources"]["app_source"])
    )

    mpi_type = MARKETPLACE_ITEM.TYPES.BLUEPRINT
    if LV(CALM_VERSION) >= LV("3.2.0"):
        mpi_type = mpi["status"]["resources"]["type"]

    if mpi_type == MARKETPLACE_ITEM.TYPES.BLUEPRINT:
        blueprint_template = mpi["status"]["resources"]["app_blueprint_template"]
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
    else:
        published_with_endpoint = mpi["status"]["resources"]["runbook_template_info"][
            "is_published_with_endpoints"
        ]
        published_with_secret = mpi["status"]["resources"]["runbook_template_info"][
            "is_published_with_secrets"
        ]
        click.echo(
            "Published with Endpoints: " + highlight_text(published_with_endpoint)
        )
        click.echo("Published with Secrets:: " + highlight_text(published_with_secret))


def launch_marketplace_bp(
    name,
    version,
    project,
    environment,
    app_name=None,
    profile_name=None,
    patch_editables=True,
    app_source=None,
    launch_params=None,
    watch=False,
    poll_interval=10,
):
    """
    Launch marketplace blueprints
    If version not there search in published, pendingm, accepted blueprints
    """

    if not version:
        LOG.info("Fetching latest version of Marketplace Blueprint {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_source=app_source,
            app_states=[
                MARKETPLACE_ITEM.STATES.ACCEPTED,
                MARKETPLACE_ITEM.STATES.PUBLISHED,
                MARKETPLACE_ITEM.STATES.PENDING,
            ],
            type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
        )
        LOG.info(version)

    LOG.info("Converting MPI to blueprint")
    bp_payload = convert_mpi_into_blueprint(
        name=name,
        version=version,
        project_name=project,
        environment_name=environment,
        app_source=app_source,
    )

    app_name = app_name or "Mpi-App-{}-{}".format(name, str(uuid.uuid4())[-10:])
    launch_blueprint_simple(
        patch_editables=patch_editables,
        profile_name=profile_name,
        app_name=app_name,
        blueprint=bp_payload,
        launch_params=launch_params,
    )
    LOG.info("App {} creation is successful".format(app_name))

    if watch:

        def display_action(screen):
            watch_app(app_name, screen, poll_interval=poll_interval)
            screen.wait_for_input(10.0)

        Display.wrapper(display_action, watch=True)
        LOG.info("Action runs completed for app {}".format(app_name))


def decompile_marketplace_bp(
    name, version, app_source, bp_name, project, with_secrets, bp_dir
):
    """decompiles marketplace blueprint"""

    if not version:
        LOG.info("Fetching latest version of Marketplace Blueprint {} ".format(name))
        version = get_mpi_latest_version(
            name=name, app_source=app_source, type=MARKETPLACE_ITEM.TYPES.BLUEPRINT
        )
        LOG.info(version)

    LOG.info("Converting MPI into blueprint")
    bp_payload = convert_mpi_into_blueprint(
        name=name, version=version, project_name=project, app_source=app_source
    )
    del bp_payload["status"]

    client = get_api_client()
    blueprint_uuid = bp_payload["metadata"]["uuid"]
    res, err = client.blueprint.export_file(blueprint_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_payload = res.json()
    blueprint = bp_payload["spec"]["resources"]
    blueprint_name = get_valid_identifier(bp_name or name)

    if not bp_dir:
        bp_dir_suffix = bp_name or "mpi_bp_{}_v{}".format(blueprint_name, version)
        bp_dir = os.path.join(os.getcwd(), bp_dir_suffix)

    blueprint_description = bp_payload["spec"].get("description", "")
    LOG.info("Decompiling marketplace blueprint {}".format(name))
    for sub_obj in blueprint.get("substrate_definition_list"):
        sub_type = sub_obj.get("type", "") or "AHV_VM"
        if sub_type == "K8S_POD":
            raise NotImplementedError(
                "Decompilation for k8s pod is not supported right now"
            )
        elif sub_type != "AHV_VM":
            LOG.warning(
                "Decompilation support for providers other than AHV is experimental."
            )
            break

    bp_cls = BlueprintType.decompile(blueprint)
    bp_cls.__name__ = blueprint_name
    bp_cls.__doc__ = blueprint_description

    create_bp_dir(bp_cls=bp_cls, bp_dir=bp_dir, with_secrets=with_secrets)
    click.echo(
        "\nSuccessfully decompiled. Directory location: {}. Blueprint location: {}".format(
            get_bp_dir(), os.path.join(get_bp_dir(), "blueprint.py")
        )
    )


def launch_marketplace_item(
    name,
    version,
    project,
    environment,
    app_name=None,
    profile_name=None,
    patch_editables=True,
    app_source=None,
    launch_params=None,
    watch=False,
    poll_interval=10,
):
    """
    Launch marketplace items
    If version not there search in published blueprints
    """

    client = get_api_client()

    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) >= LV("3.2.0"):
        params = {
            "filter": "name=={};type=={}".format(name, MARKETPLACE_ITEM.TYPES.BLUEPRINT)
        }
        mp_item_map = client.market_place.get_name_uuid_map(params=params)
        if not mp_item_map:
            LOG.error("No marketplace blueprint found with name {}".format(name))
            sys.exit(-1)

    if not version:
        LOG.info("Fetching latest version of Marketplace Item {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_source=app_source,
            app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
            type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
        )
        LOG.info(version)

    LOG.info("Converting MPI to blueprint")
    bp_payload = convert_mpi_into_blueprint(
        name=name,
        version=version,
        project_name=project,
        environment_name=environment,
        app_source=app_source,
    )

    app_name = app_name or "Mpi-App-{}-{}".format(name, str(uuid.uuid4())[-10:])
    launch_blueprint_simple(
        patch_editables=patch_editables,
        profile_name=profile_name,
        app_name=app_name,
        blueprint=bp_payload,
        launch_params=launch_params,
    )
    LOG.info("App {} creation is successful".format(app_name))

    if watch:

        def display_action(screen):
            watch_app(app_name, screen, poll_interval=poll_interval)
            screen.wait_for_input(10.0)

        Display.wrapper(display_action, watch=True)
        LOG.info("Action runs completed for app {}".format(app_name))


def convert_mpi_into_blueprint(
    name, version, project_name=None, environment_name=None, app_source=None
):

    client = get_api_client()
    context = get_context()
    project_config = context.get_project_config()

    project_name = project_name or project_config["name"]
    environment_data, project_data = get_project_environment(
        name=environment_name, project_name=project_name
    )
    project_uuid = project_data["metadata"]["uuid"]
    environments = project_data["status"]["resources"]["environment_reference_list"]
    if not environments:
        LOG.error("No environment registered to project '{}'".format(project_name))
        sys.exit(-1)

    # Added in 3.2
    default_environment_uuid = (
        project_data["status"]["resources"]
        .get("default_environment_reference", {})
        .get("uuid")
    )

    # If there is no default environment, select first one
    default_environment_uuid = default_environment_uuid or environments[0]["uuid"]

    env_uuid = ""
    if environment_data:  # if user supplies environment
        env_uuid = environment_data["metadata"]["uuid"]
    else:
        env_uuid = default_environment_uuid

    LOG.info("Fetching MPI details")
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=[
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ],
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )

    # If BP is in published state, provided project should be associated with the bp
    app_state = mpi_data["status"]["resources"]["app_state"]
    if app_state == MARKETPLACE_ITEM.STATES.PUBLISHED:
        project_ref_list = mpi_data["status"]["resources"].get(
            "project_reference_list", []
        )
        ref_projects = []
        for project in project_ref_list:
            ref_projects.append(project["name"])

        if project_name not in ref_projects:
            LOG.debug("Associated Projects: {}".format(ref_projects))
            LOG.error(
                "Project {} is not shared with marketplace item {} with version {}".format(
                    project_name, name, version
                )
            )
            sys.exit(-1)

    bp_spec = {}
    bp_spec["spec"] = mpi_data["spec"]["resources"]["app_blueprint_template"]["spec"]
    del bp_spec["spec"]["name"]
    bp_spec["spec"]["environment_uuid"] = env_uuid

    bp_spec["spec"]["app_blueprint_name"] = "Mpi-Bp-{}-{}".format(
        name, str(uuid.uuid4())[-10:]
    )

    bp_spec["metadata"] = {
        "kind": "blueprint",
        "project_reference": {"kind": "project", "uuid": project_uuid},
        "categories": mpi_data["metadata"].get("categories", {}),
    }
    bp_spec["api_version"] = "3.0"

    LOG.info("Creating MPI blueprint")
    bp_res, err = client.blueprint.marketplace_launch(bp_spec)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_res = bp_res.json()
    del bp_res["spec"]["environment_uuid"]
    bp_status = bp_res["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error("Blueprint went to {} state".format(bp_status))
        sys.exit(-1)

    return bp_res


def publish_bp_to_marketplace_manager(
    bp_name,
    marketplace_bp_name,
    version,
    description="",
    with_secrets=False,
    app_group_uuid=None,
    icon_name=None,
    icon_file=None,
):

    client = get_api_client()
    context = get_context()
    server_config = context.get_server_config()

    bp = get_blueprint(bp_name)
    bp_uuid = bp.get("metadata", {}).get("uuid", "")

    LOG.info("Fetching blueprint details")
    if with_secrets:
        bp_data, err = client.blueprint.export_json_with_secrets(bp_uuid)

    else:
        bp_data, err = client.blueprint.export_json(bp_uuid)

    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = bp_data.json()
    bp_status = bp_data["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error(
            "Blueprint is in {} state. Unable to publish it to marketplace manager".format(
                bp_status
            )
        )
        sys.exit(-1)

    bp_template = {
        "spec": {
            "name": marketplace_bp_name,
            "description": description,
            "resources": {
                "app_attribute_list": ["FEATURED"],
                "icon_reference_list": [],
                "author": server_config["pc_username"],
                "version": version,
                "app_group_uuid": app_group_uuid or str(uuid.uuid4()),
                "app_blueprint_template": {
                    "status": bp_data["status"],
                    "spec": bp_data["spec"],
                },
            },
        },
        "api_version": "3.0",
        "metadata": {"kind": "marketplace_item"},
    }

    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) >= LV("3.2.0"):
        bp_template["spec"]["resources"]["type"] = MARKETPLACE_ITEM.TYPES.BLUEPRINT

    if icon_name:
        if icon_file:
            # If file is there, upload first and then use it for marketplace item
            client.app_icon.upload(icon_name, icon_file)

        app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()
        app_icon_uuid = app_icon_name_uuid_map.get(icon_name, None)
        if not app_icon_uuid:
            LOG.error("App icon: {} not found".format(icon_name))
            sys.exit(-1)

        bp_template["spec"]["resources"]["icon_reference_list"] = [
            {
                "icon_type": "ICON",
                "icon_reference": {"kind": "file_item", "uuid": app_icon_uuid},
            }
        ]

    res, err = client.market_place.create(bp_template)
    LOG.debug("Api response: {}".format(res.json()))
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info("Marketplace Blueprint is published to marketplace manager successfully")


def publish_bp_as_new_marketplace_bp(
    bp_name,
    marketplace_bp_name,
    version,
    description="",
    with_secrets=False,
    publish_to_marketplace=False,
    auto_approve=False,
    projects=[],
    category=None,
    icon_name=None,
    icon_file=None,
    all_projects=False,
):

    # Search whether this marketplace item exists or not
    LOG.info(
        "Fetching existing marketplace blueprints with name {}".format(
            marketplace_bp_name
        )
    )
    res = get_mpis_group_call(
        name=marketplace_bp_name,
        group_member_count=1,
        app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )
    group_count = res["filtered_group_count"]

    if group_count:
        LOG.error(
            "A local marketplace item exists with same name ({}) in another app family".format(
                marketplace_bp_name
            )
        )
        sys.exit(-1)

    publish_bp_to_marketplace_manager(
        bp_name=bp_name,
        marketplace_bp_name=marketplace_bp_name,
        version=version,
        description=description,
        with_secrets=with_secrets,
        icon_name=icon_name,
        icon_file=icon_file,
    )

    if publish_to_marketplace or auto_approve:
        if not projects:
            context = get_context()
            project_config = context.get_project_config()
            projects = [project_config["name"]]

        approve_marketplace_item(
            name=marketplace_bp_name,
            version=version,
            projects=projects,
            category=category,
            all_projects=all_projects,
        )

        if publish_to_marketplace:
            publish_marketplace_item(
                name=marketplace_bp_name,
                version=version,
                app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
            )


def publish_bp_as_existing_marketplace_bp(
    bp_name,
    marketplace_bp_name,
    version,
    description="",
    with_secrets=False,
    publish_to_marketplace=False,
    auto_approve=False,
    projects=[],
    category=None,
    icon_name=None,
    icon_file=None,
    all_projects=False,
):

    LOG.info(
        "Fetching existing marketplace blueprints with name {}".format(
            marketplace_bp_name
        )
    )
    res = get_mpis_group_call(
        name=marketplace_bp_name,
        group_member_count=1,
        app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )
    group_results = res["group_results"]
    if not group_results:
        LOG.error(
            "No local marketplace blueprint exists with name {}".format(
                marketplace_bp_name
            )
        )
        sys.exit(-1)

    entity_group = group_results[0]
    app_group_uuid = entity_group["group_by_column_value"]

    # Search whether given version of marketplace items already exists or not
    # Rejected MPIs with same name and version can exist
    LOG.info(
        "Fetching existing versions of Marketplace Item {}".format(marketplace_bp_name)
    )
    res = get_mpis_group_call(
        app_group_uuid=app_group_uuid,
        app_states=[
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ],
    )

    group_results = res["group_results"]
    entity_results = group_results[0]["entity_results"]

    for entity in entity_results:
        entity_version = get_group_data_value(entity["data"], "version")
        entity_app_state = get_group_data_value(entity["data"], "app_state")

        if entity_version == version:
            LOG.error(
                "An item exists with same version ({}) and app_state ({}) in the chosen app family.".format(
                    entity_version, entity_app_state
                )
            )
            sys.exit(-1)

    publish_bp_to_marketplace_manager(
        bp_name=bp_name,
        marketplace_bp_name=marketplace_bp_name,
        version=version,
        description=description,
        with_secrets=with_secrets,
        app_group_uuid=app_group_uuid,
        icon_name=icon_name,
        icon_file=icon_file,
    )

    if publish_to_marketplace or auto_approve:
        if not projects:
            context = get_context()
            project_config = context.get_project_config()
            projects = [project_config["name"]]

        approve_marketplace_item(
            name=marketplace_bp_name,
            version=version,
            projects=projects,
            category=category,
            all_projects=all_projects,
        )

        if publish_to_marketplace:
            publish_marketplace_item(
                name=marketplace_bp_name,
                version=version,
                app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
            )


def approve_marketplace_item(
    name,
    version=None,
    projects=[],
    category=None,
    all_projects=False,
    type=None,
):

    client = get_api_client()
    if not version:
        # Search for pending items, Only those items can be approved
        LOG.info("Fetching latest version of Marketplace Item {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_ITEM.STATES.PENDING],
            type=type,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of pending marketplace item {} with version {}".format(
            name, version
        )
    )
    item = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        app_states=[MARKETPLACE_ITEM.STATES.PENDING],
        type=type,
    )
    item_uuid = item["metadata"]["uuid"]
    item_type = MARKETPLACE_ITEM.TYPES.BLUEPRINT
    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) >= LV("3.2.0"):
        item_type = item["status"]["resources"]["type"]

    if item_type == MARKETPLACE_ITEM.TYPES.BLUEPRINT:
        item_status = item["status"]["resources"]["app_blueprint_template"]["status"][
            "state"
        ]
        if item_status != "ACTIVE":
            LOG.error("Item is in {} state. Unable to approve it".format(item_status))
            sys.exit(-1)

    res, err = client.market_place.read(item_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    item_data = res.json()
    item_data.pop("status", None)
    item_data["api_version"] = "3.0"
    item_data["spec"]["resources"]["app_state"] = MARKETPLACE_ITEM.STATES.ACCEPTED

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        item_data["metadata"]["categories"] = {"AppFamily": category}

    if not item_data["spec"]["resources"].get("project_reference_list", {}):
        item_data["spec"]["resources"]["project_reference_list"] = []

    project_name_uuid_map = client.project.get_name_uuid_map(params={"length": 250})
    if all_projects:
        for k, v in project_name_uuid_map.items():
            item_data["spec"]["resources"]["project_reference_list"].append(
                {
                    "kind": "project",
                    "name": k,
                    "uuid": v,
                }
            )

    else:
        for _project in projects:
            item_data["spec"]["resources"]["project_reference_list"].append(
                {
                    "kind": "project",
                    "name": _project,
                    "uuid": project_name_uuid_map[_project],
                }
            )

    res, err = client.market_place.update(uuid=item_uuid, payload=item_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Item {} with version {} is approved successfully".format(
            name, version
        )
    )


def publish_marketplace_item(
    name,
    version=None,
    projects=[],
    category=None,
    app_source=None,
    all_projects=False,
    type=None,
):

    client = get_api_client()
    if not version:
        # Search for accepted items, only those items can be published
        LOG.info(
            "Fetching latest version of accepted Marketplace Item {} ".format(name)
        )
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_ITEM.STATES.ACCEPTED],
            app_source=app_source,
            type=type,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of accepted marketplace item {} with version {}".format(
            name, version
        )
    )
    item = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=[MARKETPLACE_ITEM.STATES.ACCEPTED],
        type=type,
    )
    item_uuid = item["metadata"]["uuid"]
    item_type = MARKETPLACE_ITEM.TYPES.BLUEPRINT
    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) >= LV("3.2.0"):
        item_type = item["status"]["resources"]["type"]

    if item_type == MARKETPLACE_ITEM.TYPES.BLUEPRINT:
        item_status = item["status"]["resources"]["app_blueprint_template"]["status"][
            "state"
        ]
        if item_status != "ACTIVE":
            LOG.error(
                "Item is in {} state. Unable to publish it to marketplace".format(
                    item_status
                )
            )
            sys.exit(-1)

    res, err = client.market_place.read(item_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    item_data = res.json()
    item_data.pop("status", None)
    item_data["api_version"] = "3.0"
    item_data["spec"]["resources"]["app_state"] = MARKETPLACE_ITEM.STATES.PUBLISHED

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        item_data["metadata"]["categories"] = {"AppFamily": category}

    if projects or all_projects:
        # Clear the stored projects
        item_data["spec"]["resources"]["project_reference_list"] = []
        project_name_uuid_map = client.project.get_name_uuid_map(params={"length": 250})

        if all_projects:
            for k, v in project_name_uuid_map.items():
                item_data["spec"]["resources"]["project_reference_list"].append(
                    {
                        "kind": "project",
                        "name": k,
                        "uuid": v,
                    }
                )
        else:
            for _project in projects:
                item_data["spec"]["resources"]["project_reference_list"].append(
                    {
                        "kind": "project",
                        "name": _project,
                        "uuid": project_name_uuid_map[_project],
                    }
                )

    # Atleast 1 project required for publishing to marketplace
    if not item_data["spec"]["resources"].get("project_reference_list", None):
        LOG.error("To publish to the Marketplace, please provide a project first.")
        sys.exit(-1)

    res, err = client.market_place.update(uuid=item_uuid, payload=item_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info("Marketplace Item is published to marketplace successfully")


def update_marketplace_item(
    name,
    version,
    category=None,
    projects=[],
    description=None,
    app_source=None,
    type=None,
):
    """
    updates the marketplace item
    version is required to prevent unwanted update of another mpi
    """

    client = get_api_client()

    LOG.info(
        "Fetching details of marketplace item {} with version {}".format(name, version)
    )
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=[
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ],
        type=type,
    )
    item_uuid = mpi_data["metadata"]["uuid"]

    res, err = client.market_place.read(item_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    item_data = res.json()
    item_data.pop("status", None)
    item_data["api_version"] = "3.0"

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        item_data["metadata"]["categories"] = {"AppFamily": category}

    if projects:
        # Clear all stored projects
        item_data["spec"]["resources"]["project_reference_list"] = []
        for project in projects:
            project_data = get_project(project)

            item_data["spec"]["resources"]["project_reference_list"].append(
                {
                    "kind": "project",
                    "name": project,
                    "uuid": project_data["metadata"]["uuid"],
                }
            )

    if description:
        item_data["spec"]["description"] = description

    res, err = client.market_place.update(uuid=item_uuid, payload=item_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Item {} with version {} is updated successfully".format(
            name, version
        )
    )


def delete_marketplace_item(
    name,
    version,
    app_source=None,
    app_state=None,
    type=None,
):

    client = get_api_client()

    if app_state == MARKETPLACE_ITEM.STATES.PUBLISHED:
        LOG.error("Unpublish MPI {} first to delete it".format(name))
        sys.exit(-1)

    app_states = (
        [app_state]
        if app_state
        else [
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.REJECTED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ]
    )

    LOG.info(
        "Fetching details of unpublished marketplace item {} with version {}".format(
            name, version
        )
    )
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=app_states,
        type=type,
    )
    item_uuid = mpi_data["metadata"]["uuid"]

    res, err = client.market_place.delete(item_uuid)
    LOG.debug("Api response: {}".format(res.json()))
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Item {} with version {} is deleted successfully".format(
            name, version
        )
    )


def reject_marketplace_item(name, version, type=None):

    client = get_api_client()
    if not version:
        # Search for pending items, Only those items can be rejected
        LOG.info("Fetching latest version of pending Marketplace Item {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_ITEM.STATES.PENDING],
            type=type,
        )
        LOG.info(version)

    # Pending BP will always of type LOCAL, so no need to apply that filter
    LOG.info(
        "Fetching details of pending marketplace item {} with version {}".format(
            name, version
        )
    )
    item = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_states=[MARKETPLACE_ITEM.STATES.PENDING],
        type=type,
    )
    item_uuid = item["metadata"]["uuid"]

    res, err = client.market_place.read(item_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    item_data = res.json()
    item_data.pop("status", None)
    item_data["api_version"] = "3.0"
    item_data["spec"]["resources"]["app_state"] = MARKETPLACE_ITEM.STATES.REJECTED

    res, err = client.market_place.update(uuid=item_uuid, payload=item_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Item {} with version {} is rejected successfully".format(
            name, version
        )
    )


def unpublish_marketplace_item(name, version, app_source=None, type=None):

    client = get_api_client()
    if not version:
        # Search for published items, only those can be unpublished
        LOG.info(
            "Fetching latest version of published Marketplace Item {} ".format(name)
        )
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
            app_source=app_source,
            type=type,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of published marketplace item {} with version {}".format(
            name, version
        )
    )
    item = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
        app_source=app_source,
        type=type,
    )
    item_uuid = item["metadata"]["uuid"]

    res, err = client.market_place.read(item_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    item_data = res.json()
    item_data.pop("status", None)
    item_data["api_version"] = "3.0"
    item_data["spec"]["resources"]["app_state"] = MARKETPLACE_ITEM.STATES.ACCEPTED

    res, err = client.market_place.update(uuid=item_uuid, payload=item_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Item {} with version {} is unpublished successfully".format(
            name, version
        )
    )


def unpublish_marketplace_bp(name, version, app_source=None):
    """unpublishes marketplace blueprint"""

    if not version:
        # Search for published blueprints, only those can be unpublished
        LOG.info(
            "Fetching latest version of published Marketplace Item {} ".format(name)
        )
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
            app_source=app_source,
            type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of published marketplace blueprint {} with version {}".format(
            name, version
        )
    )
    mpi_item = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_states=[MARKETPLACE_ITEM.STATES.PUBLISHED],
        app_source=app_source,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )

    item_type = MARKETPLACE_ITEM.TYPES.BLUEPRINT
    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) >= LV("3.2.0"):
        item_type = mpi_item["status"]["resources"]["type"]

    if item_type != "blueprint":
        LOG.error(
            "Marketplace blueprint {} with version {} not found".format(name, version)
        )
        sys.exit(-1)

    unpublish_marketplace_item(
        name=name,
        version=version,
        app_source=app_source,
        type=MARKETPLACE_ITEM.TYPES.BLUEPRINT,
    )


def publish_runbook_to_marketplace_manager(
    runbook_name,
    marketplace_item_name,
    version,
    description="",
    with_secrets=False,
    with_endpoints=False,
    app_group_uuid=None,
    icon_name=None,
    icon_file=None,
):

    client = get_api_client()
    context = get_context()
    server_config = context.get_server_config()

    runbook = get_runbook(client, runbook_name)
    runbook_uuid = runbook.get("metadata", {}).get("uuid", "")

    mpi_spec = {
        "spec": {
            "name": marketplace_item_name,
            "description": description,
            "resources": {
                "app_attribute_list": ["FEATURED"],
                "icon_reference_list": [],
                "author": server_config["pc_username"],
                "version": version,
                "type": MARKETPLACE_ITEM.TYPES.RUNBOOK,
                "app_group_uuid": app_group_uuid or str(uuid.uuid4()),
                "runbook_template_info": {
                    "is_published_with_secrets": with_secrets,
                    "is_published_with_endpoints": with_endpoints,
                    "source_runbook_reference": {
                        "uuid": runbook_uuid,
                        "kind": "runbook",
                        "name": runbook_name,
                    },
                },
            },
        },
        "api_version": "3.0",
        "metadata": {"kind": "marketplace_item"},
    }

    if icon_name:
        if icon_file:
            # If file is there, upload first and then use it for marketplace item
            client.app_icon.upload(icon_name, icon_file)

        app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()
        app_icon_uuid = app_icon_name_uuid_map.get(icon_name, None)
        if not app_icon_uuid:
            LOG.error("App icon: {} not found".format(icon_name))
            sys.exit(-1)

        mpi_spec["spec"]["resources"]["icon_reference_list"] = [
            {
                "icon_type": "ICON",
                "icon_reference": {"kind": "file_item", "uuid": app_icon_uuid},
            }
        ]

    res, err = client.market_place.create(mpi_spec)
    LOG.debug("Api response: {}".format(res.json()))
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info("Marketplace Runbook is published to marketplace manager successfully")


def publish_runbook_as_new_marketplace_item(
    runbook_name,
    marketplace_item_name,
    version,
    description="",
    with_secrets=False,
    with_endpoints=False,
    publish_to_marketplace=False,
    auto_approve=False,
    projects=[],
    category=None,
    icon_name=None,
    icon_file=None,
):

    # Search whether this marketplace item exists or not
    LOG.info(
        "Fetching existing marketplace runbooks with name {}".format(
            marketplace_item_name
        )
    )
    res = get_mpis_group_call(
        name=marketplace_item_name,
        group_member_count=1,
        app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
    )
    group_count = res["filtered_group_count"]

    if group_count:
        LOG.error(
            "A local marketplace item exists with same name ({}) in another app family".format(
                marketplace_item_name
            )
        )
        sys.exit(-1)

    publish_runbook_to_marketplace_manager(
        runbook_name=runbook_name,
        marketplace_item_name=marketplace_item_name,
        version=version,
        description=description,
        with_secrets=with_secrets,
        with_endpoints=with_endpoints,
        icon_name=icon_name,
        icon_file=icon_file,
    )

    if publish_to_marketplace or auto_approve:
        if not projects:
            context = get_context()
            project_config = context.get_project_config()
            projects = [project_config["name"]]

        approve_marketplace_item(
            name=marketplace_item_name,
            version=version,
            projects=projects,
            category=category,
        )

        if publish_to_marketplace:
            publish_marketplace_item(
                name=marketplace_item_name,
                version=version,
                app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
            )


def publish_runbook_as_existing_marketplace_item(
    runbook_name,
    marketplace_item_name,
    version,
    description="",
    with_secrets=False,
    with_endpoints=False,
    publish_to_marketplace=False,
    auto_approve=False,
    projects=[],
    category=None,
    icon_name=None,
    icon_file=None,
):

    LOG.info(
        "Fetching existing marketplace runbooks with name {}".format(
            marketplace_item_name
        )
    )
    res = get_mpis_group_call(
        name=marketplace_item_name,
        group_member_count=1,
        app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
    )
    group_results = res["group_results"]
    if not group_results:
        LOG.error(
            "No local marketplace runbook exists with name {}".format(
                marketplace_item_name
            )
        )
        sys.exit(-1)

    entity_group = group_results[0]
    app_group_uuid = entity_group["group_by_column_value"]

    # Search whether given version of marketplace items already exists or not
    # Rejected MPIs with same name and version can exist
    LOG.info(
        "Fetching existing versions of Marketplace Item {}".format(
            marketplace_item_name
        )
    )
    res = get_mpis_group_call(
        app_group_uuid=app_group_uuid,
        app_states=[
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ],
    )

    group_results = res["group_results"]
    entity_results = group_results[0]["entity_results"]

    for entity in entity_results:
        entity_version = get_group_data_value(entity["data"], "version")
        entity_app_state = get_group_data_value(entity["data"], "app_state")

        if entity_version == version:
            LOG.error(
                "An item exists with same version ({}) and app_state ({}) in the chosen app family.".format(
                    entity_version, entity_app_state
                )
            )
            sys.exit(-1)

    publish_runbook_to_marketplace_manager(
        runbook_name=runbook_name,
        marketplace_item_name=marketplace_item_name,
        version=version,
        description=description,
        with_secrets=with_secrets,
        app_group_uuid=app_group_uuid,
        icon_name=icon_name,
        icon_file=icon_file,
    )

    if publish_to_marketplace or auto_approve:
        if not projects:
            context = get_context()
            project_config = context.get_project_config()
            projects = [project_config["name"]]

        approve_marketplace_item(
            name=marketplace_item_name,
            version=version,
            projects=projects,
            category=category,
        )

        if publish_to_marketplace:
            publish_marketplace_item(
                name=marketplace_item_name,
                version=version,
                app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
            )


def execute_marketplace_runbook(
    name,
    version,
    project_name,
    app_source=None,
    ignore_runtime_variables=False,
    watch=False,
    app_states=[],
):
    """
    Execute marketplace runbooks
    If version not there search in published, pending, accepted runbooks
    """

    client = get_api_client()
    params = {
        "filter": "name=={};type=={}".format(name, MARKETPLACE_ITEM.TYPES.RUNBOOK)
    }
    mp_item_map = client.market_place.get_name_uuid_map(params=params)
    if not mp_item_map:
        LOG.error("No marketplace runbook found with name {}".format(name))
        sys.exit(-1)

    if not app_states:
        app_states = [
            MARKETPLACE_ITEM.STATES.ACCEPTED,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            MARKETPLACE_ITEM.STATES.PENDING,
        ]

    if not version:
        LOG.info("Fetching latest version of Marketplace Runbook {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_source=app_source,
            app_states=app_states,
            type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
        )
        LOG.info(version)

    client = get_api_client()
    context = get_context()

    project_config = context.get_project_config()

    project_name = project_name or project_config["name"]
    project_data = get_project(project_name)

    project_uuid = project_data["metadata"]["uuid"]

    LOG.info("Fetching MPI details")
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=app_states,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )

    mpi_type = mpi_data["status"]["resources"]["type"]
    if mpi_type != MARKETPLACE_ITEM.TYPES.RUNBOOK:
        LOG.error("Selected marketplace item is not of type runbook")
        return

    mpi_uuid = mpi_data["metadata"]["uuid"]
    payload = {
        "api_version": "3.0",
        "metadata": {
            "kind": "runbook",
            "project_reference": {"uuid": project_uuid, "kind": "project"},
        },
        "spec": {
            "resources": {
                "args": [],
                "marketplace_reference": {"kind": "marketplace_item", "uuid": mpi_uuid},
            }
        },
    }

    patch_runbook_endpoints(client, mpi_data, payload)
    if not ignore_runtime_variables:
        patch_runbook_runtime_editables(client, mpi_data, payload)

    def render_runbook(screen):
        screen.clear()
        screen.refresh()
        execute_marketplace_runbook_renderer(screen, client, watch, payload=payload)
        screen.wait_for_input(10.0)

    Display.wrapper(render_runbook, watch)


def execute_marketplace_runbook_renderer(screen, client, watch, payload={}):

    res, err = client.runbook.marketplace_execute(payload)
    if not err:
        screen.clear()
        screen.print_at("Runbook queued for run", 0, 0)
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]

    def poll_runlog_status():
        return client.runbook.poll_action_run(runlog_uuid)

    screen.refresh()
    should_continue = poll_action(poll_runlog_status, get_runlog_status(screen))
    if not should_continue:
        return
    res, err = client.runbook.poll_action_run(runlog_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    runbook = response["status"]["runbook_json"]["resources"]["runbook"]

    if watch:
        screen.refresh()
        watch_runbook(runlog_uuid, runbook, screen=screen)

    context = get_context()
    server_config = context.get_server_config()

    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    run_url = "https://{}:{}/console/#page/explore/calm/runbooks/runlogs/{}".format(
        pc_ip, pc_port, runlog_uuid
    )
    if not watch:
        screen.print_at(
            "Runbook execution url: {}".format(highlight_text(run_url)), 0, 0
        )
    screen.refresh()


def patch_runbook_endpoints(client, mpi_data, payload):
    template_info = mpi_data["status"]["resources"].get("runbook_template_info", {})
    runbook = template_info.get("runbook_template", {})

    if template_info.get("is_published_with_endpoints", False):
        # No patching of endpoints required as runbook is published with endpoints
        return payload

    default_target = input("Default target for execution of Marketplace Runbook:")

    if default_target:
        endpoint = get_endpoint(client, default_target)
        endpoint_id = endpoint.get("metadata", {}).get("uuid", "")
        payload["spec"]["resources"]["default_target_reference"] = {
            "kind": "app_endpoint",
            "uuid": endpoint_id,
            "name": default_target,
        }

    tasks = runbook["spec"]["resources"]["runbook"]["task_definition_list"]
    used_endpoints = []
    for task in tasks:
        target_name = task.get("target_any_local_reference", {}).get("name", "")
        if target_name:
            used_endpoints.append(target_name)

    endpoints_description_map = {}
    for ep_info in runbook["spec"]["resources"].get("endpoints_information", []):
        ep_name = ep_info.get("endpoint_reference", {}).get("name", "")
        ep_description = ep_info.get("description", "")
        if ep_name and ep_description:
            endpoints_description_map[ep_name] = ep_description

    if used_endpoints:
        LOG.info(
            "Please select an endpoint belonging to the selected project for every endpoint used in the marketplace\
              /item."
        )
    endpoints_mapping = {}
    for used_endpoint in used_endpoints:
        des = endpoints_description_map.get(used_endpoint, used_endpoint)
        selected_endpoint = input("{}:".format(des))
        if selected_endpoint:
            endpoint = get_endpoint(client, selected_endpoint)
            endpoint_id = endpoint.get("metadata", {}).get("uuid", "")
            endpoints_mapping[used_endpoint] = endpoint_id

    payload["spec"]["resources"]["endpoints_mapping"] = endpoints_mapping


def patch_runbook_runtime_editables(client, mpi_data, payload):

    runbook = (
        mpi_data["status"]["resources"]
        .get("runbook_template_info", {})
        .get("runbook_template", {})
    )
    variable_list = runbook["spec"]["resources"]["runbook"].get("variable_list", [])
    args = payload.get("spec", {}).get("resources", {}).get("args", [])

    for variable in variable_list:
        if variable.get("editables", {}).get("value", False):
            new_val = input(
                "Value for Variable {} in Runbook (default value={}): ".format(
                    variable.get("name"), variable.get("value", "")
                )
            )
            if new_val:
                args.append(
                    {
                        "name": variable.get("name"),
                        "value": type(variable.get("value", ""))(new_val),
                    }
                )

    payload["spec"]["resources"]["args"] = args
    return payload
