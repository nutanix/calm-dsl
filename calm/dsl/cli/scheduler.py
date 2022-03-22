import sys
import json
import time
import calendar
import arrow
import click
from prettytable import PrettyTable
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


from calm.dsl.api import get_api_client
from calm.dsl.builtins import Job
from calm.dsl.builtins.models import job
from calm.dsl.cli import runbooks
from calm.dsl.cli import apps
from calm.dsl.config import get_context
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.tools import get_module_from_file

# from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from .utils import (
    Display,
    get_name_query,
    highlight_text,
    get_states_filter,
    import_var_from_file,
)
from .constants import JOBS, JOBINSTANCES, SYSTEM_ACTIONS

LOG = get_logging_handle(__name__)


def create_job_command(job_file, name, description, force):
    """Creates a job in scheduler"""

    # if job_file.endswith(".json"):
    #     res, err = create_job_from_json(
    #         client, job_file, name=name, description=description, force_create=force
    #     )
    if job_file.endswith(".py"):
        res, err = create_job_from_dsl(
            job_file, name=name, description=description, force_create=force
        )
    else:
        LOG.error("Unknown file format {}".format(job_file))
        return

    if err:
        LOG.error(err["error"])
        return err["error"]

    job = res.json()

    job_uuid = job["metadata"]["uuid"]
    job_name = job["metadata"]["name"]
    job_state = job["resources"]["state"]
    LOG.debug("Job {} has uuid: {}".format(job_name, job_uuid))

    if job_state != "ACTIVE":
        msg_list = job.get("resources").get("message_list", [])
        if not msg_list:
            LOG.error("Job {} created with errors.".format(job_name))
            LOG.debug(json.dumps(job))
            return job

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Job {} created with {} error(s): {}".format(job_name, len(msg_list), msgs)
        )
        return job

    LOG.info("Job {} created successfully.".format(job_name))
    return job


#
# def create_job_from_json(
#     client, path_to_json, name=None, description=None, force_create=False
# ):
#
#     runbook_payload = json.loads(open(path_to_json, "r").read())
#     return create_runbook(
#         client,
#         runbook_payload,
#         name=name,
#         description=description,
#         force_create=force_create,
#     )


def get_job_module_from_file(job_file):
    """Returns Job module given a user job dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_job", job_file)


def get_job_class_from_module(user_bp_module):
    """Returns Job class given a module"""

    UserJob = None
    for item in dir(user_bp_module):
        obj = getattr(user_bp_module, item)
        if isinstance(obj, (type(Job))):
            if obj.__bases__[0] == Job:
                UserJob = obj

    return UserJob


def create_job_from_dsl(job_file, name=None, description=None, force_create=False):

    job_payload = compile_job(job_file)
    if job_payload is None:
        err_msg = "User job not found in {}".format(job_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_job(
        job_payload,
        name=name,
        description=description,
        force_create=force_create,
    )


def create_job(job_payload, name=None, description=None, force_create=False):

    if name:
        job_payload["resources"]["name"] = name
        job_payload["metadata"]["name"] = name

    if description:
        job_payload["resources"]["description"] = description

    client = get_api_client()
    return client.job.create(job_payload)


def compile_job(job_file):
    """returns compiled payload from dsl file"""

    # metadata_payload = get_metadata_payload(job_file)

    user_job_module = get_job_module_from_file(job_file)
    UserJob = get_job_class_from_module(user_job_module)
    if UserJob is None:
        LOG.error("Job not found in {}".format(job_file))
        return

    # create job payload
    job_payload = {
        "resources": UserJob.get_dict(),
        "metadata": {
            "name": UserJob.get_dict()["name"],
            "kind": "job",
        },
        "api_version": "3.0",
    }

    # if "project_reference" in metadata_payload:
    #     # Read metadata payload and set project reference
    #     job_payload["metadata"]["project_reference"] = metadata_payload[
    #         "project_reference"
    #     ]
    # else:
    # Read project name and uuid from config and set in job payload
    ContextObj = get_context()
    project_config = ContextObj.get_project_config()
    project_name = project_config["name"]
    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=project_name
    )

    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit("Project not found.")

    project_uuid = project_cache_data.get("uuid", "")
    job_payload["metadata"]["project_reference"] = {
        "kind": "project",
        "uuid": project_uuid,
        "name": project_name,
    }

    executable_type = job_payload["resources"]["executable"].get("entity").get("type")
    project_uuid = job_payload["metadata"]["project_reference"].get("uuid")
    project_name = job_payload["metadata"]["project_reference"].get("name")
    executable_uuid = job_payload["resources"]["executable"].get("entity").get("uuid")

    if executable_type == "app":
        # Get app uuid from name
        client = get_api_client()
        res, err = client.application.read(executable_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(err["error"])

        app = res.json()

        # Check if project uuid in config is same as project uuid of the app
        if app["metadata"]["project_reference"]["uuid"] != project_uuid:
            application_name = app["metadata"]["name"]

            LOG.error(
                "Application {} does not belong to project {}.".format(
                    application_name, project_name
                )
            )
            sys.exit(
                "Application {} does not belong to project {}.".format(
                    application_name, project_name
                )
            )
    elif executable_type == "runbook":
        client = get_api_client()
        res, err = client.runbook.read(executable_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(err["error"])

        runbook = res.json()

        # Check if project uuid in config is same as project uuid of the runbook
        if runbook["metadata"]["project_reference"]["uuid"] != project_uuid:
            runbook_name = runbook["metadata"]["name"]
            LOG.error(
                "Runbook '{}' does not belong to project '{}'.".format(
                    runbook_name, project_name
                )
            )
            sys.exit(
                "Runbook '{}' does not belong to project '{}'.".format(
                    runbook_name, project_name
                )
            )

    return job_payload


def get_job(client, name, all=False):

    # find job
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";deleted==FALSE"

    res, err = client.job.list(params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(err["error"])

    response = res.json()
    entities = response.get("entities", None)
    job_data = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one job found - {}".format(entities))

        LOG.info("Job {} found ".format(name))
        job_data = entities[0]
    else:
        raise Exception("No job found with name {} found".format(name))
    return job_data


def describe_job_command(job_name, out):
    """Displays job data"""
    client = get_api_client()
    job_get_res = get_job(client, job_name, all=True)

    res, err = client.job.read(job_get_res["metadata"]["uuid"])

    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(err["error"])

    job_response = res.json()

    if out == "json":
        job_response.pop("status", None)
        click.echo(json.dumps(job_response, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Job Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(job_response["resources"]["name"])
        + " (uuid: "
        + highlight_text(job_response["metadata"]["uuid"])
        + " (project: "
        + highlight_text(job_response["metadata"]["project_reference"]["name"])
        + ")"
    )

    description = job_response["resources"].get("description", "")
    click.echo("Description: " + highlight_text(description))

    schedule_type = job_response["resources"]["type"]
    click.echo("Status: " + highlight_text(job_response["resources"]["state"]))

    owner = job_response["metadata"]["owner_reference"]["name"]
    click.echo("Owner: " + highlight_text(owner))

    created_on = int(job_response["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    last_updated = int(job_response["metadata"]["last_update_time"]) // 1000000
    past = arrow.get(last_updated).humanize()
    click.echo(
        "Last Updated: {} ({})\n".format(
            highlight_text(time.ctime(last_updated)), highlight_text(past)
        )
    )

    message_list = job_response["resources"].get("message_list", "")
    messages = []
    if len(message_list) != 0:
        for message in message_list:
            messages.append(message)

    if len(messages) > 0:
        click.echo("----Errors----")
        click.echo("Messages:")
        for message in messages:
            click.echo(
                highlight_text(message.get("reason", ""))
                + " for attribute "
                + highlight_text(message.get("details").get("attribute_name"))
                + " ."
                + highlight_text(message.get("message", ""))
            )
        click.echo("")

    executable_type = job_response["resources"]["executable"]["entity"]["type"]

    click.echo("--Schedule Info--")

    click.echo("Schedule Type: " + highlight_text(schedule_type))
    time_zone = job_response["resources"]["schedule_info"]["time_zone"]
    click.echo("Time Zone: " + highlight_text(time_zone))

    if schedule_type == "ONE-TIME":
        start_time = int(job_response["resources"]["schedule_info"]["execution_time"])
        past = arrow.get(start_time).humanize()
        click.echo(
            "Starts On: {} ({})".format(
                highlight_text(time.ctime(start_time)), highlight_text(past)
            )
        )

    elif schedule_type == "RECURRING":
        start_time = int(job_response["resources"]["schedule_info"]["start_time"])
        past = arrow.get(start_time).humanize()
        click.echo(
            "Starts On: {} ({})".format(
                highlight_text(time.ctime(start_time)), highlight_text(past)
            )
        )

        expiry_time = job_response["resources"]["schedule_info"].get("expiry_time", "")
        if expiry_time == "":
            click.echo("Ends: {}".format(highlight_text("Never")))
        else:
            past = arrow.get(expiry_time).humanize()
            click.echo(
                "Ends On: {} ({})".format(
                    highlight_text(time.ctime(int(expiry_time))), highlight_text(past)
                )
            )

        schedule = job_response["resources"]["schedule_info"]["schedule"]
        click.echo("Schedule: {}".format(highlight_text(schedule)))

    next_execution_time = int(job_response["resources"]["next_execution_time"])
    past = arrow.get(next_execution_time).humanize()
    click.echo(
        "Next Execution Time: {} ({})\n".format(
            highlight_text(time.ctime(next_execution_time)), highlight_text(past)
        )
    )
    if executable_type == "runbook":
        runbook_uuid = job_response["resources"]["executable"]["entity"]["uuid"]
        res, err = client.runbook.read(runbook_uuid)
        runbook = res.json()

        msg_list = runbook.get("message_list", [])
        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        click.echo("--Executable Info--")

        click.echo("Type: " + highlight_text(executable_type))

        # If runbook is not found
        if len(msg_list) != 0 or len(msgs) != 0:
            click.echo(msgs)

        else:
            click.echo(
                "Name: "
                + highlight_text(runbook["metadata"]["name"])
                + " (uuid: "
                + highlight_text(runbook["metadata"]["uuid"])
                + ")"
            )

            variable_list_string = job_response["resources"]["executable"]["action"][
                "spec"
            ].get("payload", "")
            endpoint_name = ""
            endpoint_uuid = ""
            if variable_list_string != "":
                variable_list = json.loads(variable_list_string)
                endpoint_target_reference = variable_list.get("spec").get(
                    "default_target_reference"
                )
                if endpoint_target_reference is not None:
                    endpoint_name = endpoint_target_reference.get("name", "")
                    endpoint_uuid = endpoint_target_reference.get("uuid", "")

                variable_list = variable_list["spec"]["args"]

                click.echo("Runbook :")

                variable_types = []

                for var in variable_list:
                    var_name = var.get("name")
                    var_value = var.get("value", "")
                    variable_types.append(
                        "Name: " + var_name + " | " + "Value: " + var_value
                    )

                click.echo(
                    "\tVariables [{}]:".format(highlight_text(len(variable_types)))
                )
                click.echo("\t\t{}\n".format(highlight_text(", ".join(variable_types))))

                click.echo(
                    "Default Endpoint Target: "
                    + highlight_text(endpoint_name)
                    + " (uuid: "
                    + highlight_text(endpoint_uuid)
                    + ")"
                )
    elif executable_type == "app":
        click.echo("--Executable Info--")

        app_uuid = job_response["resources"]["executable"]["entity"]["uuid"]
        res, err = client.application.read(app_uuid)
        application = res.json()

        click.echo("Type: " + highlight_text(executable_type.upper()))
        click.echo(
            "Application Name: " + highlight_text(application["metadata"]["name"])
        )
        app_spec = application["spec"]
        calm_action_uuid = job_response["resources"]["executable"]["action"]["spec"][
            "uuid"
        ]
        action_payload = next(
            (
                action
                for action in app_spec["resources"]["action_list"]
                if action["uuid"] == calm_action_uuid
            ),
            None,
        )
        click.echo(
            "Application Action: " + highlight_text(action_payload.get("name", ""))
        )
        action_args = apps.get_action_runtime_args(
            app_uuid=app_uuid,
            action_payload=action_payload,
            patch_editables=False,
            runtime_params_file=False,
        )
        if not action_payload:
            LOG.error("No action found")
            sys.exit(-1)

        if len(action_args) > 0:
            variable_types = []

            for var in action_args:
                var_name = var.get("name")
                var_value = var.get("value", "")
                variable_types.append(
                    "Name: " + var_name + " | " + "Value: " + var_value
                )

            click.echo("\tVariables [{}]:".format(highlight_text(len(variable_types))))
            click.echo("\t\t{}\n".format(highlight_text(", ".join(variable_types))))


def get_job_list_command(name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"

    if all_items:
        filter_query += get_states_filter(JOBS.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.job.list(params=params)

    if err:
        LOG.warning("Cannot fetch jobs.")
        return

    json_rows = res.json().get("entities", "")

    if not json_rows:
        click.echo(highlight_text("No jobs found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["resources"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        # "DESCRIPTION",
        "PROJECT",
        "STATE",
        "TYPE",
        # "EXECUTION HISTORY",
        "CREATED BY",
        # "LAST EXECUTED AT",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["resources"]
        metadata = _row["metadata"]

        created_by = metadata.get("owner_reference", {}).get("name", "-")
        description = row.get("description", "-")
        # last_run = int(row.get("last_run_time", 0)) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        project = metadata.get("project_reference", {}).get("name", "")
        # total_runs = int(row.get("run_count", 0)) + int(row.get("running_runs", 0))

        table.add_row(
            [
                highlight_text(row["name"]),
                # highlight_text(description),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(row["type"]),
                # highlight_text(total_runs if total_runs else "-"),
                highlight_text(created_by),
                # "{}".format(arrow.get(last_run).humanize()) if last_run else "-",
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)
    return table


def get_job_instances_command(job_name, out, filter_by, limit, offset, all_items):
    """Displays job instance data"""
    client = get_api_client()
    job_get_res = get_job(client, job_name, all=True)

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"

    if all_items:
        filter_query += get_states_filter(JOBINSTANCES.STATES)

    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.job.instances(job_get_res["metadata"]["uuid"], params=params)

    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(err["error"])

    json_rows = res.json().get("entities", "")

    if not json_rows:
        click.echo(highlight_text("No job instances found !!!\n"))
        LOG.debug("response:{}".format(res.json()))
        return "[]"

    if out == "json":
        click.echo(json.dumps(json_rows, indent=4, separators=(",", ": ")))
        return json.dumps(json_rows, indent=4)

    click.echo("\nJob Name: {}\n".format(highlight_text(job_name)))

    click.echo("--Job Instances List--\n")

    table = PrettyTable()
    table.field_names = [
        "STATE",
        "SCHEDULED TIME",
        "START TIME",
        "END TIME",
        "CREATED",
        "REASON",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["resources"]
        metadata = _row["metadata"]

        start_timestamp = ""
        past_start_time_output = "-"
        start_time = int(row["start_time"])

        reason = row.get("reason", "-")

        if start_time != 0:
            start_timestamp = time.ctime(start_time)
            past_start_time = arrow.get(start_time).humanize()
            past_start_time_output = " ({})".format(past_start_time)

        scheduled_time = int(row["scheduled_time"])
        past_scheduled_time = arrow.get(scheduled_time).humanize()

        creation_time = int(metadata["creation_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["state"]),
                highlight_text(
                    str(time.ctime(scheduled_time))
                    + " ({})".format(past_scheduled_time)
                ),
                highlight_text(str(start_timestamp) + past_start_time_output),
                highlight_text("-"),
                "{}".format(arrow.get(creation_time).humanize()),
                highlight_text(reason),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def delete_job(job_names):
    """Delete jobs"""
    client = get_api_client()

    for job_name in job_names:

        job_get_res = get_job(client, job_name, all=True)

        job_uuid = job_get_res["metadata"]["uuid"]

        _, err = client.job.delete(job_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)
        LOG.info("Job {} deleted".format(job_name))
