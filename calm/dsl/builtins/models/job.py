import json
import sys
import click
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from .entity import EntityType, Entity
from .validator import PropertyValidator

from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .constants import SYSTEM_ACTIONS

LOG = get_logging_handle(__name__)


# # Job Schedule Info
class JobSchedule(EntityType):
    __schema_name__ = "JobScheduleInfo"
    __openapi_type__ = "job_schedule_info"

    def compile(cls):
        cdict = super().compile()
        if cdict["execution_time"] != "":
            cdict.pop("schedule", None)
            cdict.pop("expiry_time", None)
            cdict.pop("start_time", None)
        else:
            cdict.pop("execution_time", None)
        return cdict


class JobScheduleValidator(PropertyValidator, openapi_type="job_schedule_info"):
    __default__ = None
    __kind__ = JobSchedule


def _jobschedule_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return JobSchedule(name, bases, kwargs)


JobScheduleInfo = _jobschedule_payload()

# Job Executable
class JobExecutable(EntityType):
    __schema_name__ = "JobExecutable"
    __openapi_type__ = "executable_resources"

    def compile(cls):
        cdict = super().compile()
        if cdict.get("action").get("type") == "RUNBOOK_RUN":
            cdict["action"]["spec"].pop("uuid", None)

        return cdict


class JobExecuableValidator(PropertyValidator, openapi_type="executable_resources"):
    __default__ = None
    __kind__ = JobExecutable


def _jobexecutable_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return JobExecutable(name, bases, kwargs)


JobExec = _jobexecutable_payload()


def _create_job_executable_payload(
    entity_type, entity_uuid, action_type, payload, action_uuid=None
):

    payload = {
        "entity": {
            "type": entity_type,
            "uuid": entity_uuid,
        },
        "action": {
            "type": action_type,
            "spec": {"payload": str(json.dumps(payload))},
        },
    }

    if (
        action_type == "APP_ACTION_RUN"
        or action_type == "APP_ACTION_DELETE"
        or action_type == "APP_ACTION_SOFT_DELETE"
    ):
        payload["action"]["spec"]["uuid"] = action_uuid

    return _jobexecutable_payload(**payload)


# def _create_job_executable_payload_for_app_action(
#     entity_type, entity_uuid, action_type, action_uuid, payload
# ):
#
#     payload = {
#         "entity": {
#             "type": entity_type,
#             "uuid": entity_uuid,
#         },
#         "action": {
#             "type": action_type,
#             "spec": {
#                 "uuid": action_uuid,
#                 "payload": str(json.dumps(payload))
#             },
#         },
#     }
#
#     return _jobexecutable_payload(**payload)


# create payload for One Time job
def _create_one_time_job_schedule_payload(execution_time, time_zone):

    payload = {"execution_time": str(execution_time), "time_zone": time_zone}

    return _jobschedule_payload(**payload)


# create payload for recurring job
def _create_recurring_job_schedule_payload(
    schedule, expiry_time, start_time, time_zone
):

    payload = {
        "schedule": schedule,
        "expiry_time": str(expiry_time),
        "start_time": str(start_time),
        "time_zone": str(time_zone),
    }

    return _jobschedule_payload(**payload)


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


# Job
class JobType(EntityType):
    __schema_name__ = "Job"
    __openapi_type__ = "scheduler_job"

    def compile(cls):
        cdict = super().compile()
        cdict["state"] = "ACTIVE"
        cdict["skip_concurrent_execution"] = False

        # Setting value of type based on execution_time present in schedule_info or not
        if cdict["schedule_info"].execution_time != "":
            cdict["type"] = "ONE-TIME"
        else:
            cdict["type"] = "RECURRING"

        return cdict


class JobValidator(PropertyValidator, openapi_type="scheduler_job"):
    __default__ = None
    __kind__ = JobType


def _job_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return JobType(name, bases, kwargs)


Job = _job_payload()


# Interfaces exposed to users


def patch_runbook_runtime_editables(client, runbook):

    from calm.dsl.cli import runbooks

    args = []
    variable_list = runbook["spec"]["resources"]["runbook"].get("variable_list", [])
    for variable in variable_list:
        if variable.get("editables", {}).get("value", False):
            options = variable.get("options", {})
            choices = options.get("choices", [])
            if choices:
                click.echo("Choose from given choices: ")
                for choice in choices:
                    click.echo("\t{}".format(highlight_text(repr(choice))))

            default_val = variable.get("value", "")
            is_secret = variable.get("type") == "SECRET"

            new_val = click.prompt(
                "Value for variable '{}' [{}]".format(
                    variable["name"],
                    highlight_text(default_val if not is_secret else "*****"),
                ),
                default=default_val,
                show_default=False,
                hide_input=is_secret,
                type=click.Choice(choices) if choices else type(default_val),
                show_choices=False,
            )
            if new_val:
                args.append(
                    {
                        "name": variable.get("name"),
                        "value": type(variable.get("value", ""))(new_val),
                    }
                )

    for arg in args:
        for variable in variable_list:
            if variable["name"] == arg["name"]:
                variable["value"] = arg["value"]

    payload = {"spec": {"args": variable_list}}

    default_target = (
        runbook["spec"]["resources"]
        .get("default_target_reference", {})
        .get("name", None)
    )
    target = input(
        "Endpoint target for the Runbook Run (default target={}): ".format(
            default_target
        )
    )
    if target == "":
        target = default_target
    if target:
        endpoint = runbooks.get_endpoint(client, target)
        endpoint_id = endpoint.get("metadata", {}).get("uuid", "")
        payload["spec"]["default_target_reference"] = {
            "kind": "app_endpoint",
            "uuid": endpoint_id,
            "name": target,
        }
    return payload


def exec_runbook(runbook_name, patch_editables=True):
    # Get runbook uuid  from name

    from calm.dsl.cli import runbooks

    client = get_api_client()
    runbook = runbooks.get_runbook(client, runbook_name, all=True)
    res, err = client.runbook.read(runbook["metadata"]["uuid"])
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(err["error"])

    runbook = res.json()
    runbook_uuid = runbook["metadata"]["uuid"]
    if not patch_editables:
        payload = {}
    else:
        payload = patch_runbook_runtime_editables(client, runbook)
    return _create_job_executable_payload(
        "runbook", runbook_uuid, "RUNBOOK_RUN", payload, None
    )


def exec_app_action(
    app_name, action_name, patch_editables=True, runtime_params_file=False
):
    from calm.dsl.cli import apps

    # Get app uuid  from name
    client = get_api_client()
    app = apps._get_app(client, app_name, all=True)
    res, err = client.application.read(app["metadata"]["uuid"])
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(err["error"])

    app = res.json()
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

    action_args = apps.get_action_runtime_args(
        app_uuid=app_id,
        action_payload=action_payload,
        patch_editables=patch_editables,
        runtime_params_file=runtime_params_file,
    )

    action_id = action_payload["uuid"]

    if action_name.lower() == SYSTEM_ACTIONS.CREATE:
        click.echo(
            "The Create Action is triggered automatically when you deploy a blueprint. It cannot be run separately."
        )
        return
    if action_name.lower() == SYSTEM_ACTIONS.DELETE:
        return _create_job_executable_payload(
            "app", app_id, "APP_ACTION_DELETE", app, action_id
        )
    if action_name.lower() == SYSTEM_ACTIONS.SOFT_DELETE:
        return _create_job_executable_payload(
            "app", app_id, "APP_ACTION_SOFT_DELETE", app, action_id
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
                action_args.append(apps.get_snapshot_name_arg(config, task["uuid"]))
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
                    apps.get_recovery_point_group_arg(
                        config, task["uuid"], res.json()["entities"]
                    )
                )

    app["spec"] = {
        "args": action_args,
        "target_kind": "Application",
        "target_uuid": app_id,
    }

    return _create_job_executable_payload(
        "app", app_id, "APP_ACTION_RUN", app, action_id
    )


def set_one_time_schedule_info(start_time, time_zone="UTC"):
    # Get User timezone
    user_tz = ZoneInfo(time_zone)
    # Convert datetime string to datetime object
    datetime_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    # Append timezone to datetime object
    datetime_obj_with_tz = datetime(
        datetime_obj.year,
        datetime_obj.month,
        datetime_obj.day,
        datetime_obj.hour,
        datetime_obj.minute,
        datetime_obj.second,
        tzinfo=user_tz,
    )
    # Convert to Epoch
    seconds_since_epoch = int(datetime_obj_with_tz.timestamp())

    return _create_one_time_job_schedule_payload(seconds_since_epoch, time_zone)


def set_recurring_schedule_info(schedule, start_time, expiry_time, time_zone="UTC"):
    # Get User timezone
    user_tz = ZoneInfo(time_zone)
    # Convert datetime string to datetime object
    datetime_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    # Append timezone to datetime object
    datetime_obj_with_tz = datetime(
        datetime_obj.year,
        datetime_obj.month,
        datetime_obj.day,
        datetime_obj.hour,
        datetime_obj.minute,
        datetime_obj.second,
        tzinfo=user_tz,
    )
    # Convert to Epoch
    seconds_since_epoch_start_time = int(datetime_obj_with_tz.timestamp())

    datetime_obj = datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
    datetime_obj_with_tz = datetime(
        datetime_obj.year,
        datetime_obj.month,
        datetime_obj.day,
        datetime_obj.hour,
        datetime_obj.minute,
        datetime_obj.second,
        tzinfo=user_tz,
    )
    seconds_since_epoch_expiry_time = int(datetime_obj_with_tz.timestamp())

    return _create_recurring_job_schedule_payload(
        schedule,
        seconds_since_epoch_expiry_time,
        seconds_since_epoch_start_time,
        time_zone,
    )


class JobScheduler:
    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        runbook = exec_runbook
        app_action = exec_app_action

    class ScheduleInfo:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        oneTime = set_one_time_schedule_info
        recurring = set_recurring_schedule_info
