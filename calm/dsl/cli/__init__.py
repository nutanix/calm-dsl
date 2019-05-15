import time
import warnings
from functools import reduce
import importlib.util
from pprint import pprint
import json

import click
import arrow
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.utils.server_utils import ping
from calm.dsl.builtins import Blueprint

from .constants import RUNLOG
from .config import get_config, get_api_client


@click.group()
@click.option(
    "--ip",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism Central server IP or hostname",
)
@click.option(
    "--port",
    envvar="PRISM_SERVER_PORT",
    default=9440,
    help="Prism Central server port number. Defaults to 9440.",
)
@click.option(
    "--username",
    envvar="PRISM_USERNAME",
    default="admin",
    help="Prism Central username",
)
@click.option(
    "--password", envvar="PRISM_PASSWORD", default=None, help="Prism Central password"
)
@click.option(
    "--config",
    "-c",
    "config_file",
    envvar="CALM_CONFIG",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file, defaults to ~/.calm/config",
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("0.1")
@click.pass_context
def main(ctx, ip, port, username, password, config_file, verbose):
    """Calm CLI"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(
        ip=ip, port=port, username=username, password=password, config_file=config_file
    )
    ctx.obj["client"] = get_api_client()
    ctx.obj["verbose"] = verbose


@main.group()
def get():
    """Get various things like blueprints, apps and so on"""
    pass


@get.group()
def server():
    """Get calm server details"""
    pass


@server.command("status")
@click.pass_obj
def get_server_status(obj):
    """Get calm server connection status"""

    client = obj.get("client")
    host = client.connection.host
    ping_status = "Success" if ping(ip=host) is True else "Fail"

    click.echo("Server Ping Status: {}".format(ping_status))
    click.echo("Server URL: {}".format(client.connection.base_url))
    # TODO - Add info about PC and Calm server version


@get.command("bps")
@click.option(
    "--filter", "filter_by", default=None, help="Filter blueprints with this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.pass_obj
def get_blueprint_list(obj, filter_by, limit):
    """Get the blueprints, optionally filtered by a string"""

    client = obj.get("client")
    config = obj.get("config")

    params = {"length": limit, "offset": 0}
    if filter_by:
        params["filter"] = _get_name_query(filter_by)
    res, err = client.list(params=params)

    if not err:
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
        json_rows = res.json()["entities"]
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
                    _highlight_text(row["name"]),
                    _highlight_text(bp_type),
                    _highlight_text(row["description"]),
                    _highlight_text(row["application_count"]),
                    _highlight_text(project),
                    _highlight_text(row["state"]),
                    _highlight_text(time.ctime(creation_time)),
                    "{}".format(arrow.get(last_update_time).humanize()),
                    _highlight_text(row["uuid"]),

                ]
            )
        click.echo(table)
    else:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(pc_ip)))


@get.command("apps")
@click.option("--names", default=None, help="The name of apps to filter by")
@click.option("--limit", default=20, help="Number of results to return")
@click.pass_obj
def get_apps(obj, names, limit):
    """Get Apps, optionally filtered by a string"""

    client = obj.get("client")
    config = obj.get("config")

    params = {"length": limit, "offset": 0}
    if names:
        params["filter"] = _get_name_query(names)
    res, err = client.list_apps(params=params)

    if not err:
        table = PrettyTable()
        table.field_names = [
            "Application Name",
            "Source Blueprint",
            "State",
            "Owner",
            "Created On",
        ]
        json_rows = res.json()["entities"]
        for _row in json_rows:
            row = _row["status"]
            metadata = _row["metadata"]

            created_on = int(metadata["creation_time"]) // 1000000
            table.add_row(
                [
                    _highlight_text(row["name"]),
                    _highlight_text(
                        row["resources"]["app_blueprint_reference"]["name"]
                    ),
                    _highlight_text(row["state"]),
                    _highlight_text(metadata["owner_reference"]["name"]),
                    "{} ({}) ".format(
                        _highlight_text(time.ctime(created_on)),
                        arrow.get(created_on).humanize(),
                    ),
                ]
            )
        click.echo("\n----Application List----")
        click.echo(table)
        assert res.ok is True
    else:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch applications from {}".format(pc_ip)))


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


@main.group()
def compile():
    """Compile blueprint to json/yaml"""
    pass


@compile.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Blueprint file to upload",
)
@click.option(
    "--out",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
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


@main.group()
def create():
    """Create blueprint, optionally launch too"""
    pass


def create_blueprint(client, bp_payload, name=None, description=None):

    bp_payload.pop("status", None)

    if name:
        bp_payload["spec"]["name"] = name
        bp_payload["metadata"]["name"] = name

    if description:
        bp_payload["spec"]["description"] = description

    bp_resources = bp_payload["spec"]["resources"]
    bp_name = bp_payload["spec"]["name"]
    bp_desc = bp_payload["spec"]["description"]

    return client.upload_with_secrets(bp_name, bp_desc, bp_resources)


def create_blueprint_from_json(client, path_to_json, name=None, description=None):

    bp_payload = json.loads(open(path_to_json, "r").read())
    return create_blueprint(client, bp_payload, name=name, description=description)


def create_blueprint_from_dsl(client, bp_file, name=None, description=None):

    bp_payload = compile_blueprint(bp_file)
    if bp_payload is None:
        err_msg = "User blueprint not found in {}".format(bp_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_blueprint(client, bp_payload, name=name, description=description)


@create.command("bp")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Blueprint file to upload",
)
@click.option("--name", default=None, help="Blueprint name (Optional)")
@click.option("--description", default=None, help="Blueprint description (Optional)")
@click.pass_obj
def create_blueprint_command(obj, bp_file, name, description):
    """Create a blueprint"""

    client = obj.get("client")

    if bp_file.endswith(".json"):
        res, err = create_blueprint_from_json(
            client, bp_file, name=name, description=description
        )
    elif bp_file.endswith(".py"):
        res, err = create_blueprint_from_dsl(
            client, bp_file, name=name, description=description
        )
    else:
        click.echo("Unknown file format {}".format(bp_file))
        return

    if err:
        click.echo(err["error"])
        return

    bp = res.json()
    bp_state = bp["status"]["state"]
    click.echo(">> Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"


def get_blueprint(client, name):

    # find bp
    params = {"filter": "name=={};state!=DELETED".format(name)}

    res, err = client.list(params=params)
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


@get.command("bp")
@click.argument("name")
@click.pass_obj
def get_blueprint_command(obj, name):
    """Get a specific blueprint"""

    client = obj.get("client")
    get_blueprint(client, name)


@main.group()
def delete():
    """Delete blueprints"""
    pass


@delete.command("bp")
@click.argument("blueprint_name")
@click.pass_obj
def delete_blueprint(obj, blueprint_name, blueprint=None):

    client = obj.get("client")
    blueprint = get_blueprint(client, blueprint_name)
    blueprint_id = blueprint["metadata"]["uuid"]
    res, err = client.delete(blueprint_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    click.echo("Blueprint {} deleted".format(blueprint_name))


@main.group()
def launch():
    """Launch blueprints to create Apps"""
    pass


def get_blueprint_runtime_editables(client, blueprint):

    bp_uuid = blueprint.get("metadata", {}).get("uuid", None)
    if not bp_uuid:
        raise Exception(">> Invalid blueprint provided {} >>".format(blueprint))
    res, err = client._get_editables(bp_uuid)
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


def launch_blueprint_simple(client, blueprint_name, blueprint=None, profile_name=None):
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
            "app_name": "TestSimpleLaunch-{}".format(int(time.time())),
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
    res, err = client.launch(blueprint_uuid, launch_payload)
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
        res, err = client.poll_launch(blueprint_uuid, launch_req_id)
        response = res.json()
        pprint(response)
        if response["status"]["state"] == "success":
            app_uuid = response["status"]["application_uuid"]

            config = get_config()
            pc_ip = config["SERVER"]["pc_ip"]
            pc_port = config["SERVER"]["pc_port"]

            # Can't give app url, as deep routing within PC doesn't work.
            # Hence just giving the app id.
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


@launch.command("bp")
@click.argument("blueprint_name")
@click.pass_obj
def launch_blueprint_command(obj, blueprint_name, blueprint=None):

    client = obj.get("client")

    launch_blueprint_simple(client, blueprint_name, blueprint=blueprint)


def _get_app(app_name, client):

    # 1. Get app_uuid from list api
    params = {"filter": "name=={}".format(app_name)}

    res, err = client.list_apps(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    app = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one app found - {}".format(entities))

        click.echo(">> {} found >>".format(app_name))
        app = entities[0]
    else:
        raise Exception(">> No app found with name {} found >>".format(app_name))
    app_id = app["metadata"]["uuid"]

    # 2. Get app details
    click.echo(">> Fetching app details")
    res, err = client.get_app(app_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    app = res.json()
    return app


@main.group()
def describe():
    """Describe apps and blueprints"""
    pass


@describe.command("app")
@click.argument("app_name")
@click.pass_obj
def describe_app(obj, app_name):
    """Describe an app"""

    client = obj.get("client")
    app = _get_app(app_name, client)

    click.echo("\n----Application Summary----\n")
    app_name = app["metadata"]["name"]
    click.echo(
        "Name: "
        + _highlight_text(app_name)
        + " (uuid: "
        + _highlight_text(app["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + _highlight_text(app["status"]["state"]))
    click.echo(
        "Owner: " + _highlight_text(app["metadata"]["owner_reference"]["name"]),
        nl=False,
    )
    click.echo(
        " Project: " + _highlight_text(app["metadata"]["project_reference"]["name"])
    )

    click.echo(
        "Blueprint: "
        + _highlight_text(app["status"]["resources"]["app_blueprint_reference"]["name"])
    )

    created_on = int(app["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            _highlight_text(time.ctime(created_on)), _highlight_text(past)
        )
    )

    click.echo(
        "Application Profile: "
        + _highlight_text(
            app["status"]["resources"]["app_profile_config_reference"]["name"]
        )
    )

    deployment_list = app["status"]["resources"]["deployment_list"]
    click.echo("Deployments [{}]:".format(_highlight_text((len(deployment_list)))))
    for deployment in deployment_list:
        click.echo(
            "\t {} {}".format(
                _highlight_text(deployment["name"]),
                _highlight_text(deployment["state"]),
            )
        )

    action_list = app["status"]["resources"]["action_list"]
    click.echo("App Actions [{}]:".format(_highlight_text(len(action_list))))
    for action in action_list:
        action_name = action["name"]
        if action_name.startswith("action_"):
            prefix_len = len("action_")
            action_name = action_name[prefix_len:]
        click.echo("\t" + _highlight_text(action_name))

    variable_list = app["status"]["resources"]["variable_list"]
    click.echo("App Variables [{}]".format(_highlight_text(len(variable_list))))
    for variable in variable_list:
        click.echo(
            "\t{}: {}  # {}".format(
                _highlight_text(variable["name"]),
                _highlight_text(variable["value"]),
                _highlight_text(variable["label"]),
            )
        )

    click.echo(
        "# Hint: You can run actions on the app using: calm <action_name> app {}".format(
            app_name
        )
    )


@main.command("app")
@click.argument("app_name")
@click.argument("action_name")
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.pass_obj
def run_actions(obj, app_name, action_name, watch):
    """App related functionality: launch, lcm actions, monitor, delete"""

    client = obj.get("client")

    app = _get_app(app_name, client)
    app_spec = app["spec"]
    app_id = app["metadata"]["uuid"]

    # 3. Get action uuid from action name
    if action_name.lower() in ["delete", "soft_delete"]:
        action_name = action_name.lower()
        is_soft_delete = action_name == "soft_delete"
        action_label = "Soft Delete" if is_soft_delete else "Delete"
        res, err = client.delete_app(app_id, is_soft_delete)
        click.echo(">> Triggering {}".format(action_label))
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        else:
            click.echo("{} action triggered".format(action_label))
            response = res.json()
            runlog_id = response["status"]["runlog_uuid"]
            click.echo("Action runlog uuid: {}".format(runlog_id))

            if watch:
                url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"
                payload = {"filter": "root_reference=={}".format(runlog_id)}

                def poll_func():
                    click.echo("Polling action run ...")
                    return client.poll_action_run(url, payload)

                def is_action_complete(response):
                    pprint(response)
                    if len(response["entities"]):
                        for action in response["entities"]:
                            if action["status"]["state"] != "SUCCESS":
                                return (False, "")
                        return (True, "{} action complete".format(action_label))
                    else:
                        return (False, "")

                poll_action(poll_func, is_action_complete)
            return

    calm_action_name = "action_" + action_name.lower()
    action = next(
        action
        for action in app_spec["resources"]["action_list"]
        if action["name"] == calm_action_name or action["name"] == action_name
    )
    if not action:
        raise Exception("No action found matching name {}".format(action_name))
    action_id = action["uuid"]

    # 4. Hit action run api (with metadata and minimal spec: [args, target_kind, target_uuid])
    app.pop("status")
    app["spec"] = {"args": [], "target_kind": "Application", "target_uuid": app_id}
    res, err = client.run_action(app_id, action_id, app)
    click.echo(">> Triggering action run")
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_id = response["status"]["runlog_uuid"]
    click.echo("Runlog uuid: ", runlog_id)
    url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_id)}

    if watch:

        def poll_func():
            click.echo("Polling action run ...")
            return client.poll_action_run(url, payload)

        def is_action_complete(response):
            pprint(response)
            if len(response["entities"]):
                for action in response["entities"]:
                    if action["status"]["state"] != "SUCCESS":
                        return (False, "")
                return (True, "{} action complete".format(action_name))
            else:
                return (False, "")

        poll_action(poll_func, is_action_complete)


def poll_action(poll_func, completion_func):
    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        res, err = poll_func()
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        (completed, msg) = completion_func(response)
        if completed:
            click.echo(msg)
            break
        count += 10
        time.sleep(10)


def watch_action(runlog_id, app_name, client):
    app = _get_app(app_name, client)
    app_id = app["metadata"]["uuid"]

    url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_id)}

    def poll_func():
        click.echo("Polling action status...")
        return client.poll_action_run(url, payload)

    def is_action_complete(response):
        pprint(response)
        if len(response["entities"]):
            for action in response["entities"]:
                state = action["status"]["state"]
                if state in RUNLOG.FAILURE_STATES:
                    return (True, "Action failed")
                if state not in RUNLOG.TERMINAL_STATES:
                    return (False, "")
            return (True, "Action ran successfully")
        return (False, "")

    poll_action(poll_func, is_action_complete)


@main.group()
def watch():
    """Get various things like blueprints, apps and so on"""
    pass


@watch.command("app")
@click.argument("app_name")
@click.option("--action", default=None, help="Watch specific action")
@click.pass_obj
def watch_app(obj, app_name, action):
    """Watch an app"""

    client = obj.get("client")

    if action:
        return watch_action(action, app_name, client)

    app = _get_app(app_name, client)
    app_id = app["metadata"]["uuid"]
    url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"

    payload = {
        "filter": "application_reference=={};(type==action_runlog,type==audit_runlog,type==ngt_runlog,type==clone_action_runlog)".format(
            app_id
        )
    }

    def poll_func():
        click.echo("Polling app status...")
        return client.poll_action_run(url, payload)

    def is_complete(response):
        pprint(response)
        if len(response["entities"]):
            for action in response["entities"]:
                state = action["status"]["state"]
                if state in RUNLOG.FAILURE_STATES:
                    return (True, "Action failed")
                if state not in RUNLOG.TERMINAL_STATES:
                    return (False, "")
            return (True, "Action ran successfully")
        return (False, "")

    poll_action(poll_func, is_complete)


def _get_name_query(names):
    if names:
        search_strings = [
            "name==.*"
            + reduce(
                lambda acc, c: "{}[{}|{}]".format(acc, c.lower(), c.upper()), name, ""
            )
            + ".*"
            for name in names
        ]
        return ",".join(search_strings)


def _highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
