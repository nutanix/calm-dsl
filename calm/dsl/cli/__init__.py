"""Calm CLI

Usage:
  calm get bps [--filter=<name>...]
  calm describe bp <name> [--json | --yaml]
  calm create bp --file=<bp_file>
  calm delete bp <bp_name>
  calm launch bp (--name <bp_name> | --file <bp_file>)
  calm get apps [--filter=<name>...]
  calm describe app <app_name>
  calm <action> app <app_name> [--watch]
  calm watch --action <action_runlog_uuid> --app <app_name>
  calm watch --app <app_name>
  calm set config [--server <ip:port>] [--username <username>] [--password <password>]
  calm get config
  calm (-h | --help)
  calm (-v | --version)

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  -s --server url            Prism Central URL in <ip:port> format
  -u --username username     Prism Central username
  -p --password password     Prism Central password
"""
import os
import time
import warnings
import configparser
import urllib3
import click
from functools import reduce
from importlib import import_module

from pprint import pprint
from calm.dsl.utils.server_utils import get_api_client as _get_api_client
from prettytable import PrettyTable
from .constants import RUNLOG


urllib3.disable_warnings()

# Defaults to be used if no config file exists.
PC_IP = "10.46.34.230"
PC_PORT = 9440
PC_USERNAME = "admin"
PC_PASSWORD = "***REMOVED***"

LOCAL_CONFIG_PATH = "config.ini"
GLOBAL_CONFIG_PATH = "~/.calm/config"


def get_api_client(
    pc_ip=PC_IP, pc_port=PC_PORT, username=PC_USERNAME, password=PC_PASSWORD
):
    return _get_api_client(pc_ip=pc_ip, pc_port=pc_port, auth=(username, password))


@click.group()
@click.option(
    "--username", envvar="PRISM_USERNAME", default=None, help="Prism Central username"
)
@click.option(
    "--password", envvar="PRISM_PASSWORD", default=None, help="Prism Central password"
)
@click.option(
    "--server",
    "-s",
    envvar="PRISM_SERVER",
    default=None,
    help="Prism Central server URL in <ip>:<port> format",
)
@click.option(
    "--config",
    "-c",
    "config_file",
    envvar="CALM_CONFIG",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of config file, default is %s in current directory, %s otherwise"
    % (LOCAL_CONFIG_PATH, GLOBAL_CONFIG_PATH),
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("0.1")
@click.pass_context
def main(ctx, username, password, server, config_file, verbose):
    """Calm CLI

\b
Usage:
  calm get bps [--filter=<name>...]
  calm describe bp <name> [--json | --yaml]
  calm create bp --file=<bp_file>
  calm delete bp <bp_name>
  calm launch bp (--name <bp_name> | --file <bp_file>)
  calm get apps [--filter=<name>...]
  calm describe app <app_name>
  calm <action> app <app_name> [--watch]
  calm watch --action <action_runlog_uuid> --app <app_name>
  calm watch --app <app_name>
  calm set config [--server <ip:port>] [--username <username>] [--password <password>]
  calm get config
    """

    global PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD

    local_config_exists = os.path.isfile(LOCAL_CONFIG_PATH)
    global_config_exists = os.path.isfile(GLOBAL_CONFIG_PATH)

    file_path = config_file

    if not file_path:
        if global_config_exists and not local_config_exists:
            file_path = GLOBAL_CONFIG_PATH
        else:
            file_path = LOCAL_CONFIG_PATH

    config = configparser.ConfigParser()
    config.read(file_path)

    if "SERVER" in config:
        PC_IP = config["SERVER"]["pc_ip"]
        PC_PORT = config["SERVER"]["pc_port"]
        PC_USERNAME = config["SERVER"]["pc_username"]
        PC_PASSWORD = config["SERVER"]["pc_password"]

    if server:
        [PC_IP, PC_PORT] = server.split(":")
    if username:
        PC_USERNAME = username
    if password:
        PC_PASSWORD = password

    if file_path or "SERVER" not in config:
        # Save to config file if explicitly set, or no config file found
        config["SERVER"] = {
            "pc_ip": PC_IP,
            "pc_port": PC_PORT,
            "pc_username": PC_USERNAME,
            "pc_password": PC_PASSWORD,
        }
        with open(file_path, "w") as configfile:
            config.write(configfile)

    ctx.ensure_object(dict)
    ctx.obj["client"] = get_api_client(PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD)

    if verbose:
        click.echo("Using user %s @ https://%s:%s" % (PC_USERNAME, PC_IP, PC_PORT))

    # if arguments["get"] and arguments["bps"]:
    #     get_blueprint_list(arguments["--filter"], client)
    # elif arguments["delete"] and arguments["<bp_name>"]:
    #     delete_blueprint(arguments["<bp_name>"], client)
    # elif arguments["launch"] and arguments["bp"]:
    #     if arguments["--name"]:
    #         launch_blueprint(arguments["<bp_name>"], client)
    #     elif arguments["--file"]:
    #         upload_blueprint(arguments["--file"], client, True)
    # elif arguments["create"] and arguments["bp"]:
    #     upload_blueprint(arguments["--file"], client)
    # elif arguments["get"] and arguments["apps"]:
    #     get_apps(arguments["--filter"], client)
    # elif arguments["describe"] and arguments["app"]:
    #     describe_app(arguments["<app_name>"], client)
    # elif arguments["<action>"] and arguments["<app_name>"]:
    #     run_actions(
    #         arguments["<action>"], arguments["<app_name>"], client, arguments["--watch"]
    #     )
    # elif arguments["watch"]:
    #     if arguments["--action"]:
    #         watch_action(
    #             arguments["<action_runlog_uuid>"], arguments["<app_name>"], client
    #         )
    #     else:
    #         watch_app(arguments["<app_name>"], client)


@main.group()
def get():
    """Get various things like blueprints, apps and so on"""


@get.command("bps")
@click.option(
    "--filter", "filter_by", default=None, help="Filter blueprints with this string"
)
@click.option("--limit", default=20, help="Number of results to return")
@click.pass_context
def get_blueprint_list(ctx, filter_by, limit):
    """Get the blueprints, optionally filtered by a string"""
    global PC_IP

    client = ctx.obj.get("client")

    params = {"length": limit, "offset": 0}
    if filter_by:
        params["filter"] = _get_name_query(filter_by)
    res, err = client.list(params=params)

    if not err:
        table = PrettyTable()
        table.field_names = [
            "Blueprint Name",
            "Type",
            "Description",
            "State",
            "Project",
            "Application Count",
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
            table.add_row(
                [
                    row["name"],
                    bp_type,
                    row["description"],
                    row["state"],
                    project,
                    row["application_count"],
                ]
            )
        print("\n----Blueprint List----")
        print(table)
        assert res.ok is True
    else:
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(PC_IP)))


@get.command("apps")
@click.option("--names", default=None, help="The name of apps to filter by")
@click.option("--limit", default=20, help="Number of results to return")
@click.pass_context
def get_apps(ctx, names, limit):
    """Get Apps, optionally filtered by a string"""

    global PC_IP

    client = ctx.obj.get("client")

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

            created_on = time.ctime(int(metadata["creation_time"]) // 1000000)
            table.add_row(
                [
                    row["name"],
                    row["resources"]["app_blueprint_reference"]["name"],
                    row["state"],
                    metadata["owner_reference"]["name"],
                    created_on,
                ]
            )
        print("\n----Application List----")
        print(table)
        assert res.ok is True
    else:
        warnings.warn(UserWarning("Cannot fetch applications from {}".format(PC_IP)))


@main.group()
def create():
    """Create blueprint, optionally launch too"""


@create.command("bp")
@click.argument("name")
@click.option(
    "--file",
    "-f",
    "bp_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Blueprint file to upload",
)
@click.option("--class", "bp_class", help="The name of the blueprint class in the file")
@click.pass_context
def upload_blueprint(ctx, name, bp_file, bp_class, launch_):
    """Upload a blueprint"""

    global PC_IP

    click.echo("Upload called. Path + name:", bp_file)

    if bp_file.startswith("."):
        bp_file = bp_file[2:]

    file_name = bp_file.replace("/", ".")[:-3]
    file_name_with_class = name.replace("/", ".")
    mod = import_module(file_name)

    Blueprint = getattr(mod, bp_class)

    client = ctx.obj.get("client")
    # seek and destroy
    params = {"filter": "name=={};state!=DELETED".format(Blueprint)}
    res, err = client.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) != 1:
            raise Exception("More than one blueprint found - {}".format(entities))

        print(">> {} found >>".format(Blueprint))
        uuid = entities[0]["metadata"]["uuid"]

        res, err = client.delete(uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        print(">> {} deleted >>".format(Blueprint))

    else:
        print(">> {} not found >>".format(Blueprint))

    # upload
    res, err = client.upload_with_secrets(Blueprint)
    if not err:
        print(">> {} uploaded with credentials >>".format(Blueprint))
        # print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        assert res.ok is True
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    bp = res.json()
    bp_state = bp["status"]["state"]
    print(">> Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"

    if launch:
        launch_blueprint(ctx, Blueprint, bp)


@get.command("bp")
@click.argument("name")
@click.pass_context
def get_blueprint(ctx, name):
    """Get a specific blueprint"""
    global PC_IP
    client = ctx.obj.get("client")

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

        print(">> {} found >>".format(name))
        blueprint = entities[0]
    else:
        raise Exception(">> No blueprint found with name {} found >>".format(name))
    return blueprint


@main.group()
def delete():
    """Delete blueprints"""


@delete.command("bp")
@click.argument("blueprint_name")
@click.pass_context
def delete_blueprint(ctx, blueprint_name, blueprint=None):

    client = ctx.obj.get("client")
    blueprint = get_blueprint(blueprint_name, client)
    blueprint_id = blueprint["metadata"]["uuid"]
    res, err = client.delete(blueprint_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    click.echo("Blueprint {} deleted".format(blueprint_name))


@main.group()
def launch():
    """Launch blueprints to create Apps"""


@launch.command("bp")
@click.argument("blueprint_name")
@click.pass_context
def launch_blueprint(blueprint_name, client, blueprint=None):
    client = ctx.obj.get("client")
    import ipdb

    ipdb.set_trace()
    if not blueprint:
        blueprint = get_blueprint(client, blueprint_name)

    blueprint_id = blueprint["metadata"]["uuid"]
    print(">> Fetching blueprint details")
    res, err = client.get(blueprint_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    blueprint = res.json()
    blueprint_spec = blueprint["spec"]

    launch_payload = {
        "api_version": "3.0",
        "metadata": blueprint["metadata"],
        "spec": {
            "application_name": "NextDemoApp-{}".format(int(time.time())),
            "app_profile_reference": {
                "kind": "app_profile",
                "name": "{}".format(
                    blueprint_spec["resources"]["app_profile_list"][0]["name"]
                ),
                "uuid": "{}".format(
                    blueprint_spec["resources"]["app_profile_list"][0]["uuid"]
                ),
            },
            "resources": blueprint_spec["resources"],
        },
    }

    res, err = client.full_launch(blueprint_id, launch_payload)
    if not err:
        print(">> {} queued for launch >>".format(blueprint_name))
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    launch_req_id = response["status"]["request_id"]

    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        print("Polling status of Launch")
        res, err = client.poll_launch(blueprint_id, launch_req_id)
        response = res.json()
        pprint(response)
        if response["status"]["state"] == "success":
            app_uuid = response["status"]["application_uuid"]

            # Can't give app url, as deep routing within PC doesn't work.
            # Hence just giving the app id.
            print("Successfully launched. App uuid is: {}".format(app_uuid))
            print(
                "App url: https://{}:{}/console/#page/explore/calm/applications/{}".format(
                    PC_IP, PC_PORT, app_uuid
                )
            )
            break
        elif response["status"]["state"] == "failure":
            print("Failed to launch blueprint. Check API response above.")
            break
        elif err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        count += 10
        time.sleep(10)


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

        print(">> {} found >>".format(app_name))
        app = entities[0]
    else:
        raise Exception(">> No app found with name {} found >>".format(app_name))
    app_id = app["metadata"]["uuid"]

    # 2. Get app details
    print(">> Fetching app details")
    res, err = client.get_app(app_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    app = res.json()
    return app


@main.group()
def describe():
    """Describe apps and blueprints"""


@describe.command("app")
@click.argument("app_name")
@click.pass_context
def describe_app(ctx, app_name):
    """Describe an app"""

    client = ctx.obj.get("client")
    app = _get_app(app_name, client)

    print("\n----Application Summary----\n")
    app_name = app["metadata"]["name"]
    print("Name: {}".format(app_name))
    print("UUID: {}".format(app["metadata"]["uuid"]))
    print("Status: {}".format(app["status"]["state"]))
    print("Owner: {}".format(app["metadata"]["owner_reference"]["name"]))
    print("Project: {}".format(app["metadata"]["project_reference"]["name"]))

    created_on = time.ctime(int(app["metadata"]["creation_time"]) // 1000000)
    print("Created On: {}".format(created_on))

    print(
        "Source Blueprint: {}".format(
            app["status"]["resources"]["app_blueprint_reference"]["name"]
        )
    )

    print(
        "Application Profile: {}".format(
            app["status"]["resources"]["app_profile_config_reference"]["name"]
        )
    )

    deployment_list = app["status"]["resources"]["deployment_list"]
    print("Deployments ({}):".format(len(deployment_list)))
    for deployment in deployment_list:
        print("\t{} {}".format(deployment["name"], deployment["state"]))

    action_list = app["status"]["resources"]["action_list"]
    print("App Actions ({}):".format(len(action_list)))
    for action in action_list:
        action_name = action["name"]
        if action_name.startswith("action_"):
            action_name = action_name[len("action_") :]
        print("\t{}".format(action_name))

    variable_list = app["status"]["resources"]["variable_list"]
    print("App Variables ({}):".format(len(variable_list)))
    for variable in variable_list:
        print(
            "\t{}: {}  # {}".format(
                variable["name"], variable["value"], variable["label"]
            )
        )

    print(
        "# You can run actions on the app using: calm <action_name> app {}".format(
            app_name
        )
    )


@main.command("app")
@click.argument("app_name")
@click.argument("action_name")
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
@click.pass_context
def run_actions(ctx, app_name, action_name, watch):
    """App related functionality: launch, lcm actions, monitor, delete"""

    client = ctx.obj.get("client")

    app = _get_app(app_name, client)
    app_spec = app["spec"]
    app_id = app["metadata"]["uuid"]

    # 3. Get action uuid from action name
    if action_name.lower() == "delete":
        res, err = client.delete_app(app_id)
        print(">> Triggering Delete")
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("Delete action triggered")
            response = res.json()
            runlog_id = response["status"]["runlog_uuid"]
            print("Action runlog uuid: {}".format(runlog_id))

            def poll_func():
                print("Polling Delete action...")
                return client.get_app(app_id)

            def is_deletion_complete(response):
                status = response["status"]["state"]
                print("Current app status: {}".format(status))
                is_deleted = status == "deleted"
                return (is_deleted, "Successfully deleted app {}".format(app_name))

            if watch:
                poll_action(poll_func, is_deletion_complete)
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
    print(">> Triggering action run")
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_id = response["status"]["runlog_uuid"]
    print("Runlog uuid: ", runlog_id)
    url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_id)}

    def poll_func():
        print("Polling action run ...")
        return client.poll_action_run(url, payload)

    def is_action_complete(response):
        pprint(response)
        if len(response["entities"]):
            for action in response["entities"]:
                if action["status"]["state"] != "SUCCESS":
                    return (False, "")
            return (True, "{} action complete".format(action_name.upper()))
        return (False, "")

    if watch:
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
            print(msg)
            break
        count += 10
        time.sleep(10)


def watch_action(runlog_id, app_name, client):
    app = _get_app(app_name, client)
    app_id = app["metadata"]["uuid"]

    url = client.APP_ITEM.format(app_id) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_id)}

    def poll_func():
        print("Polling action status...")
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


@watch.command("app")
@click.argument("app_name")
@click.option("--action", default=None, help="Watch specific action")
@click.pass_context
def watch_app(ctx, app_name, action):
    """Watch an app"""

    client = ctx.obj.get("client")

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
        print("Polling app status...")
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


if __name__ == "__main__":
    main()
