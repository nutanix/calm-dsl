import json

from .entity import EntityType, Entity
from .validator import PropertyValidator

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
