from .entity import EntityType, Entity
from .validator import PropertyValidator


# Task


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_task"


class TaskValidator(PropertyValidator, openapi_type="app_task"):
    __default__ = None
    __kind__ = TaskType


def _task(**kwargs):
    name = getattr(TaskType, "__schema_name__")
    bases = (Entity,)
    return TaskType(name, bases, kwargs)


Task = _task()


def exec_ssh(script):

    kwargs = {
        "type": "EXEC",
        # "timeout_secs": "0", # TODO - fix class creation params
        # "retries": "0",
        # "state": "ACTIVE",
        "attrs": {
            "script_type": "sh",
            "script": script,
            "login_credential_local_reference": {
                "kind": "app_credential",
                "name": "Credential",  # TODO
            },
        },
    }

    return _task(**kwargs)

def dag(**kwargs):
    return _task(**kwargs)
