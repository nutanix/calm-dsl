import time
import warnings
import urllib3
from functools import reduce
from importlib import import_module
from pprint import pprint

import click
import arrow
from prettytable import PrettyTable

from calm.dsl.utils.server_utils import ping

from .constants import RUNLOG
from .config import get_config, get_api_client


urllib3.disable_warnings()


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
    help="Prism Central username"
)
@click.option(
    "--password",
    envvar="PRISM_PASSWORD",
    default=None,
    help="Prism Central password"
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
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enables verbose mode.",
)
@click.version_option("0.1")
@click.pass_context
def main(ctx, ip, port, username, password, config_file, verbose):
    """Calm CLI"""

    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(
        ip=ip,
        port=port,
        username=username,
        password=password,
        config_file=config_file,
    )
    ctx.obj["client"] = get_api_client()
    ctx.obj["verbose"] = verbose


@main.group()
def get():
    """Get various things like blueprints, apps and so on"""


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
                    _highlight_text(row["name"]),
                    _highlight_text(bp_type),
                    _highlight_text(row["description"]),
                    _highlight_text(row["state"]),
                    _highlight_text(project),
                    _highlight_text(row["application_count"]),
                ]
            )
        click.echo("\n----Blueprint List----")
        click.echo(table)
        assert res.ok is True
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
@click.pass_obj
def upload_blueprint(obj, name, bp_file, bp_class, launch_):
    """Upload a blueprint"""

    click.echo("Upload called. Path + name:", bp_file)

    if bp_file.startswith("."):
        bp_file = bp_file[2:]

    file_name = bp_file.replace("/", ".")[:-3]
    # file_name_with_class = name.replace("/", ".")
    mod = import_module(file_name)

    Blueprint = getattr(mod, bp_class)

    client = obj.get("client")
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
        launch_blueprint(client, str(Blueprint), blueprint=bp)


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

        print(">> {} found >>".format(name))
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


def launch_blueprint(client, blueprint_name, blueprint=None):

    config = get_config()
    pc_ip = config["SERVER"]["pc_ip"]
    pc_port = config["SERVER"]["pc_port"]

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
                    pc_ip, pc_port, app_uuid
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


@launch.command("bp")
@click.argument("blueprint_name")
@click.pass_obj
def launch_blueprint_command(obj, blueprint_name, blueprint=None):

    client = obj.get("client")

    launch_blueprint(client, blueprint_name, blueprint=blueprint)


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


def _highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


if __name__ == "__main__":
    main()
