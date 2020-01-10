import time
import warnings
import importlib.util

import arrow
import click
from prettytable import PrettyTable

from calm.dsl.builtins import RunbookService, create_runbook_payload
from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from .utils import get_name_query, highlight_text, get_states_filter
from .constants import RUNBOOK, RUNLOG
from .runlog import get_completion_func, get_runlog_status
from .endpoints import get_endpoint


def get_runbook_list(obj, name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""

    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by

    if all_items:
        filter_query += get_states_filter(RUNBOOK.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.runbook.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch runbooks from {}".format(pc_ip)))
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
        "DESCRIPTION",
        "RUN COUNT",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
        "PROJECT",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        project = metadata.get("project_reference", {}).get("name", "")

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(row["run_count"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
                highlight_text(project),
            ]
        )
    click.echo(table)


def get_runbook_module_from_file(runbook_file):
    """Return Runbook module given a user runbook dsl file (.py)"""

    spec = importlib.util.spec_from_file_location("calm.dsl.user_bp", runbook_file)
    user_runbook_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_runbook_module)

    return user_runbook_module


def get_runbook_class_from_module(user_runbook_module):
    """Returns runbook class given a module"""

    UserRunbook = None
    for item in dir(user_runbook_module):
        obj = getattr(user_runbook_module, item)
        if isinstance(obj, type(RunbookService)):
            if obj.__bases__[0] is RunbookService:
                UserRunbook = obj

    return UserRunbook


def compile_runbook(runbook_file):

    user_runbook_module = get_runbook_module_from_file(runbook_file)
    UserRunbook = get_runbook_class_from_module(user_runbook_module)
    if UserRunbook is None:
        return None

    runbook_payload = None
    UserRunbookPayload, _ = create_runbook_payload(UserRunbook)
    runbook_payload = UserRunbookPayload.get_dict()

    return runbook_payload


def get_previous_runs(obj, name, filter_by, limit, offset):
    client = get_api_client()
    config = get_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        runbook = get_runbook(client, name)
        runbook_uuid = runbook["metadata"]["uuid"]
        filter_query = filter_query + ";action_reference=={}".format(runbook_uuid)
    if filter_by:
        filter_query = filter_query + ";" + filter_by if name else filter_by
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.runbook.list_previous_runs(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        warnings.warn(UserWarning("Cannot fetch previous runs from {}".format(pc_ip)))
        return

    json_rows = res.json()["entities"]

    table = PrettyTable()
    table.field_names = [
        "SOURCE RUNBOOK",
        "STARTED AT",
        "ENDED AT",
        "COMPLETED IN",
        "RUN BY",
        "UUID",
        "STATE",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        state = row["state"]
        started_at = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        completed_in = last_update_time - started_at
        hours, rem = divmod(completed_in, 3600)
        minutes, seconds = divmod(rem, 60)
        timetaken = ""
        if hours:
            timetaken = "{} hours {} minutes".format(hours, minutes)
        elif minutes:
            timetaken = "{} minutes {} seconds".format(minutes, seconds)
        else:
            timetaken = "{} seconds".format(seconds)

        if state not in RUNLOG.TERMINAL_STATES:
            timetaken = "-"

        table.add_row(
            [
                highlight_text(row["action_reference"]["name"]),
                highlight_text(time.ctime(started_at)),
                "{}".format(arrow.get(last_update_time).humanize()) if state in RUNLOG.TERMINAL_STATES else "-",
                highlight_text(timetaken),
                highlight_text(row["userdata_reference"]["name"]),
                highlight_text(metadata["uuid"]),
                highlight_text(state),
            ]
        )
    click.echo(table)


def get_runbook(client, name, all=False):

    # find runbook
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";deleted==FALSE"

    res, err = client.runbook.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    runbook = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one runbook found - {}".format(entities))

        click.echo(">> Runbook {} found >>".format(name))
        runbook = entities[0]
    else:
        raise Exception(">> No runbook found with name {} found >>".format(name))
    return runbook


def patch_runbook_runtime_editables(client, runbook):

    args = []
    variable_list = runbook["spec"]["resources"]["runbook"].get("variable_list", [])
    for variable in variable_list:
        if variable.get("editables", {}).get("value", False):
            new_val = input(
                "Value for Variable {} in Runbook (default value={}): ".format(
                    variable.get("name"), variable.get("value", "")
                )
            )
            if new_val:
                args.append({"name": variable.get("name"), "value": type(variable.get("value"))(new_val)})

    payload = {"spec": {"args": args}}
    default_target = runbook["spec"]["resources"].get("default_target_reference", {}).get("name", None)
    target = input(
        "Endpoint target for the Runbook Run (default target={}): ".format(default_target)
    )
    if target:
        endpoint = get_endpoint(client, target)
        endpoint_id = endpoint.get("metadata", {}).get("uuid", "")
        payload["spec"]["default_target_reference"] = {
            "kind": "app_endpoint",
            "uuid": endpoint_id,
            "name": target
        }
    return payload


def run_runbook(
    screen,
    client,
    runbook_uuid,
    watch,
    input_data={},
    payload={}
):

    res, err = client.runbook.run(runbook_uuid, payload)
    if not err:
        screen.clear()
        screen.print_at(">> Runbook queued for run", 0, 0)
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]

    def poll_runlog_status():
        return client.runbook.poll_action_run(runlog_uuid)
    screen.refresh()
    should_continue = poll_action(poll_runlog_status, get_runlog_status(screen))
    if not should_continue:
        return
    res, err = client.runbook.poll_action_run(runlog_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    runbook = response['status']['runbook_json']['resources']['runbook']

    if watch:
        screen.refresh()
        watch_runbook(runlog_uuid, runbook, screen=screen, input_data=input_data)

    config = get_config()
    pc_ip = config["SERVER"]["pc_ip"]
    pc_port = config["SERVER"]["pc_port"]
    run_url = "https://{}:{}/console/#page/explore/calm/runs/{}?runbookId={}".format(pc_ip, pc_port, runlog_uuid, runbook_uuid)
    if not watch:
        screen.print_at("Runbook run url: {}".format(highlight_text(run_url)), 0, 0)
    screen.refresh()


def watch_runbook(runlog_uuid, runbook, screen, poll_interval=10, input_data={}):

    client = get_api_client()

    def poll_func():
        return client.runbook.list_runlogs(runlog_uuid)

    # following code block gets list of metaTask uuids and list of top level tasks uuid of runbook
    tasks = runbook['task_definition_list']
    main_task_reference = runbook['main_task_local_reference']['uuid']
    metatasks = []
    top_level_tasks = []
    for task in tasks:
        if task.get('type', '') == 'META':
            metatasks.append(task.get('uuid'))
        if task.get('uuid') == main_task_reference:
            task_list = task.get('child_tasks_local_reference_list', [])
            for t in task_list:
                top_level_tasks.append(t.get('uuid', ''))

    poll_action(poll_func, get_completion_func(screen), poll_interval=poll_interval, metatasks=metatasks, top_level_tasks=top_level_tasks, input_data=input_data, runlog_uuid=runlog_uuid)


def describe_runbook(obj, runbook_name):
    client = get_api_client()
    runbook = get_runbook(client, runbook_name, all=True)

    res, err = client.runbook.read(runbook["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    runbook = res.json()

    click.echo("\n----Runbook Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(runbook_name)
        + " (uuid: "
        + highlight_text(runbook["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(runbook["status"]["description"]))
    click.echo("Status: " + highlight_text(runbook["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(runbook["metadata"]["owner_reference"]["name"]), nl=False
    )
    project = runbook["metadata"].get("project_reference", {})
    click.echo(
        " Project: " + highlight_text(project.get("name", ""))
    )

    created_on = int(runbook["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    runbook_resources = runbook.get("status").get("resources", {})

    click.echo("Runbook :")
    runbook_dict = runbook_resources.get("runbook", {})
    main_task = runbook_dict.get("main_task_local_reference", {})
    click.echo("\tMainTask: {}".format(highlight_text(main_task.get("name", ""))))

    task_list = runbook_dict.get("task_definition_list", [])
    click.echo("\tTasks [{}]:".format(highlight_text(len(task_list))))
    for task in task_list:
        task_name = task.get("name", "")
        task_type = task.get("type", "")
        click.echo("\t\t{} ({})".format(highlight_text(task_name), highlight_text(task_type)))

    variable_types = [
        var.get("name", "")
        for var in runbook_dict.get("variable_list", [])
    ]
    click.echo("\tVariables [{}]:".format(highlight_text(len(variable_types))))
    click.echo("\t\t{}".format(highlight_text(", ".join(variable_types))))

    endpoint_types = [
        "{} ({})".format(ep.get("name", ""), ep.get("resources", {}).get("type", ""))
        for ep in runbook_resources.get("endpoint_definition_list", [])
    ]
    click.echo("Endpoints [{}]:".format(highlight_text(len(endpoint_types))))
    click.echo("\t{}".format(highlight_text(", ".join(endpoint_types))))

    credential_types = [
        "{} ({})".format(cred.get("name", ""), cred.get("type", ""))
        for cred in runbook_resources.get("credential_definition_list", [])
    ]
    click.echo("Credentials [{}]:".format(highlight_text(len(credential_types))))
    click.echo("\t{}".format(highlight_text(", ".join(credential_types))))


def delete_runbook(obj, runbook_names):

    client = get_api_client()

    for runbook_name in runbook_names:
        runbook = get_runbook(client, runbook_name)
        runbook_id = runbook["metadata"]["uuid"]
        res, err = client.runbook.delete(runbook_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        click.echo("Runbook {} deleted".format(runbook_name))


def poll_action(poll_func, completion_func, poll_interval=10, **kwargs):
    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 10 * 60
    count = 0
    while count < maxWait:
        # call status api
        res, err = poll_func()
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        (completed, msg) = completion_func(response, **kwargs)
        if completed:
            # click.echo(msg)
            if msg:
                return False
            break
        count += poll_interval
        time.sleep(poll_interval)
    return True
