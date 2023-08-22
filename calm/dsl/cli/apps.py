import os
import sys
import time
import json
import re
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
from .bps import (
    launch_blueprint_simple,
    compile_blueprint,
    create_blueprint,
    get_app,
    parse_launch_runtime_vars,
    parse_launch_params_attribute,
)
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

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
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

    patch_list = app["status"]["resources"]["patch_list"]
    click.echo("App Patches [{}]:".format(highlight_text(len(patch_list))))
    for patch in patch_list:
        patch_name = patch["name"]
        if patch_name.startswith("patch_"):
            prefix_len = len("patch_")
            patch_name = patch_name[prefix_len:]
        click.echo("\t" + highlight_text(patch_name))

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

    # Check if give app name exists or generate random app name
    if app_name:
        res = get_app(app_name)
        if res:
            LOG.debug(res)
            LOG.error("Application Name ({}) is already used.".format(app_name))
            sys.exit(-1)
    else:
        app_name = "App{}".format(str(uuid.uuid4())[:10])

    # Get the blueprint type
    bp_type = bp_payload["spec"]["resources"].get("type", "")

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
    LOG.info("Creating app {}".format(app_name))
    launch_blueprint_simple(
        blueprint_name=bp_name,
        app_name=app_name,
        profile_name=profile_name,
        patch_editables=patch_editables,
        launch_params=launch_params,
        is_brownfield=True if bp_type == "BROWNFIELD" else False,
        skip_app_name_check=True,
    )

    if bp_type != "BROWNFIELD":
        # Delete the blueprint
        res, err = client.blueprint.delete(bp_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))


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


def watch_patch_or_action(runlog_uuid, app_name, client, screen, poll_interval=10):
    app = _get_app(client, app_name, screen=screen)
    app_uuid = app["metadata"]["uuid"]

    url = client.application.ITEM.format(app_uuid) + "/app_runlogs/list"
    payload = {"filter": "root_reference=={}".format(runlog_uuid)}

    def poll_func():
        return client.application.poll_action_run(url, payload)

    poll_runnnable(poll_func, get_completion_func(screen), poll_interval)


def watch_app(app_name, screen, app=None, poll_interval=10):
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

    poll_runnnable(poll_func, is_complete, poll_interval=poll_interval)


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


def get_action_var_val_from_launch_params(launch_vars, var_name):
    """Returns variable value from launch params"""

    filtered_launch_vars = list(
        filter(
            lambda e: e["name"] == var_name,
            launch_vars,
        )
    )

    if len(filtered_launch_vars) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for value of variable '{}'".format(
                var_name
            )
        )
        sys.exit(-1)

    if len(filtered_launch_vars) == 1:
        return filtered_launch_vars[0].get("value", {}).get("value", None)

    return None


def get_patch_runtime_args(
    app_uuid, deployments, patch_payload, ignore_runtime_variables, runtime_params_file
):
    """Returns patch arguments or variable data"""

    patch_name = patch_payload["name"]

    patch_args = {}
    patch_args["patch"] = patch_payload
    patch_args["variables"] = []

    attrs_list = patch_payload["attrs_list"]

    if ignore_runtime_variables:
        return patch_args

    def disk_in_use(substrate, disk):
        boot_disk = substrate["create_spec"]["resources"]["boot_config"]["boot_device"]
        return (
            disk["disk_address"]["adapter_type"]
            == boot_disk["disk_address"]["adapter_type"]
            and disk["disk_address"]["device_index"]
            == boot_disk["disk_address"]["device_index"]
        )

    def nic_name(nic):
        return nic["subnet_reference"]["name"] if nic["subnet_reference"] else ""

    def disk_name(disk):
        return "{}-{}".format(
            disk["device_properties"]["disk_address"]["adapter_type"],
            disk["device_properties"]["disk_address"]["device_index"],
        )

    nic_index_pattern = r".+?\[([0-9]*)\]"

    # If file is supplied for launch params
    if runtime_params_file:
        click.echo("Patching values for runtime variables under patch action ...")

        for attrs in attrs_list:
            patch_items = attrs["data"]

            target_deployment_uuid = attrs["target_any_local_reference"]["uuid"]
            target_deployment = next(
                filter(
                    lambda deployment: deployment["uuid"] == target_deployment_uuid,
                    deployments,
                ),
                None,
            )
            if target_deployment == None:
                LOG.info(
                    "Target deployment with uuid {} not found. Skipping patch attributes editables".format(
                        target_deployment_uuid
                    )
                )
                continue

            substrate = target_deployment["substrate"]

            nic_in_use = -1
            nic_address = substrate["readiness_probe"]["address"]
            readiness_probe_disabled = substrate["readiness_probe"][
                "disable_readiness_probe"
            ]
            if nic_address:
                matches = re.search(nic_index_pattern, nic_address)
                if matches != None and not readiness_probe_disabled:
                    nic_in_use = int(matches.group(1))

            # Skip nics that are being used by the vm
            nics = (
                patch_items["pre_defined_nic_list"]
                if nic_in_use == -1
                else patch_items["pre_defined_nic_list"][nic_in_use + 1 :]
            )

            disks = patch_items["pre_defined_disk_list"]

            patch_attrs_editables = parse_launch_params_attribute(
                launch_params=runtime_params_file, parse_attribute="patch_attrs"
            )

            editables = next(
                filter(
                    lambda patch_attrs: patch_attrs["patch_attributes_uuid"]
                    == attrs["uuid"],
                    patch_attrs_editables,
                ),
                None,
            )

            if editables == None:
                LOG.info(
                    "No patch editables found for patch attributes with uuid {}".format(
                        attrs["uuid"]
                    )
                )
                continue

            vm_config_editables = editables.get("vm_config", {})
            nic_editables = editables.get("nics", {})
            disk_editables = editables.get("disks", {})
            category_editables = editables.get("categories", {})

            # VM config editables
            for key, value in vm_config_editables.items():
                patch_item = patch_items[key + "_ruleset"]
                if (
                    patch_item["editable"]
                    and patch_item["min_value"] <= value <= patch_item["max_value"]
                ):
                    if patch_item["value"] != value:
                        LOG.info(
                            "Attribute {} marked for modify with value {}".format(
                                key, value
                            )
                        )
                        patch_item["value"] = value

            # NIC delete
            if patch_items["nic_delete_allowed"]:
                for i, nic in enumerate(nics):
                    nic_index = i if nic_in_use == -1 else i + nic_in_use
                    if nic_index in nic_editables.get("delete", []):
                        LOG.info('NIC "{}" marked for deletion'.format(nic_name(nic)))
                        nic["operation"] = "delete"

            nics_not_added = []

            # NIC add
            for i, nic in enumerate(nics):
                if nic["operation"] == "add" and nic["editable"]:
                    nic_edit = next(
                        filter(
                            lambda n: n["identifier"] == nic["identifier"],
                            nic_editables.get("add", []),
                        ),
                        None,
                    )
                    if (
                        nic_edit
                        and nic["subnet_reference"]["uuid"]
                        != nic_edit["subnet_reference"]["uuid"]
                    ):
                        LOG.info(
                            "NIC with identifier {} marked for modify with subnet {}".format(
                                nic["identifier"], nic_name(nic_edit)
                            )
                        )
                        nic["subnet_reference"] = nic_edit["subnet_reference"]

                if nic["operation"] == "add" and i in nic_editables.get("delete", []):
                    LOG.info(
                        "NIC with identifier {} skipped from addition".format(
                            nic["identifier"]
                        )
                    )
                    nics_not_added.append(i)

            # Skip adding nics that are deleted
            nics = [nic for i, nic in enumerate(nics) if i not in nics_not_added]

            patch_items["pre_defined_nic_list"] = nics

            # Disk delete
            if patch_items["disk_delete_allowed"]:
                for i, disk in enumerate(disks):
                    if i in disk_editables.get("delete", []) and not disk_in_use(
                        substrate, disk["device_properties"]
                    ):
                        LOG.info("Disk {} marked for deletion".format(disk_name(disk)))
                        disk["operation"] = "delete"

            # Disk modify
            for disk in disks:
                if (
                    disk["operation"] == "modify"
                    and disk["disk_size_mib"]
                    and disk["disk_size_mib"]["editable"]
                ):
                    disk_edit = next(
                        filter(
                            lambda d: disk_name(d) == disk_name(disk),
                            disk_editables.get("modify", []),
                        ),
                        None,
                    )
                    if (
                        disk_edit
                        and disk["disk_size_mib"]["min_value"]
                        <= disk_edit["disk_size_mib"]["value"]
                        <= disk["disk_size_mib"]["max_value"]
                    ):
                        if (
                            disk["disk_size_mib"]["value"]
                            != disk_edit["disk_size_mib"]["value"]
                        ):
                            LOG.info(
                                "Disk {} marked for modify with size {}".format(
                                    disk_name(disk), disk_edit["disk_size_mib"]["value"]
                                )
                            )
                            disk["disk_size_mib"]["value"] = disk_edit["disk_size_mib"][
                                "value"
                            ]

            disks_not_added = []

            # Disk add
            for i, disk in enumerate(disks):
                if (
                    disk["operation"] == "add"
                    and disk["disk_size_mib"]
                    and disk["disk_size_mib"]["editable"]
                ):
                    disk_edit = next(
                        filter(
                            lambda d: i == d["index"],
                            disk_editables.get("add", []),
                        ),
                        None,
                    )
                    if (
                        disk_edit
                        and disk["disk_size_mib"]["min_value"]
                        <= disk_edit["disk_size_mib"]["value"]
                        <= disk["disk_size_mib"]["max_value"]
                    ):
                        if (
                            disk["disk_size_mib"]["value"]
                            != disk_edit["disk_size_mib"]["value"]
                        ):
                            LOG.info(
                                "Disk {} marked for addition with size {}".format(
                                    disk_name(disk), disk_edit["disk_size_mib"]["value"]
                                )
                            )
                            disk["disk_size_mib"]["value"] = disk_edit["disk_size_mib"][
                                "value"
                            ]
                if disk["operation"] == "add" and i in disk_editables.get("delete", []):
                    LOG.info("Disk {} skipped from addition".format(disk_name(disk)))
                    disks_not_added.append(i)

            # Skip adding disks that are deleted
            disks = [disk for i, disk in enumerate(disks) if i not in disks_not_added]

            patch_items["pre_defined_disk_list"] = disks

            categories = patch_items["pre_defined_categories"]

            # Category delete
            if patch_items["categories_delete_allowed"]:
                for i, category in enumerate(categories):
                    if i in category_editables.get("delete", []):
                        LOG.info(
                            "Category {} marked for deletion".format(category["value"])
                        )
                        category["operation"] = "delete"

            # Category add
            if patch_items["categories_add_allowed"]:
                for category in category_editables.get("add", []):
                    LOG.info("Category {} marked for addition".format(category))
                    patch_items["pre_defined_categories"].append(
                        {"operation": "add", "value": category}
                    )

        return patch_args

    # Else prompt for runtime variable values

    click.echo("Please provide values for runtime variables in the patch action")

    for attrs in attrs_list:

        patch_items = attrs["data"]
        target_deployment_uuid = attrs["target_any_local_reference"]["uuid"]

        click.echo(
            "Patch editables targeted at deployment {} are as follows \n {}".format(
                target_deployment_uuid,
                json.dumps(patch_items, indent=4, separators=(",", ": ")),
            )
        )

        nic_in_use = -1
        disk_in_use = ""

        # find out which nic and disk is currently used
        for deployment in deployments:
            if deployment["uuid"] == target_deployment_uuid:
                substrate = deployment["substrate"]

                nic_address = substrate["readiness_probe"]["address"]
                readiness_probe_disabled = substrate["readiness_probe"][
                    "disable_readiness_probe"
                ]
                if nic_address:
                    matches = re.search(nic_index_pattern, nic_address)
                    if matches != None and not readiness_probe_disabled:
                        nic_in_use = int(matches.group(1))

                disk_address = substrate["create_spec"]["resources"]["boot_config"][
                    "boot_device"
                ]["disk_address"]
                disk = "{}-{}".format(
                    disk_address["adapter_type"], disk_address["device_index"]
                )
                disk_in_use = disk

        def prompt_value(patch_item, display_message):
            min_value = (
                patch_item["value"]
                if patch_item["operation"] == "increase"
                else patch_item["min_value"]
            )
            max_value = (
                patch_item["value"]
                if patch_item["operation"] == "decrease"
                else patch_item["max_value"]
            )
            click.echo()
            return click.prompt(
                display_message,
                default=highlight_text(patch_item["value"]),
                type=click.IntRange(min=min_value, max=max_value),
            )

        def prompt_bool(display_message):
            click.echo()
            return click.prompt(
                display_message,
                default=highlight_text("n"),
                type=click.Choice(["y", "n"]),
            )

        click.echo("\n\t\t\t", nl=False)
        click.secho("VM CONFIGURATION", underline=True, bold=True)

        # Sockets, cores and memory modify
        display_names = {
            "num_sockets_ruleset": "vCPUs",
            "num_vcpus_per_socket_ruleset": "Cores per vCPU",
            "memory_size_mib_ruleset": "Memory (MiB)",
        }
        for ruleset in display_names:
            patch_item = patch_items[ruleset]
            if patch_item["editable"]:
                new_val = prompt_value(
                    patch_item,
                    "Enter value for {}".format(display_names[ruleset]),
                )
                patch_item["value"] = new_val

        nics = (
            patch_items["pre_defined_nic_list"]
            if nic_in_use == -1
            else patch_items["pre_defined_nic_list"][nic_in_use + 1 :]
        )

        click.echo("\n\t\t\t", nl=False)
        click.secho("NETWORK CONFIGURATION", underline=True, bold=True)

        # NIC add
        nics_not_added = []
        for i, nic in enumerate(nics):
            if nic["operation"] == "add":
                to_add = prompt_bool(
                    'Do you want to add the NIC "{}" with identifier {}'.format(
                        nic["subnet_reference"]["name"], nic["identifier"]
                    )
                )
                if to_add == "n":
                    nics_not_added.append(i)

        # remove NICs not added from patch list
        nics = [nic for i, nic in enumerate(nics) if i not in nics_not_added]

        # NIC delete
        if patch_items["nic_delete_allowed"] and len(nics) > 0:
            to_delete = prompt_bool("Do you want to delete a NIC")

            if to_delete == "y":
                click.echo()
                click.echo("Choose from following options")
                for i, nic in enumerate(nics):
                    click.echo(
                        "\t{}. NIC-{} {}".format(
                            highlight_text(i), i + 1, nic["subnet_reference"]["name"]
                        )
                    )

                click.echo()
                nic_to_delete = click.prompt(
                    "Choose nic to delete",
                    default=0,
                    type=click.IntRange(max=len(nics)),
                )

                nics[nic_to_delete]["operation"] = "delete"
                LOG.info(
                    "Delete NIC-{} {}".format(
                        nic_to_delete + 1,
                        nics[nic_to_delete]["subnet_reference"]["name"],
                    )
                )
        patch_items["pre_defined_nic_list"] = nics

        click.echo("\n\t\t\t", nl=False)
        click.secho("STORAGE CONFIGURATION", underline=True, bold=True)

        # Disk delete
        disks = list(
            filter(
                lambda disk: disk_name(disk) != disk_in_use,
                patch_items["pre_defined_disk_list"],
            )
        )
        if patch_items["disk_delete_allowed"] and len(disks) > 0:
            to_delete = prompt_bool("Do you want to delete a disk")
            if to_delete == "y":
                click.echo()
                click.echo("Choose from following options")
                for i, disk in enumerate(disks):
                    click.echo(
                        "\t{}. DISK-{} {} {}".format(
                            highlight_text(i),
                            i + 1,
                            disk_name(disk),
                            disk["disk_size_mib"]["value"],
                        )
                    )
                click.echo()
                disk_to_delete = click.prompt(
                    "Choose disk to delete",
                    default=0,
                    type=click.IntRange(max=len(disks)),
                )
                disks[disk_to_delete]["operation"] = "delete"
                LOG.info(
                    "Delete DISK-{} {}".format(
                        disk_to_delete + 1, disk_name(disks[disk_to_delete])
                    )
                )

        # Disk modify
        for disk in disks:
            disk_size = disk["disk_size_mib"]
            if disk_size != None and disk_size["editable"]:
                new_val = prompt_value(
                    disk_size,
                    "Enter size for disk {}".format(disk_name(disk)),
                )
                disk_size["value"] = new_val
        patch_items["pre_defined_disk_list"] = disks

        click.echo("\n\t\t\t", nl=False)
        click.secho("CATEGORIES", underline=True, bold=True)

        # Category delete
        categories = patch_items["pre_defined_categories"]
        if patch_items["categories_delete_allowed"] and len(categories) > 0:
            to_delete = prompt_bool("Do you want to delete a category")
            if to_delete == "y":
                click.echo()
                click.echo("Choose from following options")
                for i, category in enumerate(categories):
                    click.echo("\t{}. {}".format(highlight_text(i), category["value"]))
                click.echo()
                category_to_delete = click.prompt(
                    "Choose category to delete",
                    default=0,
                    type=click.IntRange(max=len(categories)),
                )
                categories[category_to_delete]["operation"] = "delete"
                LOG.info(
                    "Delete category {}".format(categories[category_to_delete]["value"])
                )

        # Category add
        if patch_items["categories_add_allowed"]:
            to_add = prompt_bool("Add a category?")
            while to_add == "y":
                click.echo()
                new_val = click.prompt(
                    "Enter value for category", default="", show_default=False
                )
                patch_items["pre_defined_categories"].append(
                    {"operation": "add", "value": new_val}
                )
                to_add = prompt_bool("Add another category?")

    return patch_args


def get_action_runtime_args(
    app_uuid, action_payload, patch_editables, runtime_params_file
):
    """Returns action arguments or variable data"""

    action_name = action_payload["name"]

    runtime_vars = {}
    runbook_vars = action_payload["runbook"].get("variable_list", None) or []
    for _var in runbook_vars:
        editable_dict = _var.get("editables", None) or {}
        if editable_dict.get("value", False):
            runtime_vars[_var["name"]] = _var

    client = get_api_client()
    res, err = client.application.action_variables(
        app_id=app_uuid, action_name=action_name
    )
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    action_args = res.json()

    # If no need to patch editable or there is not runtime var, return action args received from api
    if not (patch_editables and runtime_vars):
        return action_args or []

    # If file is supplied for launch params
    if runtime_params_file:
        click.echo("Patching values for runtime variables under action ...")

        parsed_runtime_vars = parse_launch_runtime_vars(
            launch_params=runtime_params_file
        )
        for _arg in action_args:
            var_name = _arg["name"]
            if var_name in runtime_vars:

                new_val = get_action_var_val_from_launch_params(
                    launch_vars=parsed_runtime_vars, var_name=var_name
                )
                if new_val is not None:
                    _arg["value"] = new_val

        return action_args

    # Else prompt for runtime variable values
    click.echo(
        "Found runtime variables in action. Please provide values for runtime variables"
    )

    for _arg in action_args:
        if _arg["name"] in runtime_vars:

            _var = runtime_vars[_arg["name"]]
            options = _var.get("options", {})
            choices = options.get("choices", [])
            click.echo("")
            if choices:
                click.echo("Choose from given choices: ")
                for choice in choices:
                    click.echo("\t{}".format(highlight_text(repr(choice))))

            default_val = _arg["value"]
            is_secret = _var.get("type") == "SECRET"

            new_val = click.prompt(
                "Value for variable '{}' [{}]".format(
                    _arg["name"],
                    highlight_text(default_val if not is_secret else "*****"),
                ),
                default=default_val,
                show_default=False,
                hide_input=is_secret,
                type=click.Choice(choices) if choices else type(default_val),
                show_choices=False,
            )

            _arg["value"] = new_val

    return action_args


def run_patches(
    app_name,
    patch_name,
    watch,
    ignore_runtime_variables=False,
    runtime_params_file=None,
):
    client = get_api_client()

    app = _get_app(client, app_name)
    app_spec = app["spec"]
    app_id = app["metadata"]["uuid"]

    calm_patch_name = "patch_" + patch_name.lower()
    patch_payload = next(
        (
            patch
            for patch in app_spec["resources"]["patch_list"]
            if patch["name"] == calm_patch_name or patch["name"] == patch_name
        ),
        None,
    )
    if not patch_payload:
        LOG.error("No patch found matching name {}".format(patch_name))
        sys.exit(-1)

    patch_id = patch_payload["uuid"]

    deployments = app_spec["resources"]["deployment_list"]

    patch_args = get_patch_runtime_args(
        app_uuid=app_id,
        deployments=deployments,
        patch_payload=patch_payload,
        ignore_runtime_variables=ignore_runtime_variables,
        runtime_params_file=runtime_params_file,
    )

    # Hit action run api (with metadata and minimal spec: [args, target_kind, target_uuid])
    app.pop("status")
    app["spec"] = {
        "args": patch_args,
        "target_kind": "Application",
        "target_uuid": app_id,
    }
    res, err = client.application.run_patch(app_id, patch_id, app)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]
    click.echo(
        "Patch is triggered. Got Runlog uuid: {}".format(highlight_text(runlog_uuid))
    )

    if watch:

        def display_patch(screen):
            screen.clear()
            screen.print_at(
                "Fetching runlog tree for patch '{}'".format(patch_name), 0, 0
            )
            screen.refresh()
            watch_patch_or_action(
                runlog_uuid,
                app_name,
                get_api_client(),
                screen,
            )
            screen.wait_for_input(10.0)

        Display.wrapper(display_patch, watch=True)

    else:
        click.echo("")
        click.echo(
            "# Hint1: You can run patch in watch mode using: calm run patch {} --app {} --watch".format(
                patch_name, app_name
            )
        )
        click.echo(
            "# Hint2: You can watch patch runlog on the app using: calm watch action_runlog {} --app {}".format(
                runlog_uuid, app_name
            )
        )


def get_snapshot_name_arg(config, config_task_id):
    default_value = next(
        (
            var["value"]
            for var in config["variable_list"]
            if var["name"] == "snapshot_name"
        ),
        "",
    )
    val = click.prompt(
        "Value for Snapshot Name [{}]".format(highlight_text(repr(default_value))),
        default=default_value,
        show_default=False,
    )
    return {"name": "snapshot_name", "value": val, "task_uuid": config_task_id}


def get_recovery_point_group_arg(config, config_task_id, recovery_groups):
    choices = {}
    for i, rg in enumerate(recovery_groups):
        choices[i + 1] = {
            "label": "{}. {} [Created On: {} Expires On: {}]".format(
                i + 1,
                rg["status"]["name"],
                time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.gmtime(
                        rg["status"]["recovery_point_info_list"][0]["creation_time"]
                        // 1000000
                    ),
                ),
                time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.gmtime(
                        rg["status"]["recovery_point_info_list"][0]["expiration_time"]
                        // 1000000
                    ),
                ),
            ),
            "uuid": rg["status"]["uuid"],
        }
    if not choices:
        LOG.error(
            "No recovery group found. Please take a snapshot before running restore action"
        )
        sys.exit(-1)
    default_idx = 1

    click.echo("Choose from given choices: ")
    for choice in choices.values():
        click.echo("\t{}".format(highlight_text(repr(choice["label"]))))
    selected_val = click.prompt(
        "Selected Recovery Group [{}]".format(highlight_text(repr(default_idx))),
        default=default_idx,
        show_default=False,
    )
    if selected_val not in choices:
        LOG.error(
            "Invalid value {}, not present in choices: {}".format(
                selected_val, choices.keys()
            )
        )
        sys.exit(-1)
    return {
        "name": "recovery_point_group_uuid",
        "value": choices[selected_val]["uuid"],
        "task_uuid": config_task_id,
    }


def run_actions(
    app_name, action_name, watch, patch_editables=False, runtime_params_file=None
):
    client = get_api_client()
    if action_name.lower() == SYSTEM_ACTIONS.CREATE:
        click.echo(
            "The Create Action is triggered automatically when you deploy a blueprint. It cannot be run separately."
        )
        return
    if action_name.lower() == SYSTEM_ACTIONS.DELETE:
        # Because Delete requries a differernt API workflow
        delete_app([app_name])
        return
    if action_name.lower() == SYSTEM_ACTIONS.SOFT_DELETE:
        delete_app(
            [app_name], soft=True
        )  # Because Soft Delete also requries the differernt API workflow
        return

    app = _get_app(client, app_name)
    app_spec = app["spec"]
    app_id = app["metadata"]["uuid"]

    calm_action_name = "action_" + action_name.lower()
    action_payload = next(
        (
            action
            for action in app_spec["resources"]["action_list"]
            if action["name"] == calm_action_name or action["name"] == action_name
        ),
        None,
    )
    if not action_payload:
        LOG.error("No action found matching name {}".format(action_name))
        sys.exit(-1)

    action_id = action_payload["uuid"]

    action_args = get_action_runtime_args(
        app_uuid=app_id,
        action_payload=action_payload,
        patch_editables=patch_editables,
        runtime_params_file=runtime_params_file,
    )

    # Hit action run api (with metadata and minimal spec: [args, target_kind, target_uuid])
    status = app.pop("status")
    config_list = status["resources"]["snapshot_config_list"]
    config_list.extend(status["resources"]["restore_config_list"])
    for task in action_payload["runbook"]["task_definition_list"]:
        if task["type"] == "CALL_CONFIG":
            config = next(
                config
                for config in config_list
                if config["uuid"] == task["attrs"]["config_spec_reference"]["uuid"]
            )
            if config["type"] == "AHV_SNAPSHOT":
                action_args.append(get_snapshot_name_arg(config, task["uuid"]))
            elif config["type"] == "AHV_RESTORE":
                substrate_id = next(
                    (
                        dep["substrate_configuration"]["uuid"]
                        for dep in status["resources"]["deployment_list"]
                        if dep["uuid"]
                        == config["attrs_list"][0]["target_any_local_reference"]["uuid"]
                    ),
                    None,
                )
                api_filter = ""
                if substrate_id:
                    api_filter = "substrate_reference==" + substrate_id
                res, err = client.application.get_recovery_groups(app_id, api_filter)
                if err:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))
                action_args.append(
                    get_recovery_point_group_arg(
                        config, task["uuid"], res.json()["entities"]
                    )
                )

    app["spec"] = {
        "args": action_args,
        "target_kind": "Application",
        "target_uuid": app_id,
    }
    res, err = client.application.run_action(app_id, action_id, app)

    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]
    click.echo(
        "Action is triggered. Got Action Runlog uuid: {}".format(
            highlight_text(runlog_uuid)
        )
    )

    if watch:

        def display_action(screen):
            screen.clear()
            screen.print_at(
                "Fetching runlog tree for action '{}'".format(action_name), 0, 0
            )
            screen.refresh()
            watch_patch_or_action(
                runlog_uuid,
                app_name,
                get_api_client(),
                screen,
            )
            screen.wait_for_input(10.0)

        Display.wrapper(display_action, watch=True)

    else:
        click.echo("")
        click.echo(
            "# Hint1: You can run action in watch mode using: calm run action {} --app {} --watch".format(
                action_name, app_name
            )
        )
        click.echo(
            "# Hint2: You can watch action runlog on the app using: calm watch action_runlog {} --app {}".format(
                runlog_uuid, app_name
            )
        )


def poll_runnnable(poll_func, completion_func, poll_interval=10):
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
