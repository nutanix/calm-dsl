"""Calm CLI

Usage:
  calm get blueprints [<name> ...]
  calm describe blueprint <name> [--json|--yaml]
  calm upload blueprint <name>
  calm launch blueprint <name>
  calm config [--server <ip:port>] [--username <username>] [--password <password>]
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
import json
import time
import warnings
import configparser
from functools import reduce
from docopt import docopt
from pprint import pprint
from calm.dsl.utils.server_utils import get_api_client as _get_api_client, ping

# Defaults to be used if no config file exists.
PC_IP = "10.51.152.102"
PC_PORT = 9440
PC_USERNAME = "admin"
PC_PASSWORD = "***REMOVED***"

LOCAL_CONFIG_PATH = "config.ini"
GLOBAL_CONFIG_PATH = "~/.calm/config"


def get_api_client(pc_ip=PC_IP, pc_port=PC_PORT, username=PC_USERNAME, password=PC_PASSWORD):
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

        config["SERVER"] = {
            "pc_ip": PC_IP,
            "pc_port": PC_PORT,
            "pc_username": PC_USERNAME,
            "pc_password": PC_PASSWORD
        }
        with open(file_path, "w") as configfile:
            config.write(configfile)
    client = get_api_client(PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD)
    if arguments["get"]:
        get_blueprint_list(arguments["<name>"], client)
    if arguments["launch"]:
        launch_blueprint(arguments["<name>"][0], client)


def get_blueprint_list(names, client):
    global PC_IP
    assert ping(PC_IP) is True

    params = {
        "length": 20,
        "offset": 0,
    }
    if names:
        search_strings = ["name==.*" + reduce(lambda acc, c: "{}[{}|{}]".
                          format(acc, c.lower(), c.upper()), name, "") + ".*" for name in names
                          ]
        params["filter"] = ",".join(search_strings)
    res, err = client.list(params=params)

    if not err:
        print(">> Blueprint List >>")
        print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        assert res.ok is True
    else:
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(PC_IP)))


def launch_blueprint(blueprint_name, client):
    global PC_IP, PC_PORT
    client = get_api_client()
    # find bp
    params = {
        "filter": "name=={};state!=DELETED".format(blueprint_name)
    }

    res, err = client.list(params=params)
    if err:
        print("[{}] - {}".format(err["code"], err["error"]))
        return

    response = res.json()
    entities = response.get("entities", None)
    blueprint = None
    if entities:
        if len(entities) != 1:
            print("More than one blueprint found - {}".format(entities))
            return

        print(">> {} found >>".format(blueprint_name))
        blueprint = entities[0]
    else:
        print(">>No blueprint found with name {} found >>".format(blueprint_name))
        return

    blueprint_id = blueprint["metadata"]["uuid"]
    print(">>Fetching blueprint details")
    res, err = client.get(blueprint_id)
    if err:
        print("[{}] - {}".format(err["code"], err["error"]))
        return
    blueprint = res.json()
    blueprint_spec = blueprint["spec"]

    launch_payload = {
        "api_version": "3.0",
        "metadata": blueprint["metadata"],
        "spec": {
            "application_name": "ExistingVMApp-{}".format(int(time.time())),
            "app_profile_reference": {
                "kind": "app_profile",
                "name": "{}".format(blueprint_spec["resources"]["app_profile_list"][0]["name"]),
                "uuid": "{}".format(blueprint_spec["resources"]["app_profile_list"][0]["uuid"]),
            },
            "resources": blueprint_spec["resources"]
        },
    }

    res, err = client.full_launch(blueprint_id, launch_payload)
    if not err:
        print(">> {} queued for launch >>".format(blueprint_name))
        print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
    else:
        print("[{}] - {}".format(err["code"], err["error"]))
        return
    response = res.json()
    launch_req_id = response["status"]["request_id"]

    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        print("Polling status of Launch")
        res, err = client.launch_poll(blueprint_id, launch_req_id)
        response = res.json()
        pprint(response)
        if response["status"]["state"] == "success":
            app_uuid = response["status"]["application_uuid"]
            # Can't give app url, as deep routing within PC doesn't work.
            # Hence just giving the app id.
            print("Successfully launched. App uuid is: {}".format(app_uuid))
            break
        elif err:
            print("[{}] - {}".format(err["code"], err["error"]))
            break
        count += 10
        time.sleep(10)


if __name__ == "__main__":
    main()
