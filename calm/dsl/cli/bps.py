import time
import json
import sys
from pprint import pprint
import pathlib

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable
from black import format_file_in_place, WriteBack, FileMode

from calm.dsl.builtins import (
    Blueprint,
    SimpleBlueprint,
    create_blueprint_payload,
    file_exists,
)
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client

from .utils import (
    get_name_query,
    get_states_filter,
    highlight_text,
    get_module_from_file,
    import_var_from_file,
)
from .constants import BLUEPRINT
from calm.dsl.store import Cache
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def get_blueprint_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""

    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(BLUEPRINT.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.blueprint.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch blueprints from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No blueprint found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "BLUEPRINT TYPE",
        "DESCRIPTION",
        "APPLICATION COUNT",
        "PROJECT",
        "STATE",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        bp_type = (
            "Single VM"
            if "categories" in metadata
            and "TemplateType" in metadata["categories"]
            and metadata["categories"]["TemplateType"] == "Vm"
            else "Multi VM/Pod"
        )

        project = (
            metadata["project_reference"]["name"]
            if "project_reference" in metadata
            else None
        )

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(bp_type),
                highlight_text(row["description"]),
                highlight_text(row["application_count"]),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)


def describe_bp(blueprint_name, out):
    """Displays blueprint data"""

    client = get_api_client()
    bp = get_blueprint(client, blueprint_name, all=True)

    res, err = client.blueprint.read(bp["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    bp = res.json()

    if out == "json":
        bp.pop("status", None)
        click.echo(json.dumps(bp, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Blueprint Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(blueprint_name)
        + " (uuid: "
        + highlight_text(bp["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(bp["status"]["description"]))
    click.echo("Status: " + highlight_text(bp["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(bp["metadata"]["owner_reference"]["name"]), nl=False
    )
    click.echo(
        " Project: " + highlight_text(bp["metadata"]["project_reference"]["name"])
    )

    created_on = int(bp["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    bp_resources = bp.get("status").get("resources", {})
    profile_list = bp_resources.get("app_profile_list", [])
    click.echo("Application Profiles [{}]:".format(highlight_text(len(profile_list))))
    for profile in profile_list:
        profile_name = profile["name"]
        click.echo("\t" + highlight_text(profile_name))

        substrate_ids = [
            dep.get("substrate_local_reference", {}).get("uuid")
            for dep in profile.get("deployment_create_list", [])
        ]
        substrate_types = [
            sub.get("type")
            for sub in bp_resources.get("substrate_definition_list")
            if sub.get("uuid") in substrate_ids
        ]
        click.echo("\tSubstrates[{}]:".format(highlight_text(len(substrate_types))))
        click.echo("\t\t{}".format(highlight_text(", ".join(substrate_types))))

        click.echo("\tActions[{}]:".format(highlight_text(len(profile["action_list"]))))
        for action in profile["action_list"]:
            action_name = action["name"]
            if action_name.startswith("action_"):
                prefix_len = len("action_")
                action_name = action_name[prefix_len:]
            click.echo("\t\t" + highlight_text(action_name))

    service_list = (
        bp.get("status").get("resources", {}).get("service_definition_list", [])
    )
    click.echo("Services [{}]:".format(highlight_text(len(service_list))))
    for service in service_list:
        service_name = service["name"]
        click.echo("\t" + highlight_text(service_name))
        # click.echo("\tActions:")


def get_blueprint_module_from_file(bp_file):
    """Returns Blueprint module given a user blueprint dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_bp", bp_file)


def get_blueprint_class_from_module(user_bp_module):
    """Returns blueprint class given a module"""

    UserBlueprint = None
    for item in dir(user_bp_module):
        obj = getattr(user_bp_module, item)
        if isinstance(obj, (type(Blueprint), type(SimpleBlueprint))):
            if obj.__bases__[0] in (Blueprint, SimpleBlueprint):
                UserBlueprint = obj

    return UserBlueprint


def compile_blueprint(bp_file, no_sync=False):

    # Sync only if no_sync flag is not set
    if not no_sync:
        LOG.info("Syncing cache")
        Cache.sync()

    user_bp_module = get_blueprint_module_from_file(bp_file)
    UserBlueprint = get_blueprint_class_from_module(user_bp_module)
    if UserBlueprint is None:
        return None

    bp_payload = None
    if isinstance(UserBlueprint, type(SimpleBlueprint)):
        bp_payload = UserBlueprint.make_bp_dict()
    else:
        UserBlueprintPayload, _ = create_blueprint_payload(UserBlueprint)
        bp_payload = UserBlueprintPayload.get_dict()

        # Note - Install/Uninstall runbooks are not actions in Packages.
        # Remove package actions after compiling.
        cdict = bp_payload["spec"]["resources"]
        for package in cdict["package_definition_list"]:
            if "action_list" in package:
                del package["action_list"]

    return bp_payload


def compile_blueprint_command(bp_file, out, no_sync=False):

    bp_payload = compile_blueprint(bp_file, no_sync)
    if bp_payload is None:
        LOG.error("User blueprint not found in {}".format(bp_file))
        return

    config = get_config()

    project_name = config["PROJECT"].get("name", "default")
    project_uuid = Cache.get_entity_uuid("PROJECT", project_name)

    if not project_uuid:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )

    bp_payload["metadata"]["project_reference"] = {
        "type": "project",
        "uuid": project_uuid,
        "name": project_name,
    }

    credential_list = bp_payload["spec"]["resources"]["credential_definition_list"]
    is_secret_avl = False
    for cred in credential_list:
        if cred["secret"].get("secret", None):
            cred["secret"].pop("secret")
            is_secret_avl = True
            # At compile time, value will be empty
            cred["secret"]["value"] = ""

    if is_secret_avl:
        LOG.warning("Secrets are not shown in payload !!!")

    if out == "json":
        click.echo(json.dumps(bp_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(bp_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def format_blueprint_command(bp_file):
    path = pathlib.Path(bp_file)
    LOG.debug("Formatting blueprint {} using black".format(path))
    if format_file_in_place(
        path, fast=False, mode=FileMode(), write_back=WriteBack.DIFF
    ):
        LOG.info("Patching above diff to blueprint - {}".format(path))
        format_file_in_place(
            path, fast=False, mode=FileMode(), write_back=WriteBack.YES
        )
        LOG.info("All done!")
    else:
        LOG.info("Blueprint {} left unchanged.".format(path))


def get_blueprint(client, name, all=False):

    # find bp
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";state!=DELETED"

    res, err = client.blueprint.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    blueprint = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one blueprint found - {}".format(entities))

        LOG.info("{} found ".format(name))
        blueprint = entities[0]
    else:
        raise Exception("No blueprint found with name {} found".format(name))
    return blueprint


def get_blueprint_runtime_editables(client, blueprint):

    bp_uuid = blueprint.get("metadata", {}).get("uuid", None)
    if not bp_uuid:
        LOG.debug("Blueprint UUID not present in metadata")
        raise Exception("Invalid blueprint provided {} ".format(blueprint))
    res, err = client.blueprint._get_editables(bp_uuid)
    response = res.json()
    return response.get("resources", [])


def get_field_values(
    entity_dict, context, path=None, hide_input=False, launch_runtime_vars=None,
):
    path = path or ""
    for field, value in entity_dict.items():
        if isinstance(value, dict):
            get_field_values(
                entity_dict[field],
                context,
                path=path + "." + field,
                hide_input=hide_input,
                launch_runtime_vars=launch_runtime_vars,
            )
        else:
            new_val = None
            if launch_runtime_vars:
                new_val = get_val_launch_runtime_vars(
                    launch_runtime_vars, field, path, context
                )
            else:
                prompt_str = "{} -> {}".format(
                    highlight_text(context), path + "." + field
                )
                new_val = click.prompt(prompt_str, default=value, hide_input=hide_input)
            if new_val:
                entity_dict[field] = type(value)(new_val)


def get_val_launch_runtime_vars(launch_runtime_vars, field, path, context):
    filtered_launch_runtime_vars = list(
        filter(
            lambda e: is_launch_runtime_vars_context_matching(e["context"], context)
            and e["name"] == path,
            launch_runtime_vars,
        )
    )
    if len(filtered_launch_runtime_vars) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for name {} and context {}".format(
                path, context
            )
        )
        sys.exit(-1)
    if len(filtered_launch_runtime_vars) == 1:
        return filtered_launch_runtime_vars[0].get("value", {}).get(field, None)
    return None


def is_launch_runtime_vars_context_matching(launch_runtime_var_context, context):
    context_list = context.split(".")
    if len(context_list) > 1 and context_list[-1] == "variable":
        return context_list[-2] == launch_runtime_var_context or (
            is_launch_runtime_var_action_match(launch_runtime_var_context, context_list)
        )
    return False


def is_launch_runtime_var_action_match(launch_runtime_var_context, context_list):
    launch_runtime_var_context_list = launch_runtime_var_context.split(".")

    # Note: As variables under profile level actions can be marked as runtime_editable only
    # Context ex: app_profile.<profile_name>.action.<action_name>.runbook.<runbook_name>.variable
    if len(launch_runtime_var_context_list) == 2 and len(context_list) >= 4:
        if (
            context_list[1] == launch_runtime_var_context_list[0]
            and context_list[3] == launch_runtime_var_context_list[1]
        ):
            return True
    return False


def parse_launch_runtime_vars(launch_params):
    if launch_params:
        if file_exists(launch_params) and launch_params.endswith(".py"):
            return import_var_from_file(launch_params, "runtime_vars", [])
        else:
            LOG.warning(
                "Invalid launch_params passed! Must be a valid and existing.py file! Ignoring..."
            )
    return []


def launch_blueprint_simple(
    blueprint_name=None,
    app_name=None,
    blueprint=None,
    profile_name=None,
    patch_editables=True,
    launch_params=None,
):
    client = get_api_client()
    if not blueprint:
        blueprint = get_blueprint(client, blueprint_name)

    blueprint_uuid = blueprint.get("metadata", {}).get("uuid", "")
    blueprint_name = blueprint_name or blueprint.get("metadata", {}).get("name", "")

    bp_status = blueprint["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error("Blueprint is in {} state. Unable to launch it".format(bp_status))
        sys.exit(-1)

    LOG.info("Fetching runtime editables in the blueprint")
    profiles = get_blueprint_runtime_editables(client, blueprint)
    profile = None
    if profile_name is None:
        profile = profiles[0]
    else:
        for app_profile in profiles:
            app_prof_ref = app_profile.get("app_profile_reference", {})
            if app_prof_ref.get("name") == profile_name:
                profile = app_profile

                break
        if not profile:
            raise Exception("No profile found with name {}".format(profile_name))

    runtime_editables = profile.pop("runtime_editables", [])

    # Popping out substrate list in runtime editables for now.
    runtime_editables.pop("substrate_list", None)
    launch_payload = {
        "spec": {
            "app_name": app_name
            if app_name
            else "App-{}-{}".format(blueprint_name, int(time.time())),
            "app_description": "",
            "app_profile_reference": profile.get("app_profile_reference", {}),
            "runtime_editables": runtime_editables,
        }
    }

    if runtime_editables and patch_editables:
        runtime_editables_json = json.dumps(
            runtime_editables, indent=4, separators=(",", ": ")
        )
        click.echo("Blueprint editables are:\n{}".format(runtime_editables_json))
        # Check user input
        launch_runtime_vars = parse_launch_runtime_vars(launch_params)
        for entity_type, entity_list in runtime_editables.items():
            for entity in entity_list:
                context = entity["context"]
                editables = entity["value"]
                hide_input = entity.get("type") == "SECRET"
                get_field_values(
                    editables,
                    context,
                    path=entity.get("name", ""),
                    hide_input=hide_input,
                    launch_runtime_vars=launch_runtime_vars,
                )
        runtime_editables_json = json.dumps(
            runtime_editables, indent=4, separators=(",", ": ")
        )
        LOG.info("Updated blueprint editables are:\n{}".format(runtime_editables_json))
    res, err = client.blueprint.launch(blueprint_uuid, launch_payload)
    if not err:
        LOG.info("Blueprint {} queued for launch".format(blueprint_name))
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    launch_req_id = response["status"]["request_id"]

    poll_launch_status(client, blueprint_uuid, launch_req_id)


def poll_launch_status(client, blueprint_uuid, launch_req_id):
    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        LOG.info("Polling status of Launch")
        res, err = client.blueprint.poll_launch(blueprint_uuid, launch_req_id)
        response = res.json()
        app_state = response["status"]["state"]
        pprint(response)
        if app_state == "success":
            app_uuid = response["status"]["application_uuid"]

            config = get_config()
            pc_ip = config["SERVER"]["pc_ip"]
            pc_port = config["SERVER"]["pc_port"]

            click.echo("Successfully launched. App uuid is: {}".format(app_uuid))

            LOG.info(
                "App url: https://{}:{}/console/#page/explore/calm/applications/{}".format(
                    pc_ip, pc_port, app_uuid
                )
            )
            break
        elif app_state == "failure":
            LOG.error("Failed to launch blueprint. Check API response above.")
            break
        elif err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info(app_state)
        count += 10
        time.sleep(10)


def delete_blueprint(blueprint_names):

    client = get_api_client()

    for blueprint_name in blueprint_names:
        blueprint = get_blueprint(client, blueprint_name)
        blueprint_id = blueprint["metadata"]["uuid"]
        res, err = client.blueprint.delete(blueprint_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Blueprint {} deleted".format(blueprint_name))
