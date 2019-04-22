import uuid

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


def _task_create(**kwargs):
    name = getattr(TaskType, "__schema_name__") + '_' + str(uuid.uuid4())[:8]
    name = kwargs.get('name', kwargs.get('__name__', name))
    bases = (Task,)
    return TaskType(name, bases, kwargs)


def exec_ssh(script, name=None):

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
    if name is not None:
        kwargs["name"] = name

    return _task_create(**kwargs)


def dag(**kwargs):

    # This follows UI naming convention for runbooks
    name = str(uuid.uuid4())[:8] + '_dag'
    name = kwargs.get('name', kwargs.get('__name__', name))
    new_kwargs = kwargs.copy()
    new_kwargs['name'] = name

    return _task_create(**new_kwargs)
