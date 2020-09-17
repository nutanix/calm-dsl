import os
import sys
import time
import json
import uuid
from json import JSONEncoder

import arrow
import click
from prettytable import PrettyTable
from anytree import NodeMixin, RenderTree

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context

from .utils import get_name_query, get_states_filter, highlight_text, Display
from .constants import APPLICATION, RUNLOG, SYSTEM_ACTIONS
from .bps import launch_blueprint_simple, compile_blueprint, create_blueprint
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_apps(name, filter_by, limit, offset, quiet, all_items, out):
    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(APPLICATION.STATES, state_key="_state")
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.application.list(params=params)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch applications from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No application found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "SOURCE BLUEPRINT",
        "STATE",
        "PROJECT",
        "OWNER",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

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
                highlight_text(row["resources"]["app_blueprint_reference"]["name"]),
                highlight_text(row["state"]),
                highlight_text(project),
                highlight_text(metadata["owner_reference"]["name"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)


def _get_app(client, app_name, screen=Display(), all=False):
    # 1. Get app_uuid from list api
    params = {"filter": "name=={}".format(app_name)}
    if all:
        params["filter"] += get_states_filter(APPLICATION.STATES, state_key="_state")

    res, err = client.application.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    app = None
    if entities:
        app = entities[0]
        if len(entities) != 1:
            # If more than one item found, check if an exact name match is present. Else raise.
            found = False
            for ent in entities:
                if ent["metadata"]["name"] == app_name:
                    app = ent
                    found = True
                    break
            if not found:
                raise Exception("More than one app found - {}".format(entities))

        screen.clear()
        LOG.info("App {} found".format(app_name))
        screen.refresh()
        app = entities[0]
    else:
        raise Exception("No app found with name {} found".format(app_name))
    app_id = app["metadata"]["uuid"]

    # 2. Get app details
    screen.clear()
    LOG.info("Fetching app details")
    screen.refresh()
    res, err = client.application.read(app_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    app = res.json()
    return app


def describe_app(app_name, out):
    client = get_api_client()
    app = _get_app(client, app_name, all=True)

    if out == "json":
        click.echo(json.dumps(app, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Application Summary----\n")
    app_name = app["metadata"]["name"]
    click.echo(
        "Name: "
        + highlight_text(app_name)
        + " (uuid: "
        + highlight_text(app["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + highlight_text(app["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(app["metadata"]["owner_reference"]["name"]), nl=False
    )
    click.echo(
        " Project: " + highlight_text(app["metadata"]["project_reference"]["name"])
    )

    click.echo(
        "Blueprint: "
        + highlight_text(app["status"]["resources"]["app_blueprint_reference"]["name"])
    )

    created_on = int(app["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )

    click.echo(
        "Application Profile: "
        + highlight_text(
            app["status"]["resources"]["app_profile_config_reference"]["name"]
        )
    )

    deployment_list = app["status"]["resources"]["deployment_list"]
    click.echo("Deployments [{}]:".format(highlight_text((len(deployment_list)))))
    for deployment in deployment_list:
        click.echo(
            "\t {} {}".format(
                highlight_text(deployment["name"]), highlight_text(deployment["state"])
            )
        )

    action_list = app["status"]["resources"]["action_list"]
    click.echo("App Actions [{}]:".format(highlight_text(len(action_list))))
    for action in action_list:
        action_name = action["name"]
        if action_name.startswith("action_"):
            prefix_len = len("action_")
            action_name = action_name[prefix_len:]
        click.echo("\t" + highlight_text(action_name))

    variable_list = app["status"]["resources"]["variable_list"]
    click.echo("App Variables [{}]".format(highlight_text(len(variable_list))))
    for variable in variable_list:
        click.echo(
            "\t{}: {}  # {}".format(
                highlight_text(variable["name"]),
                highlight_text(variable["value"]),
                highlight_text(variable["label"]),
            )
        )

    click.echo("App Runlogs:")

    def display_runlogs(screen):
        watch_app(app_name, screen, app)

    Display.wrapper(display_runlogs, watch=False)

    click.echo(
        "# Hint: You can run actions on the app using: calm run action <action_name> --app {}".format(
            app_name
        )
    )


def create_app(
    bp_file,
    brownfield_deployment_file=None,
    app_name=None,
    profile_name=None,
    patch_editables=True,
    launch_params=None,
):
    client = get_api_client()

    # Compile blueprint
    bp_payload = compile_blueprint(
        bp_file, brownfield_deployment_file=brownfield_deployment_file
    )
    if bp_payload is None:
        LOG.error("User blueprint not found in {}".format(bp_file))
        sys.exit(-1)

    if bp_payload["spec"]["resources"].get("type", "") != "BROWNFIELD":
        LOG.error(
            "Command only allowed for brownfield application. Please use 'calm create bp' and 'calm launch bp' for USER applications"
        )
        sys.exit(-1)

    # Create blueprint from dsl file
    bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
    LOG.info("Creating blueprint {}".format(bp_name))
    res, err = create_blueprint(client=client, bp_payload=bp_payload, name=bp_name)
    if err:
        LOG.error(err["error"])
        return

    bp = res.json()
    bp_state = bp["status"].get("state", "DRAFT")
    bp_uuid = bp["metadata"].get("uuid", "")

    if bp_state != "ACTIVE":
        LOG.debug("message_list: {}".format(bp["status"].get("message_list", [])))
        LOG.error("Blueprint {} went to {} state".format(bp_name, bp_state))
        sys.exit(-1)

    LOG.info(
        "Blueprint {}(uuid={}) created successfully.".format(
            highlight_text(bp_name), highlight_text(bp_uuid)
        )
    )

    # Creating an app
    app_name = app_name or "App{}".format(str(uuid.uuid4())[:10])
    LOG.info("Creating app {}".format(app_name))
    launch_blueprint_simple(
        blueprint_name=bp_name,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=patch_editables,
        launch_params=launch_params,
        is_brownfield=True,
    )


class RunlogNode(NodeMixin):
    def __init__(self, runlog, parent=None, children=None):
        self.runlog = runlog
        self.parent = parent
        if children:
            self.children = children


class RunlogJSONEncoder(JSONEncoder):
    def default(self, obj):

        if not isinstance(obj, RunlogNode):
            return super().default(obj)

        metadata = obj.runlog["metadata"]
        status = obj.runlog["status"]
        state = status["state"]

        if status["type"] == "task_runlog":
            name = status["task_reference"]["name"]
        elif status["type"] == "runbook_runlog":
            if "call_runbook_reference" in status:
                name = status["call_runbook_reference"]["name"]
            else:
                name = status["runbook_reference"]["name"]
        elif status["type"] == "action_runlog" and "action_reference" in status:
            name = status["action_reference"]["name"]
        elif status["type"] == "app":
            return status["name"]
        else:
            return "root"

        # TODO - Fix KeyError for action_runlog
        """
        elif status["type"] == "action_runlog":
            name = status["action_reference"]["name"]
        elif status["type"] == "app":
            return status["name"]
        """

        creation_time = int(metadata["creation_time"]) // 1000000
        username = (
            status["userdata_reference"]["name"]
            if "userdata_reference" in status
            else None
        )
        last_update_time = int(metadata["last_update_time"]) // 1000000

        encodedStringList = []
        encodedStringList.append("{} (Status: {})".format(name, state))
        if status["type"] == "action_runlog":
            encodedStringList.append("\tRunlog UUID: {}".format(metadata["uuid"]))
        encodedStringList.append("\tStarted: {}".format(time.ctime(creation_time)))

        if username:
            encodedStringList.append("\tRun by: {}".format(username))
        if state in RUNLOG.TERMINAL_STATES:
            encodedStringList.append(
                "\tFinished: {}".format(time.ctime(last_update_time))
            )
        else:
            encodedStringList.append(
                "\tLast Updated: {}".format(time.ctime(last_update_time))
            )

        return "\n".join(encodedStringList)


def get_completion_func(screen):
    def is_action_complete(response):

        entities = response["entities"]
        if len(entities):

            # Sort entities based on creation time
            sorted_entities = sorted(
                entities, key=lambda x: int(x["metadata"]["creation_time"])
            )

            # Create nodes of runlog tree and a map based on uuid
            root = None
            nodes = {}
            for runlog in sorted_entities:
                # Create root node
                # TODO - Get details of root node
                if not root:
                    root_uuid = runlog["status"]["root_reference"]["uuid"]
                    root_runlog = {
                        "metadata": {"uuid": root_uuid},
                        "status": {"type": "action_runlog", "state": ""},
                    }
                    root = RunlogNode(root_runlog)
                    nodes[str(root_uuid)] = root

                uuid = runlog["metadata"]["uuid"]
                nodes[str(uuid)] = RunlogNode(runlog, parent=root)

            # Attach parent to nodes
            for runlog in sorted_entities:
                uuid = runlog["metadata"]["uuid"]
                parent_uuid = runlog["status"]["parent_reference"]["uuid"]
                node = nodes[str(uuid)]
                node.parent = nodes[str(parent_uuid)]

            # Show Progress
            # TODO - Draw progress bar
            total_tasks = 0
            completed_tasks = 0
            for runlog in sorted_entities:
                runlog_type = runlog["status"]["type"]
                if runlog_type == "task_runlog":
                    total_tasks += 1
                    state = runlog["status"]["state"]
                    if state in RUNLOG.STATUS.SUCCESS:
                        completed_tasks += 1

            if total_tasks:
                screen.clear()
                progress = "{0:.2f}".format(completed_tasks / total_tasks * 100)
                screen.print_at("Progress: {}%".format(progress), 0, 0)

            # Render Tree on next line
            line = 1
            for pre, fill, node in RenderTree(root):
                lines = json.dumps(node, cls=RunlogJSONEncoder).split("\\n")
                for linestr in lines:
                    tabcount = linestr.count("\\t")
                    if not tabcount:
                        screen.print_at("{}{}".format(pre, linestr), 0, line)
                    else:
                        screen.print_at(
                            "{}{}".format(fill, linestr.replace("\\t", "")), 0, line
                        )
                    line += 1
            screen.refresh()

            for runlog in sorted_entities:
                state = runlog["status"]["state"]
                if state in RUNLOG.FAILURE_STATES:
                    msg = "Action failed."
                    screen.print_at(msg, 0, line)
                    screen.refresh()
                    return (True, msg)
                if state not in RUNLOG.TERMINAL_STATES:
                    return (False, "")

            msg = "Action ran successfully."
            if os.isatty(sys.stdout.fileno()):
                msg += " Exit screen? "
            screen.print_at(msg, 0, line)
            screen.refresh()

            return (True, msg)
        return (False, "")

    return is_action_complete


def watch_action(runlog_uuid, app_name, client, screen, poll_interval=10):
    app = _get_app(client, app_name, screen=screen)
    app_uuid = app["metadata"]["uuid"]

    url = client.application.ITEM.format(app_uuid) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_uuid)}

    def poll_func():
        return client.application.poll_action_run(url, payload)

    poll_action(poll_func, get_completion_func(screen), poll_interval)


def watch_app(app_name, screen, app=None):
    """Watch an app"""

    client = get_api_client()
    is_app_describe = False

    if not app:
        app = _get_app(client, app_name, screen=screen)
    else:
        is_app_describe = True
    app_id = app["metadata"]["uuid"]
    url = client.application.ITEM.format(app_id) + "/app_runlogs/list"

    payload = {
        "filter": "application_reference=={};(type==action_runlog,type==audit_runlog,type==ngt_runlog,type==clone_action_runlog)".format(
            app_id
        )
    }

    def poll_func():
        # screen.echo("Polling app status...")
        return client.application.poll_action_run(url, payload)

    def is_complete(response):
        entities = response["entities"]

        if len(entities):

            # Sort entities based on creation time
            sorted_entities = sorted(
                entities, key=lambda x: int(x["metadata"]["creation_time"])
            )

            # Create nodes of runlog tree and a map based on uuid
            root = RunlogNode(
                {
                    "metadata": {"uuid": app_id},
                    "status": {"type": "app", "state": "", "name": app_name},
                }
            )
            nodes = {}
            nodes[app_id] = root
            for runlog in sorted_entities:
                uuid = runlog["metadata"]["uuid"]
                nodes[str(uuid)] = RunlogNode(runlog, parent=root)

            # Attach parent to nodes
            for runlog in sorted_entities:
                uuid = runlog["metadata"]["uuid"]
                parent_uuid = runlog["status"]["application_reference"]["uuid"]
                node = nodes[str(uuid)]
                node.parent = nodes[str(parent_uuid)]

            # Show Progress
            # TODO - Draw progress bar
            total_tasks = 0
            completed_tasks = 0
            for runlog in sorted_entities:
                runlog_type = runlog["status"]["type"]
                if runlog_type == "action_runlog":
                    total_tasks += 1
                    state = runlog["status"]["state"]
                    if state in RUNLOG.STATUS.SUCCESS:
                        completed_tasks += 1

            if not is_app_describe and total_tasks:
                screen.clear()
                progress = "{0:.2f}".format(completed_tasks / total_tasks * 100)
                screen.print_at("Progress: {}%".format(progress), 0, 0)

            # Render Tree on next line
            line = 1
            for pre, fill, node in RenderTree(root):
                lines = json.dumps(node, cls=RunlogJSONEncoder).split("\\n")
                for linestr in lines:
                    tabcount = linestr.count("\\t")
                    if not tabcount:
                        screen.print_at("{}{}".format(pre, linestr), 0, line)
                    else:
                        screen.print_at(
                            "{}{}".format(fill, linestr.replace("\\t", "")), 0, line
                        )
                    line += 1
            screen.refresh()

            msg = ""
            is_complete = True
            if not is_app_describe:
                for runlog in sorted_entities:
                    state = runlog["status"]["state"]
                    if state in RUNLOG.FAILURE_STATES:
                        msg = "Action failed."
                        is_complete = True
                    if state not in RUNLOG.TERMINAL_STATES:
                        is_complete = False

            if is_complete:
                if not msg:
                    msg = "Action ran successfully."

                if os.isatty(sys.stdout.fileno()):
                    msg += " Exit screen? "
            if not is_app_describe:
                screen.print_at(msg, 0, line)
                screen.refresh()
                time.sleep(10)
            return (is_complete, msg)
        return (False, "")

    poll_action(poll_func, is_complete)


def delete_app(app_names, soft=False):
    client = get_api_client()

    for app_name in app_names:
        app = _get_app(client, app_name)
        app_id = app["metadata"]["uuid"]
        action_label = "Soft Delete" if soft else "Delete"
        LOG.info("Triggering {}".format(action_label))
        res, err = client.application.delete(app_id, soft_delete=soft)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        LOG.info("{} action triggered".format(action_label))
        response = res.json()
        runlog_id = response["status"]["runlog_uuid"]
        LOG.info("Action runlog uuid: {}".format(runlog_id))


def run_actions(screen, app_name, action_name, watch):
    client = get_api_client()

    if action_name.lower() == SYSTEM_ACTIONS.CREATE:
        click.echo(
            "The Create Action is triggered automatically when you deploy a blueprint. It cannot be run separately."
        )
        return
    if action_name.lower() == SYSTEM_ACTIONS.DELETE:
        delete_app([app_name])  # Because Delete requries a differernt API workflow
        return
    if action_name.lower() == SYSTEM_ACTIONS.SOFT_DELETE:
        delete_app(
            [app_name], soft=True
        )  # Because Soft Delete also requries the differernt API workflow
        return

    app = _get_app(client, app_name, screen=screen)
    app_spec = app["spec"]
    app_id = app["metadata"]["uuid"]

    calm_action_name = "action_" + action_name.lower()
    action = next(
        action
        for action in app_spec["resources"]["action_list"]
        if action["name"] == calm_action_name or action["name"] == action_name
    )
    if not action:
        raise Exception("No action found matching name {}".format(action_name))
    action_id = action["uuid"]

    # Hit action run api (with metadata and minimal spec: [args, target_kind, target_uuid])
    app.pop("status")
    app["spec"] = {"args": [], "target_kind": "Application", "target_uuid": app_id}
    res, err = client.application.run_action(app_id, action_id, app)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]
    screen.clear()
    screen.print_at(
        "Got Action Runlog uuid: {}. Fetching runlog tree ...".format(runlog_uuid), 0, 0
    )
    screen.refresh()
    if watch:
        watch_action(runlog_uuid, app_name, client, screen=screen)


def poll_action(poll_func, completion_func, poll_interval=10):
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
            # click.echo(msg)
            break
        count += poll_interval
        time.sleep(poll_interval)


def download_runlog(runlog_id, app_name, file_name):
    """Download runlogs, given runlog uuid and app name"""

    client = get_api_client()
    app = _get_app(client, app_name)
    app_id = app["metadata"]["uuid"]

    if not file_name:
        file_name = "runlog_{}.zip".format(runlog_id)

    res, err = client.application.download_runlog(app_id, runlog_id)
    if not err:
        with open(file_name, "wb") as fw:
            fw.write(res.content)
        click.echo("Runlogs saved as {}".format(highlight_text(file_name)))
    else:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
