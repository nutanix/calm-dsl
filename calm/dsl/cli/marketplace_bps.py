import uuid
import click
import sys
import json
from prettytable import PrettyTable

from calm.dsl.builtins import BlueprintType, get_valid_identifier
from calm.dsl.decompile.decompile_render import create_bp_dir
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_context

from .utils import highlight_text, get_states_filter
from .bps import launch_blueprint_simple, get_blueprint
from .projects import get_project
from calm.dsl.log import get_logging_handle
from .constants import MARKETPLACE_BLUEPRINT

LOG = get_logging_handle(__name__)
APP_STATES = [
    MARKETPLACE_BLUEPRINT.STATES.PENDING,
    MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
    MARKETPLACE_BLUEPRINT.STATES.REJECTED,
    MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_BLUEPRINT.SOURCES.GLOBAL,
    MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
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

    if name:
        filter += ";name=={}".format(name)

    if app_source:
        filter += ";app_source=={}".format(app_source)

    if app_group_uuid:
        filter += ";app_group_uuid=={}".format(app_group_uuid)

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

    Obj = get_resource_api("groups", client.connection)
    res, err = Obj.create(payload=payload)

    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    return res


def get_marketplace_items(name, quiet, app_family, display_all):
    """Lists marketplace items"""

    group_member_count = 0
    if not display_all:
        group_member_count = 1

    res = get_mpis_group_call(
        name=name,
        app_family=app_family,
        app_states=[MARKETPLACE_BLUEPRINT.STATES.PUBLISHED],
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
    field_names = ["NAME", "DESCRIPTION", "AUTHOR", "APP_SOURCE"]
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


def get_marketplace_bps(name, quiet, app_family, app_states=[]):
    """ List all the blueprints in marketplace manager"""

    res = get_mpis_group_call(name=name, app_family=app_family, app_states=app_states)
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


def get_mpi_latest_version(name, app_source=None, app_states=[]):

    res = get_mpis_group_call(
        name=name, app_states=app_states, group_member_count=1, app_source=app_source
    )
    group_results = res["group_results"]

    if not group_results:
        LOG.error("No Marketplace Blueprint found with name {}".format(name))
        sys.exit(-1)

    entity_results = group_results[0]["entity_results"]
    entity_version = get_group_data_value(entity_results[0]["data"], "version")

    return entity_version


def get_mpi_by_name_n_version(name, version, app_states=[], app_source=None):
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

    payload = {"length": 250, "filter": filter}

    LOG.debug("Calling list api on marketplace_items")
    res, err = client.market_place.list(params=payload)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    if not res["entities"]:
        LOG.error(
            "No Marketplace Blueprint found with name {} and version {}".format(
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


def describe_marketplace_item(name, out, version=None, app_source=None):
    """describes the marketplace blueprint related to marketplace item"""

    describe_marketplace_bp(
        name=name,
        out=out,
        version=version,
        app_source=app_source,
        app_state=MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
    )


def describe_marketplace_bp(name, out, version=None, app_source=None, app_state=None):
    """describes the marketplace blueprint"""

    app_states = [app_state] if app_state else []
    if not version:
        LOG.info("Fetching latest version of Marketplace Blueprint {} ".format(name))
        version = get_mpi_latest_version(
            name=name, app_source=app_source, app_states=app_states
        )
        LOG.info(version)

    LOG.info("Fetching details of Marketplace Blueprint {}".format(name))
    bp = get_mpi_by_name_n_version(
        name=name, version=version, app_states=app_states, app_source=app_source
    )

    if out == "json":
        blueprint = bp["status"]["resources"]["app_blueprint_template"]
        blueprint.pop("status", None)
        click.echo(json.dumps(blueprint, indent=4, separators=(",", ": ")))
        return

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

    project_name_list = bp["status"]["resources"]["project_reference_list"]
    click.echo(
        "Projects shared with [{}]: ".format(highlight_text(len(project_name_list)))
    )
    for project in project_name_list:
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


def launch_marketplace_bp(
    name,
    version,
    project,
    app_name=None,
    profile_name=None,
    patch_editables=True,
    app_source=None,
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
                MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
                MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
                MARKETPLACE_BLUEPRINT.STATES.PENDING,
            ],
        )
        LOG.info(version)

    LOG.info("Converting MPI to blueprint")
    bp_payload = convert_mpi_into_blueprint(
        name=name, version=version, project_name=project, app_source=app_source
    )

    app_name = app_name or "Mpi-App-{}-{}".format(name, str(uuid.uuid4())[-10:])
    launch_blueprint_simple(
        patch_editables=patch_editables,
        profile_name=profile_name,
        app_name=app_name,
        blueprint=bp_payload,
    )
    LOG.info("App {} creation is successful".format(app_name))


def decompile_marketplace_bp(name, version, app_source, bp_name, project, with_secrets):
    """decompiles marketplace blueprint"""

    if not version:
        LOG.info("Fetching latest version of Marketplace Blueprint {} ".format(name))
        version = get_mpi_latest_version(name=name, app_source=app_source)
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
    blueprint_dir = bp_name or "mpi_bp_{}_v{}".format(blueprint_name, version)
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

    create_bp_dir(bp_cls, blueprint_dir, with_secrets)
    click.echo("\nSuccessfully decompiled. Directory location: {}".format(get_bp_dir()))


def launch_marketplace_item(
    name,
    version,
    project,
    app_name=None,
    profile_name=None,
    patch_editables=True,
    app_source=None,
):
    """
    Launch marketplace items
    If version not there search in published blueprints
    """

    if not version:
        LOG.info("Fetching latest version of Marketplace Item {} ".format(name))
        version = get_mpi_latest_version(
            name=name,
            app_source=app_source,
            app_states=[MARKETPLACE_BLUEPRINT.STATES.PUBLISHED],
        )
        LOG.info(version)

    LOG.info("Converting MPI to blueprint")
    bp_payload = convert_mpi_into_blueprint(
        name=name, version=version, project_name=project, app_source=app_source
    )

    app_name = app_name or "Mpi-App-{}-{}".format(name, str(uuid.uuid4())[-10:])
    launch_blueprint_simple(
        patch_editables=patch_editables,
        profile_name=profile_name,
        app_name=app_name,
        blueprint=bp_payload,
    )
    LOG.info("App {} creation is successful".format(app_name))


def convert_mpi_into_blueprint(name, version, project_name=None, app_source=None):

    client = get_api_client()
    context = get_context()
    project_config = context.get_project_config()

    project_name = project_name or project_config["name"]
    project_data = get_project(project_name)

    project_uuid = project_data["metadata"]["uuid"]

    LOG.info("Fetching details of project {}".format(project_name))
    res, err = client.project.read(project_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    res = res.json()
    environments = res["status"]["resources"]["environment_reference_list"]

    # For now only single environment exists
    if not environments:
        LOG.error("No environment registered to project '{}'".format(project_name))
        sys.exit(-1)

    env_uuid = environments[0]["uuid"]

    LOG.info("Fetching MPI details")
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=[
            MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
            MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
            MARKETPLACE_BLUEPRINT.STATES.PENDING,
        ],
    )

    # If BP is in published state, provided project should be associated with the bp
    app_state = mpi_data["status"]["resources"]["app_state"]
    if app_state == MARKETPLACE_BLUEPRINT.STATES.PUBLISHED:
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

    LOG.debug("Creating MPI blueprint")
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

    bp = get_blueprint(client, bp_name)
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
        app_source=MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
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

        approve_marketplace_bp(
            bp_name=marketplace_bp_name,
            version=version,
            projects=projects,
            category=category,
        )

        if publish_to_marketplace:
            publish_marketplace_bp(
                bp_name=marketplace_bp_name,
                version=version,
                app_source=MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
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
):

    LOG.info(
        "Fetching existing marketplace blueprints with name {}".format(
            marketplace_bp_name
        )
    )
    res = get_mpis_group_call(
        name=marketplace_bp_name,
        group_member_count=1,
        app_source=MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
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
            MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
            MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
            MARKETPLACE_BLUEPRINT.STATES.PENDING,
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

        approve_marketplace_bp(
            bp_name=marketplace_bp_name,
            version=version,
            projects=projects,
            category=category,
        )

        if publish_to_marketplace:
            publish_marketplace_bp(
                bp_name=marketplace_bp_name,
                version=version,
                app_source=MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
            )


def approve_marketplace_bp(bp_name, version=None, projects=[], category=None):

    client = get_api_client()
    if not version:
        # Search for pending blueprints, Only those blueprints can be approved
        LOG.info("Fetching latest version of Marketplace Blueprint {} ".format(bp_name))
        version = get_mpi_latest_version(
            name=bp_name, app_states=[MARKETPLACE_BLUEPRINT.STATES.PENDING]
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of pending marketplace blueprint {} with version {}".format(
            bp_name, version
        )
    )
    bp = get_mpi_by_name_n_version(
        name=bp_name,
        version=version,
        app_source=MARKETPLACE_BLUEPRINT.SOURCES.LOCAL,
        app_states=[MARKETPLACE_BLUEPRINT.STATES.PENDING],
    )
    bp_uuid = bp["metadata"]["uuid"]
    bp_status = bp["status"]["resources"]["app_blueprint_template"]["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error("Blueprint is in {} state. Unable to approve it".format(bp_status))
        sys.exit(-1)

    res, err = client.market_place.read(bp_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = res.json()
    bp_data.pop("status", None)
    bp_data["api_version"] = "3.0"
    bp_data["spec"]["resources"]["app_state"] = MARKETPLACE_BLUEPRINT.STATES.ACCEPTED

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        bp_data["metadata"]["categories"] = {"AppFamily": category}

    for project in projects:
        project_data = get_project(project)

        bp_data["spec"]["resources"]["project_reference_list"].append(
            {
                "kind": "project",
                "name": project,
                "uuid": project_data["metadata"]["uuid"],
            }
        )

    res, err = client.market_place.update(uuid=bp_uuid, payload=bp_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Blueprint {} with version {} is approved successfully".format(
            bp_name, version
        )
    )


def publish_marketplace_bp(
    bp_name, version=None, projects=[], category=None, app_source=None
):

    client = get_api_client()
    if not version:
        # Search for accepted blueprints, only those blueprints can be published
        LOG.info(
            "Fetching latest version of accepted Marketplace Blueprint {} ".format(
                bp_name
            )
        )
        version = get_mpi_latest_version(
            name=bp_name,
            app_states=[MARKETPLACE_BLUEPRINT.STATES.ACCEPTED],
            app_source=app_source,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of accepted marketplace blueprint {} with version {}".format(
            bp_name, version
        )
    )
    bp = get_mpi_by_name_n_version(
        name=bp_name,
        version=version,
        app_source=app_source,
        app_states=[MARKETPLACE_BLUEPRINT.STATES.ACCEPTED],
    )
    bp_uuid = bp["metadata"]["uuid"]
    bp_status = bp["status"]["resources"]["app_blueprint_template"]["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error(
            "Blueprint is in {} state. Unable to publish it to marketplace".format(
                bp_status
            )
        )
        sys.exit(-1)

    res, err = client.market_place.read(bp_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = res.json()
    bp_data.pop("status", None)
    bp_data["api_version"] = "3.0"
    bp_data["spec"]["resources"]["app_state"] = MARKETPLACE_BLUEPRINT.STATES.PUBLISHED

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        bp_data["metadata"]["categories"] = {"AppFamily": category}

    if projects:
        # Clear the stored projects
        bp_data["spec"]["resources"]["project_reference_list"] = []
        for project in projects:
            project_data = get_project(project)

            bp_data["spec"]["resources"]["project_reference_list"].append(
                {
                    "kind": "project",
                    "name": project,
                    "uuid": project_data["metadata"]["uuid"],
                }
            )

    # Atleast 1 project required for publishing to marketplace
    if not bp_data["spec"]["resources"].get("project_reference_list", None):
        LOG.error("To publish to the Marketplace, please provide a project first.")
        sys.exit(-1)

    res, err = client.market_place.update(uuid=bp_uuid, payload=bp_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info("Marketplace Blueprint is published to marketplace successfully")


def update_marketplace_bp(
    name, version, category=None, projects=[], description=None, app_source=None
):
    """
    updates the marketplace bp
    version is required to prevent unwanted update of another mpi
    """

    client = get_api_client()

    LOG.info(
        "Fetching details of marketplace blueprint {} with version {}".format(
            name, version
        )
    )
    mpi_data = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_source=app_source,
        app_states=[
            MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
            MARKETPLACE_BLUEPRINT.STATES.PUBLISHED,
            MARKETPLACE_BLUEPRINT.STATES.PENDING,
        ],
    )
    bp_uuid = mpi_data["metadata"]["uuid"]

    res, err = client.market_place.read(bp_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = res.json()
    bp_data.pop("status", None)
    bp_data["api_version"] = "3.0"

    if category:
        app_families = get_app_family_list()
        if category not in app_families:
            LOG.error("{} is not a valid App Family category".format(category))
            sys.exit(-1)

        bp_data["metadata"]["categories"] = {"AppFamily": category}

    if projects:
        # Clear all stored projects
        bp_data["spec"]["resources"]["project_reference_list"] = []
        for project in projects:
            project_data = get_project(project)

            bp_data["spec"]["resources"]["project_reference_list"].append(
                {
                    "kind": "project",
                    "name": project,
                    "uuid": project_data["metadata"]["uuid"],
                }
            )

    if description:
        bp_data["spec"]["description"] = description

    res, err = client.market_place.update(uuid=bp_uuid, payload=bp_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Blueprint {} with version {} is updated successfully".format(
            name, version
        )
    )


def delete_marketplace_bp(name, version, app_source=None, app_state=None):

    client = get_api_client()

    if app_state == MARKETPLACE_BLUEPRINT.STATES.PUBLISHED:
        LOG.error("Unpublish MPI {} first to delete it".format(name))
        sys.exit(-1)

    app_states = (
        [app_state]
        if app_state
        else [
            MARKETPLACE_BLUEPRINT.STATES.ACCEPTED,
            MARKETPLACE_BLUEPRINT.STATES.REJECTED,
            MARKETPLACE_BLUEPRINT.STATES.PENDING,
        ]
    )

    LOG.info(
        "Fetching details of unpublished marketplace blueprint {} with version {}".format(
            name, version
        )
    )
    mpi_data = get_mpi_by_name_n_version(
        name=name, version=version, app_source=app_source, app_states=app_states
    )
    bp_uuid = mpi_data["metadata"]["uuid"]

    res, err = client.market_place.delete(bp_uuid)
    LOG.debug("Api response: {}".format(res.json()))
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Blueprint {} with version {} is deleted successfully".format(
            name, version
        )
    )


def reject_marketplace_bp(name, version):

    client = get_api_client()
    if not version:
        # Search for pending blueprints, Only those blueprints can be rejected
        LOG.info(
            "Fetching latest version of pending Marketplace Blueprint {} ".format(name)
        )
        version = get_mpi_latest_version(
            name=name, app_states=[MARKETPLACE_BLUEPRINT.STATES.PENDING]
        )
        LOG.info(version)

    # Pending BP will always of type LOCAL, so no need to apply that filter
    LOG.info(
        "Fetching details of pending marketplace blueprint {} with version {}".format(
            name, version
        )
    )
    bp = get_mpi_by_name_n_version(
        name=name, version=version, app_states=[MARKETPLACE_BLUEPRINT.STATES.PENDING]
    )
    bp_uuid = bp["metadata"]["uuid"]

    res, err = client.market_place.read(bp_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = res.json()
    bp_data.pop("status", None)
    bp_data["api_version"] = "3.0"
    bp_data["spec"]["resources"]["app_state"] = MARKETPLACE_BLUEPRINT.STATES.REJECTED

    res, err = client.market_place.update(uuid=bp_uuid, payload=bp_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Blueprint {} with version {} is rejected successfully".format(
            name, version
        )
    )


def unpublish_marketplace_bp(name, version, app_source=None):

    client = get_api_client()
    if not version:
        # Search for published blueprints, only those can be unpublished
        LOG.info(
            "Fetching latest version of published Marketplace Blueprint {} ".format(
                name
            )
        )
        version = get_mpi_latest_version(
            name=name,
            app_states=[MARKETPLACE_BLUEPRINT.STATES.PUBLISHED],
            app_source=app_source,
        )
        LOG.info(version)

    LOG.info(
        "Fetching details of published marketplace blueprint {} with version {}".format(
            name, version
        )
    )
    bp = get_mpi_by_name_n_version(
        name=name,
        version=version,
        app_states=[MARKETPLACE_BLUEPRINT.STATES.PUBLISHED],
        app_source=app_source,
    )
    bp_uuid = bp["metadata"]["uuid"]

    res, err = client.market_place.read(bp_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_data = res.json()
    bp_data.pop("status", None)
    bp_data["api_version"] = "3.0"
    bp_data["spec"]["resources"]["app_state"] = MARKETPLACE_BLUEPRINT.STATES.ACCEPTED

    res, err = client.market_place.update(uuid=bp_uuid, payload=bp_data)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info(
        "Marketplace Blueprint {} with version {} is unpublished successfully".format(
            name, version
        )
    )
