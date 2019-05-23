import time
import warnings
import json
import importlib.util
from pprint import pprint

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable

from calm.dsl.builtins import Blueprint
from .config import get_config
from .utils import get_name_query, get_states_filter, highlight_text
from .constants import BLUEPRINT


def get_blueprint_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the blueprints, optionally filtered by a string"""

    client = obj.get("client")
    config = obj.get("config")

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by
    if all_items:
        filter_query += get_states_filter(BLUEPRINT.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.blueprint.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(pc_ip)))
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


def get_blueprint_module_from_file(bp_file):
    """Returns Blueprint module given a user blueprint dsl file (.py)"""

    spec = importlib.util.spec_from_file_location("calm.dsl.user_bp", bp_file)
    user_bp_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_bp_module)

    return user_bp_module


def get_blueprint_class_from_module(user_bp_module):
    """Returns blueprint class given a module"""

    UserBlueprint = None
    for item in dir(user_bp_module):
        obj = getattr(user_bp_module, item)
        if isinstance(obj, type(Blueprint)):
            if obj.__bases__[0] == Blueprint:
                UserBlueprint = obj

    return UserBlueprint


def compile_blueprint(bp_file):

    user_bp_module = get_blueprint_module_from_file(bp_file)
    UserBlueprint = get_blueprint_class_from_module(user_bp_module)
    if UserBlueprint is None:
        return None

    # TODO - use secret option in cli to handle secrets
    bp_resources = json.loads(UserBlueprint.json_dumps())

    # TODO - fill metadata section using module details (categories, project, etc)
    bp_payload = {
        "spec": {
            "name": UserBlueprint.__name__,
            "description": UserBlueprint.__doc__,
            "resources": bp_resources,
        },
        "metadata": {
            "spec_version": 1,
            "name": UserBlueprint.__name__,
            "kind": "blueprint",
        },
        "api_version": "3.0",
    }

    return bp_payload


def compile_blueprint_command(bp_file, out):

    bp_payload = compile_blueprint(bp_file)
    if bp_payload is None:
        click.echo("User blueprint not found in {}".format(bp_file))
        return

    if out == "json":
        click.echo(json.dumps(bp_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(bp_payload, default_flow_style=False))
    else:
        click.echo("Unknown output format {} given".format(out))


def get_blueprint(client, name):

    # find bp
    params = {"filter": "name=={};state!=DELETED".format(name)}

    res, err = client.blueprint.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    blueprint = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one blueprint found - {}".format(entities))

        click.echo(">> {} found >>".format(name))
        blueprint = entities[0]
    else:
        raise Exception(">> No blueprint found with name {} found >>".format(name))
    return blueprint


def get_blueprint_runtime_editables(client, blueprint):

    bp_uuid = blueprint.get("metadata", {}).get("uuid", None)
    if not bp_uuid:
        raise Exception(">> Invalid blueprint provided {} >>".format(blueprint))
    res, err = client.blueprint._get_editables(bp_uuid)
    response = res.json()
    return response.get("resources", [])


def get_field_values(entity_dict, context, path=None):
    path = path or ""
    for field, value in entity_dict.items():
        if isinstance(value, dict):
            get_field_values(entity_dict[field], context, path=path + "." + field)
        else:
            new_val = input(
                "Value for {} in {} (default value={}): ".format(
                    path + "." + field, context, value
                )
            )
            if new_val:
                entity_dict[field] = type(value)(new_val)


def launch_blueprint_simple(
    client, blueprint_name, app_name=None, blueprint=None, profile_name=None
):
    if not blueprint:
        blueprint = get_blueprint(client, blueprint_name)

    blueprint_uuid = blueprint.get("metadata", {}).get("uuid", "")
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
            raise Exception(">> No profile found with name {} >>".format(profile_name))

    runtime_editables = profile.pop("runtime_editables", [])
    launch_payload = {
        "spec": {
            "app_name": app_name
            if app_name
            else "TestSimpleLaunch-{}".format(int(time.time())),
            "app_description": "",
            "app_profile_reference": profile.get("app_profile_reference", {}),
            "runtime_editables": runtime_editables,
        }
    }
    if runtime_editables:
        click.echo("Blueprint editables are:\n{}".format(runtime_editables))
        for entity_type, entity_list in runtime_editables.items():
            for entity in entity_list:
                context = entity["context"]
                editables = entity["value"]
                get_field_values(editables, context, path=entity.get("name", ""))
        click.echo("Updated blueprint editables are:\n{}".format(runtime_editables))
    res, err = client.blueprint.launch(blueprint_uuid, launch_payload)
    if not err:
        click.echo(">> {} queued for launch >>".format(blueprint_name))
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    launch_req_id = response["status"]["request_id"]

    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        click.echo("Polling status of Launch")
        res, err = client.blueprint.poll_launch(blueprint_uuid, launch_req_id)
        response = res.json()
        pprint(response)
        if response["status"]["state"] == "success":
            app_uuid = response["status"]["application_uuid"]

            config = get_config()
            pc_ip = config["SERVER"]["pc_ip"]
            pc_port = config["SERVER"]["pc_port"]

            click.echo("Successfully launched. App uuid is: {}".format(app_uuid))

            click.echo(
                "App url: https://{}:{}/console/#page/explore/calm/applications/{}".format(
                    pc_ip, pc_port, app_uuid
                )
            )
            break
        elif response["status"]["state"] == "failure":
            click.echo("Failed to launch blueprint. Check API response above.")
            break
        elif err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        count += 10
        time.sleep(10)


def delete_blueprint(obj, blueprint_names):

    client = obj.get("client")

    for blueprint_name in blueprint_names:
        blueprint = get_blueprint(client, blueprint_name)
        blueprint_id = blueprint["metadata"]["uuid"]
        res, err = client.blueprint.delete(blueprint_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        click.echo("Blueprint {} deleted".format(blueprint_name))
