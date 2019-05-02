"""Calm CLI

Usage:
  calm get bps [--filter=<name>...]
  calm describe bp <name> [--json | --yaml]
  calm create bp --file=<bp_file> [--launch]
  calm launch bp <name>
  calm get apps [--filter=<name>...]
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
from functools import reduce
from importlib import import_module
from docopt import docopt
from pprint import pprint
from calm.dsl.utils.server_utils import get_api_client as _get_api_client, ping
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


def main():
    global PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD
    local_config_exists = os.path.isfile(LOCAL_CONFIG_PATH)
    global_config_exists = os.path.isfile(GLOBAL_CONFIG_PATH)

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

    arguments = docopt(__doc__, version="Calm CLI v0.1.0")

    if arguments["config"]:
        if arguments["--server"]:
            [PC_IP, PC_PORT] = arguments["--server"].split(":")
        if arguments["--username"]:
            PC_USERNAME = arguments["--username"]
        if arguments["--password"]:
            PC_PASSWORD = arguments["--password"]

    if arguments["set"] and arguments["config"]:
        # Save to config file if setting values
        config["SERVER"] = {
            "pc_ip": PC_IP,
            "pc_port": PC_PORT,
            "pc_username": PC_USERNAME,
            "pc_password": PC_PASSWORD,
        }
        with open(file_path, "w") as configfile:
            config.write(configfile)

    client = get_api_client(PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD)

    if arguments["get"] and arguments["bps"]:
        get_blueprint_list(arguments["--filter"], client)
    elif arguments["launch"] and arguments["bp"]:
        launch_blueprint(arguments["<name>"], client)
    elif arguments["create"] and arguments["bp"]:
        upload_blueprint(arguments["--file"], client, arguments["--launch"])
    elif arguments["get"] and arguments["apps"]:
        get_apps(arguments["--filter"], client)
    elif arguments["<action>"] and arguments["<app_name>"]:
        run_actions(
            arguments["<action>"], arguments["<app_name>"], client, arguments["--watch"]
        )
    elif arguments["watch"]:
        if arguments["--action"]:
            watch_action(arguments["<runlog_uuid>"], arguments["<app_name>"], client)
        else:
            watch_app(arguments["<app_name>"], client)


def get_name_query(names):
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


def get_blueprint_list(names, client):
    global PC_IP
    assert ping(PC_IP) is True

    params = {"length": 20, "offset": 0}
    if names:
        params["filter"] = get_name_query(names)
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


def get_apps(names, client):
    global PC_IP
    assert ping(PC_IP) is True

    params = {"length": 20, "offset": 0}
    if names:
        params["filter"] = get_name_query(names)
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


def upload_blueprint(name_with_class, client, launch=False):
    global PC_IP
    assert ping(PC_IP) is True

    name_with_class = name_with_class.replace("/", ".")
    (file_name, class_name) = name_with_class.rsplit(".", 1)
    mod = import_module(file_name)
    Blueprint = getattr(mod, class_name)

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
        launch_blueprint(Blueprint, client, bp)


def get_blueprint(blueprint_name, client):
    global PC_IP
    assert ping(PC_IP) is True

    # find bp
    params = {"filter": "name=={};state!=DELETED".format(blueprint_name)}

    res, err = client.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    blueprint = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one blueprint found - {}".format(entities))

        print(">> {} found >>".format(blueprint_name))
        blueprint = entities[0]
    else:
        raise Exception(
            ">> No blueprint found with name {} found >>".format(blueprint_name)
        )
    return blueprint


def launch_blueprint(blueprint_name, client, blueprint=None):
    if not blueprint:
        blueprint = get_blueprint(blueprint_name, client)

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
    global PC_IP
    assert ping(PC_IP) is True

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


def run_actions(action_name, app_name, client, watch=False):
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
                pprint(response)
                is_deleted = response["status"]["state"] == "deleted"
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


def watch_app(app_name, client):
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


if __name__ == "__main__":
    main()
